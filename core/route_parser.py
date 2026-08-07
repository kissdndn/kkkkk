# -*- coding: utf-8 -*-
"""
路由表解析器

从三台大核心交换机导出的路由表文件中提取有效路由，
构建 IP→区域 的最长前缀匹配索引。

自动处理:
  - 空格分隔的文本/CSV格式
  - 表头、空行、分隔线过滤
  - 互联端口丢弃
  - 非关注区域丢弃
  - 多设备路由合并去重
"""

import ipaddress
import os
import glob
import re
from collections import defaultdict


class RouteTableParser:
    """路由表解析器"""

    def __init__(self, port_zone_map, focus_zones):
        self.port_zone_map = port_zone_map
        self.focus_zones = focus_zones
        self.routes = []      # [(network_obj, zone, raw_line, source_file)]
        self.stats = {}       # 每台设备的统计

    def load_from_directory(self, directory, pattern='*.csv'):
        """
        从目录中加载所有路由表文件

        Args:
            directory: 路由表文件存放目录
            pattern: 文件匹配模式，默认 '*.csv'
        """
        self.routes = []
        self.stats = {}

        search_path = os.path.join(directory, pattern)
        files = glob.glob(search_path)

        if not files:
            raise FileNotFoundError(f"未找到路由表文件: {search_path}")

        # 按修改时间排序（最新的优先，但所有文件都会读取）
        files.sort(key=os.path.getmtime, reverse=True)
        print(f"📁 发现 {len(files)} 个路由表文件")

        for filepath in files:
            filename = os.path.basename(filepath)
            print(f"\n📄 解析: {filename}")
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                count = self._parse_content(content, filename)
                print(f"   有效路由: {count} 条")
                if self.stats[filename].get('skipped'):
                    for reason, cnt in self.stats[filename]['skipped'].items():
                        print(f"   跳过({reason}): {cnt} 条")
            except Exception as e:
                print(f"   ❌ 解析失败: {e}")

        # 去重：同一网段只保留一次
        seen = {}
        deduped = []
        for net_obj, zone, raw, filename in self.routes:
            net_str = str(net_obj)
            if net_str not in seen:
                seen[net_str] = (net_obj, zone, raw, filename)
                deduped.append((net_obj, zone, raw, filename))

        self.routes = deduped
        # 按前缀长度降序排列（最长匹配优先）
        self.routes.sort(key=lambda x: x[0].prefixlen, reverse=True)

        total = sum(s['valid'] for s in self.stats.values())
        print(f"\n✅ 合并去重后: {len(self.routes)} 条有效路由（原始共 {total} 条）")
        return len(self.routes)

    def _parse_content(self, content, filename):
        """解析单个文件内容"""
        lines = content.strip().split('\n')
        valid_count = 0
        skipped_reasons = defaultdict(int)

        for line in lines:
            line = line.strip()

            # 跳过空行
            if not line:
                continue

            # 跳过表头行（包含关键词且不以IP开头）
            if any(keyword in line for keyword in ['Destination', 'Mask', 'Proto', 'Interface']):
                if not re.match(r'^\d', line):
                    continue

            # 跳过分隔线
            if set(line) <= set('-=| '):
                continue

            # 按空格分割
            parts = line.split()
            if len(parts) < 3:
                skipped_reasons['列数不足'] += 1
                continue

            # 第一列必须是有效的CIDR格式
            dest = parts[0]
            if not re.match(r'^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$', dest):
                skipped_reasons['无效网段格式'] += 1
                continue

            try:
                net_obj = ipaddress.ip_network(dest, strict=False)
            except ValueError:
                skipped_reasons['无效网段格式'] += 1
                continue

            # 最后一列是出端口
            interface = parts[-1]

            # 查端口映射
            zone = self.port_zone_map.get(interface, "UNKNOWN")

            # 丢弃互联端口
            if zone == "INTERCONNECT":
                skipped_reasons['互联端口'] += 1
                continue

            # 丢弃非关注区域
            if zone not in self.focus_zones:
                skipped_reasons['非关注区域'] += 1
                continue

            self.routes.append((net_obj, zone, line, filename))
            valid_count += 1

        self.stats[filename] = {
            'valid': valid_count,
            'skipped': dict(skipped_reasons)
        }
        return valid_count

    def find_zone(self, ip_str):
        """
        查询IP所属区域（最长前缀匹配）

        Args:
            ip_str: IP地址字符串，如 "10.1.5.100"

        Returns:
            (zone_name, detail_info) 或 (None, error_message)
        """
        try:
            ip_obj = ipaddress.ip_address(ip_str)
        except ValueError:
            return None, f"无效的IP地址: {ip_str}"

        for net_obj, zone, raw, filename in self.routes:
            if ip_obj in net_obj:
                return zone, f"匹配路由: {raw} | 来源: {filename}"

        return None, f"IP {ip_str} 在路由表中无匹配，可能未发布路由"

    def get_zone_summary(self):
        """获取各区域路由统计"""
        summary = defaultdict(list)
        for net_obj, zone, raw, filename in self.routes:
            summary[zone].append(str(net_obj))

        result = {}
        for zone, nets in sorted(summary.items()):
            result[zone] = {
                'count': len(nets),
                'networks': nets
            }
        return result

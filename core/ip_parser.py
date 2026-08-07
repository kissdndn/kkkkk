# -*- coding: utf-8 -*-
"""
IP地址翻译模块

支持输入格式:
  - 单个IP: 10.1.5.100
  - CIDR网段: 10.1.0.0/24
  - IP范围: 10.1.5.1-10.1.5.5
  - 混合输入（逗号/换行/空格分隔）

输出: 统一转换为标准CIDR网段列表
"""

import ipaddress
import re


class IPParser:
    """IP地址解析器"""

    @staticmethod
    def parse(raw_input):
        """
        解析用户输入的IP/网段

        Args:
            raw_input: 字符串，支持单个IP、CIDR、IP范围、混合输入

        Returns:
            list of dict: [{type, value, networks, count}]
                type: 'single' | 'cidr' | 'range' | 'invalid'
                value: 原始输入值
                networks: [ipaddress.ip_network对象列表]
                count: 包含的IP数量
        """
        results = []
        # 按逗号、换行、空格分隔
        items = re.split(r'[,\s]+', raw_input.strip())
        items = [s.strip() for s in items if s.strip()]

        for item in items:
            item = item.strip()

            # 判断类型1: IP范围 (如 10.1.5.1-10.1.5.5)
            if '-' in item and '/' not in item:
                parts = item.split('-')
                if len(parts) == 2:
                    try:
                        start_ip = ipaddress.ip_address(parts[0].strip())
                        end_ip = ipaddress.ip_address(parts[1].strip())
                        # 使用summarize_address_range精确合并
                        networks = list(ipaddress.summarize_address_range(start_ip, end_ip))
                        count = sum(n.num_addresses for n in networks)
                        results.append({
                            'type': 'range',
                            'value': item,
                            'networks': networks,
                            'count': count
                        })
                        continue
                    except ValueError:
                        pass

            # 判断类型2: CIDR网段 (如 10.1.0.0/24)
            if '/' in item:
                try:
                    network = ipaddress.ip_network(item, strict=False)
                    results.append({
                        'type': 'cidr',
                        'value': item,
                        'networks': [network],
                        'count': network.num_addresses
                    })
                    continue
                except ValueError:
                    pass

            # 判断类型3: 单个IP
            try:
                ip = ipaddress.ip_address(item)
                network = ipaddress.ip_network(f"{item}/32")
                results.append({
                    'type': 'single',
                    'value': item,
                    'networks': [network],
                    'count': 1
                })
            except ValueError:
                results.append({
                    'type': 'invalid',
                    'value': item,
                    'error': '无法解析的IP格式',
                    'networks': [],
                    'count': 0
                })

        return results

    @staticmethod
    def to_firewall_entries(parsed_items):
        """
        将解析结果转换为防火墙配置条目列表

        Args:
            parsed_items: parse()的返回结果

        Returns:
            list of dict: [{ip, mask}]
                ip: 网段地址字符串
                mask: 子网掩码字符串
        """
        entries = []
        for item in parsed_items:
            if item['type'] == 'invalid':
                continue
            for network in item['networks']:
                entries.append({
                    'ip': str(network.network_address),
                    'mask': str(network.netmask)
                })
        return entries

    @staticmethod
    def get_all_ips(parsed_items):
        """获取所有解析结果中的IP地址列表（用于区域查询）"""
        ips = []
        for item in parsed_items:
            if item['type'] == 'invalid':
                continue
            for network in item['networks']:
                # 对于区域查询，使用网段的第一个可用IP
                hosts = list(network.hosts())
                if hosts:
                    ips.append(str(hosts[0]))
                else:
                    ips.append(str(network.network_address))
        return ips

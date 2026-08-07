#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络配置生成器 v1.0
银行内网环境：根据源/目的IP和端口自动生成网络设备配置脚本

功能:
  - 读取三台大核心交换机路由表（合并去重）
  - 自动识别IP所属区域（最长前缀匹配）
  - 根据策略矩阵判断路径和控制级别
  - 支持多厂商配置模板（华为/H3C/Cisco）
  - 模块化地址表达方式（明细/新建对象组/存量对象组）
  - 支持批量IP/端口输入（CIDR网段、IP范围）

使用:
  1. 将路由表文件放入 routing_tables/ 目录
  2. 修改 config/ 下的配置文件
  3. 运行: python main.py

作者: [你的名字]
日期: 2026-08-07
"""

import os
import sys
import yaml
from datetime import datetime

from core.ip_parser import IPParser
from core.route_parser import RouteTableParser
from core.path_engine import PathEngine
from core.config_gen import ConfigGenerator


def load_yaml(filepath):
    """加载YAML配置文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def print_header():
    print("=" * 60)
    print("🏦 银行内网网络配置生成器 v1.0")
    print("=" * 60)


def step1_input():
    """Step 1: 基础输入（标准化，仅用于判断流量走向）"""
    print("\n" + "-" * 60)
    print("📋 Step 1: 基础输入（支持单个IP / CIDR / IP范围）")
    print("-" * 60)
    print("💡 此处输入仅用于识别区域和路径")
    print("   后续可选择使用存量对象组替代明细地址\n")

    src_input = input("  源IP地址: ").strip()
    dst_input = input("  目的IP地址: ").strip()
    port_input = input("  目的端口: ").strip()
    protocol = input("  协议(tcp/udp/icmp) [默认tcp]: ").strip() or "tcp"
    desc = input("  业务描述(可选): ").strip()

    return {
        'src_input': src_input,
        'dst_input': dst_input,
        'port_input': port_input,
        'protocol': protocol,
        'desc': desc
    }


def step2_analyze(inputs, route_parser, path_engine):
    """Step 2: 路径分析"""
    print("\n" + "-" * 60)
    print("🛤️  Step 2: 路径分析")
    print("-" * 60)

    # 解析IP输入
    src_parsed = IPParser.parse(inputs['src_input'])
    dst_parsed = IPParser.parse(inputs['dst_input'])

    # 检查无效输入
    invalid_src = [p for p in src_parsed if p['type'] == 'invalid']
    invalid_dst = [p for p in dst_parsed if p['type'] == 'invalid']
    if invalid_src:
        print(f"❌ 源地址解析失败: {[p['value'] for p in invalid_src]}")
        return None
    if invalid_dst:
        print(f"❌ 目的地址解析失败: {[p['value'] for p in invalid_dst]}")
        return None

    # 获取用于区域查询的IP（取第一个可用IP）
    src_query_ips = IPParser.get_all_ips(src_parsed)
    dst_query_ips = IPParser.get_all_ips(dst_parsed)

    if not src_query_ips:
        print("❌ 无法从源地址中提取有效IP")
        return None
    if not dst_query_ips:
        print("❌ 无法从目的地址中提取有效IP")
        return None

    src_ip = src_query_ips[0]
    dst_ip = dst_query_ips[0]

    # 查询区域
    src_zone, src_info = route_parser.find_zone(src_ip)
    dst_zone, dst_info = route_parser.find_zone(dst_ip)

    print(f"\n📍 区域识别:")
    if src_zone:
        print(f"   源IP {src_ip} → {src_zone}")
    else:
        print(f"   ❌ 源IP {src_ip}: {src_info}")
        return None

    if dst_zone:
        print(f"   目的IP {dst_ip} → {dst_zone}")
    else:
        print(f"   ❌ 目的IP {dst_ip}: {dst_info}")
        return None

    # 路径分析
    scene, devices, desc, policy = path_engine.analyze(src_zone, dst_zone)

    print(f"\n📊 路径分析: {desc}")
    print(f"   场景: {scene}")
    print(f"   控制级别: {policy.get('control', 'N/A')}")
    print(f"   需要配置的设备:")
    for dev in devices:
        print(f"      • {dev['name']} ({dev.get('model', 'N/A')})")

    # 解析端口
    ports = [p.strip() for p in inputs['port_input'].split(',') if p.strip()]

    return {
        'src_zone': src_zone,
        'dst_zone': dst_zone,
        'src_parsed': src_parsed,
        'dst_parsed': dst_parsed,
        'ports': ports,
        'protocol': inputs['protocol'],
        'devices': devices,
        'scene': scene,
        'policy': policy
    }


def step3_addr_mode(path_data):
    """Step 3: 地址表达方式（每台设备独立选择）"""
    print("\n" + "-" * 60)
    print("🔧  Step 3: 地址表达方式")
    print("-" * 60)
    print("💡 为每台设备选择源/目的地址和端口的表达方式\n")

    device_configs = []

    for idx, dev in enumerate(path_data['devices']):
        print(f"\n📟 {dev['name']} ({dev.get('model', 'N/A')})")
        print(f"   方向: {dev.get('direction', 'N/A')}")

        is_fw = dev['type'] == 'firewall'

        # 源地址
        print(f"\n   [源地址表达]")
        print(f"      1. 明细IP(输入)")
        if is_fw:
            print(f"      2. 新建Address-set")
            print(f"      3. 存量Address-set")
        src_choice = input(f"   选择 [1]: ").strip() or "1"

        src_mode = 'detail'
        src_addrset_name = ''
        src_existing = ''
        if is_fw and src_choice == '2':
            src_mode = 'addrset'
            src_addrset_name = input(f"   新建Address-set名称 [ADDR_{dev['zone']}_SRC]: ").strip() or f"ADDR_{dev['zone']}_SRC"
        elif is_fw and src_choice == '3':
            src_mode = 'existing'
            src_existing = input(f"   存量Address-set名称: ").strip()

        # 目的地址
        print(f"\n   [目的地址表达]")
        print(f"      1. 明细IP(输入)")
        if is_fw:
            print(f"      2. 新建Address-set")
            print(f"      3. 存量Address-set")
        dst_choice = input(f"   选择 [1]: ").strip() or "1"

        dst_mode = 'detail'
        dst_addrset_name = ''
        dst_existing = ''
        if is_fw and dst_choice == '2':
            dst_mode = 'addrset'
            dst_addrset_name = input(f"   新建Address-set名称 [ADDR_{dev['zone']}_DST]: ").strip() or f"ADDR_{dev['zone']}_DST"
        elif is_fw and dst_choice == '3':
            dst_mode = 'existing'
            dst_existing = input(f"   存量Address-set名称: ").strip()

        # 端口（仅防火墙）
        port_mode = 'detail'
        port_svcset_name = ''
        port_existing = ''
        if is_fw:
            print(f"\n   [端口表达]")
            print(f"      1. 明细端口(输入)")
            print(f"      2. 新建Service-set")
            print(f"      3. 存量Service-set")
            port_choice = input(f"   选择 [1]: ").strip() or "1"

            if port_choice == '2':
                port_mode = 'svcset'
                port_svcset_name = input(f"   新建Service-set名称 [SVC_{dev['zone']}_PORT]: ").strip() or f"SVC_{dev['zone']}_PORT"
            elif port_choice == '3':
                port_mode = 'existing'
                port_existing = input(f"   存量Service-set名称: ").strip()

        device_configs.append({
            'device': dev,
            'src_mode': src_mode,
            'dst_mode': dst_mode,
            'port_mode': port_mode,
            'src_addrset_name': src_addrset_name,
            'dst_addrset_name': dst_addrset_name,
            'port_svcset_name': port_svcset_name,
            'src_existing': src_existing,
            'dst_existing': dst_existing,
            'port_existing': port_existing
        })

    return device_configs


def step4_naming(path_data):
    """Step 4: 命名规则"""
    print("\n" + "-" * 60)
    print("🏷️  Step 4: 命名规则")
    print("-" * 60)
    print("📋 命名规范: acl-{inside/outside}-{YYYYMMDD}-{序号}\n")

    today = datetime.now().strftime('%Y%m%d')
    seq = input(f"  起始序号 [001]: ").strip() or "001"

    print(f"\n📊 命名预览:")
    for dev in path_data['devices']:
        if dev['type'] == 'firewall':
            name = f"acl-{dev['acl_prefix']}-{today}-{seq}"
            print(f"   {dev['name']} ({dev['direction']}): {name}")

    return {'today': today, 'seq': seq}


def step5_generate(path_data, device_configs, naming, config_gen):
    """Step 5: 生成配置"""
    print("\n" + "-" * 60)
    print("⚙️  Step 5: 配置输出")
    print("=" * 60)

    src_entries = IPParser.to_firewall_entries(path_data['src_parsed'])
    dst_entries = IPParser.to_firewall_entries(path_data['dst_parsed'])

    for idx, cfg in enumerate(device_configs):
        dev = cfg['device']
        rule_name = f"acl-{dev['acl_prefix']}-{naming['today']}-{naming['seq']}"

        print(f"\n{'─' * 50}")
        print(f"📟 {dev['name']} ({dev.get('model', 'N/A')})")
        print(f"   {dev.get('direction', '')} | {rule_name}")
        print(f"{'─' * 50}")

        config = config_gen.generate(
            device=dev,
            src_entries=src_entries,
            dst_entries=dst_entries,
            ports=path_data['ports'],
            protocol=path_data['protocol'],
            rule_name=rule_name,
            src_mode=cfg['src_mode'],
            dst_mode=cfg['dst_mode'],
            port_mode=cfg['port_mode'],
            src_addrset_name=cfg['src_addrset_name'],
            dst_addrset_name=cfg['dst_addrset_name'],
            port_svcset_name=cfg['port_svcset_name'],
            src_existing=cfg['src_existing'],
            dst_existing=cfg['dst_existing'],
            port_existing=cfg['port_existing']
        )

        print(config)

    print(f"\n{'=' * 60}")
    print("✅ 配置生成完成")
    print("=" * 60)


def main():
    """主程序入口"""
    print_header()

    # 加载配置
    config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')

    port_map = load_yaml(os.path.join(config_dir, 'port_map.yaml'))['port_to_zone']

    # 初始化路由解析器
    from config.policy_matrix import FOCUS_ZONES
    route_parser = RouteTableParser(port_map, FOCUS_ZONES)

    # 加载路由表
    routing_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'routing_tables')
    try:
        route_parser.load_from_directory(routing_dir, '*.csv')
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        print(f"   请确保路由表文件已放置在: {os.path.abspath(routing_dir)}")
        return

    # 初始化路径引擎和配置生成器
    path_engine = PathEngine()
    config_gen = ConfigGenerator()

    # 执行5步流程
    inputs = step1_input()
    path_data = step2_analyze(inputs, route_parser, path_engine)

    if not path_data:
        print("\n❌ 路径分析失败，程序退出")
        return

    if path_data['scene'] == 'same_zone':
        print("\n⚠️ 同区域访问，配置核心交换机ACL")

    device_configs = step3_addr_mode(path_data)
    naming = step4_naming(path_data)
    step5_generate(path_data, device_configs, naming, config_gen)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
银行内网网络配置生成器 - Web 前端
Flask 应用入口
"""

import os
import sys
from flask import Flask, render_template, request, jsonify
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.ip_parser import IPParser
from core.route_parser import RouteTableParser
from core.path_engine import PathEngine
from core.config_gen import ConfigGenerator
from config.policy_matrix import POLICY_MATRIX, ZONES, FOCUS_ZONES
import yaml


app = Flask(__name__)
app.config['SECRET_KEY'] = 'bank-network-config-generator-2026'

# 全局变量存储路由表解析器
route_parser = None


def init_route_parser():
    """初始化路由表解析器"""
    global route_parser
    try:
        # 加载配置
        with open('config/port_map.yaml', 'r', encoding='utf-8') as f:
            port_map_data = yaml.safe_load(f)
        
        port_zone_map = port_map_data.get('port_to_zone', {})
        
        route_parser = RouteTableParser(port_zone_map, FOCUS_ZONES)
        
        # 尝试加载路由表
        routing_tables_dir = 'routing_tables'
        if os.path.exists(routing_tables_dir):
            route_parser.load_from_directory(routing_tables_dir)
        
        return True, "路由表加载成功"
    except Exception as e:
        return False, f"路由表加载失败：{str(e)}"


@app.route('/')
def index():
    """首页 - 基础输入"""
    return render_template('web/index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Step 2: 路径分析 API"""
    try:
        data = request.json
        src_input = data.get('src_ip', '')
        dst_input = data.get('dst_ip', '')
        port_input = data.get('port', '')
        protocol = data.get('protocol', 'tcp')
        desc = data.get('description', '')
        
        # 解析 IP
        src_parsed = IPParser.parse(src_input)
        dst_parsed = IPParser.parse(dst_input)
        
        # 检查无效输入
        invalid_src = [p for p in src_parsed if p['type'] == 'invalid']
        invalid_dst = [p for p in dst_parsed if p['type'] == 'invalid']
        
        if invalid_src:
            return jsonify({
                'success': False,
                'error': f"源地址解析失败：{[p['value'] for p in invalid_src]}"
            })
        
        if invalid_dst:
            return jsonify({
                'success': False,
                'error': f"目的地址解析失败：{[p['value'] for p in invalid_dst]}"
            })
        
        # 获取用于区域查询的 IP
        src_query_ips = IPParser.get_all_ips(src_parsed)
        dst_query_ips = IPParser.get_all_ips(dst_parsed)
        
        # 查询区域（如果有路由表）
        src_zone = None
        dst_zone = None
        src_detail = ""
        dst_detail = ""
        
        if route_parser and src_query_ips:
            src_zone, src_detail = route_parser.find_zone(src_query_ips[0])
        
        if route_parser and dst_query_ips:
            dst_zone, dst_detail = route_parser.find_zone(dst_query_ips[0])
        
        # 路径分析
        path_engine = PathEngine()
        scene_type, devices, description, policy_info = path_engine.analyze(src_zone, dst_zone)
        
        # 解析端口
        port_parts = port_input.split(',') if port_input else []
        
        return jsonify({
            'success': True,
            'src_parsed': {
                'input': src_input,
                'zones': [src_zone] if src_zone else ['未知'],
                'detail': src_detail,
                'ip_count': sum(p['count'] for p in src_parsed if p['type'] != 'invalid')
            },
            'dst_parsed': {
                'input': dst_input,
                'zones': [dst_zone] if dst_zone else ['未知'],
                'detail': dst_detail,
                'ip_count': sum(p['count'] for p in dst_parsed if p['type'] != 'invalid')
            },
            'port_input': port_input,
            'protocol': protocol,
            'description': desc,
            'scene_type': scene_type,
            'scene_description': description,
            'control_level': policy_info.get('control', '未知') if policy_info else '未知',
            'devices': devices,
            'policy_info': policy_info
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/generate', methods=['POST'])
def generate():
    """Step 5: 生成配置 API"""
    try:
        data = request.json
        
        # 基础信息
        src_entries_data = data.get('src_entries', [])
        dst_entries_data = data.get('dst_entries', [])
        ports = data.get('ports', [])
        protocol = data.get('protocol', 'tcp')
        global_rule_name = data.get('rule_name', '')
        
        # 转换地址条目格式
        src_entries = [{'ip': e['ip'], 'mask': e['mask']} for e in src_entries_data]
        dst_entries = [{'ip': e['ip'], 'mask': e['mask']} for e in dst_entries_data]
        
        # 设备配置模式
        devices_config = data.get('devices_config', [])
        
        results = []
        config_generator = ConfigGenerator()
        
        for dev_config in devices_config:
            device = dev_config['device']
            src_mode = dev_config.get('src_mode', 'detail')
            dst_mode = dev_config.get('dst_mode', 'detail')
            port_mode = dev_config.get('port_mode', 'detail')
            src_addrset_name = dev_config.get('src_addrset_name', '')
            dst_addrset_name = dev_config.get('dst_addrset_name', '')
            port_svcset_name = dev_config.get('port_svcset_name', '')
            src_existing = dev_config.get('src_existing', '')
            dst_existing = dev_config.get('dst_existing', '')
            port_existing = dev_config.get('port_existing', '')
            # 优先使用设备独立的策略名称，否则使用全局规则名称
            rule_name = dev_config.get('rule_name', global_rule_name)
            
            config = config_generator.generate(
                device=device,
                src_entries=src_entries,
                dst_entries=dst_entries,
                ports=ports,
                protocol=protocol,
                rule_name=rule_name,
                src_mode=src_mode,
                dst_mode=dst_mode,
                port_mode=port_mode,
                src_addrset_name=src_addrset_name,
                dst_addrset_name=dst_addrset_name,
                port_svcset_name=port_svcset_name,
                src_existing=src_existing,
                dst_existing=dst_existing,
                port_existing=port_existing
            )
            
            results.append({
                'device_name': device['name'],
                'device_type': device['type'],
                'vendor': device.get('vendor', ''),
                'direction': device.get('direction', ''),
                'config': config
            })
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/zones')
def get_zones():
    """获取区域列表"""
    return jsonify({
        'success': True,
        'zones': list(ZONES.keys()),
        'focus_zones': list(FOCUS_ZONES)
    })


if __name__ == '__main__':
    import yaml
    
    print("=" * 60)
    print("🏦 银行内网网络配置生成器 v1.0 - Web 版")
    print("=" * 60)
    
    # 初始化路由表
    success, msg = init_route_parser()
    if success:
        print(f"✅ {msg}")
    else:
        print(f"⚠️  {msg}")
    
    print("\n🌐 启动 Web 服务器...")
    print("   访问地址：http://localhost:5000")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

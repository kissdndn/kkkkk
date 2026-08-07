# -*- coding: utf-8 -*-
"""
配置生成器

根据设备类型、厂商、地址表达方式生成对应的配置脚本
"""

from jinja2 import Environment, FileSystemLoader
import os


class ConfigGenerator:
    """配置生成器"""

    def __init__(self, template_dir=None):
        if template_dir is None:
            template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates')
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def generate(self, device, src_entries, dst_entries, ports, protocol, rule_name, 
                 src_mode='detail', dst_mode='detail', port_mode='detail',
                 src_addrset_name='', dst_addrset_name='', port_svcset_name='',
                 src_existing='', dst_existing='', port_existing=''):
        """
        生成单台设备的配置

        Args:
            device: 设备信息字典
            src_entries: 源地址条目列表 [{ip, mask}]
            dst_entries: 目的地址条目列表 [{ip, mask}]
            ports: 端口列表
            protocol: 协议字符串
            rule_name: 规则名称
            src_mode: 'detail' | 'addrset' | 'existing'
            dst_mode: 'detail' | 'addrset' | 'existing'
            port_mode: 'detail' | 'svcset' | 'existing'
            src_addrset_name: 新建源Address-set名称
            dst_addrset_name: 新建目的Address-set名称
            port_svcset_name: 新建Service-set名称
            src_existing: 存量源Address-set名称
            dst_existing: 存量目的Address-set名称
            port_existing: 存量Service-set名称
        """
        vendor = device.get('vendor', '')
        dev_type = device.get('type', '')

        template_name = None
        if vendor == 'huawei' and dev_type == 'firewall':
            template_name = 'huawei_fw.j2'
        elif vendor == 'h3c' and dev_type == 'firewall':
            template_name = 'h3c_fw.j2'
        elif vendor == 'cisco' and dev_type == 'firewall':
            template_name = 'cisco_fw.j2'
        elif vendor == 'huawei' and dev_type == 'switch':
            template_name = 'huawei_sw.j2'
        elif vendor == 'h3c' and dev_type == 'switch':
            template_name = 'h3c_sw.j2'

        if not template_name:
            return f"# 未找到设备 {device['name']} ({vendor}/{dev_type}) 的模板"

        template = self.env.get_template(template_name)

        context = {
            'device': device,
            'src_entries': src_entries,
            'dst_entries': dst_entries,
            'ports': ports,
            'protocol': protocol,
            'rule_name': rule_name,
            'src_mode': src_mode,
            'dst_mode': dst_mode,
            'port_mode': port_mode,
            'src_addrset_name': src_addrset_name,
            'dst_addrset_name': dst_addrset_name,
            'port_svcset_name': port_svcset_name,
            'src_existing': src_existing,
            'dst_existing': dst_existing,
            'port_existing': port_existing,
        }

        return template.render(**context)

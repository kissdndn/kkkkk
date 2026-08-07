# -*- coding: utf-8 -*-
"""
路径决策引擎

根据源/目的区域判断访问场景，决定需要配置哪些设备
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.policy_matrix import POLICY_MATRIX, ZONES


class PathEngine:
    """路径决策引擎"""

    def analyze(self, src_zone, dst_zone):
        """
        分析访问路径

        Args:
            src_zone: 源区域名称
            dst_zone: 目的区域名称

        Returns:
            (scene_type, devices_to_config, description, policy_info)
            scene_type: 'cross_zone' | 'same_zone' | 'error'
        """
        if src_zone is None or dst_zone is None:
            return "error", [], "区域识别失败", {}

        policy = POLICY_MATRIX.get((src_zone, dst_zone))
        if not policy:
            return "error", [], f"未找到策略: {src_zone} → {dst_zone}", {}

        devices = []
        for dev_name in policy['devices']:
            zone = dev_name.replace('防火墙', '').replace('核心交换机', '')
            if '防火墙' in dev_name:
                is_src_fw = (zone == src_zone)
                devices.append({
                    'name': dev_name,
                    'type': 'firewall',
                    'zone': zone,
                    'vendor': ZONES[zone].get('firewall', {}).get('vendor') if zone in ZONES else None,
                    'model': ZONES[zone].get('firewall', {}).get('model') if zone in ZONES else None,
                    'direction': 'inside→outside' if is_src_fw else 'outside→inside',
                    'acl_prefix': 'inside' if is_src_fw else 'outside',
                    'is_src_fw': is_src_fw
                })
            else:
                devices.append({
                    'name': dev_name,
                    'type': 'switch',
                    'zone': zone,
                    'vendor': ZONES[zone].get('core_switch', {}).get('vendor') if zone in ZONES else None,
                    'model': ZONES[zone].get('core_switch', {}).get('model') if zone in ZONES else None,
                })

        return policy['scene'], devices, policy['note'], policy

# -*- coding: utf-8 -*-
"""
策略矩阵模块
根据源/目的区域决定控制级别和需要配置的设备

规则:
1. 同区域 → 核心交换机ACL（连总除外）
2. 涉及灾备 → 只在灾备防火墙配置（无论方向）
3. 涉及连总 → 只配置分行端防火墙（连总侧不生成）
4. 其他跨区域 → 两端防火墙都配置
5. 控制级别根据安全规范自动判断
"""

from collections import defaultdict

# 区域定义
ZONES = {
    "业务": {"level": 4, "role": "内部网络", "has_firewall": True, "has_acl": True},
    "OA": {"level": 3, "role": "内部网络", "has_firewall": True, "has_acl": True},
    "灾备": {"level": 3, "role": "内部网络", "has_firewall": True, "has_acl": True},
    "城域网": {"level": 2, "role": "内部边界", "has_firewall": True, "has_acl": True},
    "连总": {"level": 5, "role": "一级骨干网", "has_firewall": False, "has_acl": False},
    "外联": {"level": 1, "role": "外部边界", "has_firewall": True, "has_acl": True},
}

# 关注区域白名单
FOCUS_ZONES = {"业务", "OA", "城域网", "外联", "灾备", "连总"}


def build_policy_matrix():
    """构建完整的策略矩阵"""
    matrix = {}
    zone_names = list(ZONES.keys())

    for src in zone_names:
        for dst in zone_names:
            # 同区域
            if src == dst:
                if src == "连总":
                    matrix[(src, dst)] = {
                        "devices": [],
                        "control": "无",
                        "scene": "same_zone",
                        "note": "连总无ACL"
                    }
                else:
                    matrix[(src, dst)] = {
                        "devices": [f"{src}核心交换机"],
                        "control": "ACL",
                        "scene": "same_zone",
                        "note": f"{src}内部ACL"
                    }
                continue

            # 涉及灾备 → 只在灾备防火墙配置
            if src == "灾备" or dst == "灾备":
                matrix[(src, dst)] = {
                    "devices": ["灾备防火墙"],
                    "control": "普通",
                    "scene": "cross_zone",
                    "note": f"灾备特殊：无论{src}→{dst}，只在灾备防火墙配置"
                }
                continue

            # 涉及连总 → 只配置分行端防火墙
            if src == "连总" or dst == "连总":
                branch_zone = dst if src == "连总" else src
                control = "普通" if branch_zone == "城域网" else "严格"
                matrix[(src, dst)] = {
                    "devices": [f"{branch_zone}防火墙"],
                    "control": control,
                    "scene": "cross_zone",
                    "note": f"连总特殊：只配置分行端({branch_zone}防火墙)，总行端忽略"
                }
                continue

            # 其他跨区域
            src_level = ZONES[src]["level"]
            dst_level = ZONES[dst]["level"]

            # 判断控制级别
            if ZONES[src]["role"] == "外部边界":
                control = "严格"
            elif ZONES[src]["role"] == "内部边界" and ZONES[dst]["role"] == "内部网络":
                control = "严格"
            elif src_level < dst_level:
                control = "严格"
            elif src_level == dst_level:
                control = "严格"
            else:
                control = "普通"

            matrix[(src, dst)] = {
                "devices": [f"{src}防火墙", f"{dst}防火墙"],
                "control": control,
                "scene": "cross_zone",
                "note": f"{src}→{dst}: {control}控制"
            }

    return matrix


# 预构建策略矩阵
POLICY_MATRIX = build_policy_matrix()


def get_policy(src_zone, dst_zone):
    """获取指定源/目的区域的策略"""
    return POLICY_MATRIX.get((src_zone, dst_zone), None)


def get_zone_summary():
    """获取区域统计信息"""
    return ZONES

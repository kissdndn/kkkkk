#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
离线安装脚本

使用方式:
  1. 在外网机器上执行: python prepare_packages.py
  2. 将 packages/ 文件夹和本项目一起拷贝到内网
  3. 在内网执行: python install_offline.py
"""

import subprocess
import sys
import os

def install():
    print("=" * 60)
    print("📦 离线安装网络配置生成器依赖")
    print("=" * 60)

    packages_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'packages')

    if not os.path.exists(packages_dir):
        print(f"\n❌ 未找到 packages/ 目录")
        print(f"   请先在外网执行: python prepare_packages.py")
        print(f"   然后将 packages/ 文件夹拷贝到项目目录")
        return

    print(f"\n📁 从 {packages_dir} 安装依赖...")

    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install',
            '--no-index', '--find-links=' + packages_dir,
            '-r', 'requirements.txt'
        ])
        print("\n✅ 依赖安装完成")
        print("\n🚀 运行程序: python main.py")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 安装失败: {e}")
        print("   请检查 packages/ 目录是否包含所有依赖包")

if __name__ == '__main__':
    install()

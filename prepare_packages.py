#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
外网准备离线包脚本

使用方式:
  1. 在有互联网连接的机器上执行: python prepare_packages.py
  2. 等待下载完成
  3. 将 packages/ 文件夹和项目一起拷贝到内网
  4. 在内网执行: python install_offline.py
"""

import subprocess
import sys
import os

def prepare():
    print("=" * 60)
    print("📦 准备离线安装包")
    print("=" * 60)

    packages_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'packages')
    os.makedirs(packages_dir, exist_ok=True)

    print(f"\n📥 下载依赖包到 {packages_dir}/ ...")

    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'download',
            '-r', 'requirements.txt',
            '-d', packages_dir
        ])
        print("\n✅ 离线包准备完成")
        print(f"\n📁 请将 packages/ 文件夹拷贝到内网机器的项目目录下")
        print("   然后在内网执行: python install_offline.py")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 下载失败: {e}")

if __name__ == '__main__':
    prepare()

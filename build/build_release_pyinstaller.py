#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发布版本打包脚本
窗口版本，不包含控制台输出
"""

import os
import subprocess
import shutil
import site
import sys

# 项目根目录（相对路径，脚本位于build目录下）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

# 构建配置
BUILD_NAME = "GPXStudio"
BUILD_DIR = os.path.join(PROJECT_ROOT, "build", BUILD_NAME)
DIST_FILE = os.path.join(PROJECT_ROOT, "dist", f"{BUILD_NAME}.exe")

# 动态查找xyzservices包的位置
try:
    import xyzservices
    xyzservices_path = os.path.dirname(xyzservices.__file__)
    XYZ_SERVICES_DATA = os.path.join(xyzservices_path, "data")
except ImportError:
    # 如果无法导入，尝试从site-packages中查找
    site_packages = site.getsitepackages()
    XYZ_SERVICES_DATA = None
    for sp in site_packages:
        candidate_path = os.path.join(sp, "xyzservices", "data")
        if os.path.exists(candidate_path):
            XYZ_SERVICES_DATA = candidate_path
            break
    if not XYZ_SERVICES_DATA:
        # 如果仍然找不到，回退到相对路径（适用于开发环境）
        XYZ_SERVICES_DATA = os.path.join(PROJECT_ROOT, ".venv", "lib", "site-packages", "xyzservices", "data")


def main():
    print("[GPXStudio] 开始构建发布版本...")

    # 进入项目根目录
    os.chdir(PROJECT_ROOT)

    # 清理之前的构建文件
    if os.path.exists(BUILD_DIR):
        print(f"[GPXStudio] 清理之前的构建目录: {BUILD_DIR}")
        shutil.rmtree(BUILD_DIR)

    if os.path.exists(DIST_FILE):
        print(f"[GPXStudio] 删除之前的可执行文件: {DIST_FILE}")
        os.remove(DIST_FILE)

    # 执行PyInstaller命令构建发布版本
    print("[GPXStudio] 执行PyInstaller构建命令...")
    # 获取pyinstaller的完整路径
    pyinstaller_path = shutil.which('pyinstaller')
    if not pyinstaller_path:
        # 尝试从虚拟环境中查找
        pyinstaller_path = os.path.join(PROJECT_ROOT, '.venv', 'Scripts', 'pyinstaller.exe')
    print(f"[GPXStudio] 使用pyinstaller路径: {pyinstaller_path}")
    
    # 在Windows中，--add-data参数使用分号分隔，需要正确处理路径
    command = [
        pyinstaller_path,
        "--onefile",
        "--windowed",
        f"--name={BUILD_NAME}",
        "--add-data", "services/config/config;services/config/config",
        "--add-data", "ui;ui",
        "--add-data", "modules;modules",
        "--add-data", "services;services",
        "--add-data", "core;core",
        "--add-data", "app;app",
        "--add-data", f"{XYZ_SERVICES_DATA};xyzservices/data",
        "--hidden-import", "PyQt5.sip",
        "--hidden-import", "PyQt5.QtCore",
        "--hidden-import", "PyQt5.QtGui",
        "--hidden-import", "PyQt5.QtWidgets",
        "--hidden-import", "PyQt5.QtWebEngineWidgets",
        "--hidden-import", "PyQt5.QtWebEngineCore",
        "main.py"
    ]

    # 验证所有路径是否存在
    print("[GPXStudio] 验证路径是否存在...")
    paths_to_check = [
        "services/config/config",
        "ui",
        "modules",
        "services",
        "core",
        "app",
        XYZ_SERVICES_DATA,
        "main.py"
    ]
    
    for path in paths_to_check:
        if os.path.exists(path):
            print(f"[GPXStudio] ✅ 路径存在: {path}")
        else:
            print(f"[GPXStudio] ❌ 路径不存在: {path}")
    
    # 打印完整的命令
    print("[GPXStudio] 执行命令:")
    print(' '.join(command))

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )

        print("[GPXStudio] 发布版本构建成功！")
        print(f"[GPXStudio] 可执行文件位置: {DIST_FILE}")
        print("[GPXStudio] 构建完成！")
        input("按Enter键退出...")

    except subprocess.CalledProcessError as e:
        print("[GPXStudio] 发布版本构建失败！")
        print(f"[GPXStudio] 返回代码: {e.returncode}")
        print(f"[GPXStudio] 标准输出: {e.stdout}")
        print(f"[GPXStudio] 标准错误: {e.stderr}")
        input("按Enter键退出...")
        return 1
    except Exception as e:
        print("[GPXStudio] 发布版本构建失败！")
        print(f"[GPXStudio] 错误类型: {type(e).__name__}")
        print(f"[GPXStudio] 错误信息: {str(e)}")
        import traceback
        print(f"[GPXStudio] 堆栈跟踪: {traceback.format_exc()}")
        input("按Enter键退出...")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())

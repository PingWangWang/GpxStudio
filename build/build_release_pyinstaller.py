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

# 读取项目版本号
VERSION_FILE = os.path.join(PROJECT_ROOT, "src", "version.py")
with open(VERSION_FILE, "r", encoding="utf-8") as f:
    exec(f.read())

# 构建配置
BUILD_NAME = f"GPXStudio-{__version__}"
BUILD_DIR = os.path.join(PROJECT_ROOT, "build", BUILD_NAME)
DIST_FILE = os.path.join(PROJECT_ROOT, "dist", f"{BUILD_NAME}.exe")

# 虚拟环境配置
VENV_DIR = os.path.join(PROJECT_ROOT, ".venv")
REQUIREMENTS_FILE = os.path.join(PROJECT_ROOT, "requirements.txt")

# 声明全局变量，将在main函数中初始化
XYZ_SERVICES_DATA = None


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

    # 清理和重新创建虚拟环境
    print(f"[GPXStudio] 清理和重新创建虚拟环境...")
    print(f"[GPXStudio] 虚拟环境路径: {VENV_DIR}")
        # 删除现有的虚拟环境
    if os.path.exists(VENV_DIR):
        print(f"[GPXStudio] 删除现有的虚拟环境: {VENV_DIR}")
        shutil.rmtree(VENV_DIR)

    # 创建新的虚拟环境
    print("[GPXStudio] 创建新的虚拟环境...")
    venv_create_cmd = [sys.executable, "-m", "venv", VENV_DIR]
    result = subprocess.run(venv_create_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[GPXStudio] 错误：创建虚拟环境失败")
        print(f"[GPXStudio] 错误信息: {result.stderr}")
        return 1

    # 安装依赖包
    print("[GPXStudio] 安装项目依赖包...")
    pip_path = os.path.join(VENV_DIR, "Scripts", "pip.exe")
    install_cmd = [pip_path, "install", "-r", REQUIREMENTS_FILE]
    result = subprocess.run(install_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[GPXStudio] 错误：安装依赖包失败")
        print(f"[GPXStudio] 错误信息: {result.stderr}")
        return 1

    # 导入site模块
    import site

    # 更新sys.path以使用虚拟环境
    sys.path.insert(0, os.path.join(VENV_DIR, "lib", "site-packages"))

    # 刷新site-packages路径
    import importlib
    importlib.reload(site)

    # 确保使用新虚拟环境中的模块
    print("[GPXStudio] 更新Python路径，使用新的虚拟环境...")

    # 动态查找xyzservices包的位置（在新虚拟环境中）
    global XYZ_SERVICES_DATA
    print("[GPXStudio] 查找xyzservices包的位置...")
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
            XYZ_SERVICES_DATA = os.path.join(VENV_DIR, "lib", "site-packages", "xyzservices", "data")

    print(f"[GPXStudio] 使用xyzservices数据路径: {XYZ_SERVICES_DATA}")

    # 验证xyzservices路径是否存在
    if not os.path.exists(XYZ_SERVICES_DATA):
        print(f"[GPXStudio] ❌ xyzservices数据路径不存在: {XYZ_SERVICES_DATA}")
        return 1

    # 执行PyInstaller命令构建发布版本
    print("[GPXStudio] 执行PyInstaller构建命令...")
    # 使用系统的pyinstaller
    pyinstaller_path = "pyinstaller.exe"
    print(f"[GPXStudio] 使用pyinstaller路径: {pyinstaller_path}")

    # 在Windows中，--add-data参数使用分号分隔，需要正确处理路径
    command = [
        pyinstaller_path,
        "--onefile",
        "--windowed",
        f"--name={BUILD_NAME}",
        "--add-data", "src/services/config/config;services/config/config",
        "--add-data", "src/ui;ui",
        "--add-data", "src/modules;modules",
        "--add-data", "src/services;services",
        "--add-data", "src/core;core",
        "--add-data", "src/app;app",
        "--add-data", "src/version.py;version.py",
        "--add-data", f"{XYZ_SERVICES_DATA};xyzservices/data",
        "--hidden-import", "PyQt5.sip",
        "--hidden-import", "PyQt5.QtCore",
        "--hidden-import", "PyQt5.QtGui",
        "--hidden-import", "PyQt5.QtWidgets",
        "--hidden-import", "PyQt5.QtWebEngineWidgets",
        "--hidden-import", "PyQt5.QtWebEngineCore",
        "--hidden-import", "logging.handlers",
        "--hidden-import", "json",
        "--hidden-import", "requests",
        "--hidden-import", "geopy",
        "--hidden-import", "gpxpy",
        "--hidden-import", "folium",
        "--hidden-import", "folium.plugins",
        "--hidden-import", "xyzservices",
        "--hidden-import", "jinja2",
        "--hidden-import", "numpy",
        "--hidden-import", "branca",
        "--hidden-import", "version",
        "--hidden-import", "geopy.distance",
        "main.py"
    ]

    # 验证所有路径是否存在
    print("[GPXStudio] 验证路径是否存在...")
    paths_to_check = [
        "src/services/config/config",
        "src/ui",
        "src/modules",
        "src/services",
        "src/core",
        "src/app",
        "src/version.py",
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
        # 执行PyInstaller命令并显示进度条
        print("[GPXStudio] 正在构建...")

        # PyInstaller构建步骤及对应进度百分比
        build_steps = [
            ("analyzing", 10),    # 分析脚本依赖
            ("collecting", 30),   # 收集依赖文件
            ("extracting", 50),   # 提取二进制文件
            ("building", 70),     # 构建可执行文件
            ("copying", 85),      # 复制资源文件
            ("compressing", 95),  # 压缩文件
            ("completed", 100)    # 构建完成
        ]

        current_progress = 0
        step_index = 0

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        # 实时处理输出
        for line in iter(process.stdout.readline, ''):
            line = line.strip()

            # 解析PyInstaller输出，更新进度
            for i, (step, percent) in enumerate(build_steps[step_index:], start=step_index):
                if step in line.lower():
                    current_progress = percent
                    step_index = i
                    break

            # 如果没有匹配到步骤，逐步增加进度
            if current_progress < 95 and step_index < len(build_steps) - 1:
                current_progress += 0.1
                if current_progress > build_steps[step_index + 1][1]:
                    current_progress = build_steps[step_index + 1][1]

            # 确保进度不超过100%
            current_progress = min(current_progress, 100)

            # 绘制进度条
            bar_length = 50
            filled_length = int(bar_length * current_progress // 100)
            bar = "█" * filled_length + "-" * (bar_length - filled_length)

            # 显示进度条和百分比
            sys.stdout.write(f"\r[GPXStudio] 构建中 [{bar}] {current_progress:.1f}% ")
            sys.stdout.flush()

        process.wait()

        # 确保进度条显示100%
        if process.returncode == 0:
            bar = "█" * 50
            sys.stdout.write(f"\r[GPXStudio] 构建中 [{bar}] 100.0% \n")
            sys.stdout.flush()

            print("[GPXStudio] 发布版本构建成功！")
            print(f"[GPXStudio] 可执行文件位置: {DIST_FILE}")
            print("[GPXStudio] 构建完成！")
            input("按Enter键退出...")
        else:
            raise subprocess.CalledProcessError(process.returncode, command)

    except subprocess.CalledProcessError as e:
        print("\n[GPXStudio] 发布版本构建失败！")
        print(f"[GPXStudio] 返回代码: {e.returncode}")
        print(f"[GPXStudio] 请查看以上输出获取详细错误信息")
        input("按Enter键退出...")
        return 1
    except Exception as e:
        print("\n[GPXStudio] 发布版本构建失败！")
        print(f"[GPXStudio] 错误类型: {type(e).__name__}")
        print(f"[GPXStudio] 错误信息: {str(e)}")
        import traceback
        print(f"[GPXStudio] 堆栈跟踪: {traceback.format_exc()}")
        input("按Enter键退出...")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())

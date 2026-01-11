#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发布版本打包脚本 (Nuitka)
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
BUILD_DIR = os.path.join(PROJECT_ROOT, "build", f"{BUILD_NAME}_nuitka")
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
    print("[GPXStudio] 开始构建发布版本 (Nuitka)...")

    # 进入项目根目录
    os.chdir(PROJECT_ROOT)

    # 清理之前的构建文件
    if os.path.exists(BUILD_DIR):
        print(f"[GPXStudio] 清理之前的构建目录: {BUILD_DIR}")
        shutil.rmtree(BUILD_DIR)

    if os.path.exists(DIST_FILE):
        print(f"[GPXStudio] 删除之前的可执行文件: {DIST_FILE}")
        os.remove(DIST_FILE)

    # 执行Nuitka命令构建发布版本
    print("[GPXStudio] 执行Nuitka构建命令...")
    # 使用虚拟环境中的Python
    python_exe = os.path.join(PROJECT_ROOT, ".venv", "Scripts", "python.exe")
    command = [
        python_exe, "-m", "nuitka",
        "--standalone",
        "--windows-disable-console",
        f"--output-dir={BUILD_DIR}",
        "--plugin-enable=pyqt5",
        "--include-package=PyQt5",
        "--include-package=PyQt5.QtWebEngineWidgets",
        "--include-package=PyQt5.QtWebEngineCore",
        "--include-package=services",
        "--include-package=modules",
        "--include-package=core",
        "--include-package=app",
        "--include-package=ui",
        "--include-package=xyzservices",
        f"--include-data-dir={XYZ_SERVICES_DATA}=xyzservices/data",
        "--include-data-dir=services/config/config=services/config/config",
        "--include-data-dir=ui=ui",
        "--include-data-dir=modules=modules",
        "--include-data-dir=services=services",
        "--include-data-dir=core=core",
        "--include-data-dir=app=app",
        "main.py"
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )

        # 复制构建结果到dist目录
        build_exe = os.path.join(BUILD_DIR, "main.exe")
        if os.path.exists(build_exe):
            os.makedirs(os.path.dirname(DIST_FILE), exist_ok=True)
            shutil.copy2(build_exe, DIST_FILE)
            print("[GPXStudio] 可执行文件已复制到dist目录")

        print("[GPXStudio] 发布版本构建成功！")
        print(f"[GPXStudio] 可执行文件位置: {DIST_FILE}")
        print("[GPXStudio] 构建完成！")
        input("按Enter键退出...")

    except subprocess.CalledProcessError as e:
        print("[GPXStudio] 发布版本构建失败！")
        print(f"[GPXStudio] 错误信息: {e.stderr}")
        input("按Enter键退出...")
        return 1
    except Exception as e:
        print("[GPXStudio] 发布版本构建失败！")
        print(f"[GPXStudio] 错误信息: {str(e)}")
        input("按Enter键退出...")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())

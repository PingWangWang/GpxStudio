#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发布版本打包脚本
窗口版本，不包含控制台输出
"""

import os
import subprocess
import shutil

# 项目根目录（相对路径，脚本位于build目录下）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

# 构建配置
BUILD_NAME = "GPXStudio"
BUILD_DIR = os.path.join(PROJECT_ROOT, "build", BUILD_NAME)
DIST_FILE = os.path.join(PROJECT_ROOT, "dist", f"{BUILD_NAME}.exe")


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
    command = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        f"--name={BUILD_NAME}",
        "--add-data=services/config/config;services/config/config",
        "--add-data=ui;ui",
        "--add-data=modules;modules",
        "--add-data=services;services",
        "--add-data=core;core",
        "--add-data=app;app",
        "main.py"
    ]

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

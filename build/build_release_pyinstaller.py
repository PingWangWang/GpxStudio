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
import time

# 项目根目录（相对路径，脚本位于build目录下）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

# 读取项目版本号
VERSION_FILE = os.path.join(PROJECT_ROOT, "version.py")
with open(VERSION_FILE, "r", encoding="utf-8") as f:
    exec(f.read())

# 构建配置
BUILD_NAME = f"GPXStudio_{__version__}"
BUILD_DIR = os.path.join(PROJECT_ROOT, "build", BUILD_NAME)
DIST_FILE = os.path.join(PROJECT_ROOT, "dist", f"{BUILD_NAME}.exe")

# 虚拟环境配置
VENV_DIR = os.path.join(PROJECT_ROOT, ".venv")
REQUIREMENTS_FILE = os.path.join(PROJECT_ROOT, "requirements.txt")

# 图标文件配置
ICON_FILE = os.path.join(PROJECT_ROOT, "res", "GPXStudio.png")
ICO_FILE = os.path.join(PROJECT_ROOT, "res", "GPXStudio.ico")

# 声明全局变量，将在main函数中初始化
XYZ_SERVICES_DATA = None


def convert_png_to_ico():
    """将PNG图标转换为ICO格式，如果需要的话"""
    try:
        from PIL import Image

        # 如果ICO文件不存在或者比PNG文件旧，则转换
        if not os.path.exists(ICO_FILE) or os.path.getmtime(ICON_FILE) > os.path.getmtime(ICO_FILE):
            print(f"[GPXStudio] 转换图标文件: {ICON_FILE} -> {ICO_FILE}")
            img = Image.open(ICON_FILE)

            # 确保图标是正方形的
            if img.size[0] != img.size[1]:
                # 如果不是正方形，裁剪成正方形
                size = min(img.size)
                img = img.crop(((img.size[0] - size) // 2, (img.size[1] - size) // 2,
                               (img.size[0] + size) // 2, (img.size[1] + size) // 2))

            # 转换为ICO格式，包含多种尺寸
            img.save(ICO_FILE, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
            print(f"[GPXStudio] 图标转换完成")
        else:
            print(f"[GPXStudio] ICO图标文件已是最新版本")

    except ImportError:
        print(f"[GPXStudio] 警告：Pillow库未安装，无法转换PNG到ICO格式")
        print(f"[GPXStudio] 请手动转换 {ICON_FILE} 为 {ICO_FILE}")
        return False
    except Exception as e:
        print(f"[GPXStudio] 警告：图标转换失败: {e}")
        return False

    return True


def main():
    print("[GPXStudio] 开始构建发布版本...")

    # 进入项目根目录
    os.chdir(PROJECT_ROOT)

    # 检查和转换图标文件
    print("[GPXStudio] 准备图标文件...")
    if os.path.exists(ICON_FILE):
        convert_png_to_ico()
    else:
        print(f"[GPXStudio] 警告：找不到图标文件: {ICON_FILE}")

    # 清理之前的构建文件
    if os.path.exists(BUILD_DIR):
        print(f"[GPXStudio] 清理之前的构建目录: {BUILD_DIR}")
        shutil.rmtree(BUILD_DIR)

    # 清理dist目录中的旧文件，但保留GPXStudioData数据目录
    dist_dir = os.path.join(PROJECT_ROOT, "dist")
    if os.path.exists(dist_dir):
        print(f"[GPXStudio] 清理dist目录中的旧文件（保留GPXStudioData）...")
        for item in os.listdir(dist_dir):
            item_path = os.path.join(dist_dir, item)
            # 跳过GPXStudioData目录
            if item == "GPXStudioData":
                print(f"[GPXStudio] 保留数据目录: {item_path}")
                continue
            # 删除其他文件和目录
            try:
                if os.path.isfile(item_path):
                    os.remove(item_path)
                    print(f"[GPXStudio] 删除文件: {item_path}")
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    print(f"[GPXStudio] 删除目录: {item_path}")
            except Exception as e:
                print(f"[GPXStudio] 警告：无法删除 {item_path}: {e}")
    else:
        print(f"[GPXStudio] dist目录不存在，将自动创建")

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

    # 安装Pillow库用于图标转换
    print("[GPXStudio] 安装Pillow库用于图标转换...")
    pillow_cmd = [pip_path, "install", "Pillow"]
    result = subprocess.run(pillow_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[GPXStudio] 警告：安装Pillow库失败，将无法自动转换图标格式")
        print(f"[GPXStudio] 错误信息: {result.stderr}")

    # 导入site模块
    import site

    # 更新sys.path以使用虚拟环境
    venv_site_packages = os.path.join(VENV_DIR, "Lib", "site-packages")
    sys.path.insert(0, venv_site_packages)

    # 刷新site-packages路径
    import importlib
    importlib.reload(site)

    # 确保使用新虚拟环境中的模块
    print("[GPXStudio] 更新Python路径，使用新的虚拟环境...")

    # 动态查找xyzservices包的位置（在新虚拟环境中）
    global XYZ_SERVICES_DATA
    print("[GPXStudio] 查找xyzservices包的位置...")
    try:
        # 直接从虚拟环境路径查找
        xyzservices_path = os.path.join(venv_site_packages, "xyzservices")
        XYZ_SERVICES_DATA = os.path.join(xyzservices_path, "data")

        if not os.path.exists(XYZ_SERVICES_DATA):
            # 如果直接路径不存在，尝试导入方式
            import xyzservices
            xyzservices_path = os.path.dirname(xyzservices.__file__)
            XYZ_SERVICES_DATA = os.path.join(xyzservices_path, "data")
    except ImportError:
        # 如果无法导入，尝试从site-packages中查找
        site_packages_list = [venv_site_packages]
        XYZ_SERVICES_DATA = None
        for sp in site_packages_list:
            candidate_path = os.path.join(sp, "xyzservices", "data")
            if os.path.exists(candidate_path):
                XYZ_SERVICES_DATA = candidate_path
                break
        if not XYZ_SERVICES_DATA:
            # 如果仍然找不到，使用默认路径
            XYZ_SERVICES_DATA = os.path.join(venv_site_packages, "xyzservices", "data")

    print(f"[GPXStudio] 使用xyzservices数据路径: {XYZ_SERVICES_DATA}")

    # 验证xyzservices路径是否存在
    if not os.path.exists(XYZ_SERVICES_DATA):
        print(f"[GPXStudio] ❌ xyzservices数据路径不存在: {XYZ_SERVICES_DATA}")
        return 1

    # 执行PyInstaller命令构建发布版本
    print("[GPXStudio] 执行PyInstaller构建命令...")
    # 使用虚拟环境的pyinstaller提高兼容性
    pyinstaller_path = os.path.join(VENV_DIR, "Scripts", "pyinstaller.exe")
    print(f"[GPXStudio] 使用pyinstaller路径: {pyinstaller_path}")

    # 在Windows中，--add-data参数使用分号分隔，需要正确处理路径
    command = [
        pyinstaller_path,
        "--onefile",
        "--windowed",
        "--clean",  # 强制清理，确保图标正确应用
        "--noconfirm",  # 不询问覆盖
        "--noupx",  # 禁用UPX压缩，加快打包速度
        "--optimize=2",  # 优化级别2
        f"--name={BUILD_NAME}"
    ]

    # 如果ICO文件存在，立即添加图标参数（在其他参数之前）
    if os.path.exists(ICO_FILE):
        abs_ico_path = os.path.abspath(ICO_FILE)
        command.extend(["--icon", abs_ico_path])
        print(f"[GPXStudio] 使用图标文件: {abs_ico_path}")
    else:
        print(f"[GPXStudio] 警告：未找到ICO图标文件，将使用默认图标")

    # 继续添加其他参数
    command.extend([
        # 数据文件
        "--add-data", "src/services/config/config;services/config/config",
        "--add-data", "src/ui;ui",
        "--add-data", "src/modules;modules",
        "--add-data", "src/services;services",
        "--add-data", "src/core;core",
        "--add-data", "src/app;app",
        "--add-data", "version.py;version.py",
        "--add-data", "res;res",
        "--add-data", f"{XYZ_SERVICES_DATA};xyzservices/data",
        # 排除不需要的模块减小体积
        "--exclude-module", "tkinter",
        "--exclude-module", "matplotlib",
        "--exclude-module", "scipy",
        "--exclude-module", "pandas",
        "--exclude-module", "IPython",
        "--exclude-module", "jupyter",
        "--exclude-module", "notebook",
        # 只添加必要的hidden-import
        "--hidden-import", "PyQt5.sip",
        "--hidden-import", "PyQt5.QtCore",
        "--hidden-import", "PyQt5.QtGui",
        "--hidden-import", "PyQt5.QtWidgets",
        "--hidden-import", "PyQt5.QtWebEngineWidgets",
        "--hidden-import", "PyQt5.QtWebEngineCore",
        "--hidden-import", "logging.handlers",  # 修复启动错误
        "--hidden-import", "logging.config",
        "--hidden-import", "json",
        "--hidden-import", "requests",
        "--hidden-import", "geopy.distance",
        "--hidden-import", "geopy.geocoders",
        "--hidden-import", "gpxpy",
        "--hidden-import", "folium",
        "--hidden-import", "folium.plugins",
        "--hidden-import", "xyzservices",
        "--hidden-import", "jinja2",
        "--hidden-import", "branca",
        "--hidden-import", "core.resource_path",
        "--hidden-import", "version",
        "--hidden-import", "PyQt5.QtWebKit",
        "--hidden-import", "winrt.windows.devices.geolocation"
    ])

    # 最后添加主文件
    command.append("main.py")

    # 验证所有路径是否存在
    print("[GPXStudio] 验证路径是否存在...")
    paths_to_check = [
        "src/services/config/config",
        "src/ui",
        "src/modules",
        "src/services",
        "src/core",
        "src/app",
        "version.py",
        "res",
        XYZ_SERVICES_DATA,
        "main.py"
    ]

    for path in paths_to_check:
        if os.path.exists(path):
            print(f"[GPXStudio] ✅ 路径存在: {path}")
        else:
            print(f"[GPXStudio] ❌ 路径不存在: {path}")

    # 验证图标文件
    if os.path.exists(ICON_FILE):
        print(f"[GPXStudio] ✅ PNG图标文件存在: {ICON_FILE}")
    else:
        print(f"[GPXStudio] ❌ PNG图标文件不存在: {ICON_FILE}")

    if os.path.exists(ICO_FILE):
        print(f"[GPXStudio] ✅ ICO图标文件存在: {ICO_FILE}")
    else:
        print(f"[GPXStudio] ❌ ICO图标文件不存在: {ICO_FILE}")

    # 打印完整的命令
    print("[GPXStudio] 执行命令:")
    print(' '.join(command))

    try:
        # 执行PyInstaller命令并显示进度条
        print("[GPXStudio] 正在构建...")

        # PyInstaller构建步骤及对应进度百分比
        build_steps = {
            "analyzing": 10,
            "collecting": 25,
            "building exe": 40,
            "building pkg": 55,
            "copying": 70,
            "extracting": 85,
            "completed successfully": 100
        }

        current_progress = 0
        max_progress = 0  # 防止进度回跳
        start_time = time.time()
        last_update_time = start_time

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        # 实时处理输出
        for line in iter(process.stdout.readline, ''):
            line = line.strip().lower()
            current_time = time.time()

            # 检查关键词匹配
            matched_progress = 0
            for keyword, progress in build_steps.items():
                if keyword in line:
                    matched_progress = progress
                    break

            # 如果匹配到关键词，更新进度
            if matched_progress > 0:
                current_progress = matched_progress
            # 如果没有匹配到且距离上次更新超过2秒，小幅增加进度
            elif current_time - last_update_time > 2 and current_progress < 90:
                current_progress += 2
                last_update_time = current_time

            # 防止进度回跳，确保进度只能增加
            if current_progress > max_progress:
                max_progress = current_progress
            else:
                current_progress = max_progress

            # 确保进度不超过99%（除非明确完成）
            if "completed successfully" not in line:
                current_progress = min(current_progress, 99)

            # 绘制进度条
            bar_length = 50
            filled_length = int(bar_length * current_progress // 100)
            bar = "█" * filled_length + "-" * (bar_length - filled_length)

            # 计算用时
            elapsed_time = current_time - start_time

            # 显示进度条、百分比和用时
            sys.stdout.write(f"\r[GPXStudio] 构建中 [{bar}] {current_progress:.0f}% ({elapsed_time:.0f}s) ")
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
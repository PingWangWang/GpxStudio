#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nuitka 发布版本打包脚本
使用 Nuitka 编译器，相比 PyInstaller 可以获得更小的体积和更好的性能
"""

import os
import subprocess
import shutil
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
BUILD_NAME = f"GPXStudio_{__version__}_nu"
BUILD_DIR = os.path.join(PROJECT_ROOT, "build", f"{BUILD_NAME}.dist")
DIST_FILE = os.path.join(PROJECT_ROOT, "dist", f"{BUILD_NAME}.exe")

# 虚拟环境配置
VENV_DIR = os.path.join(PROJECT_ROOT, ".venv_nuitka")
REQUIREMENTS_FILE = os.path.join(PROJECT_ROOT, "requirements.txt")

# 图标文件配置
ICON_FILE = os.path.join(PROJECT_ROOT, "res", "GPXStudio.png")
ICO_FILE = os.path.join(PROJECT_ROOT, "res", "GPXStudio.ico")


def convert_png_to_ico():
    """将PNG图标转换为ICO格式，如果需要的话"""
    try:
        from PIL import Image

        # 如果ICO文件不存在或者比PNG文件旧，则转换
        if not os.path.exists(ICO_FILE) or (os.path.exists(ICON_FILE) and os.path.getmtime(ICON_FILE) < os.path.getmtime(ICON_FILE)):
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


def check_nuitka_installed(pip_path):
    """检查 Nuitka 是否已安装"""
    try:
        result = subprocess.run(
            [pip_path, "show", "nuitka"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False


def main():
    import time
    total_start_time = time.time()
    print(f"[GPXStudio] [{time.strftime('%Y-%m-%d %H:%M:%S')}] 开始使用 Nuitka 构建发布版本...")
    print("[GPXStudio] Nuitka 优势：更小的体积、更快的启动速度、更好的性能")

    # 进入项目根目录
    os.chdir(PROJECT_ROOT)

    # 检查和转换图标文件
    icon_start_time = time.time()
    print(f"[GPXStudio] [{time.strftime('%Y-%m-%d %H:%M:%S')}] 准备图标文件...")
    if os.path.exists(ICON_FILE):
        convert_png_to_ico()
    else:
        print(f"[GPXStudio] 警告：找不到图标文件: {ICON_FILE}")
    print(f"[GPXStudio] [{time.strftime('%Y-%m-%d %H:%M:%S')}] 图标准备完成，耗时: {(time.time() - icon_start_time):.2f}秒")

    # 清理之前的构建文件
    clean_start_time = time.time()
    print(f"[GPXStudio] [{time.strftime('%Y-%m-%d %H:%M:%S')}] 开始清理构建文件...")
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
    print(f"[GPXStudio] [{time.strftime('%Y-%m-%d %H:%M:%S')}] 清理完成，耗时: {(time.time() - clean_start_time):.2f}秒")

    # 清理和重新创建虚拟环境
    venv_start_time = time.time()
    print(f"[GPXStudio] [{time.strftime('%Y-%m-%d %H:%M:%S')}] 准备 Nuitka 构建环境...")
    print(f"[GPXStudio] 虚拟环境路径: {VENV_DIR}")

    # 删除现有的虚拟环境
    if os.path.exists(VENV_DIR):
        print(f"[GPXStudio] 删除现有的虚拟环境: {VENV_DIR}")
        shutil.rmtree(VENV_DIR)

    # 创建新的虚拟环境
    create_venv_start = time.time()
    print(f"[GPXStudio] [{time.strftime('%Y-%m-%d %H:%M:%S')}] 创建新的虚拟环境...")
    venv_create_cmd = [sys.executable, "-m", "venv", VENV_DIR]
    result = subprocess.run(venv_create_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[GPXStudio] 错误：创建虚拟环境失败")
        print(f"[GPXStudio] 错误信息: {result.stderr}")
        return 1
    print(f"[GPXStudio] [{time.strftime('%Y-%m-%d %H:%M:%S')}] 虚拟环境创建完成，耗时: {(time.time() - create_venv_start):.2f}秒")

    # 安装依赖包
    install_start = time.time()
    print(f"[GPXStudio] [{time.strftime('%Y-%m-%d %H:%M:%S')}] 安装项目依赖包...")
    pip_path = os.path.join(VENV_DIR, "Scripts", "pip.exe")
    install_cmd = [pip_path, "install", "-r", REQUIREMENTS_FILE]
    result = subprocess.run(install_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[GPXStudio] 错误：安装依赖包失败")
        print(f"[GPXStudio] 错误信息: {result.stderr}")
        return 1
    print(f"[GPXStudio] [{time.strftime('%Y-%m-%d %H:%M:%S')}] 依赖包安装完成，耗时: {(time.time() - install_start):.2f}秒")

    # 安装 Nuitka
    nuitka_install_start = time.time()
    print(f"[GPXStudio] [{time.strftime('%Y-%m-%d %H:%M:%S')}] 安装 Nuitka 编译器...")
    if not check_nuitka_installed(pip_path):
        nuitka_cmd = [pip_path, "install", "nuitka", "ordered-set", "zstandard"]
        result = subprocess.run(nuitka_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[GPXStudio] 错误：安装 Nuitka 失败")
            print(f"[GPXStudio] 错误信息: {result.stderr}")
            return 1
    else:
        print("[GPXStudio] Nuitka 已安装")
    print(f"[GPXStudio] [{time.strftime('%Y-%m-%d %H:%M:%S')}] Nuitka 安装完成，耗时: {(time.time() - nuitka_install_start):.2f}秒")

    # 安装Pillow库用于图标转换
    pillow_start = time.time()
    print(f"[GPXStudio] [{time.strftime('%Y-%m-%d %H:%M:%S')}] 安装Pillow库用于图标转换...")
    pillow_cmd = [pip_path, "install", "Pillow"]
    result = subprocess.run(pillow_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[GPXStudio] 警告：安装Pillow库失败，将无法自动转换图标格式")
    print(f"[GPXStudio] [{time.strftime('%Y-%m-%d %H:%M:%S')}] Pillow 安装完成，耗时: {(time.time() - pillow_start):.2f}秒")

    # 查找 xyzservices 数据路径
    xyz_start = time.time()
    print(f"[GPXStudio] [{time.strftime('%Y-%m-%d %H:%M:%S')}] 查找 xyzservices 包的位置...")
    venv_site_packages = os.path.join(VENV_DIR, "Lib", "site-packages")
    xyzservices_data = os.path.join(venv_site_packages, "xyzservices", "data")

    if not os.path.exists(xyzservices_data):
        print(f"[GPXStudio] ❌ xyzservices数据路径不存在: {xyzservices_data}")
        return 1

    print(f"[GPXStudio] 使用 xyzservices 数据路径: {xyzservices_data}")
    print(f"[GPXStudio] [{time.strftime('%Y-%m-%d %H:%M:%S')}] 环境准备完成，总耗时: {(time.time() - venv_start_time):.2f}秒")

    # 执行 Nuitka 命令构建发布版本
    build_start_time = time.time()
    print(f"[GPXStudio] [{time.strftime('%Y-%m-%d %H:%M:%S')}] 执行 Nuitka 构建命令...")
    python_path = os.path.join(VENV_DIR, "Scripts", "python.exe")

    # 构建 Nuitka 命令
    command = [
        python_path,
        "-m", "nuitka",
        "--standalone",  # 独立模式，包含所有依赖
        "--onefile",  # 单文件模式
        "--windows-disable-console",  # 禁用控制台窗口
        "--enable-plugin=pyqt5",  # 启用 PyQt5 插件
        "--follow-imports",  # 跟踪所有导入
        "--assume-yes-for-downloads",  # 自动下载依赖
        f"--output-filename={BUILD_NAME}.exe",  # 输出文件名
        "--output-dir=dist",  # 输出目录
    ]

    # 如果ICO文件存在，添加图标参数
    if os.path.exists(ICO_FILE):
        abs_ico_path = os.path.abspath(ICO_FILE)
        command.append(f"--windows-icon-from-ico={abs_ico_path}")
        print(f"[GPXStudio] 使用图标文件: {abs_ico_path}")
    else:
        print(f"[GPXStudio] 警告：未找到ICO图标文件，将使用默认图标")

    # 添加数据目录包含
    data_dirs = [
        ("src/services/config/config", "services/config/config"),
        ("src/ui", "ui"),
        ("src/modules", "modules"),
        ("src/services", "services"),
        ("src/core", "core"),
        ("src/app", "app"),
        ("res", "res"),
        ("src", "src"),  # 包含整个src目录，确保所有Python文件都被包含
        (xyzservices_data, "xyzservices/data"),
    ]

    for src, dst in data_dirs:
        if os.path.exists(src):
            command.append(f"--include-data-dir={src}={dst}")
            print(f"[GPXStudio] ✅ 包含数据目录: {src} -> {dst}")
        else:
            print(f"[GPXStudio] ⚠️ 数据路径不存在: {src}")

    # 添加数据文件包含
    data_files = [
        ("version.py", "version.py"),
    ]

    for src, dst in data_files:
        if os.path.exists(src):
            command.append(f"--include-data-file={src}={dst}")
            print(f"[GPXStudio] ✅ 包含数据文件: {src} -> {dst}")
        else:
            print(f"[GPXStudio] ⚠️ 数据文件不存在: {src}")

    # 添加必要的模块包含
    include_modules = [
        "PyQt5.sip",
        "PyQt5.QtCore",
        "PyQt5.QtGui",
        "PyQt5.QtWidgets",
        "PyQt5.QtWebEngineWidgets",
        "PyQt5.QtWebEngineCore",
        "logging.handlers",
        "logging.config",
        "json",
        "requests",
        "geopy.distance",
        "geopy.geocoders",
        "gpxpy",
        "folium",
        "folium.plugins",
        "xyzservices",
        "jinja2",
        "branca",
        "winrt.windows.devices.geolocation",
        "numpy",
        "pandas",
        "timezonefinder",
        "pytz",
    ]

    for module in include_modules:
        command.append(f"--include-module={module}")

    # 排除不需要的模块以减小体积
    exclude_modules = [
        "tkinter",
        "matplotlib",
        "scipy",
        "pandas",
        "IPython",
        "jupyter",
        "notebook",
        "test",
        "unittest",
        "distutils",
    ]

    for module in exclude_modules:
        command.append(f"--nofollow-import-to={module}")

    # 优化选项
    command.extend([
        "--remove-output",  # 删除构建目录
        "--show-progress",  # 显示进度
        "--show-memory",  # 显示内存使用
        "--enable-plugin=numpy",  # 启用numpy插件
        "--python-flag=-O",  # 启用Python优化模式
        "--noinclude-pytest-mode=nofollow",  # 排除pytest
        "--noinclude-unittest-mode=nofollow",  # 排除unittest
    ])

    # 最后添加主文件
    command.append("main.py")

    # 打印完整的命令
    print("[GPXStudio] 执行命令:")
    print(' '.join(command))

    try:
        # 执行 Nuitka 命令
        print("[GPXStudio] 正在使用 Nuitka 编译...")
        print("[GPXStudio] 注意：首次编译可能需要较长时间（10-30分钟），请耐心等待")

        start_time = time.time()

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        # 实时处理输出
        for line in iter(process.stdout.readline, ''):
            line_stripped = line.strip()
            if line_stripped:
                # 显示 Nuitka 的输出
                print(f"[Nuitka] {line_stripped}")

        process.wait()

        elapsed_time = time.time() - start_time

        if process.returncode == 0:
            print(f"\n[GPXStudio] [{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ Nuitka 编译成功！")
            print(f"[GPXStudio] 编译用时: {elapsed_time:.1f} 秒")
            total_elapsed_time = time.time() - total_start_time
            print(f"[GPXStudio] 总构建耗时: {total_elapsed_time:.1f} 秒")
            print(f"[GPXStudio] 可执行文件位置: {DIST_FILE}")

            # 检查文件大小
            if os.path.exists(DIST_FILE):
                file_size = os.path.getsize(DIST_FILE) / (1024 * 1024)  # MB
                print(f"[GPXStudio] 文件大小: {file_size:.2f} MB")

            print(f"[GPXStudio] [{time.strftime('%Y-%m-%d %H:%M:%S')}] 构建完成！")
            input("按Enter键退出...")
        else:
            raise subprocess.CalledProcessError(process.returncode, command)

    except subprocess.CalledProcessError as e:
        print("\n[GPXStudio] ❌ Nuitka 编译失败！")
        print(f"[GPXStudio] 返回代码: {e.returncode}")
        print(f"[GPXStudio] 请查看以上输出获取详细错误信息")
        input("按Enter键退出...")
        return 1
    except Exception as e:
        print("\n[GPXStudio] ❌ Nuitka 编译失败！")
        print(f"[GPXStudio] 错误类型: {type(e).__name__}")
        print(f"[GPXStudio] 错误信息: {str(e)}")
        import traceback
        print(f"[GPXStudio] 堆栈跟踪: {traceback.format_exc()}")
        input("按Enter键退出...")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())

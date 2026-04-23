#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发布版本打包脚本
窗口版本，不包含控制台输出
"""

import os
import subprocess
import shutil
import sys
import time
import winreg
import site
import importlib
from datetime import datetime

# 项目根目录（相对路径，脚本位于build目录下）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))


def log(msg):
    """带时间戳的日志输出"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")

# 读取项目版本号
VERSION_FILE = os.path.join(PROJECT_ROOT, "version.py")
with open(VERSION_FILE, "r", encoding="utf-8") as f:
    exec(f.read())

# 构建配置
BUILD_NAME = f"GPXStudio_{__version__}"
VENV_DIR = os.path.join(PROJECT_ROOT, ".venv")
REQUIREMENTS_FILE = os.path.join(PROJECT_ROOT, "requirements.txt")
ICON_FILE = os.path.join(PROJECT_ROOT, "res", "GPXStudio.png")
ICO_FILE = os.path.join(PROJECT_ROOT, "res", "GPXStudio.ico")
XYZ_SERVICES_DATA = None


def clean_old_builds():
    """清理旧版本的构建产物"""
    for dir_name in ["build", "dist"]:
        target_dir = os.path.join(PROJECT_ROOT, dir_name)
        if not os.path.exists(target_dir):
            continue
        
        for item in os.listdir(target_dir):
            item_path = os.path.join(target_dir, item)
            # 跳过保留项
            if item == BUILD_NAME or item == "GPXStudioData" or item.endswith(".py") or (item.endswith(".exe") and "nsis" in item.lower()):
                continue
            
            try:
                if item.startswith("GPXStudio_") and os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                elif item.startswith("GPXStudio_Setup_") and item.endswith(".exe"):
                    os.remove(item_path)
            except Exception as e:
                log(f"警告：无法删除 {item_path}: {e}")


def handle_virtual_environment():
    """处理虚拟环境：创建或保留"""
    cleanup_venv = False
    if os.path.exists(VENV_DIR):
        user_input = input("是否清理现有的虚拟环境(直接回车为不清理)？(y/N): ")
        if user_input.strip().lower() == 'y':
            cleanup_venv = True
            shutil.rmtree(VENV_DIR)

    if not os.path.exists(VENV_DIR):
        log("创建新的虚拟环境...")
        result = subprocess.run([sys.executable, "-m", "venv", VENV_DIR], capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"创建虚拟环境失败: {result.stderr}")

    # 更新路径
    venv_site_packages = os.path.join(VENV_DIR, "Lib", "site-packages")
    sys.path.insert(0, venv_site_packages)
    importlib.reload(site)


def install_dependencies():
    """安装项目依赖和 Pillow"""
    pip_path = os.path.join(VENV_DIR, "Scripts", "pip.exe")
    mirrors = [
        "https://pypi.tuna.tsinghua.edu.cn/simple/",
        "https://mirrors.aliyun.com/pypi/simple/"
    ]
    
    def try_install(packages, index_url=None):
        cmd = [pip_path, "install"] + packages
        if index_url:
            cmd.extend(["-i", index_url])
        return subprocess.run(cmd, capture_output=True, text=True).returncode == 0

    # 安装 requirements
    if not try_install(["-r", REQUIREMENTS_FILE]):
        for mirror in mirrors:
            if try_install(["-r", REQUIREMENTS_FILE], mirror):
                break
        else:
            raise Exception("安装依赖包失败")

    # 安装 Pillow
    if not try_install(["Pillow"]):
        for mirror in mirrors:
            if try_install(["Pillow"], mirror):
                break


def prepare_packaging_paths():
    """准备打包所需的路径信息"""
    global XYZ_SERVICES_DATA
    venv_site_packages = os.path.join(VENV_DIR, "Lib", "site-packages")
    
    # 查找 xyzservices 数据路径
    xyzservices_path = os.path.join(venv_site_packages, "xyzservices")
    XYZ_SERVICES_DATA = os.path.join(xyzservices_path, "data")
    
    if not os.path.exists(XYZ_SERVICES_DATA):
        try:
            import xyzservices
            XYZ_SERVICES_DATA = os.path.join(os.path.dirname(xyzservices.__file__), "data")
        except ImportError:
            pass


def run_pyinstaller():
    """执行 PyInstaller 打包"""
    pyinstaller_path = os.path.join(VENV_DIR, "Scripts", "pyinstaller.exe")
    command = [
        pyinstaller_path,
        "--onedir", "--windowed", "--clean", "--noconfirm", "--noupx", "--optimize=2",
        f"--name={BUILD_NAME}"
    ]
    
    if os.path.exists(ICO_FILE):
        command.extend(["--icon", os.path.abspath(ICO_FILE)])
    
    # 添加数据和隐藏导入
    data_files = [
        ("src/services/config/config", "services/config/config"),
        ("src/ui", "ui"), ("src/modules", "modules"), ("src/services", "services"),
        ("src/core", "core"), ("src/app", "app"), ("src/infrastructure", "infrastructure"),
        ("src/domain", "domain"), ("version.py", "."),
        ("res/GPXStudio.png", "res"), ("res/GPXStudio.ico", "res"),
        ("res/icons/Loading.svg", "res/icons")
    ]
    if XYZ_SERVICES_DATA:
        data_files.append((XYZ_SERVICES_DATA, "xyzservices/data"))
    
    for src, dst in data_files:
        command.extend(["--add-data", f"{src};{dst}"])
    
    hidden_imports = [
        "PyQt5.sip", "PyQt5.QtCore", "PyQt5.QtGui", "PyQt5.QtWidgets",
        "PyQt5.QtWebEngineWidgets", "PyQt5.QtWebEngineCore", "PyQt5.QtSvg",
        "logging.handlers", "logging.config", "json", "requests",
        "geopy.distance", "geopy.geocoders", "gpxpy", "folium", "folium.plugins",
        "xyzservices", "jinja2", "branca", "core.resource_path", "version",
        "PyQt5.QtWebKit", "winrt.windows.devices.geolocation",
        "winrt.windows.foundation", "winrt.windows.foundation.collections",
        "http.server", "socketserver", "tempfile", "threading",
        "injector",
        "timezonefinder", "pytz",
        "numpy", "pandas",
        "pkg_resources", "pkg_resources.py2_compat",
    ]
    for imp in hidden_imports:
        command.extend(["--hidden-import", imp])
    
    command.append("main.py")
    
    print("[GPXStudio] 正在构建...")
    # 按阶段顺序排列，确保进度单调递增
    build_steps = [
        ("analyzing",            10),
        ("collecting",           25),
        ("building exe",         40),
        ("building pkg",         55),
        ("copying",              70),
        ("extracting",           85),
        ("completed successfully", 99),
    ]
    
    current_progress = 0
    start_time = time.time()
    last_update_time = start_time
    
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                               text=True, encoding='utf-8', errors='replace', bufsize=1)
    
    for line in iter(process.stdout.readline, ''):
        line_lower = line.strip().lower()
        current_time = time.time()
        
        # 只取比当前进度更大的匹配值，保证单调递增
        for keyword, progress in build_steps:
            if keyword in line_lower and progress > current_progress:
                current_progress = progress
                last_update_time = current_time
                break
        else:
            # 无关键词匹配时，每2秒小步递增（上限90）
            if current_time - last_update_time > 2 and current_progress < 90:
                current_progress += 1
                last_update_time = current_time
            
        bar_length = 50
        filled_length = int(bar_length * min(current_progress, 99) // 100)
        bar = "█" * filled_length + "-" * (bar_length - filled_length)
        elapsed_time = current_time - start_time
        
        ts = datetime.now().strftime("%H:%M:%S")
        sys.stdout.write(f"\r[{ts}] 构建中 [{bar}] {current_progress}% ({elapsed_time:.0f}s) ")
        sys.stdout.flush()
    
    process.wait()
    
    if process.returncode == 0:
        ts = datetime.now().strftime("%H:%M:%S")
        sys.stdout.write(f"\r[{ts}] 构建中 [{'█' * 50}] 100.0% \n")
        sys.stdout.flush()
        log("发布版本构建成功！")
        update_nsis_script()
        return True
    return False





def find_nsis_path():
    """查找 NSIS 的安装路径"""
    # 1. 从注册表查找
    try:
        for flag in [winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY]:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\NSIS",
                               0, winreg.KEY_READ | flag)
            install_location, _ = winreg.QueryValueEx(key, "InstallLocation")
            winreg.CloseKey(key)
            return install_location
    except Exception:
        pass
    
    # 2. 检查常见安装路径
    common_paths = [
        r"D:\Program Files (x86)\NSIS",
        r"C:\Program Files (x86)\NSIS",
        r"C:\Program Files\NSIS"
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    # 3. 检查 PATH 环境变量
    for path in os.environ.get("PATH", "").split(os.pathsep):
        if "NSIS" in path and os.path.exists(path):
            return path
    
    return None


def update_nsis_script():
    """更新 NSIS 脚本中的版本号和文件路径（优先使用 GBK 编码）"""
    nsis_file = os.path.join(SCRIPT_DIR, "gpxstudio.nsi")
    if not os.path.exists(nsis_file):
        return

    lines = []
    encoding_used = "gbk"
    
    try:
        # 优先尝试使用 GBK 读取
        try:
            with open(nsis_file, "r", encoding="gbk") as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            log("GBK 读取失败，尝试使用 UTF-8...")
            encoding_used = "utf-8"
            with open(nsis_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
        new_lines = []
        for line in lines:
            if line.strip().startswith('!define PRODUCT_VERSION'):
                new_lines.append(f'!define PRODUCT_VERSION "{__version__}"\n')
            elif line.strip().startswith('!define PRODUCT_EXE'):
                new_lines.append(f'!define PRODUCT_EXE "GPXStudio_{__version__}.exe"\n')
            elif line.strip().startswith('!define BUILD_DIR'):
                new_lines.append(f'!define BUILD_DIR "..\\dist\\GPXStudio_{__version__}"\n')
            else:
                new_lines.append(line)
        
        # 使用读取时成功的编码写入
        with open(nsis_file, "w", encoding=encoding_used) as f:
            f.writelines(new_lines)
            
    except Exception as e:
        log(f"警告：更新 NSIS 脚本失败: {e}")


def build_installer():
    """使用 NSIS 构建安装包"""
    log("正在使用 NSIS 构建安装包...")
    nsis_path = find_nsis_path()
    if not nsis_path:
        log("错误：找不到 NSIS 安装路径，跳过安装包构建")
        return False
    
    makensis_path = os.path.join(nsis_path, "makensis.exe")
    nsi_file = os.path.join(SCRIPT_DIR, "gpxstudio.nsi")
    
    if not os.path.exists(makensis_path) or not os.path.exists(nsi_file):
        log("错误：找不到 NSIS 必要文件，跳过安装包构建")
        return False
    
    update_nsis_script()
    
    try:
        result = subprocess.run([makensis_path, nsi_file], capture_output=True, text=True)
        if result.returncode == 0:
            log("安装包构建完成")
            return True
        else:
            log(f"安装包构建失败: {result.stderr[:200]}")
            return False
    except Exception as e:
        log(f"安装包构建异常: {e}")
        return False


def convert_png_to_ico():
    """将PNG图标转换为ICO格式（仅在需要时转换）"""
    if not os.path.exists(ICON_FILE):
        return False

    # 如果 ICO 存在且比 PNG 新，则跳过
    if os.path.exists(ICO_FILE) and os.path.getmtime(ICO_FILE) >= os.path.getmtime(ICON_FILE):
        return True

    try:
        from PIL import Image
        img = Image.open(ICON_FILE)
        
        # 确保正方形并裁剪
        if img.size[0] != img.size[1]:
            size = min(img.size)
            left = (img.size[0] - size) // 2
            top = (img.size[1] - size) // 2
            img = img.crop((left, top, left + size, top + size))

        img.save(ICO_FILE, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
        return True
    except ImportError:
        return False
    except Exception:
        return False


def main():
    log("开始构建发布版本...")
    os.chdir(PROJECT_ROOT)

    try:
        # 1. 准备图标文件
        convert_png_to_ico()

        # 2. 清理旧版本产物
        clean_old_builds()

        # 3. 处理虚拟环境
        handle_virtual_environment()

        # 4. 安装依赖
        install_dependencies()

        # 5. 准备打包路径
        prepare_packaging_paths()

        # 6. 执行 PyInstaller 打包
        if not run_pyinstaller():
            log("错误：PyInstaller 打包失败。")
            input("按Enter键退出...")
            return 1

        # 7. 构建安装包
        installer_success = build_installer()
        
        # 8. 输出结果
        if installer_success:
            setup_path = os.path.join(PROJECT_ROOT, 'dist', f'GPXStudio_Setup_{__version__}.exe')
            log(f"安装包路径: {setup_path}")
            if os.path.exists(setup_path):
                size_mb = os.path.getsize(setup_path) / (1024 * 1024)
                log(f"安装包大小: {size_mb:.2f} MB")
        else:
            log("错误：安装包构建失败。")
    except Exception as e:
        log(f"构建过程中发生严重错误: {e}")
        import traceback
        traceback.print_exc()
    
    input("按Enter键退出...")
    return 0


if __name__ == "__main__":
    exit(main())
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPX Studio 项目清理脚本
用于删除项目中的临时文件、构建目录、编译文件等，保持项目整洁
"""

import os
import shutil
import glob

def main():
    """主函数"""
    print("GPX Studio 项目清理脚本")
    print("=" * 30)

    # 清理构建目录中的临时文件，保留Python构建脚本
    try:
        if os.path.exists("build"):
            print(f"清理构建目录中的临时文件: build")
            # 获取build目录中的所有文件和子目录
            for item in os.listdir("build"):
                item_path = os.path.join("build", item)
                if os.path.isdir(item_path):
                    # 删除所有子目录（临时构建目录）
                    print(f"  清理目录: {item_path}")
                    shutil.rmtree(item_path, ignore_errors=True)
                elif not item.endswith(".py"):
                    # 删除非Python脚本文件（临时文件）
                    print(f"  清理文件: {item_path}")
                    os.remove(item_path)
            print(f"✓ 成功清理 build 目录中的临时文件")
    except Exception as e:
        print(f"✗ 清理 build 目录中的临时文件失败: {e}")

    try:
        if os.path.exists("dist"):
            print(f"清理构建目录: dist")
            shutil.rmtree("dist", ignore_errors=True)
            print(f"✓ 成功清理 dist")
    except Exception as e:
        print(f"✗ 清理 dist 目录失败: {e}")

    # 清理测试相关文件
    try:
        if os.path.exists(".pytest_cache"):
            print(f"清理测试相关文件: .pytest_cache")
            shutil.rmtree(".pytest_cache", ignore_errors=True)
            print(f"✓ 成功清理 .pytest_cache")
    except Exception as e:
        print(f"✗ 清理 .pytest_cache 失败: {e}")

    try:
        if os.path.exists("htmlcov"):
            print(f"清理测试相关文件: htmlcov")
            shutil.rmtree("htmlcov", ignore_errors=True)
            print(f"✓ 成功清理 htmlcov")
    except Exception as e:
        print(f"✗ 清理 htmlcov 失败: {e}")

    try:
        if os.path.exists(".coverage"):
            print(f"清理测试相关文件: .coverage")
            os.remove(".coverage")
            print(f"✓ 成功清理 .coverage")
    except Exception as e:
        print(f"✗ 清理 .coverage 失败: {e}")

    # 清理日志文件
    try:
        print("清理日志文件...")
        log_files = glob.glob("*.log")
        for file in log_files:
            print(f"  清理: {file}")
            os.remove(file)
        print("✓ 成功清理日志文件")
    except Exception as e:
        print(f"✗ 清理日志文件失败: {e}")

    # 清理临时文件
    try:
        print("清理临时文件...")
        temp_files = ["*.tmp", "*.temp"]
        for pattern in temp_files:
            for file in glob.glob(pattern):
                print(f"  清理: {file}")
                os.remove(file)
        print("✓ 成功清理临时文件")
    except Exception as e:
        print(f"✗ 清理临时文件失败: {e}")

    # 清理PyInstaller生成的spec文件
    try:
        print("清理PyInstaller生成的spec文件...")
        spec_files = glob.glob("*.spec")
        for file in spec_files:
            print(f"  清理: {file}")
            os.remove(file)
        print("✓ 成功清理spec文件")
    except Exception as e:
        print(f"✗ 清理spec文件失败: {e}")

    print("\n" + "=" * 30)
    print("清理完成！")
    print("项目已保持整洁。")

if __name__ == "__main__":
    main()

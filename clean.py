#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPX Studio 项目清理脚本
用于删除项目中的临时文件、构建目录、编译文件等，保持项目整洁
"""

import os
import shutil
import glob
import argparse

def main():
    """主函数"""
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description="GPX Studio 项目清理脚本")
    parser.add_argument("-a", "--all", action="store_true", help="清理所有内容")
    parser.add_argument("-b", "--build", action="store_true", help="清理构建目录")
    parser.add_argument("-t", "--test", action="store_true", help="清理测试相关文件")
    parser.add_argument("-l", "--logs", action="store_true", help="清理日志文件")
    parser.add_argument("-c", "--cache", action="store_true", help="清理缓存文件")
    parser.add_argument("-e", "--editor", action="store_true", help="清理编辑器相关文件")
    parser.add_argument("-v", "--venv", action="store_true", help="清理虚拟环境")
    parser.add_argument("--force", action="store_true", help="强制清理，不询问确认")

    args = parser.parse_args()

    # 打印欢迎信息
    print("GPX Studio 项目清理脚本")
    print("=" * 50)

    # 如果没有指定任何选项，默认清理所有
    if not any([args.all, args.build, args.test, args.logs, args.cache, args.editor, args.venv]):
        args.all = True

    # 确认提示
    if not args.force:
        print("即将清理以下内容：")
        if args.all or args.build:
                print("- 构建目录中的临时文件 (build目录中的Python脚本将保留)")
                print("- 构建目录: dist")
        if args.all or args.test:
            print("- 测试相关文件 (.pytest_cache, htmlcov, .coverage)")
        if args.all or args.logs:
            print("- 日志文件 (*.log)")
        if args.all or args.cache:
            print("- 缓存文件 (*.tmp, *.temp, __pycache__, *.pyc)")
        if args.all or args.editor:
                print("- 编辑器相关文件 (.idea, *.swp)")
        if args.all or args.venv:
            print("- 虚拟环境 (.venv, venv)")

        confirm = input("\n确定要继续清理吗？(y/N): ")
        if confirm.lower() != 'y':
            print("取消清理操作")
            return

    # 清理构建目录
    if args.all or args.build:
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
                        # 删除非Python脚本文件（临时文件），保留Python打包脚本
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

        try:
            print("清理PyInstaller生成的spec文件...")
            spec_files = glob.glob("*.spec")
            for file in spec_files:
                print(f"  清理: {file}")
                os.remove(file)
            print("✓ 成功清理spec文件")
        except Exception as e:
            print(f"✗ 清理spec文件失败: {e}")

    # 清理测试相关文件
    if args.all or args.test:
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
    if args.all or args.logs:
        try:
            print("清理日志文件...")
            log_files = glob.glob("*.log")
            for file in log_files:
                print(f"  清理: {file}")
                os.remove(file)
            print("✓ 成功清理日志文件")
        except Exception as e:
            print(f"✗ 清理日志文件失败: {e}")

    # 清理缓存文件
    if args.all or args.cache:
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

        try:
            print("清理Python编译文件...")
            # 清理所有__pycache__目录
            for root, dirs, files in os.walk("."):
                for dir in dirs:
                    if dir == "__pycache__":
                        pycache_path = os.path.join(root, dir)
                        print(f"  清理: {pycache_path}")
                        shutil.rmtree(pycache_path, ignore_errors=True)
            # 清理所有.pyc文件
            pyc_files = glob.glob("**/*.pyc", recursive=True)
            for file in pyc_files:
                print(f"  清理: {file}")
                os.remove(file)
            print("✓ 成功清理Python编译文件")
        except Exception as e:
            print(f"✗ 清理Python编译文件失败: {e}")

    # 清理编辑器相关文件
    if args.all or args.editor:
        try:
            if os.path.exists(".idea"):
                print(f"清理编辑器相关文件: .idea")
                shutil.rmtree(".idea", ignore_errors=True)
                print(f"✓ 成功清理 .idea")
        except Exception as e:
            print(f"✗ 清理 .idea 失败: {e}")

        try:
            print("清理vim交换文件...")
            swap_files = glob.glob("*.swp")
            for file in swap_files:
                print(f"  清理: {file}")
                os.remove(file)
            print("✓ 成功清理vim交换文件")
        except Exception as e:
            print(f"✗ 清理vim交换文件失败: {e}")

    # 清理虚拟环境
    if args.all or args.venv:
        try:
            if os.path.exists(".venv"):
                print(f"清理虚拟环境: .venv")
                shutil.rmtree(".venv", ignore_errors=True)
                print(f"✓ 成功清理 .venv")
        except Exception as e:
            print(f"✗ 清理 .venv 失败: {e}")

        try:
            if os.path.exists("venv"):
                print(f"清理虚拟环境: venv")
                shutil.rmtree("venv", ignore_errors=True)
                print(f"✓ 成功清理 venv")
        except Exception as e:
            print(f"✗ 清理 venv 失败: {e}")

    print("\n" + "=" * 50)
    print("清理完成！")
    print("项目已保持整洁。")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
测试日志清理功能
"""

import os
import sys
import time

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.logging_setup import get_log_path, get_log_size, clean_logs, open_log_directory


def test_log_cleanup():
    """测试日志清理功能"""
    print("=== 测试日志清理功能 ===")
    
    # 获取日志文件路径
    log_path = get_log_path()
    print(f"日志文件路径: {log_path}")
    
    # 获取当前日志大小
    initial_size = get_log_size()
    print(f"清理前日志大小: {initial_size:.2f} MB")
    
    # 检查日志文件是否存在
    if os.path.exists(log_path):
        print("日志文件存在")
    else:
        print("日志文件不存在")
    
    # 执行清理操作
    print("执行日志清理...")
    success = clean_logs()
    
    # 检查清理结果
    print(f"清理操作结果: {'成功' if success else '失败'}")
    
    # 获取清理后日志大小
    time.sleep(1)  # 等待文件系统更新
    final_size = get_log_size()
    print(f"清理后日志大小: {final_size:.2f} MB")
    
    # 检查日志文件是否存在
    if os.path.exists(log_path):
        print("清理后日志文件存在 (新的空日志文件)")
    else:
        print("清理后日志文件不存在")
    
    # 打开日志目录
    print("打开日志目录...")
    open_log_directory()
    
    print("=== 测试完成 ===")


if __name__ == "__main__":
    test_log_cleanup()

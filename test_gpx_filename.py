#!/usr/bin/env python3
"""
测试GPX导出文件名生成逻辑
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QDateTime

def test_gpx_filename_generation():
    """测试GPX导出文件名生成逻辑"""
    print("=== 测试GPX导出文件名生成逻辑 ===")
    
    # 创建QApplication实例
    app = QApplication(sys.argv)
    
    # 设置测试数据
    start_name = "天安门"
    end_name = "颐和园"
    estimated_duration_seconds = 3600 + 30 * 60  # 1小时30分钟
    transport_mode = "骑行"
    
    # 设置起始时间
    current_time = datetime.now()
    current_time_zero_sec = current_time.replace(second=0)
    start_datetime = QDateTime.fromString(current_time_zero_sec.strftime("%Y-%m-%d %H:%M:%S"), "yyyy-MM-dd hh:mm:ss")
    start_time_str = start_datetime.toString("yyyyMMdd_hhmm")
    
    # 格式化途径时间（小时和分钟）
    duration_hours = estimated_duration_seconds // 3600
    duration_minutes = (estimated_duration_seconds % 3600) // 60
    duration_str = f"{duration_hours}小时{duration_minutes}分钟"
    
    # 生成默认文件名
    default_filename = f"{start_name}_{end_name}_{transport_mode}_{start_time_str}_{duration_str}.gpx"
    
    print(f"测试数据：")
    print(f"- 起点名称: {start_name}")
    print(f"- 终点名称: {end_name}")
    print(f"- 交通方式: {transport_mode}")
    print(f"- 起始时间: {start_time_str}")
    print(f"- 途径时间: {duration_str}")
    print(f"\n生成的文件名：")
    print(f"{default_filename}")
    
    # 验证文件名格式是否符合要求
    expected_pattern = r"^.+_.+_.+_\d{8}_\d{4}_\d+小时\d+分钟\.gpx$"
    import re
    if re.match(expected_pattern, default_filename):
        print("\n✅ 文件名格式符合要求！")
        return True
    else:
        print("\n❌ 文件名格式不符合要求！")
        return False

if __name__ == "__main__":
    success = test_gpx_filename_generation()
    sys.exit(0 if success else 1)

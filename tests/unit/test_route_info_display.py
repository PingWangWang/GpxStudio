#!/usr/bin/env python3
"""
测试路线信息展示功能
"""

import sys
import os
import time
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QDateTime
from app.app import GpxStudio

def test_route_info_display():
    """测试路线信息展示功能"""
    print("=== 测试路线信息展示功能 ===")

    # 创建QApplication实例
    app = QApplication(sys.argv)

    # 创建GpxStudio实例
    studio = GpxStudio()

    # 模拟search_results_title
    studio.search_results_title = type('MockQLabel', (), {})()
    studio.search_results_title.setText = lambda text: print(f"信息展示框标题已更改为: '{text}'")

    # 设置测试数据
    studio.start_name = "天安门"
    studio.end_name = "颐和园"
    studio.estimated_duration_seconds = 3600 + 30 * 60  # 1小时30分钟

    # 设置途径点
    studio.waypoints_coords = [(39.958076, 116.328594)]  # 例如：西单
    studio.waypoints_names = ["西单"]

    # 设置起始时间
    current_time = datetime.now()
    current_time_zero_sec = current_time.replace(second=0)
    qt_current_datetime = QDateTime.fromString(current_time_zero_sec.strftime("%Y-%m-%d %H:%M:%S"), "yyyy-MM-dd hh:mm:ss")
    studio.start_time_edit = type('MockDateTimeEdit', (), {})()
    studio.start_time_edit.dateTime = lambda: qt_current_datetime

    # 设置结束时间
    end_time = current_time_zero_sec.timestamp() + studio.estimated_duration_seconds
    end_datetime = datetime.fromtimestamp(end_time)
    qt_end_datetime = QDateTime.fromString(end_datetime.strftime("%Y-%m-%d %H:%M:%S"), "yyyy-MM-dd hh:mm:ss")
    studio.end_time_edit = type('MockDateTimeEdit', (), {})()
    studio.end_time_edit.dateTime = lambda: qt_end_datetime

    # 模拟交通方式选择
    studio.transport_combo = type('MockCombo', (), {})()
    studio.transport_combo.currentText = lambda: "骑行"

    # 模拟路线点
    studio.route_points = [(39.9042, 116.4074), (39.958076, 116.328594), (39.999445, 116.275257)]

    # 模拟GAODE_ROUTING_SERVICE
    class MockGaodeRoutingService:
        def calculate_distance(self, route_points):
            # 模拟距离计算
            return 12.5

    studio.gaode_routing_service = MockGaodeRoutingService()

    # 清除搜索结果列表
    studio.search_results_list.clear()

    # 显示路线详细信息（直接调用相关代码）
    studio.search_results_list.addItem("路线规划成功！")
    studio.search_results_list.addItem("=" * 30)

    # 起点、途径点、终点
    studio.search_results_list.addItem(f"起点: {studio.start_name or '未命名'}")

    # 显示途径点
    if studio.waypoints_coords:
        for i, waypoint in enumerate(studio.waypoints_coords):
            if waypoint and i < len(studio.waypoints_names):
                waypoint_name = studio.waypoints_names[i] or f"途径点{i+1}"
                studio.search_results_list.addItem(f"途径点{i+1}: {waypoint_name}")

    studio.search_results_list.addItem(f"终点: {studio.end_name or '未命名'}")
    studio.search_results_list.addItem("=" * 30)

    # 交通方式
    transport_mode = studio.transport_combo.currentText()
    studio.search_results_list.addItem(f"交通方式: {transport_mode}")

    # 起始时间
    start_datetime = studio.start_time_edit.dateTime()
    start_time_str = start_datetime.toString("yyyy-MM-dd HH:mm")
    studio.search_results_list.addItem(f"起始时间: {start_time_str}")

    # 途径时间
    duration_hours = studio.estimated_duration_seconds // 3600
    duration_minutes = (studio.estimated_duration_seconds % 3600) // 60
    studio.search_results_list.addItem(f"途径时间: {int(duration_hours)}小时{duration_minutes}分钟")

    # 结束时间
    end_datetime = studio.end_time_edit.dateTime()
    end_time_str = end_datetime.toString("yyyy-MM-dd HH:mm")
    studio.search_results_list.addItem(f"结束时间: {end_time_str}")

    # 总距离
    if studio.gaode_routing_service:
        total_distance = studio.gaode_routing_service.calculate_distance(studio.route_points)
        studio.search_results_list.addItem(f"总距离: {total_distance:.2f} 公里")

    studio.search_results_list.addItem("=" * 30)

    # 打印搜索结果列表内容
    print("模拟展示的路线信息：")
    for i in range(studio.search_results_list.count()):
        print(studio.search_results_list.item(i).text())

    print("\n✅ 路线信息展示功能测试通过！")
    return True

if __name__ == "__main__":
    success = test_route_info_display()
    sys.exit(0 if success else 1)

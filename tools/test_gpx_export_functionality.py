"""
测试GPX导出功能
验证历史记录中的导出按钮状态管理和弹出面板功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from modules.routing.ui.route_plan_panel import RouteHistoryItem
from ui.popups.gpx_export_popup import GpxExportPopup

def test_route_history_item():
    """测试路线历史记录项的导出按钮状态"""
    app = QApplication(sys.argv)
    
    # 创建测试历史数据
    history_data_with_route = {
        'start': '北京站',
        'end': '天安门',
        'mode': 'driving',
        'route_points': [(39.9042, 116.4074), (39.9163, 116.3972)],  # 有路线数据
        'distance': 5000,
        'duration': 600
    }
    
    history_data_without_route = {
        'start': '上海站',
        'end': '外滩',
        'mode': 'driving',
        'route_points': [],  # 没有路线数据
        'distance': 0,
        'duration': 0
    }
    
    # 测试有路线数据的历史记录项
    print("测试有路线数据的历史记录项...")
    item_with_route = RouteHistoryItem(history_data_with_route)
    
    # 初始状态：未选中，按钮应该禁用
    print(f"初始状态 - 选中: {item_with_route.is_selected}, 有数据: {item_with_route.has_route_data}, 按钮启用: {item_with_route.export_button.isEnabled()}")
    assert not item_with_route.export_button.isEnabled(), "初始状态按钮应该禁用"
    
    # 设置为选中状态，但还没有路线数据
    item_with_route.set_selected(True)
    print(f"选中后 - 选中: {item_with_route.is_selected}, 有数据: {item_with_route.has_route_data}, 按钮启用: {item_with_route.export_button.isEnabled()}")
    assert not item_with_route.export_button.isEnabled(), "只选中但没有路线数据时按钮应该禁用"
    
    # 设置有路线数据
    item_with_route.set_route_data_available(True)
    print(f"有数据后 - 选中: {item_with_route.is_selected}, 有数据: {item_with_route.has_route_data}, 按钮启用: {item_with_route.export_button.isEnabled()}")
    assert item_with_route.export_button.isEnabled(), "选中且有路线数据时按钮应该启用"
    
    # 测试没有路线数据的历史记录项
    print("\n测试没有路线数据的历史记录项...")
    item_without_route = RouteHistoryItem(history_data_without_route)
    
    # 设置为选中状态
    item_without_route.set_selected(True)
    print(f"选中后 - 选中: {item_without_route.is_selected}, 有数据: {item_without_route.has_route_data}, 按钮启用: {item_without_route.export_button.isEnabled()}")
    assert not item_without_route.export_button.isEnabled(), "选中但没有路线数据时按钮应该禁用"
    
    print("\n✅ 所有测试通过！")
    
    app.quit()

def test_gpx_export_popup():
    """测试GPX导出弹出面板"""
    app = QApplication(sys.argv)
    
    # 创建测试路线数据
    route_data = {
        'description': '推荐方案',
        'distance': 5000,
        'duration': 600,
        'route_points': [(39.9042, 116.4074), (39.9163, 116.3972)]
    }
    
    print("测试GPX导出弹出面板...")
    popup = GpxExportPopup(route_data)
    
    # 检查弹出面板是否正确创建
    assert popup is not None, "弹出面板应该成功创建"
    print("✅ GPX导出弹出面板创建成功")
    
    # 检查起始时间是否设置为当前时间
    start_time = popup.get_start_time()
    assert start_time is not None, "起始时间应该有默认值"
    print(f"✅ 默认起始时间: {start_time.toString()}")
    
    app.quit()

if __name__ == '__main__':
    print("开始测试GPX导出功能...")
    print("=" * 50)
    
    test_route_history_item()
    print("\n" + "=" * 50)
    test_gpx_export_popup()
    
    print("\n" + "=" * 50)
    print("所有测试完成！")
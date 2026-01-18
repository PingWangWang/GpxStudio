#!/usr/bin/env python3
"""
测试历史记录选择和导出按钮状态的调试工具
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import Qt

from src.modules.routing.ui.route_plan_panel import RoutePlanPanel


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("历史记录选择调试")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 创建路线规划面板
        self.route_panel = RoutePlanPanel()
        layout.addWidget(self.route_panel)
        
        # 创建测试按钮
        test_button = QPushButton("加载测试历史记录")
        test_button.clicked.connect(self.load_test_history)
        layout.addWidget(test_button)
        
        select_button = QPushButton("选择第一条历史记录")
        select_button.clicked.connect(self.select_first_history)
        layout.addWidget(select_button)
        
        debug_button = QPushButton("调试历史记录状态")
        debug_button.clicked.connect(self.debug_history_state)
        layout.addWidget(debug_button)
        
        # 测试历史记录数据
        self.test_history = [
            {
                'start': '西安钟楼',
                'end': '大雁塔',
                'mode': 'driving',
                'search_count': 1,
                'start_coords': [108.9434, 34.2583],
                'end_coords': [108.9649, 34.2244],
                'distance': 8500,
                'duration': 1200,
                'route_points': []  # 空的路线点，模拟没有完整路线数据
            },
            {
                'start': '西安火车站',
                'end': '西安北站',
                'mode': 'driving',
                'search_count': 2,
                'start_coords': [108.9515, 34.2778],
                'end_coords': [108.9298, 34.3708],
                'distance': 12000,
                'duration': 1800,
                'route_points': []
            },
            {
                'start': '曲江池',
                'end': '大唐芙蓉园',
                'mode': 'walking',
                'search_count': 1,
                'start_coords': [108.9789, 34.2089],
                'end_coords': [108.9567, 34.2156],
                'distance': 2500,
                'duration': 1800,
                'route_points': []
            }
        ]
    
    def load_test_history(self):
        """加载测试历史记录"""
        print("=== 加载测试历史记录 ===")
        self.route_panel.load_history(self.test_history)
        print(f"已加载 {len(self.test_history)} 条历史记录")
        self.debug_history_state()
    
    def select_first_history(self):
        """选择第一条历史记录"""
        print("=== 选择第一条历史记录 ===")
        if self.test_history:
            first_history = self.test_history[0]
            print(f"选择历史记录: {first_history['start']} → {first_history['end']}")
            
            # 模拟restore_history_mode + set_selected_history的调用顺序
            print("1. 调用 restore_history_mode()")
            self.route_panel.restore_history_mode()
            
            print("2. 调用 set_selected_history()")
            self.route_panel.set_selected_history(first_history)
            
            print("3. 调试选择后的状态")
            self.debug_history_state()
    
    def debug_history_state(self):
        """调试历史记录状态"""
        print("=== 调试历史记录状态 ===")
        
        if not hasattr(self.route_panel, 'history_widgets'):
            print("❌ history_widgets 属性不存在")
            return
        
        if not self.route_panel.history_widgets:
            print("❌ history_widgets 列表为空")
            return
        
        print(f"✅ 找到 {len(self.route_panel.history_widgets)} 个历史记录widget")
        
        for i, widget in enumerate(self.route_panel.history_widgets):
            print(f"--- 历史记录 {i+1} ---")
            print(f"  起点: {widget.history_data.get('start', 'N/A')}")
            print(f"  终点: {widget.history_data.get('end', 'N/A')}")
            print(f"  选中状态: {widget.is_selected}")
            print(f"  路线数据: {widget.has_route_data}")
            print(f"  导出按钮启用: {widget.export_button.isEnabled()}")
            
            # 检查按钮图标
            icon = widget.export_button.icon()
            if not icon.isNull():
                print(f"  按钮图标: 已设置")
            else:
                print(f"  按钮图标: 未设置")
        
        # 检查列表选中状态
        current_row = self.route_panel.history_list.currentRow()
        print(f"列表当前选中行: {current_row}")


def main():
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle('Fusion')
    
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
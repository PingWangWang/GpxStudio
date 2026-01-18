#!/usr/bin/env python3
"""
测试历史记录导出按钮逻辑
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt

from src.modules.routing.ui.route_plan_panel import RoutePlanPanel


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("历史记录导出按钮逻辑测试")
        self.setGeometry(100, 100, 900, 700)
        
        # 创建中央widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 说明标签
        info_label = QLabel("""
历史记录导出按钮逻辑测试：

1. 路线规划面板刚打开时，所有GPX导出按钮应该都禁用（灰色）
2. 用户点击某条记录后，检查该条记录的路线数据是否存在：
   - 如果有路线数据：导出按钮变为白色（启用）
   - 如果没有路线数据：导出按钮保持灰色（禁用）
3. 测试ESC键关闭面板功能

测试步骤：
1. 点击"显示路线规划面板"
2. 观察所有导出按钮初始状态（应该都是灰色）
3. 点击不同的历史记录，观察导出按钮状态变化
4. 按ESC键测试面板关闭功能
        """)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 10px;
                font-size: 12px;
            }
        """)
        layout.addWidget(info_label)
        
        # 控制按钮
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        
        show_panel_btn = QPushButton("显示路线规划面板")
        show_panel_btn.clicked.connect(self.show_route_panel)
        button_layout.addWidget(show_panel_btn)
        
        hide_panel_btn = QPushButton("隐藏路线规划面板")
        hide_panel_btn.clicked.connect(self.hide_route_panel)
        button_layout.addWidget(hide_panel_btn)
        
        reload_history_btn = QPushButton("重新加载历史记录")
        reload_history_btn.clicked.connect(self.reload_test_history)
        button_layout.addWidget(reload_history_btn)
        
        layout.addWidget(button_container)
        
        # 状态标签
        self.status_label = QLabel("状态: 准备就绪")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #e8f5e8;
                border: 1px solid #4CAF50;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.status_label)
        
        # 创建路线规划面板
        self.route_panel = RoutePlanPanel()
        self.route_panel.cancel_clicked.connect(self.on_panel_cancelled)
        self.route_panel.history_selected.connect(self.on_history_selected)
        self.route_panel.history_export_gpx_clicked.connect(self.on_export_gpx_clicked)
        self.route_panel.hide()
        layout.addWidget(self.route_panel)
        
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
                'route_points': [  # 有路线数据
                    [108.9434, 34.2583],
                    [108.9500, 34.2500],
                    [108.9649, 34.2244]
                ]
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
                'route_points': []  # 没有路线数据
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
                'route_points': [  # 有路线数据
                    [108.9789, 34.2089],
                    [108.9678, 34.2123],
                    [108.9567, 34.2156]
                ]
            }
        ]
        
        # 加载测试历史记录
        self.reload_test_history()
    
    def show_route_panel(self):
        """显示路线规划面板"""
        self.status_label.setText("状态: 显示路线规划面板")
        self.route_panel.show()
        print("[测试] 路线规划面板已显示")
        
        # 检查初始状态
        self.check_initial_button_states()
    
    def hide_route_panel(self):
        """隐藏路线规划面板"""
        self.status_label.setText("状态: 隐藏路线规划面板")
        self.route_panel.hide()
        print("[测试] 路线规划面板已隐藏")
    
    def reload_test_history(self):
        """重新加载测试历史记录"""
        self.route_panel.load_history(self.test_history)
        self.status_label.setText("状态: 已加载测试历史记录")
        print("[测试] 已加载测试历史记录")
        
        # 检查初始状态
        self.check_initial_button_states()
    
    def check_initial_button_states(self):
        """检查初始按钮状态"""
        if not hasattr(self.route_panel, 'history_widgets'):
            print("[测试] 警告: 历史记录widgets不存在")
            return
        
        print("=== 检查初始按钮状态 ===")
        all_disabled = True
        for i, widget in enumerate(self.route_panel.history_widgets):
            is_enabled = widget.export_button.isEnabled()
            is_selected = widget.is_selected
            has_route_data = widget.has_route_data
            
            print(f"历史记录 {i+1}: {widget.history_data.get('start', 'N/A')} → {widget.history_data.get('end', 'N/A')}")
            print(f"  选中状态: {is_selected}")
            print(f"  路线数据: {has_route_data}")
            print(f"  导出按钮启用: {is_enabled}")
            
            if is_enabled:
                all_disabled = False
        
        if all_disabled:
            print("✅ 所有导出按钮初始状态正确（都是禁用的）")
        else:
            print("❌ 有导出按钮初始状态错误（应该都是禁用的）")
    
    def on_panel_cancelled(self):
        """面板取消/关闭"""
        self.status_label.setText("状态: 路线规划面板已关闭（ESC键或取消按钮）")
        print("[测试] 路线规划面板已关闭")
    
    def on_history_selected(self, history_data):
        """历史记录选中"""
        start = history_data.get('start', 'N/A')
        end = history_data.get('end', 'N/A')
        route_points = history_data.get('route_points', [])
        has_data = bool(route_points and len(route_points) > 0)
        
        self.status_label.setText(f"状态: 选中历史记录 {start} → {end}，路线数据: {'有' if has_data else '无'}")
        print(f"[测试] 选中历史记录: {start} → {end}")
        print(f"[测试] 路线数据状态: {'有' if has_data else '无'} ({len(route_points)} 个点)")
        
        # 检查选中后的按钮状态
        self.check_selected_button_state(history_data)
    
    def check_selected_button_state(self, selected_history):
        """检查选中后的按钮状态"""
        print("=== 检查选中后的按钮状态 ===")
        for i, widget in enumerate(self.route_panel.history_widgets):
            is_match = widget.history_data == selected_history
            is_enabled = widget.export_button.isEnabled()
            is_selected = widget.is_selected
            has_route_data = widget.has_route_data
            
            print(f"历史记录 {i+1}: {widget.history_data.get('start', 'N/A')} → {widget.history_data.get('end', 'N/A')}")
            print(f"  是否匹配选中项: {is_match}")
            print(f"  选中状态: {is_selected}")
            print(f"  路线数据: {has_route_data}")
            print(f"  导出按钮启用: {is_enabled}")
            
            if is_match:
                expected_enabled = is_selected and has_route_data
                if is_enabled == expected_enabled:
                    print(f"  ✅ 按钮状态正确")
                else:
                    print(f"  ❌ 按钮状态错误，期望: {expected_enabled}，实际: {is_enabled}")
    
    def on_export_gpx_clicked(self, history_data):
        """导出GPX按钮点击"""
        start = history_data.get('start', 'N/A')
        end = history_data.get('end', 'N/A')
        self.status_label.setText(f"状态: 点击导出GPX按钮 {start} → {end}")
        print(f"[测试] 点击导出GPX按钮: {start} → {end}")
    
    def keyPressEvent(self, event):
        """主窗口键盘事件"""
        if event.key() == Qt.Key_Escape:
            self.status_label.setText("状态: 主窗口接收到ESC键")
            print("[测试] 主窗口接收到ESC键")
        super().keyPressEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = TestWindow()
    window.show()
    
    print("=== 历史记录导出按钮逻辑测试 ===")
    print("测试数据:")
    print("1. 西安钟楼 → 大雁塔 (有路线数据)")
    print("2. 西安火车站 → 西安北站 (无路线数据)")
    print("3. 曲江池 → 大唐芙蓉园 (有路线数据)")
    print()
    print("预期行为:")
    print("- 初始状态：所有导出按钮都是灰色（禁用）")
    print("- 点击记录1或3：导出按钮变白色（启用）")
    print("- 点击记录2：导出按钮保持灰色（禁用）")
    print("- 按ESC键：关闭路线规划面板")
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
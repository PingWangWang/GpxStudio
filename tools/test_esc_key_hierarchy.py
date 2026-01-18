#!/usr/bin/env python3
"""
测试ESC键层级关闭功能
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt5.QtCore import Qt, QDateTime

from src.ui.popups.gpx_export_popup import GpxExportPopup


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ESC键层级关闭测试")
        self.setGeometry(100, 100, 600, 400)
        
        # 创建中央widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 说明标签
        info_label = QLabel("""
ESC键层级关闭测试：

1. 点击"显示GPX导出面板"按钮
2. 在GPX导出面板中点击日期时间设置按钮
3. 测试ESC键行为：
   - 第一次按ESC：关闭日期时间选择器，焦点回到GPX导出面板
   - 第二次按ESC：关闭GPX导出面板

预期行为：
- 显示日期时间选择器时，焦点自动设置到该界面
- 按ESC键时，优先关闭最上层的界面
- 关闭子界面后，焦点自动返回到父级界面
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
        
        # 测试按钮
        test_button = QPushButton("显示GPX导出面板")
        test_button.clicked.connect(self.show_gpx_export_popup)
        layout.addWidget(test_button)
        
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
        
        # 测试路线数据
        self.test_route_data = {
            'description': '西安钟楼 → 大雁塔',
            'distance': 8500,
            'duration': 1200,
            'route_points': []
        }
        
        self.gpx_popup = None
    
    def show_gpx_export_popup(self):
        """显示GPX导出弹出面板"""
        self.status_label.setText("状态: 显示GPX导出面板")
        
        # 创建GPX导出弹出面板
        self.gpx_popup = GpxExportPopup(self.test_route_data, self)
        self.gpx_popup.export_confirmed.connect(self.on_export_confirmed)
        self.gpx_popup.closed.connect(self.on_popup_closed)
        
        # 在窗口中央显示
        center_pos = self.geometry().center()
        popup_pos = center_pos - self.gpx_popup.rect().center()
        self.gpx_popup.show_at_position(popup_pos)
        
        print("[测试] GPX导出面板已显示")
    
    def on_export_confirmed(self, start_time):
        """导出确认"""
        self.status_label.setText(f"状态: 确认导出，起始时间: {start_time.toString('yyyy-MM-dd hh:mm')}")
        print(f"[测试] 用户确认导出，起始时间: {start_time.toString('yyyy-MM-dd hh:mm')}")
    
    def on_popup_closed(self):
        """弹出面板关闭"""
        self.status_label.setText("状态: GPX导出面板已关闭")
        print("[测试] GPX导出面板已关闭")
        self.gpx_popup = None
    
    def keyPressEvent(self, event):
        """主窗口键盘事件"""
        if event.key() == Qt.Key_Escape:
            self.status_label.setText("状态: 主窗口接收到ESC键")
            print("[测试] 主窗口接收到ESC键")
        super().keyPressEvent(event)


def main():
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle('Fusion')
    
    window = TestWindow()
    window.show()
    
    print("=== ESC键层级关闭测试 ===")
    print("1. 点击'显示GPX导出面板'按钮")
    print("2. 在GPX导出面板中点击日期时间设置按钮")
    print("3. 按ESC键测试层级关闭功能")
    print("4. 观察控制台输出和状态标签变化")
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
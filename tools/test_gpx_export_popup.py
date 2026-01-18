#!/usr/bin/env python3
"""
测试GPX导出弹出面板的工具
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import Qt, QPoint
from ui.popups.gpx_export_popup import GpxExportPopup


class TestWindow(QMainWindow):
    """测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GPX导出弹出面板测试")
        self.setGeometry(100, 100, 400, 300)
        
        # 创建中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignCenter)
        
        # 测试按钮
        test_button = QPushButton("测试GPX导出弹出面板")
        test_button.clicked.connect(self.show_export_popup)
        layout.addWidget(test_button)
        
        # 存储弹出面板引用
        self.popup = None
    
    def show_export_popup(self):
        """显示导出弹出面板"""
        # 模拟路线数据
        route_data = {
            'description': '推荐方案',
            'distance': 15600,  # 15.6公里
            'duration': 1800,   # 30分钟
            'route_points': [
                (39.9042, 116.4074),  # 北京天安门
                (39.9163, 116.3972),  # 北京西站
                None,  # 段分隔符
                (39.8704, 116.4619),  # 北京南站
                (39.9042, 116.4074),  # 回到天安门
            ]
        }
        
        # 如果已经有弹出面板，先关闭
        if self.popup and self.popup.isVisible():
            self.popup.hide()
        
        # 创建弹出面板
        self.popup = GpxExportPopup(route_data, self)
        self.popup.export_confirmed.connect(self.on_export_confirmed)
        self.popup.closed.connect(self.on_popup_closed)
        
        # 在按钮右侧显示
        button_pos = self.mapToGlobal(self.centralWidget().children()[1].pos())
        popup_x = button_pos.x() + 200
        popup_y = button_pos.y()
        
        self.popup.show_at_position(QPoint(popup_x, popup_y))
    
    def on_export_confirmed(self, start_time):
        """导出确认回调"""
        print(f"导出确认，起始时间: {start_time.toString('yyyy-MM-dd hh:mm:ss')}")
    
    def on_popup_closed(self):
        """弹出面板关闭回调"""
        print("弹出面板已关闭")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    window = TestWindow()
    window.show()
    
    print("GPX导出弹出面板测试启动")
    print("点击按钮测试弹出面板功能")
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
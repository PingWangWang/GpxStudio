#!/usr/bin/env python3
"""
测试GPX导出对话框的工具
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import Qt
from ui.dialogs.gpx_export_dialog import GpxExportDialog


class TestWindow(QMainWindow):
    """测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GPX导出对话框测试")
        self.setGeometry(100, 100, 300, 200)
        
        # 创建中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignCenter)
        
        # 测试按钮
        test_button = QPushButton("测试GPX导出对话框")
        test_button.clicked.connect(self.show_export_dialog)
        layout.addWidget(test_button)
    
    def show_export_dialog(self):
        """显示导出对话框"""
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
        
        # 创建并显示对话框
        dialog = GpxExportDialog(route_data, self)
        dialog.export_confirmed.connect(self.on_export_confirmed)
        
        result = dialog.exec_()
        if result == dialog.Accepted:
            print("用户确认导出")
        else:
            print("用户取消导出")
    
    def on_export_confirmed(self, start_time):
        """导出确认回调"""
        print(f"导出确认，起始时间: {start_time.toString('yyyy-MM-dd hh:mm:ss')}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    window = TestWindow()
    window.show()
    
    print("GPX导出对话框测试启动")
    print("点击按钮测试对话框功能")
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
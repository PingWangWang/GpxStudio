#!/usr/bin/env python3
"""
测试导出按钮的工具
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
from modules.routing.ui.route_plan_panel import RouteAlternativeItem


class TestWindow(QMainWindow):
    """测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("导出按钮测试")
        self.setGeometry(100, 100, 500, 300)
        
        # 设置背景色为蓝色，模拟路线面板
        self.setStyleSheet("""
            QMainWindow {
                background-color: #4A90E2;
            }
        """)
        
        # 创建中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(10)
        
        # 创建几个路线方案项进行测试
        route_data_list = [
            {
                'description': '推荐方案',
                'distance': 15600,  # 15.6公里
                'duration': 1800,   # 30分钟
                'traffic_lights': 9,
                'tolls': 0,
                'route_points': [(39.9042, 116.4074), (39.9163, 116.3972)]
            },
            {
                'description': '距离最短',
                'distance': 12300,  # 12.3公里
                'duration': 2100,   # 35分钟
                'traffic_lights': 12,
                'tolls': 5,
                'route_points': [(39.9042, 116.4074), (39.8704, 116.4619)]
            },
            {
                'description': '躲避拥堵',
                'distance': 18900,  # 18.9公里
                'duration': 1650,   # 27分钟
                'traffic_lights': 6,
                'tolls': 10,
                'route_points': [(39.9042, 116.4074), (39.9163, 116.3972), (39.8704, 116.4619)]
            }
        ]
        
        # 创建路线方案项
        for i, route_data in enumerate(route_data_list):
            route_item = RouteAlternativeItem(route_data, i, i == 0)  # 第一个默认选中
            route_item.export_gpx_clicked.connect(self.on_export_clicked)
            layout.addWidget(route_item)
    
    def on_export_clicked(self, route_data):
        """导出按钮点击回调"""
        description = route_data.get('description', '未知方案')
        distance = route_data.get('distance', 0) / 1000
        print(f"导出按钮被点击！方案: {description}, 距离: {distance:.1f}公里")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    window = TestWindow()
    window.show()
    
    print("导出按钮测试启动")
    print("测试内容:")
    print("1. 导出按钮是否显示OutPut图标")
    print("2. 导出按钮是否垂直居中")
    print("3. 导出按钮是否有动画效果")
    print("4. 点击导出按钮是否触发信号")
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
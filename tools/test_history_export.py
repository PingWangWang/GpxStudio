#!/usr/bin/env python3
"""
测试历史记录导出GPX功能
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt5.QtCore import Qt
from modules.routing.ui.route_plan_panel import RouteHistoryItem


class TestWindow(QMainWindow):
    """测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("历史记录导出GPX测试")
        self.setGeometry(100, 100, 600, 400)
        
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
        
        # 说明标签
        info_label = QLabel("历史记录导出GPX功能测试")
        info_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
            }
        """)
        layout.addWidget(info_label)
        
        # 创建几个历史记录项进行测试
        history_data_list = [
            {
                'start': '元熙越府',
                'end': '梦家寨',
                'mode': 'driving',
                'search_count': 15,
                'route_points': [  # 有完整路线数据
                    (39.9042, 116.4074),
                    (39.9163, 116.3972),
                    (39.8704, 116.4619)
                ],
                'distance': 15600,
                'duration': 1800
            },
            {
                'start': '纽约',
                'end': '西雅图',
                'mode': 'driving',
                'search_count': 3,
                'route_points': [],  # 没有路线数据
                'distance': 0,
                'duration': 0
            },
            {
                'start': '元熙越府',
                'end': '梦家寨',
                'mode': 'walking',
                'search_count': 1,
                'route_points': [  # 有完整路线数据
                    (39.9042, 116.4074),
                    (39.9100, 116.4100),
                    (39.9163, 116.3972)
                ],
                'distance': 8900,
                'duration': 3600
            }
        ]
        
        # 创建历史记录项
        self.history_items = []
        for i, history_data in enumerate(history_data_list):
            history_item = RouteHistoryItem(history_data)
            history_item.export_gpx_clicked.connect(self.on_export_clicked)
            layout.addWidget(history_item)
            self.history_items.append(history_item)
        
        # 控制按钮
        control_layout = QVBoxLayout()
        
        # 选择按钮
        select_buttons_layout = QVBoxLayout()
        for i, history_data in enumerate(history_data_list):
            btn = QPushButton(f"选择记录 {i+1}: {history_data['start']} → {history_data['end']}")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.9);
                    color: #4A90E2;
                    border: none;
                    border-radius: 4px;
                    padding: 8px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: white;
                }
            """)
            btn.clicked.connect(lambda checked, idx=i: self.select_history_item(idx))
            select_buttons_layout.addWidget(btn)
        
        control_layout.addLayout(select_buttons_layout)
        
        # 路线数据状态按钮
        data_buttons_layout = QVBoxLayout()
        for i, history_data in enumerate(history_data_list):
            has_data = len(history_data.get('route_points', [])) > 0
            btn = QPushButton(f"记录 {i+1} 路线数据: {'有' if has_data else '无'}")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.7);
                    color: #333;
                    border: none;
                    border-radius: 4px;
                    padding: 6px;
                    font-size: 11px;
                }
            """)
            btn.clicked.connect(lambda checked, idx=i, has=has_data: self.set_route_data_status(idx, has))
            data_buttons_layout.addWidget(btn)
        
        control_layout.addLayout(data_buttons_layout)
        layout.addLayout(control_layout)
        
        # 结果显示
        self.result_label = QLabel("测试说明:\n1. 点击'选择记录'按钮模拟选中历史记录\n2. 只有选中且有路线数据的记录才能导出\n3. 点击导出按钮测试功能")
        self.result_label.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 0.9);
                color: #333;
                border-radius: 4px;
                padding: 10px;
                font-size: 12px;
            }
        """)
        self.result_label.setWordWrap(True)
        layout.addWidget(self.result_label)
    
    def select_history_item(self, index):
        """选择历史记录项"""
        for i, item in enumerate(self.history_items):
            is_selected = (i == index)
            item.set_selected(is_selected)
        
        history_data = self.history_items[index].history_data
        self.result_label.setText(f"已选择记录 {index+1}: {history_data['start']} → {history_data['end']}")
        print(f"选择历史记录 {index+1}")
    
    def set_route_data_status(self, index, has_data):
        """设置路线数据状态"""
        self.history_items[index].set_route_data_available(has_data)
        status = "有" if has_data else "无"
        print(f"设置记录 {index+1} 路线数据状态: {status}")
    
    def on_export_clicked(self, history_data):
        """导出按钮点击回调"""
        start = history_data.get('start', '未知')
        end = history_data.get('end', '未知')
        route_points_count = len(history_data.get('route_points', []))
        
        result_text = f"导出GPX请求:\n起点: {start}\n终点: {end}\n路线点数: {route_points_count}"
        self.result_label.setText(result_text)
        print(f"导出GPX: {start} → {end}, 路线点数: {route_points_count}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    window = TestWindow()
    window.show()
    
    print("历史记录导出GPX测试启动")
    print("测试功能:")
    print("1. 历史记录项显示导出按钮")
    print("2. 导出按钮状态管理（选中+有数据才启用）")
    print("3. 导出按钮点击信号")
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
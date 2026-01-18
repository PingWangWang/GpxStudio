#!/usr/bin/env python3
"""
测试弹出面板管理功能
包括：
1. 历史记录导出GPX按钮功能
2. 主程序失去焦点时关闭所有弹出面板
3. 主程序窗口移动/缩放时弹出面板跟随移动
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QIcon


class TestPopupManagement(QMainWindow):
    """测试弹出面板管理的窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("弹出面板管理测试")
        self.setGeometry(100, 100, 800, 600)
        
        # 弹出面板列表
        self.active_popups = []
        
        # 安装事件过滤器
        self.installEventFilter(self)
        
        # 记录窗口初始位置
        self.last_window_geometry = self.geometry()
        
        # 创建中央控件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 创建测试按钮
        self.create_test_buttons(layout)
        
    def create_test_buttons(self, layout):
        """创建测试按钮"""
        
        # 标题
        title_label = QLabel("弹出面板管理测试")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)
        
        # 测试按钮区域
        button_layout = QHBoxLayout()
        
        # 模拟历史记录导出GPX按钮
        history_export_btn = QPushButton("测试历史记录导出GPX")
        history_export_btn.clicked.connect(self.test_history_export_gpx)
        button_layout.addWidget(history_export_btn)
        
        # 模拟设置弹出面板按钮
        settings_btn = QPushButton("测试设置弹出面板")
        settings_btn.clicked.connect(self.test_settings_popup)
        button_layout.addWidget(settings_btn)
        
        # 关闭所有弹出面板按钮
        close_all_btn = QPushButton("关闭所有弹出面板")
        close_all_btn.clicked.connect(self.close_all_popups)
        button_layout.addWidget(close_all_btn)
        
        layout.addLayout(button_layout)
        
        # 说明文字
        info_label = QLabel("""
        测试说明：
        1. 点击"测试历史记录导出GPX"按钮，应该弹出GPX导出设置面板
        2. 点击"测试设置弹出面板"按钮，应该弹出设置面板
        3. 当主窗口失去焦点时，所有弹出面板应该自动关闭
        4. 当主窗口移动或缩放时，弹出面板应该跟随移动
        5. 按ESC键应该关闭弹出面板
        
        测试步骤：
        - 打开弹出面板后，点击其他应用程序使主窗口失去焦点
        - 拖动主窗口移动位置，观察弹出面板是否跟随
        - 调整主窗口大小，观察弹出面板位置是否正确更新
        """)
        info_label.setStyleSheet("color: #666; font-size: 12px; margin: 10px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 添加弹簧
        layout.addStretch()
        
    def test_history_export_gpx(self):
        """测试历史记录导出GPX功能"""
        print("测试历史记录导出GPX功能")
        
        # 模拟历史记录数据
        history_data = {
            'start': '北京天安门',
            'end': '上海外滩',
            'distance': 1200000,  # 1200公里
            'duration': 43200,    # 12小时
            'route_points': [
                [116.3974, 39.9093],  # 北京天安门
                [116.4074, 39.9193],  # 中间点1
                [121.4944, 31.2304],  # 上海外滩
            ]
        }
        
        # 创建模拟的GPX导出弹出面板
        popup = self.create_mock_gpx_popup(history_data)
        self.register_popup(popup)
        
        # 显示弹出面板
        popup.show()
        popup.move(self.x() + self.width() + 10, self.y() + 50)
        
    def test_settings_popup(self):
        """测试设置弹出面板"""
        print("测试设置弹出面板")
        
        # 创建模拟的设置弹出面板
        popup = self.create_mock_settings_popup()
        self.register_popup(popup)
        
        # 显示弹出面板
        popup.show()
        popup.move(self.x() + self.width() + 10, self.y() + 100)
        
    def create_mock_gpx_popup(self, route_data):
        """创建模拟的GPX导出弹出面板"""
        popup = QWidget()
        popup.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        popup.setFixedSize(320, 200)
        popup.setStyleSheet("""
            QWidget {
                background-color: #4A90E2;
                border-radius: 8px;
                border: 1px solid rgba(0, 0, 0, 0.15);
                color: white;
                font-family: "Microsoft YaHei";
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.9);
                color: #4A90E2;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(popup)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # 标题
        title = QLabel("导出GPX文件")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)
        
        # 路线信息
        info = QLabel(f"路线: {route_data['start']} → {route_data['end']}")
        layout.addWidget(info)
        
        # 按钮
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(popup.hide)
        export_btn = QPushButton("确认导出")
        export_btn.clicked.connect(lambda: self.mock_export_confirmed(popup))
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(export_btn)
        layout.addLayout(button_layout)
        
        # 添加ESC键支持
        def keyPressEvent(event):
            if event.key() == Qt.Key_Escape:
                popup.hide()
            else:
                QWidget.keyPressEvent(popup, event)
        
        popup.keyPressEvent = keyPressEvent
        popup.setFocusPolicy(Qt.StrongFocus)
        
        return popup
        
    def create_mock_settings_popup(self):
        """创建模拟的设置弹出面板"""
        popup = QWidget()
        popup.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        popup.setFixedSize(400, 300)
        popup.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 2px solid rgba(0, 123, 255, 0.2);
                font-family: "Microsoft YaHei";
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        
        layout = QVBoxLayout(popup)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = QLabel("设置")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(title)
        
        # 设置项
        setting_label = QLabel("这是一个模拟的设置面板")
        setting_label.setStyleSheet("color: #666; margin: 20px 0;")
        layout.addWidget(setting_label)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(popup.hide)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        # 添加ESC键支持
        def keyPressEvent(event):
            if event.key() == Qt.Key_Escape:
                popup.hide()
            else:
                QWidget.keyPressEvent(popup, event)
        
        popup.keyPressEvent = keyPressEvent
        popup.setFocusPolicy(Qt.StrongFocus)
        
        return popup
        
    def mock_export_confirmed(self, popup):
        """模拟导出确认"""
        print("模拟GPX导出确认")
        popup.hide()
        
    def register_popup(self, popup):
        """注册弹出面板"""
        if popup not in self.active_popups:
            self.active_popups.append(popup)
            # 连接关闭事件
            popup.destroyed.connect(lambda: self.unregister_popup(popup))
            
    def unregister_popup(self, popup):
        """注销弹出面板"""
        if popup in self.active_popups:
            self.active_popups.remove(popup)
            
    def close_all_popups(self):
        """关闭所有弹出面板"""
        print(f"关闭 {len(self.active_popups)} 个弹出面板")
        for popup in self.active_popups[:]:
            if popup and popup.isVisible():
                popup.hide()
                
    def update_popup_positions(self):
        """更新所有弹出面板的位置"""
        current_geometry = self.geometry()
        
        if hasattr(self, 'last_window_geometry'):
            dx = current_geometry.x() - self.last_window_geometry.x()
            dy = current_geometry.y() - self.last_window_geometry.y()
            
            print(f"窗口移动: dx={dx}, dy={dy}")
            
            for popup in self.active_popups:
                if popup and popup.isVisible():
                    current_pos = popup.pos()
                    new_pos = current_pos + QPoint(dx, dy)
                    popup.move(new_pos)
                    print(f"弹出面板移动到: {new_pos.x()}, {new_pos.y()}")
        
        self.last_window_geometry = current_geometry
        
    def eventFilter(self, obj, event):
        """事件过滤器"""
        from PyQt5.QtCore import QEvent
        
        if obj == self:
            if event.type() == QEvent.WindowDeactivate:
                print("主窗口失去焦点，关闭所有弹出面板")
                self.close_all_popups()
            elif event.type() == QEvent.Move:
                print("主窗口移动")
                self.update_popup_positions()
            elif event.type() == QEvent.Resize:
                print("主窗口大小改变")
                self.update_popup_positions()
        
        return super().eventFilter(obj, event)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    window = TestPopupManagement()
    window.show()
    
    print("弹出面板管理测试程序已启动")
    print("测试功能:")
    print("1. 历史记录导出GPX按钮点击后弹出设置面板")
    print("2. 主程序失去焦点时自动关闭所有弹出面板")
    print("3. 主程序窗口移动/缩放时弹出面板跟随移动")
    print("4. ESC键关闭弹出面板")
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
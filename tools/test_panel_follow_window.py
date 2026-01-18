#!/usr/bin/env python3
"""
测试面板跟随窗口移动功能
"""

import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QLineEdit)
from PyQt5.QtCore import Qt, QPoint, QRect, QTimer
from PyQt5.QtGui import QFont

class MockRoutePlanPanel(QWidget):
    """模拟路线规划面板"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setFocusPolicy(Qt.StrongFocus)
        self._init_ui()
        
    def _init_ui(self):
        self.setStyleSheet("""
            MockRoutePlanPanel {
                background-color: #4A90E2;
                border-radius: 8px;
                border: 1px solid rgba(0, 0, 0, 0.15);
            }
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
            }
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.9);
                border: none;
                border-radius: 4px;
                padding: 8px;
                margin: 5px;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.9);
                color: #4A90E2;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                margin: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # 标题
        title = QLabel("路线规划")
        layout.addWidget(title)
        
        # 起点输入
        start_input = QLineEdit()
        start_input.setPlaceholderText("请输入起点")
        layout.addWidget(start_input)
        
        # 终点输入
        end_input = QLineEdit()
        end_input.setPlaceholderText("请输入终点")
        layout.addWidget(end_input)
        
        # 按钮
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("取消")
        plan_btn = QPushButton("规划路线")
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(plan_btn)
        layout.addLayout(button_layout)
        
        self.setFixedSize(300, 200)

class MockGpxExportPopup(QWidget):
    """模拟GPX导出弹出面板"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self._init_ui()
        
    def _init_ui(self):
        self.setStyleSheet("""
            MockGpxExportPopup {
                background-color: #4A90E2;
                border-radius: 8px;
                border: 1px solid rgba(0, 0, 0, 0.15);
            }
            QLabel {
                color: white;
                font-size: 13px;
                padding: 8px;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.9);
                color: #4A90E2;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                margin: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # 标题
        title = QLabel("导出GPX文件")
        title.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        layout.addWidget(title)
        
        # 信息
        info = QLabel("路线: 测试路线\n距离: 5.2公里\n预计时间: 15分钟")
        layout.addWidget(info)
        
        # 时间设置
        time_label = QLabel("起始时间: 2026-01-18 18:00")
        layout.addWidget(time_label)
        
        # 按钮
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("取消")
        export_btn = QPushButton("确认导出")
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(export_btn)
        layout.addLayout(button_layout)
        
        self.setFixedSize(280, 180)
    
    def show_at_position(self, pos):
        """在指定位置显示弹出面板"""
        self.move(pos)
        self.show()
        self.raise_()
        self.activateWindow()

class TestMainWindow(QMainWindow):
    """测试主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("面板跟随窗口移动测试")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 创建搜索容器（模拟主应用的搜索框）
        self.search_container = QWidget()
        self.search_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 6px;
                border: 1px solid rgba(0, 0, 0, 0.15);
            }
        """)
        search_layout = QHBoxLayout(self.search_container)
        search_layout.setContentsMargins(8, 6, 8, 6)
        
        search_input = QLineEdit()
        search_input.setPlaceholderText("搜索地点...")
        search_input.setStyleSheet("""
            QLineEdit {
                background-color: #f5f5f5;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 13px;
            }
        """)
        search_layout.addWidget(search_input)
        
        # 路线按钮
        route_btn = QPushButton("路线")
        route_btn.clicked.connect(self.show_route_panel)
        route_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        search_layout.addWidget(route_btn)
        
        self.search_container.setFixedHeight(50)
        layout.addWidget(self.search_container)
        
        # 添加一些填充空间
        layout.addStretch()
        
        # 控制按钮
        control_layout = QHBoxLayout()
        
        move_btn = QPushButton("移动窗口")
        move_btn.clicked.connect(self.move_window)
        control_layout.addWidget(move_btn)
        
        resize_btn = QPushButton("调整大小")
        resize_btn.clicked.connect(self.resize_window)
        control_layout.addWidget(resize_btn)
        
        gpx_btn = QPushButton("显示GPX面板")
        gpx_btn.clicked.connect(self.show_gpx_panel)
        control_layout.addWidget(gpx_btn)
        
        layout.addLayout(control_layout)
        
        # 创建面板
        self.route_plan_panel = MockRoutePlanPanel(self)
        self.route_plan_panel.hide()
        
        self.gpx_export_popup = MockGpxExportPopup(self)
        self.gpx_export_popup.hide()
        
        # 状态标签
        self.status_label = QLabel("点击'路线'按钮显示路线规划面板，然后移动窗口测试跟随效果")
        self.status_label.setStyleSheet("QLabel { padding: 10px; background-color: #f0f0f0; }")
        layout.addWidget(self.status_label)
        
    def show_route_panel(self):
        """显示路线规划面板"""
        # 获取搜索容器的全局位置
        container_rect = self.search_container.rect()
        container_global_pos = self.search_container.mapToGlobal(container_rect.topLeft())
        
        # 设置路线规划面板的位置
        self.route_plan_panel.move(container_global_pos.x(), container_global_pos.y())
        self.route_plan_panel.show()
        self.route_plan_panel.raise_()
        self.route_plan_panel.setFocus()
        
        self.status_label.setText(f"路线规划面板已显示在位置: ({container_global_pos.x()}, {container_global_pos.y()})")
        
    def show_gpx_panel(self):
        """显示GPX导出面板"""
        if not self.route_plan_panel.isVisible():
            self.status_label.setText("请先显示路线规划面板")
            return
            
        # 计算GPX面板位置（在路线面板右侧）
        panel_global_pos = self.route_plan_panel.mapToGlobal(self.route_plan_panel.rect().topLeft())
        panel_rect = self.route_plan_panel.rect()
        
        popup_x = panel_global_pos.x() + panel_rect.width() + 10
        popup_y = panel_global_pos.y() + 50
        
        self.gpx_export_popup.show_at_position(QPoint(popup_x, popup_y))
        
        self.status_label.setText(f"GPX导出面板已显示在位置: ({popup_x}, {popup_y})")
        
    def move_window(self):
        """移动窗口"""
        current_pos = self.pos()
        new_pos = QPoint(current_pos.x() + 50, current_pos.y() + 30)
        self.move(new_pos)
        self.status_label.setText(f"窗口已移动到: ({new_pos.x()}, {new_pos.y()})")
        
    def resize_window(self):
        """调整窗口大小"""
        current_size = self.size()
        new_width = current_size.width() + 50
        new_height = current_size.height() + 30
        self.resize(new_width, new_height)
        self.status_label.setText(f"窗口大小已调整为: {new_width} x {new_height}")
        
    def moveEvent(self, event):
        """窗口移动事件 - 更新面板位置"""
        super().moveEvent(event)
        self.update_panel_positions()
        
    def resizeEvent(self, event):
        """窗口大小变化事件 - 更新面板位置"""
        super().resizeEvent(event)
        self.update_panel_positions()
        
    def update_panel_positions(self):
        """更新面板位置"""
        # 更新路线规划面板位置
        if self.route_plan_panel.isVisible():
            container_rect = self.search_container.rect()
            container_global_pos = self.search_container.mapToGlobal(container_rect.topLeft())
            
            self.route_plan_panel.move(container_global_pos.x(), container_global_pos.y())
            
            print(f"[更新] 路线规划面板位置: ({container_global_pos.x()}, {container_global_pos.y()})")
            
        # 更新GPX导出面板位置
        if (self.gpx_export_popup.isVisible() and self.route_plan_panel.isVisible()):
            panel_global_pos = self.route_plan_panel.mapToGlobal(self.route_plan_panel.rect().topLeft())
            panel_rect = self.route_plan_panel.rect()
            
            popup_x = panel_global_pos.x() + panel_rect.width() + 10
            popup_y = panel_global_pos.y() + 50
            
            self.gpx_export_popup.move(popup_x, popup_y)
            
            print(f"[更新] GPX导出面板位置: ({popup_x}, {popup_y})")

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    window = TestMainWindow()
    window.show()
    
    print("=" * 60)
    print("面板跟随窗口移动测试")
    print("=" * 60)
    print("操作说明:")
    print("1. 点击'路线'按钮显示路线规划面板")
    print("2. 点击'显示GPX面板'按钮显示GPX导出面板")
    print("3. 点击'移动窗口'或'调整大小'按钮测试面板跟随效果")
    print("4. 也可以直接拖拽窗口标题栏移动窗口")
    print("5. 观察面板是否跟随主窗口移动")
    print("=" * 60)
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
简化的导出按钮逻辑测试
"""

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QPushButton, QLabel, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon


class MockRouteHistoryItem(QWidget):
    """模拟路线历史记录项"""
    
    export_gpx_clicked = pyqtSignal(dict)
    
    def __init__(self, history_data: dict, parent=None):
        super().__init__(parent)
        self.history_data = history_data
        self.is_selected = False
        self.has_route_data = False
        self._init_ui()
    
    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # 路线文本
        start = self.history_data.get('start', '')
        end = self.history_data.get('end', '')
        route_label = QLabel(f"{start} → {end}")
        route_label.setStyleSheet("QLabel { color: white; font-size: 13px; }")
        layout.addWidget(route_label, 1)
        
        # 导出按钮
        self.export_button = QPushButton("导出")
        self.export_button.setFixedSize(60, 24)
        self.export_button.clicked.connect(lambda: self.export_gpx_clicked.emit(self.history_data))
        self.export_button.setEnabled(False)  # 初始禁用
        self._update_button_style()
        layout.addWidget(self.export_button)
    
    def set_selected(self, selected: bool):
        """设置选中状态"""
        self.is_selected = selected
        self._update_export_button_state()
        
        # 更新背景色
        if selected:
            self.setStyleSheet("MockRouteHistoryItem { background-color: rgba(255, 255, 255, 0.15); border-radius: 4px; }")
        else:
            self.setStyleSheet("")
    
    def set_route_data_available(self, available: bool):
        """设置路线数据是否可用"""
        self.has_route_data = available
        self._update_export_button_state()
    
    def _update_export_button_state(self):
        """更新导出按钮状态"""
        # 只有当记录被选中且有路线数据时才启用导出按钮
        should_enable = self.is_selected and self.has_route_data
        self.export_button.setEnabled(should_enable)
        self._update_button_style()
        
        # 更新工具提示
        if self.is_selected:
            if self.has_route_data:
                self.export_button.setToolTip("导出GPX文件")
            else:
                self.export_button.setToolTip("该记录缺少路线数据，无法导出")
        else:
            self.export_button.setToolTip("请先选择此路线记录")
    
    def _update_button_style(self):
        """更新按钮样式"""
        if self.export_button.isEnabled():
            # 启用状态：白色背景
            self.export_button.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    color: #4A90E2;
                    border: 1px solid #4A90E2;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #f0f0f0;
                }
            """)
        else:
            # 禁用状态：灰色背景
            self.export_button.setStyleSheet("""
                QPushButton {
                    background-color: #cccccc;
                    color: #666666;
                    border: 1px solid #999999;
                    border-radius: 4px;
                }
                QPushButton:disabled {
                    opacity: 0.6;
                }
            """)


class MockRoutePlanPanel(QWidget):
    """模拟路线规划面板"""
    
    history_selected = pyqtSignal(dict)
    history_export_gpx_clicked = pyqtSignal(dict)
    panel_closed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.history_widgets = []
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
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.9);
                color: #4A90E2;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: white;
            }
            QListWidget {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 标题
        title_label = QLabel("路线规划面板")
        layout.addWidget(title_label)
        
        # 历史记录列表
        history_label = QLabel("路线搜索历史记录")
        layout.addWidget(history_label)
        
        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self._on_history_clicked)
        layout.addWidget(self.history_list)
        
        # 关闭按钮
        close_button = QPushButton("关闭面板")
        close_button.clicked.connect(self._on_close_clicked)
        layout.addWidget(close_button)
        
        self.setFixedSize(400, 500)
    
    def load_history(self, history_list: list):
        """加载历史记录"""
        self.history_list.clear()
        self.history_widgets = []
        
        for record in history_list:
            # 创建历史记录项widget
            history_widget = MockRouteHistoryItem(record)
            
            # 确保初始状态：未选中，无路线数据（导出按钮禁用）
            history_widget.set_selected(False)
            history_widget.set_route_data_available(False)
            
            # 连接信号
            history_widget.export_gpx_clicked.connect(self.history_export_gpx_clicked.emit)
            
            # 创建列表项
            item = QListWidgetItem()
            item.setData(Qt.UserRole, record)
            item.setSizeHint(history_widget.sizeHint())
            
            self.history_list.addItem(item)
            self.history_list.setItemWidget(item, history_widget)
            
            # 保存引用
            self.history_widgets.append(history_widget)
        
        print(f"[面板] 加载了 {len(history_list)} 条历史记录，所有导出按钮初始为禁用状态")
    
    def _on_history_clicked(self, item: QListWidgetItem):
        """历史记录点击处理"""
        history_data = item.data(Qt.UserRole)
        if history_data:
            # 更新选中状态
            self._update_history_selection(item)
            
            # 检查路线数据状态
            self._check_and_update_route_data_status(history_data)
            
            # 发送信号
            self.history_selected.emit(history_data)
    
    def _update_history_selection(self, selected_item: QListWidgetItem):
        """更新历史记录选中状态"""
        selected_row = self.history_list.row(selected_item)
        
        for i, widget in enumerate(self.history_widgets):
            is_selected = (i == selected_row)
            widget.set_selected(is_selected)
    
    def _check_and_update_route_data_status(self, history_data: dict):
        """检查并更新路线数据状态"""
        route_points = history_data.get('route_points', [])
        has_route_data = bool(route_points and len(route_points) > 0)
        
        for widget in self.history_widgets:
            if widget.history_data == history_data:
                widget.set_route_data_available(has_route_data)
                print(f"[面板] 历史记录路线数据状态: {history_data.get('start', 'N/A')} → {history_data.get('end', 'N/A')}, 有数据: {has_route_data}")
                break
    
    def _on_close_clicked(self):
        """关闭按钮点击"""
        self.hide()
        self.panel_closed.emit()
    
    def keyPressEvent(self, event):
        """键盘事件处理"""
        if event.key() == Qt.Key_Escape:
            print("[面板] ESC键关闭面板")
            self.hide()
            self.panel_closed.emit()
            event.accept()
        else:
            super().keyPressEvent(event)


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("导出按钮逻辑测试 - 简化版")
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 说明
        info_label = QLabel("""
导出按钮逻辑测试：

1. 面板刚打开时，所有导出按钮都是灰色（禁用）
2. 点击历史记录后：
   - 有路线数据的记录：导出按钮变白色（启用）
   - 无路线数据的记录：导出按钮保持灰色（禁用）
3. 按ESC键可以关闭面板

测试数据：
- 记录1：西安钟楼 → 大雁塔 (有路线数据)
- 记录2：西安火车站 → 西安北站 (无路线数据)
- 记录3：曲江池 → 大唐芙蓉园 (有路线数据)
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
        
        show_btn = QPushButton("显示路线规划面板")
        show_btn.clicked.connect(self.show_panel)
        button_layout.addWidget(show_btn)
        
        hide_btn = QPushButton("隐藏面板")
        hide_btn.clicked.connect(self.hide_panel)
        button_layout.addWidget(hide_btn)
        
        check_btn = QPushButton("检查按钮状态")
        check_btn.clicked.connect(self.check_button_states)
        button_layout.addWidget(check_btn)
        
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
        
        # 创建面板
        self.route_panel = MockRoutePlanPanel(self)
        self.route_panel.history_selected.connect(self.on_history_selected)
        self.route_panel.history_export_gpx_clicked.connect(self.on_export_clicked)
        self.route_panel.panel_closed.connect(self.on_panel_closed)
        self.route_panel.hide()
        
        # 测试数据
        self.test_history = [
            {
                'start': '西安钟楼',
                'end': '大雁塔',
                'route_points': [[108.9434, 34.2583], [108.9649, 34.2244]]  # 有数据
            },
            {
                'start': '西安火车站',
                'end': '西安北站',
                'route_points': []  # 无数据
            },
            {
                'start': '曲江池',
                'end': '大唐芙蓉园',
                'route_points': [[108.9789, 34.2089], [108.9567, 34.2156]]  # 有数据
            }
        ]
        
        # 加载测试数据
        self.route_panel.load_history(self.test_history)
    
    def show_panel(self):
        self.status_label.setText("状态: 显示路线规划面板")
        self.route_panel.show()
        self.route_panel.setFocus()  # 设置焦点以接收ESC键
        print("[测试] 面板已显示")
        self.check_button_states()
    
    def hide_panel(self):
        self.status_label.setText("状态: 隐藏面板")
        self.route_panel.hide()
        print("[测试] 面板已隐藏")
    
    def check_button_states(self):
        """检查按钮状态"""
        print("=== 检查按钮状态 ===")
        for i, widget in enumerate(self.route_panel.history_widgets):
            is_enabled = widget.export_button.isEnabled()
            is_selected = widget.is_selected
            has_route_data = widget.has_route_data
            
            print(f"记录 {i+1}: {widget.history_data.get('start', 'N/A')} → {widget.history_data.get('end', 'N/A')}")
            print(f"  选中: {is_selected}, 有数据: {has_route_data}, 按钮启用: {is_enabled}")
    
    def on_history_selected(self, history_data):
        start = history_data.get('start', 'N/A')
        end = history_data.get('end', 'N/A')
        has_data = bool(history_data.get('route_points', []))
        
        self.status_label.setText(f"状态: 选中 {start} → {end}，数据: {'有' if has_data else '无'}")
        print(f"[测试] 选中: {start} → {end}, 有数据: {has_data}")
        self.check_button_states()
    
    def on_export_clicked(self, history_data):
        start = history_data.get('start', 'N/A')
        end = history_data.get('end', 'N/A')
        self.status_label.setText(f"状态: 点击导出 {start} → {end}")
        print(f"[测试] 点击导出: {start} → {end}")
    
    def on_panel_closed(self):
        self.status_label.setText("状态: 面板已关闭")
        print("[测试] 面板已关闭")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = TestWindow()
    window.show()
    
    print("=== 导出按钮逻辑测试 ===")
    print("1. 点击'显示路线规划面板'")
    print("2. 观察初始状态（所有按钮应该是灰色）")
    print("3. 点击不同的历史记录，观察按钮状态变化")
    print("4. 按ESC键测试面板关闭")
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
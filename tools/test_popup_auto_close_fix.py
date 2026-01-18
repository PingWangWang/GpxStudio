#!/usr/bin/env python3
"""
测试弹出面板自动关闭修复
验证点击设置按钮时面板不会自动关闭
"""

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QPushButton, QLabel, QLineEdit, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal, QDateTime, QTimer, QEvent
from PyQt5.QtGui import QFont


class MockDateTimePicker(QWidget):
    """模拟日期时间选择器"""
    
    dateTimeChanged = pyqtSignal(QDateTime)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        label = QLabel("时间日期设置面板")
        label.setStyleSheet("QLabel { font-weight: bold; color: #333; }")
        layout.addWidget(label)
        
        info_label = QLabel("测试：此面板显示时，父面板不应该自动关闭")
        info_label.setStyleSheet("QLabel { color: #666; font-size: 12px; }")
        layout.addWidget(info_label)
        
        confirm_btn = QPushButton("确认选择")
        confirm_btn.clicked.connect(self._on_confirm)
        layout.addWidget(confirm_btn)
    
    def _on_confirm(self):
        self.dateTimeChanged.emit(QDateTime.currentDateTime())
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            print("[时间日期设置] ESC键关闭")
            parent_widget = self.parent()
            if parent_widget and hasattr(parent_widget, 'hide'):
                parent_widget.hide()
                event.accept()
                return
        super().keyPressEvent(event)


class MockGpxExportPopup(QWidget):
    """模拟GPX导出弹出面板 - 修复版本"""
    
    closed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 使用Tool而不是ToolTip，避免自动关闭
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setFocusPolicy(Qt.StrongFocus)
        self.picker_popup = None
        self.installEventFilter(self)
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
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 13px;
                color: #333333;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 标题
        title_label = QLabel("GPX设置面板 - 修复版本")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 说明
        info_label = QLabel("测试：点击设置按钮时，此面板不应该自动关闭")
        info_label.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
        """)
        layout.addWidget(info_label)
        
        # 时间设置区域
        time_container = QWidget()
        time_layout = QHBoxLayout(time_container)
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(8)
        
        time_label = QLabel("起始时间:")
        time_layout.addWidget(time_label)
        
        # 时间文本编辑框
        self.datetime_text_edit = QLineEdit()
        self.datetime_text_edit.setText(QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm"))
        self.datetime_text_edit.setReadOnly(True)
        time_layout.addWidget(self.datetime_text_edit, 1)
        
        # 设置按钮
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setFixedSize(32, 32)
        self.settings_btn.setToolTip("设置时间")
        self.settings_btn.clicked.connect(self._show_datetime_picker)
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.5);
            }
        """)
        time_layout.addWidget(self.settings_btn)
        
        layout.addWidget(time_container)
        
        # 按钮区域
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self._on_cancel)
        button_layout.addWidget(cancel_btn)
        
        export_btn = QPushButton("确认导出")
        export_btn.clicked.connect(self._on_export)
        button_layout.addWidget(export_btn)
        
        layout.addWidget(button_container)
        
        self.setFixedWidth(320)
    
    def _show_datetime_picker(self):
        """显示日期时间选择器"""
        print("[GPX设置] 点击设置按钮，显示时间日期选择器")
        
        if self.picker_popup and self.picker_popup.isVisible():
            self.picker_popup.hide()
            return
        
        # 创建弹出窗口 - 使用Tool而不是ToolTip
        self.picker_popup = QFrame()
        self.picker_popup.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.picker_popup.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 6px;
            }
        """)
        self.picker_popup.setFocusPolicy(Qt.StrongFocus)
        
        # 设置父窗口，确保层级关系正确
        self.picker_popup.setParent(self, Qt.Tool)
        
        # 重写键盘事件
        def keyPressEvent(event):
            if event.key() == Qt.Key_Escape:
                print("[GPX设置] ESC键关闭时间日期设置面板")
                self.picker_popup.hide()
                self.setFocus()
                event.accept()
            else:
                QFrame.keyPressEvent(self.picker_popup, event)
        
        self.picker_popup.keyPressEvent = keyPressEvent
        
        # 添加选择器
        popup_layout = QVBoxLayout(self.picker_popup)
        popup_layout.setContentsMargins(0, 0, 0, 0)
        
        picker = MockDateTimePicker()
        picker.dateTimeChanged.connect(self._on_datetime_changed)
        popup_layout.addWidget(picker)
        
        # 显示弹出窗口（在设置按钮下方）
        button_global_pos = self.settings_btn.mapToGlobal(self.settings_btn.rect().bottomLeft())
        popup_x = button_global_pos.x() - 200  # 向左偏移
        popup_y = button_global_pos.y() + 5
        
        self.picker_popup.move(popup_x, popup_y)
        self.picker_popup.adjustSize()
        self.picker_popup.show()
        self.picker_popup.raise_()
        self.picker_popup.activateWindow()
        self.picker_popup.setFocus()
        
        print("[GPX设置] 时间日期选择器已显示")
        print("[GPX设置] 重要：GPX面板应该保持显示，不应该自动关闭")
    
    def _on_datetime_changed(self, datetime):
        """日期时间改变处理"""
        self.datetime_text_edit.setText(datetime.toString("yyyy-MM-dd hh:mm"))
        if self.picker_popup:
            self.picker_popup.hide()
        self.setFocus()
        print("[GPX设置] 选择完成，焦点返回给GPX设置面板")
    
    def _on_cancel(self):
        self.hide()
        self.closed.emit()
    
    def _on_export(self):
        print("[GPX设置] 确认导出")
        self.hide()
        self.closed.emit()
    
    def show_at_position(self, pos):
        self.move(pos)
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus()
        print("[GPX设置] 显示GPX设置面板")
    
    def eventFilter(self, obj, event):
        """事件过滤器 - 防止在显示时间日期选择器时自动关闭"""
        # 如果正在显示时间日期选择器，忽略焦点丢失事件
        if hasattr(self, 'picker_popup') and self.picker_popup and self.picker_popup.isVisible():
            if event.type() == QEvent.WindowDeactivate or event.type() == QEvent.FocusOut:
                print("[GPX设置] 时间日期选择器显示中，忽略焦点丢失事件")
                return True  # 拦截事件，防止自动关闭
        
        return super().eventFilter(obj, event)
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            # 检查是否有时间日期设置面板正在显示
            if self.picker_popup and self.picker_popup.isVisible():
                self.picker_popup.hide()
                self.setFocus()
                print("[GPX设置] ESC键关闭时间日期设置面板")
                event.accept()
                return
            
            # 如果没有子弹出窗口，则关闭GPX设置面板
            print("[GPX设置] ESC键关闭GPX设置面板")
            self.hide()
            self.closed.emit()
            event.accept()
        else:
            super().keyPressEvent(event)


class MockRoutePlanPanel(QWidget):
    """模拟路线规划面板"""
    
    cancel_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
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
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 标题
        title_label = QLabel("路线规划面板")
        layout.addWidget(title_label)
        
        # 说明
        info_label = QLabel("测试：点击GPX面板的设置按钮时，此面板不应该自动关闭")
        info_label.setStyleSheet("QLabel { font-size: 12px; }")
        layout.addWidget(info_label)
        
        # 导出GPX按钮
        export_btn = QPushButton("显示GPX设置面板")
        export_btn.clicked.connect(self._show_gpx_popup)
        layout.addWidget(export_btn)
        
        # 关闭按钮
        close_button = QPushButton("关闭面板")
        close_button.clicked.connect(self._on_close_clicked)
        layout.addWidget(close_button)
        
        self.setFixedSize(300, 200)
    
    def _show_gpx_popup(self):
        """显示GPX导出面板"""
        parent_app = self.parent()
        if parent_app:
            parent_app.show_gpx_popup()
    
    def _on_close_clicked(self):
        self.hide()
        self.cancel_clicked.emit()
    
    def show_and_focus(self):
        self.show()
        self.raise_()
        self.setFocus()
        print("[路线规划] 显示路线规划面板")


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("弹出面板自动关闭修复测试")
        self.setGeometry(100, 100, 900, 700)
        
        # 安装事件过滤器模拟应用程序行为
        self.installEventFilter(self)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 说明
        info_label = QLabel("""
弹出面板自动关闭修复测试：

问题描述：
点击GPX设置面板的设置按钮时，路线规划面板和GPX设置面板会自动关闭

修复方案：
1. 将窗口标志从Qt.ToolTip改为Qt.Tool，避免自动关闭
2. 在事件过滤器中检查时间日期选择器是否显示，如果显示则不关闭父面板
3. 设置正确的父子关系和焦点管理

测试步骤：
1. 点击'显示路线规划面板'
2. 点击'显示GPX设置面板'
3. 点击GPX面板中的⚙设置按钮
4. 观察：路线规划面板和GPX设置面板应该保持显示
5. 按ESC键测试层级关闭功能

预期结果：
- 点击设置按钮时，父面板不会自动关闭
- ESC键仍然可以层级关闭面板
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
        
        show_route_btn = QPushButton("显示路线规划面板")
        show_route_btn.clicked.connect(self.show_route_panel)
        button_layout.addWidget(show_route_btn)
        
        show_gpx_btn = QPushButton("显示GPX设置面板")
        show_gpx_btn.clicked.connect(self.show_gpx_popup)
        button_layout.addWidget(show_gpx_btn)
        
        hide_all_btn = QPushButton("隐藏所有面板")
        hide_all_btn.clicked.connect(self.hide_all_panels)
        button_layout.addWidget(hide_all_btn)
        
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
        self.route_plan_panel = MockRoutePlanPanel(self)
        self.route_plan_panel.cancel_clicked.connect(self.on_route_panel_closed)
        self.route_plan_panel.hide()
        
        self.gpx_export_popup = None
    
    def eventFilter(self, obj, event):
        """事件过滤器 - 模拟应用程序的弹出面板管理"""
        if obj == self:
            if event.type() == QEvent.WindowDeactivate:
                # 检查是否有GPX导出面板正在显示时间日期选择器
                if hasattr(self, 'gpx_export_popup') and self.gpx_export_popup and self.gpx_export_popup.isVisible():
                    if hasattr(self.gpx_export_popup, 'picker_popup') and self.gpx_export_popup.picker_popup and self.gpx_export_popup.picker_popup.isVisible():
                        print("[测试应用] 时间日期选择器显示中，不关闭弹出面板")
                        return super().eventFilter(obj, event)  # 不关闭面板
                
                print("[测试应用] 主窗口失去焦点，关闭所有弹出面板")
                self.hide_all_panels()
        
        return super().eventFilter(obj, event)
    
    def show_route_panel(self):
        self.status_label.setText("状态: 显示路线规划面板")
        
        # 设置面板位置
        center_pos = self.geometry().center()
        panel_pos = center_pos - self.route_plan_panel.rect().center()
        panel_pos.setX(panel_pos.x() - 200)  # 向左偏移
        self.route_plan_panel.move(panel_pos)
        
        self.route_plan_panel.show_and_focus()
        print("[测试] 路线规划面板已显示")
    
    def show_gpx_popup(self):
        self.status_label.setText("状态: 显示GPX设置面板")
        
        if self.gpx_export_popup:
            self.gpx_export_popup.hide()
        
        self.gpx_export_popup = MockGpxExportPopup(self)
        self.gpx_export_popup.closed.connect(self.on_gpx_popup_closed)
        
        # 设置位置（在路线面板右侧）
        if self.route_plan_panel.isVisible():
            route_pos = self.route_plan_panel.pos()
            route_size = self.route_plan_panel.size()
            gpx_pos = route_pos
            gpx_pos.setX(gpx_pos.x() + route_size.width() + 20)
        else:
            center_pos = self.geometry().center()
            gpx_pos = center_pos - self.gpx_export_popup.rect().center()
        
        self.gpx_export_popup.show_at_position(gpx_pos)
        print("[测试] GPX设置面板已显示")
    
    def hide_all_panels(self):
        self.status_label.setText("状态: 隐藏所有面板")
        
        if self.gpx_export_popup:
            if hasattr(self.gpx_export_popup, 'picker_popup') and self.gpx_export_popup.picker_popup:
                self.gpx_export_popup.picker_popup.hide()
            self.gpx_export_popup.hide()
        
        self.route_plan_panel.hide()
        print("[测试] 所有面板已隐藏")
    
    def on_route_panel_closed(self):
        self.status_label.setText("状态: 路线规划面板已关闭")
        print("[测试] 路线规划面板已关闭")
    
    def on_gpx_popup_closed(self):
        self.status_label.setText("状态: GPX设置面板已关闭")
        print("[测试] GPX设置面板已关闭")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = TestWindow()
    window.show()
    
    print("=== 弹出面板自动关闭修复测试 ===")
    print("关键测试点：")
    print("1. 点击设置按钮时，父面板不应该自动关闭")
    print("2. ESC键层级关闭功能仍然正常")
    print("3. 焦点管理正确")
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
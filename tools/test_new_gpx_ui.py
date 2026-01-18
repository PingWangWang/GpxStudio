#!/usr/bin/env python3
"""
测试新的GPX设置界面
测试文本编辑框 + 设置按钮的UI，以及防止自动关闭的功能
"""

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QPushButton, QLabel, QLineEdit, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal, QDateTime, QTimer
from PyQt5.QtGui import QFont


class MockDateTimePicker(QWidget):
    """模拟日期时间选择器（最上层）"""
    
    dateTimeChanged = pyqtSignal(QDateTime)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        label = QLabel("时间日期设置面板（第4层）")
        label.setStyleSheet("QLabel { font-weight: bold; color: #333; }")
        layout.addWidget(label)
        
        info_label = QLabel("按ESC键关闭此面板")
        info_label.setStyleSheet("QLabel { color: #666; font-size: 12px; }")
        layout.addWidget(info_label)
        
        confirm_btn = QPushButton("确认选择")
        confirm_btn.clicked.connect(self._on_confirm)
        layout.addWidget(confirm_btn)
    
    def _on_confirm(self):
        self.dateTimeChanged.emit(QDateTime.currentDateTime())
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            print("[时间日期设置] ESC键关闭时间日期设置面板")
            parent_widget = self.parent()
            if parent_widget and hasattr(parent_widget, 'hide'):
                parent_widget.hide()
                event.accept()
                return
        super().keyPressEvent(event)


class MockGpxExportPopup(QWidget):
    """模拟GPX导出弹出面板（第3层）- 新UI版本"""
    
    closed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setFocusPolicy(Qt.StrongFocus)
        self.picker_popup = None
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
        title_label = QLabel("GPX设置面板（第3层）- 新UI")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 路线信息
        info_label = QLabel("路线: 测试路线\n距离: 8.5公里\n预计时间: 20分钟")
        info_label.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                padding: 8px;
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
        if self.picker_popup and self.picker_popup.isVisible():
            self.picker_popup.hide()
            return
        
        # 创建弹出窗口
        self.picker_popup = QFrame()
        self.picker_popup.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.picker_popup.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 6px;
            }
        """)
        self.picker_popup.setFocusPolicy(Qt.StrongFocus)
        
        # 重写键盘事件
        def keyPressEvent(event):
            if event.key() == Qt.Key_Escape:
                print("[GPX设置] ESC键关闭时间日期设置面板")
                self.picker_popup.hide()
                self.setFocus()
                print("[GPX设置] 焦点回到GPX设置面板")
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
        self.picker_popup.setFocus()
        
        print("[GPX设置] 显示时间日期设置面板并设置焦点")
        print("[GPX设置] 注意：GPX面板应该保持显示，不应该自动关闭")
    
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
        print("[GPX设置] 显示GPX设置面板并设置焦点")
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            # 检查是否有时间日期设置面板正在显示
            if self.picker_popup and self.picker_popup.isVisible():
                # 如果时间日期设置面板正在显示，优先关闭它
                self.picker_popup.hide()
                self.setFocus()
                print("[GPX设置] ESC键关闭时间日期设置面板，焦点回到GPX设置面板")
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
    """模拟路线规划面板（第1层）"""
    
    cancel_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
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
        title_label = QLabel("路线规划面板（第1层）")
        layout.addWidget(title_label)
        
        # 说明
        info_label = QLabel("点击'显示GPX设置面板'按钮，然后点击设置按钮测试")
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
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            # 检查是否有GPX设置面板正在显示
            parent_app = self.parent()
            while parent_app and not hasattr(parent_app, 'gpx_export_popup'):
                parent_app = parent_app.parent()
            
            if parent_app and hasattr(parent_app, 'gpx_export_popup'):
                if parent_app.gpx_export_popup and parent_app.gpx_export_popup.isVisible():
                    # 检查GPX面板是否有子弹出窗口（时间日期设置面板）
                    gpx_popup = parent_app.gpx_export_popup
                    has_child_popup = False
                    
                    # 检查时间日期设置面板
                    if hasattr(gpx_popup, 'picker_popup') and gpx_popup.picker_popup and gpx_popup.picker_popup.isVisible():
                        has_child_popup = True
                    
                    if has_child_popup:
                        # 如果有子弹出窗口，不处理ESC键，让子窗口处理
                        print("[路线规划] 有时间日期设置面板正在显示，ESC键由时间日期面板处理")
                        super().keyPressEvent(event)
                        return
                    else:
                        # 如果GPX面板显示但没有子窗口，不处理ESC键，让GPX面板处理
                        print("[路线规划] GPX设置面板正在显示，ESC键由GPX面板处理")
                        super().keyPressEvent(event)
                        return
            
            # 如果没有任何子弹出窗口显示，则关闭路线规划面板
            print("[路线规划] ESC键关闭路线规划面板")
            self.cancel_clicked.emit()
            event.accept()
        else:
            super().keyPressEvent(event)
    
    def show_and_focus(self):
        self.show()
        self.raise_()
        self.setFocus()
        print("[路线规划] 显示路线规划面板并设置焦点")


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("新GPX设置界面测试")
        self.setGeometry(100, 100, 900, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 说明
        info_label = QLabel("""
新GPX设置界面测试：

主要变化：
1. 将时间日期控件改为文本编辑框（只读）+ 设置按钮
2. 设置按钮使用Setting_white.png图标（这里用⚙符号代替）
3. 点击设置按钮弹出日期时间设置界面
4. 重要：弹出时间日期设置界面时，GPX面板和路线规划面板不应该自动关闭

测试步骤：
1. 点击'显示路线规划面板'
2. 点击'显示GPX设置面板'
3. 点击时间设置右侧的⚙按钮
4. 观察：GPX面板和路线规划面板应该保持显示
5. 按ESC键测试层级关闭功能

预期行为：
- 第1次ESC：关闭时间日期设置面板
- 第2次ESC：关闭GPX设置面板
- 第3次ESC：关闭路线规划面板
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
        
        # 层级状态显示
        self.hierarchy_label = QLabel("当前层级: 无面板显示")
        self.hierarchy_label.setStyleSheet("""
            QLabel {
                background-color: #fff3cd;
                color: #856404;
                border: 1px solid #ffeaa7;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.hierarchy_label)
        
        # 创建面板
        self.route_plan_panel = MockRoutePlanPanel(self)
        self.route_plan_panel.cancel_clicked.connect(self.on_route_panel_closed)
        self.route_plan_panel.hide()
        
        self.gpx_export_popup = None
        
        # 定时器更新层级状态
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_hierarchy_status)
        self.status_timer.start(200)  # 每200ms更新一次
    
    def _update_hierarchy_status(self):
        """更新层级状态显示"""
        hierarchy = []
        
        if self.route_plan_panel.isVisible():
            hierarchy.append("第1层: 路线规划面板")
        
        if self.gpx_export_popup and self.gpx_export_popup.isVisible():
            hierarchy.append("第3层: GPX设置面板")
            
            # 检查时间日期设置面板
            if (hasattr(self.gpx_export_popup, 'picker_popup') and 
                self.gpx_export_popup.picker_popup and 
                self.gpx_export_popup.picker_popup.isVisible()):
                hierarchy.append("第4层: 时间日期设置面板")
        
        if hierarchy:
            self.hierarchy_label.setText("当前层级: " + " → ".join(hierarchy))
        else:
            self.hierarchy_label.setText("当前层级: 无面板显示")
    
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
    
    print("=== 新GPX设置界面测试 ===")
    print("测试重点：")
    print("1. 文本编辑框 + 设置按钮的新UI")
    print("2. 点击设置按钮弹出时间日期设置界面")
    print("3. 弹出时间日期设置界面时，GPX面板和路线规划面板不应该自动关闭")
    print("4. ESC键层级关闭功能")
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
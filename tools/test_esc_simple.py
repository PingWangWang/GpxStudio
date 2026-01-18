#!/usr/bin/env python3
"""
简化的ESC键测试
"""

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QPushButton, QLabel, QFrame, QLineEdit)
from PyQt5.QtCore import Qt, QDateTime, pyqtSignal
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
        
        label = QLabel("模拟日期时间选择器")
        label.setStyleSheet("QLabel { font-weight: bold; color: #333; }")
        layout.addWidget(label)
        
        info_label = QLabel("按ESC键关闭此选择器")
        info_label.setStyleSheet("QLabel { color: #666; font-size: 12px; }")
        layout.addWidget(info_label)
        
        confirm_btn = QPushButton("确认选择")
        confirm_btn.clicked.connect(self._on_confirm)
        layout.addWidget(confirm_btn)
    
    def _on_confirm(self):
        self.dateTimeChanged.emit(QDateTime.currentDateTime())
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            print("[日期时间选择器] ESC键关闭选择器")
            parent_widget = self.parent()
            if parent_widget and hasattr(parent_widget, 'hide'):
                parent_widget.hide()
                event.accept()
                return
        super().keyPressEvent(event)


class MockDateTimeEdit(QWidget):
    """模拟日期时间编辑控件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.picker_popup = None
        self._init_ui()
    
    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.text_edit = QLineEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setText(QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm"))
        layout.addWidget(self.text_edit)
        
        dropdown_btn = QPushButton("▼")
        dropdown_btn.setFixedSize(30, 30)
        dropdown_btn.clicked.connect(self._show_picker)
        layout.addWidget(dropdown_btn)
    
    def _show_picker(self):
        if self.picker_popup and self.picker_popup.isVisible():
            self.picker_popup.hide()
            return
        
        # 创建弹出窗口
        self.picker_popup = QFrame()
        self.picker_popup.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
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
                print("[日期时间编辑] ESC键关闭弹出窗口")
                self.picker_popup.hide()
                # 将焦点返回给父级
                parent_popup = self.parent()
                while parent_popup:
                    if parent_popup.__class__.__name__ == 'MockGpxExportPopup':
                        parent_popup.setFocus()
                        print("[日期时间编辑] 焦点返回给GPX导出面板")
                        break
                    parent_popup = parent_popup.parent()
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
        
        # 显示弹出窗口
        global_pos = self.mapToGlobal(self.rect().bottomLeft())
        self.picker_popup.move(global_pos)
        self.picker_popup.adjustSize()
        self.picker_popup.show()
        self.picker_popup.raise_()
        self.picker_popup.setFocus()
        
        print("[日期时间编辑] 显示选择器并设置焦点")
    
    def _on_datetime_changed(self, datetime):
        self.text_edit.setText(datetime.toString("yyyy-MM-dd hh:mm"))
        if self.picker_popup:
            self.picker_popup.hide()
        
        # 将焦点返回给父级
        parent_popup = self.parent()
        while parent_popup:
            if parent_popup.__class__.__name__ == 'MockGpxExportPopup':
                parent_popup.setFocus()
                print("[日期时间编辑] 选择完成，焦点返回给GPX导出面板")
                break
            parent_popup = parent_popup.parent()


class MockGpxExportPopup(QWidget):
    """模拟GPX导出弹出面板"""
    
    closed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setFocusPolicy(Qt.StrongFocus)
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
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 标题
        title_label = QLabel("导出GPX文件")
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
        
        # 时间设置
        time_container = QWidget()
        time_layout = QHBoxLayout(time_container)
        time_layout.setContentsMargins(0, 0, 0, 0)
        
        time_label = QLabel("起始时间:")
        time_layout.addWidget(time_label)
        
        self.datetime_edit = MockDateTimeEdit()
        time_layout.addWidget(self.datetime_edit, 1)
        
        layout.addWidget(time_container)
        
        # 按钮
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
    
    def _on_cancel(self):
        self.hide()
        self.closed.emit()
    
    def _on_export(self):
        print("[GPX导出] 确认导出")
        self.hide()
        self.closed.emit()
    
    def show_at_position(self, pos):
        self.move(pos)
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus()
        print("[GPX导出] 显示弹出面板并设置焦点")
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            # 检查是否有日期时间选择器弹出窗口正在显示
            if hasattr(self, 'datetime_edit') and hasattr(self.datetime_edit, 'picker_popup'):
                if self.datetime_edit.picker_popup and self.datetime_edit.picker_popup.isVisible():
                    # 如果日期时间选择器正在显示，优先关闭它
                    self.datetime_edit.picker_popup.hide()
                    self.setFocus()
                    print("[GPX导出] ESC键关闭日期时间选择器，焦点回到GPX导出面板")
                    event.accept()
                    return
            
            # 如果没有子弹出窗口，则关闭GPX导出面板
            print("[GPX导出] ESC键关闭GPX导出面板")
            self.hide()
            self.closed.emit()
            event.accept()
        else:
            super().keyPressEvent(event)


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ESC键层级关闭测试 - 简化版")
        self.setGeometry(100, 100, 600, 400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 说明
        info_label = QLabel("""
ESC键层级关闭测试：

1. 点击"显示GPX导出面板"按钮
2. 在GPX导出面板中点击日期时间设置的下拉按钮
3. 测试ESC键行为：
   - 第一次按ESC：关闭日期时间选择器，焦点回到GPX导出面板
   - 第二次按ESC：关闭GPX导出面板

观察控制台输出以验证功能。
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
        test_button.clicked.connect(self.show_gpx_popup)
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
        
        self.gpx_popup = None
    
    def show_gpx_popup(self):
        self.status_label.setText("状态: 显示GPX导出面板")
        
        self.gpx_popup = MockGpxExportPopup(self)
        self.gpx_popup.closed.connect(self.on_popup_closed)
        
        # 在窗口中央显示
        center_pos = self.geometry().center()
        popup_pos = center_pos - self.gpx_popup.rect().center()
        self.gpx_popup.show_at_position(popup_pos)
    
    def on_popup_closed(self):
        self.status_label.setText("状态: GPX导出面板已关闭")
        print("[测试] GPX导出面板已关闭")
        self.gpx_popup = None


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = TestWindow()
    window.show()
    
    print("=== ESC键层级关闭测试 - 简化版 ===")
    print("1. 点击'显示GPX导出面板'按钮")
    print("2. 点击日期时间设置的下拉按钮")
    print("3. 按ESC键测试层级关闭功能")
    print("4. 观察控制台输出")
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
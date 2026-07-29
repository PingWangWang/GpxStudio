"""
自定义日期时间编辑控件
点击下拉箭头显示自定义日期时间选择器
"""

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLineEdit, QPushButton, 
                             QVBoxLayout, QFrame)
from PyQt5.QtCore import Qt, QDateTime, pyqtSignal, QPoint
from PyQt5.QtGui import QPainter, QPen, QColor, QFont
from .custom_datetime_picker import CustomDateTimePicker


class CustomDateTimeEdit(QWidget):
    """自定义日期时间编辑控件"""
    
    dateTimeChanged = pyqtSignal(QDateTime)  # 日期时间改变信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_datetime = QDateTime.currentDateTime()
        self.picker_popup = None
        self._init_ui()
        
    def _init_ui(self):
        """初始化UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 文本显示框
        self.text_edit = QLineEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setText(self.current_datetime.toString("yyyy-MM-dd hh:mm"))
        self.text_edit.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-right: none;
                border-radius: 4px;
                border-top-right-radius: 0px;
                border-bottom-right-radius: 0px;
                padding: 6px 8px;
                font-size: 13px;
                color: #333333;
            }
            QLineEdit:focus {
                border: 1px solid rgba(255, 255, 255, 0.7);
                border-right: none;
                background-color: white;
            }
        """)
        layout.addWidget(self.text_edit)
        
        # 下拉按钮
        self.dropdown_button = QPushButton()
        self.dropdown_button.setToolTip("选择日期时间")
        self.dropdown_button.setFixedSize(24, 32)  # 与输入框高度匹配
        self.dropdown_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-left: none;
                border-radius: 4px;
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
            }
            QPushButton:hover {
                background-color: white;
                border: 1px solid rgba(255, 255, 255, 0.7);
                border-left: none;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.8);
            }
        """)
        self.dropdown_button.clicked.connect(self._show_picker)
        layout.addWidget(self.dropdown_button)
        
    def paintEvent(self, event):
        """绘制下拉箭头"""
        super().paintEvent(event)
        
        # 在下拉按钮上绘制箭头
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 获取按钮区域
        button_rect = self.dropdown_button.geometry()
        center_x = button_rect.x() + button_rect.width() // 2
        center_y = button_rect.y() + button_rect.height() // 2
        
        # 绘制下拉箭头
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        arrow_size = 4
        
        # 箭头的三个点
        points = [
            QPoint(center_x - arrow_size, center_y - 2),
            QPoint(center_x, center_y + 2),
            QPoint(center_x + arrow_size, center_y - 2)
        ]
        
        # 绘制箭头线条
        painter.drawLine(points[0], points[1])
        painter.drawLine(points[1], points[2])
    
    def _show_picker(self):
        """显示日期时间选择器"""
        if self.picker_popup and self.picker_popup.isVisible():
            self.picker_popup.hide()
            return
        
        # 创建弹出窗口
        self.picker_popup = QFrame()
        self.picker_popup.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.picker_popup.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid rgba(0, 0, 0, 0.15);
                border-radius: 6px;
            }
        """)
        
        # 设置焦点策略以接收键盘事件
        self.picker_popup.setFocusPolicy(Qt.StrongFocus)
        
        # 重写键盘事件处理
        def keyPressEvent(event):
            if event.key() == Qt.Key_Escape:
                print("[日期时间选择] ESC键关闭日期时间选择器")
                self.picker_popup.hide()
                # 将焦点返回给父级GPX导出面板
                # 向上查找直到找到GpxExportPopup类型的父级
                parent_popup = self.parent()
                while parent_popup:
                    if parent_popup.__class__.__name__ == 'GpxExportPopup':
                        parent_popup.setFocus()
                        print("[日期时间选择] 焦点返回给GPX导出面板")
                        break
                    parent_popup = parent_popup.parent()
                event.accept()
            else:
                QFrame.keyPressEvent(self.picker_popup, event)
        
        self.picker_popup.keyPressEvent = keyPressEvent
        
        # 添加日期时间选择器
        popup_layout = QVBoxLayout(self.picker_popup)
        popup_layout.setContentsMargins(0, 0, 0, 0)
        
        picker = CustomDateTimePicker()
        picker.setDateTime(self.current_datetime)
        picker.dateTimeChanged.connect(self._on_datetime_changed)
        popup_layout.addWidget(picker)
        
        # 计算弹出位置
        global_pos = self.mapToGlobal(QPoint(0, self.height()))
        self.picker_popup.move(global_pos)
        
        # 调整大小并显示
        self.picker_popup.adjustSize()
        self.picker_popup.show()
        self.picker_popup.raise_()
        self.picker_popup.activateWindow()  # 激活窗口以确保获得焦点
        self.picker_popup.setFocus()  # 设置焦点以接收键盘事件
        
        print("[日期时间选择] 显示自定义选择器并设置焦点")
    
    def _on_datetime_changed(self, datetime):
        """日期时间改变处理"""
        self.current_datetime = datetime
        self.text_edit.setText(datetime.toString("yyyy-MM-dd hh:mm"))
        self.dateTimeChanged.emit(datetime)
        
        # 关闭日期时间选择器弹出窗口
        if self.picker_popup:
            self.picker_popup.hide()
        
        # 将焦点返回给父级GPX导出面板
        # 向上查找直到找到GpxExportPopup类型的父级
        parent_popup = self.parent()
        while parent_popup:
            if parent_popup.__class__.__name__ == 'GpxExportPopup':
                parent_popup.setFocus()
                print("[日期时间选择] 选择完成，焦点返回给GPX导出面板")
                break
            parent_popup = parent_popup.parent()
        
        print(f"[日期时间选择] 选择完成: {datetime.toString('yyyy-MM-dd hh:mm')}")
    
    def setDateTime(self, datetime):
        """设置日期时间"""
        self.current_datetime = datetime
        self.text_edit.setText(datetime.toString("yyyy-MM-dd hh:mm"))
    
    def dateTime(self):
        """获取当前日期时间"""
        return self.current_datetime
    
    def mousePressEvent(self, event):
        """鼠标点击事件 - 点击输入框也显示选择器"""
        if event.button() == Qt.LeftButton:
            self._show_picker()
        super().mousePressEvent(event)
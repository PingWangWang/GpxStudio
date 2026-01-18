"""
GPX导出弹出面板
用于设置路线起始时间并导出GPX文件
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QApplication)
from PyQt5.QtCore import Qt, QDateTime, pyqtSignal, QEvent, QTimer
from PyQt5.QtGui import QFont
from ui.widgets.custom_datetime_edit import CustomDateTimeEdit


class GpxExportPopup(QWidget):
    """GPX导出弹出面板"""
    
    export_confirmed = pyqtSignal(QDateTime)  # 确认导出信号，传递起始时间
    closed = pyqtSignal()  # 关闭信号
    
    def __init__(self, route_data: dict, parent=None):
        super().__init__(parent)
        self.route_data = route_data
        self._init_ui()
        
        # 设置窗口标志 - 作为工具提示窗口，不抢夺焦点
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)  # 不透明背景
        
        # 设置焦点策略以接收键盘事件
        self.setFocusPolicy(Qt.StrongFocus)
        
        # 安装事件过滤器以监听焦点变化
        self.installEventFilter(self)
        
    def _init_ui(self):
        """初始化UI"""
        # 设置弹出面板样式 - 与路线面板颜色统一
        self.setStyleSheet("""
            GpxExportPopup {
                background-color: #4A90E2;
                border-radius: 8px;
                border: 1px solid rgba(0, 0, 0, 0.15);
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QLabel {
                color: white;
                font-size: 13px;
            }
            CustomDateTimeEdit {
                background-color: transparent;
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
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.8);
            }
            QPushButton#cancelButton {
                background-color: rgba(255, 255, 255, 0.7);
                color: #666666;
            }
            QPushButton#cancelButton:hover {
                background-color: rgba(255, 255, 255, 0.85);
            }
            QPushButton#cancelButton:pressed {
                background-color: rgba(255, 255, 255, 0.6);
            }
            QFrame {
                color: rgba(255, 255, 255, 0.3);
            }
        """)
        
        # 设置自动填充背景
        self.setAutoFillBackground(True)
        
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
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("QFrame { color: #e0e0e0; }")
        layout.addWidget(separator)
        
        # 路线信息
        route_info = self._get_route_info()
        info_label = QLabel(route_info)
        info_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 12px;
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                padding: 8px;
            }
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 时间设置区域
        time_container = QWidget()
        time_layout = QHBoxLayout(time_container)
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(8)
        
        time_label = QLabel("起始时间:")
        time_layout.addWidget(time_label)
        
        # 自定义日期时间选择器
        self.datetime_edit = CustomDateTimeEdit()
        self.datetime_edit.setDateTime(QDateTime.currentDateTime())
        time_layout.addWidget(self.datetime_edit, 1)
        
        layout.addWidget(time_container)
        
        # 按钮区域
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)
        
        button_layout.addStretch()
        
        # 取消按钮
        cancel_button = QPushButton("取消")
        cancel_button.setObjectName("cancelButton")
        cancel_button.clicked.connect(self._on_cancel_clicked)
        button_layout.addWidget(cancel_button)
        
        # 确认导出按钮
        export_button = QPushButton("确认导出")
        export_button.clicked.connect(self._on_export_clicked)
        export_button.setDefault(True)
        button_layout.addWidget(export_button)
        
        layout.addWidget(button_container)
        
        # 设置固定宽度
        self.setFixedWidth(320)
        
    def _get_route_info(self):
        """获取路线信息文本"""
        description = self.route_data.get('description', '路线方案')
        distance = self.route_data.get('distance', 0)
        duration = self.route_data.get('duration', 0)
        
        distance_km = distance / 1000
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        
        if hours > 0:
            time_text = f"{hours}小时{minutes}分钟"
        else:
            time_text = f"{minutes}分钟"
            
        return f"路线: {description}\n距离: {distance_km:.1f}公里\n预计时间: {time_text}"
        
    def _on_export_clicked(self):
        """确认导出按钮点击"""
        start_time = self.datetime_edit.dateTime()
        self.export_confirmed.emit(start_time)
        self.hide()
        self.closed.emit()
        
    def _on_cancel_clicked(self):
        """取消按钮点击"""
        self.hide()
        self.closed.emit()
        
    def get_start_time(self):
        """获取设置的起始时间"""
        return self.datetime_edit.dateTime()
    
    def show_at_position(self, pos):
        """在指定位置显示弹出面板"""
        self.move(pos)
        self.show()
        self.raise_()
        self.activateWindow()  # 激活窗口以确保获得焦点
        # 自动设置焦点到弹出面板
        self.setFocus()
        print("[GPX导出] 显示弹出面板并设置焦点")
    
    def mousePressEvent(self, event):
        """鼠标按下事件 - 防止点击面板外部时关闭"""
        super().mousePressEvent(event)
        event.accept()  # 接受事件，防止传播到父组件
    
    def eventFilter(self, obj, event):
        """事件过滤器 - 监听焦点变化"""
        # 禁用自动关闭功能，只通过ESC键或按钮关闭
        # 这样可以避免在弹出时间日期设置面板时自动关闭GPX面板
        return super().eventFilter(obj, event)
    
    def _check_and_close(self):
        """检查并关闭弹出面板 - 已禁用自动关闭"""
        # 不再自动关闭，只通过ESC键或按钮关闭
        pass
    
    def focusOutEvent(self, event):
        """焦点丢失事件 - 已禁用自动关闭"""
        super().focusOutEvent(event)
        # 不再延迟检查自动关闭
    
    def keyPressEvent(self, event):
        """键盘按键事件"""
        if event.key() == Qt.Key_Escape:
            # 检查是否有日期时间选择器弹出窗口正在显示
            if hasattr(self, 'datetime_edit') and hasattr(self.datetime_edit, 'picker_popup'):
                if self.datetime_edit.picker_popup and self.datetime_edit.picker_popup.isVisible():
                    # 如果日期时间选择器正在显示，优先关闭它
                    self.datetime_edit.picker_popup.hide()
                    # 重新设置焦点到GPX导出面板
                    self.setFocus()
                    print("[GPX导出] ESC键关闭日期时间选择器，焦点回到GPX导出面板")
                    event.accept()
                    return
            
            # 如果没有子弹出窗口，则关闭GPX导出面板
            print("[GPX导出] ESC键关闭GPX导出面板")
            self.hide()
            self.closed.emit()
            
            # 将焦点返回给路线规划面板
            parent_app = self.parent()
            while parent_app and not hasattr(parent_app, 'route_plan_panel'):
                parent_app = parent_app.parent()
            
            if parent_app and hasattr(parent_app, 'route_plan_panel'):
                if parent_app.route_plan_panel and parent_app.route_plan_panel.isVisible():
                    parent_app.route_plan_panel.setFocus()
                    print("[GPX导出] 焦点返回给路线规划面板")
            
            event.accept()
        else:
            super().keyPressEvent(event)
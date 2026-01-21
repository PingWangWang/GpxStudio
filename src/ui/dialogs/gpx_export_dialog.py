"""
GPX导出对话框
用于设置路线起始时间并导出GPX文件
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QDateTimeEdit, QWidget)
from PyQt5.QtCore import Qt, QDateTime, pyqtSignal
from PyQt5.QtGui import QFont


class GpxExportDialog(QDialog):
    """GPX导出对话框"""
    
    export_confirmed = pyqtSignal(QDateTime)  # 确认导出信号，传递起始时间
    
    def __init__(self, route_data: dict, parent=None):
        super().__init__(parent)
        self.route_data = route_data
        self._init_ui()
        
    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("导出GPX文件")
        self.setFixedSize(400, 200)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        
        # 设置对话框样式
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QLabel {
                color: #333333;
                font-size: 14px;
            }
            QDateTimeEdit {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
                color: #333333;
            }
            QDateTimeEdit:focus {
                border: 1px solid #4A90E2;
                background-color: white;
            }
            QPushButton {
                background-color: #3d93fd;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357ABD;
            }
            QPushButton:pressed {
                background-color: #2E6DA4;
            }
            QPushButton#cancelButton {
                background-color: #f5f5f5;
                color: #666666;
            }
            QPushButton#cancelButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton#cancelButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 标题
        title_label = QLabel("设置路线起始时间")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 路线信息
        route_info = self._get_route_info()
        info_label = QLabel(route_info)
        info_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 12px;
                background-color: #f9f9f9;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 时间设置区域
        time_container = QWidget()
        time_layout = QHBoxLayout(time_container)
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(10)
        
        time_label = QLabel("起始时间:")
        time_layout.addWidget(time_label)
        
        # 日期时间选择器
        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setDateTime(QDateTime.currentDateTime())
        self.datetime_edit.setDisplayFormat("yyyy-MM-dd hh:mm")
        self.datetime_edit.setCalendarPopup(True)
        time_layout.addWidget(self.datetime_edit, 1)
        
        layout.addWidget(time_container)
        
        # 按钮区域
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        
        button_layout.addStretch()
        
        # 取消按钮
        cancel_button = QPushButton("取消")
        cancel_button.setObjectName("cancelButton")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        # 确认导出按钮
        export_button = QPushButton("确认导出")
        export_button.clicked.connect(self._on_export_clicked)
        export_button.setDefault(True)
        button_layout.addWidget(export_button)
        
        layout.addWidget(button_container)
        
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
        self.accept()
        
    def get_start_time(self):
        """获取设置的起始时间"""
        return self.datetime_edit.dateTime()
"""
位置信息弹出面板

当用户在地图上右键点击"这是哪儿"时，显示该位置的详细信息
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QCursor


class LocationInfoPopup(QWidget):
    """位置信息弹出面板"""
    
    # 信号
    closed = pyqtSignal()  # 关闭信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 设置窗口标志 - 使用Popup类型，点击外部自动关闭
        # Qt.Popup: 弹出窗口，失去焦点时自动关闭
        # Qt.FramelessWindowHint: 无边框
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        # 初始化UI
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        # 设置整体样式 - 参考地图设置面板的深色风格
        self.setStyleSheet("""
            LocationInfoPopup {
                background-color: #3b4453;
                border-radius: 6px;
                border: 1px solid rgba(0, 123, 255, 0.2);
            }
        """)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(8)
        
        # 标题栏
        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)
        
        # 标题
        title_label = QLabel("📍 位置信息")
        title_font = QFont("Microsoft YaHei", 9)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: white; font-family: 'Microsoft YaHei';")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # 关闭按钮
        close_button = QPushButton("✕")
        close_button.setFixedSize(24, 24)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: rgba(255, 255, 255, 0.7);
                font-size: 14px;
                font-weight: bold;
                border-radius: 12px;
            }
            QPushButton:hover {
                color: white;
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        close_button.setCursor(QCursor(Qt.PointingHandCursor))
        close_button.clicked.connect(self.hide)
        title_layout.addWidget(close_button)
        
        main_layout.addLayout(title_layout)
        
        # 分隔线
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.HLine)
        separator1.setStyleSheet("background-color: rgba(255, 255, 255, 0.1); border: none; height: 1px;")
        separator1.setFixedHeight(1)
        main_layout.addWidget(separator1)
        
        # 位置名称 - 支持文本选择和复制
        self.name_label = QLabel()
        self.name_label.setWordWrap(True)
        self.name_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        self.name_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 13px;
                font-weight: bold;
                padding: 4px 0px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
        """)
        main_layout.addWidget(self.name_label)
        
        # 详细地址 - 支持文本选择和复制
        self.address_label = QLabel()
        self.address_label.setWordWrap(True)
        self.address_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        self.address_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.85);
                font-size: 12px;
                padding: 2px 0px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
        """)
        main_layout.addWidget(self.address_label)
        
        # 坐标信息 - 支持文本选择和复制
        self.coord_label = QLabel()
        self.coord_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        self.coord_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.6);
                font-size: 11px;
                padding: 2px 0px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
        """)
        main_layout.addWidget(self.coord_label)
        
        # 类型信息（可选）- 支持文本选择和复制
        self.type_label = QLabel()
        self.type_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        self.type_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.6);
                font-size: 11px;
                padding: 2px 0px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
        """)
        self.type_label.setVisible(False)
        main_layout.addWidget(self.type_label)
        
        # 设置固定宽度
        self.setFixedWidth(300)
    
    def show_location_info(self, location_data: dict, pos):
        """
        显示位置信息
        
        Args:
            location_data: 位置数据字典，包含：
                - name: 位置名称
                - address: 详细地址（可选）
                - lat: 纬度
                - lon: 经度
                - type: 类型信息（可选）
            pos: 显示位置（全局坐标）
        """
        print(f"[位置信息面板] 准备显示位置信息: {location_data}")
        
        # 更新显示内容
        name = location_data.get('name', '未知位置')
        self.name_label.setText(name)
        
        # 详细地址
        address = location_data.get('address', '')
        if address and address != name:
            self.address_label.setText(address)
            self.address_label.setVisible(True)
        else:
            self.address_label.setVisible(False)
        
        # 坐标信息
        lat = location_data.get('lat', 0.0)
        lon = location_data.get('lon', 0.0)
        self.coord_label.setText(f"坐标: {lat:.6f}, {lon:.6f}")
        
        # 类型信息
        type_info = location_data.get('type', '')
        if type_info:
            self.type_label.setText(f"类型: {type_info}")
            self.type_label.setVisible(True)
        else:
            self.type_label.setVisible(False)
        
        # 调整大小
        self.adjustSize()
        
        print(f"[位置信息面板] 面板大小: {self.size()}")
        print(f"[位置信息面板] 显示位置: {pos}")
        
        # 显示在指定位置
        self.move(pos)
        self.show()
        self.raise_()
        self.activateWindow()
        
        print(f"[位置信息面板] 面板已显示")
    
    def keyPressEvent(self, event):
        """处理键盘事件"""
        if event.key() == Qt.Key_Escape:
            self.hide()
            event.accept()
        else:
            super().keyPressEvent(event)
    
    def hideEvent(self, event):
        """窗口隐藏事件"""
        super().hideEvent(event)
        self.closed.emit()

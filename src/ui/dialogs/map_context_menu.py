"""
地图右键菜单
在地图上右键点击时显示位置信息和操作选项
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class MapContextMenu(QWidget):
    """地图右键菜单"""

    # 定义信号
    set_as_start = pyqtSignal(str, float, float)  # 名称, 纬度, 经度
    add_as_waypoint = pyqtSignal(str, float, float)  # 名称, 纬度, 经度
    set_as_end = pyqtSignal(str, float, float)  # 名称, 纬度, 经度

    def __init__(self, parent=None):
        """初始化右键菜单"""
        super().__init__(parent)

        # 设置窗口属性
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        # 当前位置信息
        self.current_name = ""
        self.current_lat = 0.0
        self.current_lon = 0.0
        self.current_type = ""

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # 设置样式
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 2px solid #4A90E2;
                border-radius: 8px;
            }
            QLabel {
                color: #333333;
                border: none;
                font-size: 9pt;
            }
            QPushButton {
                background-color: #3d93fd;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 9pt;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #357ABD;
            }
            QPushButton:pressed {
                background-color: #2868A8;
            }
        """)

        # 标题
        title_label = QLabel("📍 位置信息")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(9)  # 统一为9pt
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 分隔线
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFrameShadow(QFrame.Sunken)
        line1.setStyleSheet("background-color: #e0e0e0; border: none;")
        layout.addWidget(line1)

        # 位置名称
        self.name_label = QLabel("名称: 加载中...")
        self.name_label.setWordWrap(True)
        self.name_label.setMaximumWidth(260)  # 从300缩小到260
        layout.addWidget(self.name_label)

        # 坐标信息
        self.coord_label = QLabel("坐标: 0.000000, 0.000000")
        layout.addWidget(self.coord_label)

        # 类型信息
        self.type_label = QLabel("类型: 未知")
        layout.addWidget(self.type_label)

        # 分隔线
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        line2.setStyleSheet("background-color: #e0e0e0; border: none;")
        layout.addWidget(line2)

        # 操作按钮
        button_layout = QVBoxLayout()
        button_layout.setSpacing(6)

        # 设为起点按钮
        self.start_button = QPushButton("🚩 设为起点")
        self.start_button.setToolTip("在地图上标记起点位置")
        self.start_button.clicked.connect(self._on_set_as_start)
        button_layout.addWidget(self.start_button)

        # 添加途径点按钮
        self.waypoint_button = QPushButton("📌 添加途径点")
        self.waypoint_button.setToolTip("在地图上添加一个途径点")
        self.waypoint_button.clicked.connect(self._on_add_as_waypoint)
        button_layout.addWidget(self.waypoint_button)

        # 设为终点按钮
        self.end_button = QPushButton("🏁 设为终点")
        self.end_button.setToolTip("在地图上标记终点位置")
        self.end_button.clicked.connect(self._on_set_as_end)
        button_layout.addWidget(self.end_button)

        layout.addLayout(button_layout)

        # 设置固定宽度（从320缩小到280）
        self.setFixedWidth(280)

    def show_menu(self, pos, name, lat, lon, type_info=""):
        """
        显示菜单

        Args:
            pos: 显示位置（全局坐标）
            name: 位置名称
            lat: 纬度
            lon: 经度
            type_info: 类型信息
        """
        # 保存当前位置信息
        self.current_name = name
        self.current_lat = lat
        self.current_lon = lon
        self.current_type = type_info

        # 更新显示
        self.name_label.setText(f"名称: {name}")
        self.coord_label.setText(f"坐标: {lat:.6f}, {lon:.6f}")

        if type_info:
            self.type_label.setText(f"类型: {type_info}")
            self.type_label.show()
        else:
            self.type_label.hide()

        # 调整大小
        self.adjustSize()

        # 显示在指定位置
        self.move(pos)
        self.show()
        self.raise_()
        self.activateWindow()

    def _on_set_as_start(self):
        """设为起点按钮点击"""
        self.set_as_start.emit(self.current_name, self.current_lat, self.current_lon)
        self.hide()

    def _on_add_as_waypoint(self):
        """添加途径点按钮点击"""
        self.add_as_waypoint.emit(self.current_name, self.current_lat, self.current_lon)
        self.hide()

    def _on_set_as_end(self):
        """设为终点按钮点击"""
        self.set_as_end.emit(self.current_name, self.current_lat, self.current_lon)
        self.hide()

    def focusOutEvent(self, event):
        """失去焦点时自动隐藏"""
        self.hide()
        super().focusOutEvent(event)

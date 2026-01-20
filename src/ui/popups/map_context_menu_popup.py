"""
地图右键菜单弹出面板
参考高德地图web版样式设计
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
from PyQt5.QtCore import Qt, pyqtSignal, QEvent
from PyQt5.QtGui import QFont, QIcon


class MapContextMenuPopup(QWidget):
    """地图右键菜单弹出面板"""

    # 定义信号
    set_as_start = pyqtSignal(float, float)  # 纬度, 经度
    set_as_via = pyqtSignal(float, float)  # 纬度, 经度
    set_as_end = pyqtSignal(float, float)  # 纬度, 经度
    query_here = pyqtSignal(float, float)  # 纬度, 经度（这是哪儿）
    set_center = pyqtSignal(float, float)  # 纬度, 经度（设置地图中心点）
    clear_route = pyqtSignal()  # 清除路线

    def __init__(self, parent=None):
        super().__init__(parent)

        # 当前位置信息
        self.current_lat = 0.0
        self.current_lon = 0.0

        # 设置窗口标志 - 使用Popup类型
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        # 设置面板样式
        self.setStyleSheet("""
            MapContextMenuPopup {
                background-color: white;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
            }
        """)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 6, 0, 6)
        main_layout.setSpacing(0)

        # 创建菜单项
        self._create_menu_item(main_layout, "设为起点", "📍", self._on_set_as_start, "#1890ff")
        self._create_menu_item(main_layout, "设为途径点", "📌", self._on_set_as_via, "#52c41a")
        self._create_menu_item(main_layout, "设为终点", "🏁", self._on_set_as_end, "#f5222d")

        # 分隔线
        self._create_separator(main_layout)

        self._create_menu_item(main_layout, "这是哪儿", "📍", self._on_query_here, "#722ed1")
        self._create_menu_item(main_layout, "设置地图中心点", "🎯", self._on_set_center, "#13c2c2")

        # 分隔线
        self._create_separator(main_layout)

        self._create_menu_item(main_layout, "清除路线", "🗑️", self._on_clear_route, "#ff4d4f")

        # 设置固定宽度
        self.setFixedWidth(200)

    def _create_menu_item(self, layout, text, icon_text, callback, icon_color):
        """
        创建菜单项

        Args:
            layout: 布局对象
            text: 菜单项文字
            icon_text: 图标文字（emoji）
            callback: 点击回调函数
            icon_color: 图标颜色
        """
        # 创建按钮作为菜单项
        item_button = QPushButton()
        item_button.setCursor(Qt.PointingHandCursor)

        # 设置按钮样式
        item_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                text-align: left;
                padding: 8px 16px;
                font-size: 13px;
                color: #262626;
                font-family: "MiSans", "Microsoft YaHei", "微软雅黑", sans-serif;
            }}
            QPushButton:hover {{
                background-color: #f5f5f5;
            }}
            QPushButton:pressed {{
                background-color: #e6e6e6;
            }}
        """)

        # 创建水平布局放置图标和文字
        item_layout = QHBoxLayout()
        item_layout.setContentsMargins(0, 0, 0, 0)
        item_layout.setSpacing(8)

        # 图标标签
        icon_label = QLabel(icon_text)
        icon_label.setStyleSheet(f"""
            QLabel {{
                color: {icon_color};
                font-size: 16px;
                min-width: 20px;
                max-width: 20px;
            }}
        """)
        icon_label.setAlignment(Qt.AlignCenter)
        item_layout.addWidget(icon_label)

        # 文字标签
        text_label = QLabel(text)
        text_label.setStyleSheet("""
            QLabel {
                color: #262626;
                font-size: 13px;
                font-family: "MiSans", "Microsoft YaHei", "微软雅黑", sans-serif;
            }
        """)
        item_layout.addWidget(text_label)
        item_layout.addStretch()

        item_button.setLayout(item_layout)
        item_button.clicked.connect(callback)

        layout.addWidget(item_button)

    def _create_separator(self, layout):
        """创建分隔线"""
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Plain)
        separator.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: none;
                max-height: 1px;
                margin: 4px 0;
            }
        """)
        layout.addWidget(separator)

    def show_menu(self, pos, lat, lon):
        """
        显示右键菜单

        Args:
            pos: 显示位置（全局坐标）
            lat: 纬度
            lon: 经度
        """
        # 保存当前位置信息
        self.current_lat = lat
        self.current_lon = lon

        # 调整大小
        self.adjustSize()

        # 显示在指定位置
        self.move(pos)
        self.show()
        self.raise_()
        self.activateWindow()

    def _on_set_as_start(self):
        """设为起点"""
        self.set_as_start.emit(self.current_lat, self.current_lon)
        self.hide()

    def _on_set_as_via(self):
        """设为途经点"""
        self.set_as_via.emit(self.current_lat, self.current_lon)
        self.hide()

    def _on_set_as_end(self):
        """设为终点"""
        self.set_as_end.emit(self.current_lat, self.current_lon)
        self.hide()

    def _on_query_here(self):
        """这是哪儿"""
        self.query_here.emit(self.current_lat, self.current_lon)
        self.hide()

    def _on_set_center(self):
        """设为地图中心点"""
        self.set_center.emit(self.current_lat, self.current_lon)
        self.hide()

    def _on_clear_route(self):
        """清除路线"""
        self.clear_route.emit()
        self.hide()

    def event(self, event: QEvent):
        """处理所有事件"""
        # 当窗口失去激活状态时自动关闭
        if event.type() == QEvent.WindowDeactivate:
            self.hide()
            return True
        return super().event(event)

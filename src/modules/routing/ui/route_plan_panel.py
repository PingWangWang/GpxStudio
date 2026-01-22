"""
路线规划面板组件

参考高德地图的路线规划界面设计
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLineEdit, QLabel, QScrollArea, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QPixmap, QTransform, QColor, QImage, QKeyEvent
import os


class RouteHistoryItem(QWidget):
    """路线历史记录列表项"""

    export_gpx_clicked = pyqtSignal(dict, object, object)  # 导出GPX按钮点击信号：(历史记录数据, 按钮实例, 条目实例)

    def __init__(self, history_data: dict, parent=None):
        super().__init__(parent)
        self.history_data = history_data
        self.is_selected = False
        self.has_route_data = False  # 是否有完整路线数据
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # 交通方式图标
        self.mode_icon_label = QLabel()
        self.mode_icon_label.setFixedSize(24, 24)
        layout.addWidget(self.mode_icon_label)

        # 路线文本
        start = self.history_data.get('start', '')
        end = self.history_data.get('end', '')
        route_label = QLabel(f"{start} → {end}")
        route_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 13px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
        """)
        route_label.setWordWrap(True)
        layout.addWidget(route_label, 1)

        # 搜索次数（放在中间）
        search_count = self.history_data.get('search_count', 1)
        if search_count > 1:
            count_label = QLabel(f"搜索 {search_count} 次")
            count_label.setStyleSheet("""
                QLabel {
                    color: rgba(255, 255, 255, 0.6);
                    font-size: 11px;
                    font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                }
            """)
            layout.addWidget(count_label)

        # 导出GPX按钮（放在最右侧）
        from PyQt5.QtGui import QIcon
        from core.resource_path import resource_path

        self.export_button = QPushButton()
        self.export_button.setFixedSize(32, 32)  # 与地图设置按钮保持一致的大小

        # 初始状态为禁用，使用灰色图标
        self._update_export_button_icon()

        self.export_button.setToolTip('导出GPX文件')
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 4px;
            }
            QPushButton:hover:enabled {
                background-color: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.5);
            }
            QPushButton:pressed:enabled {
                background-color: rgba(255, 255, 255, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.7);
            }
            QPushButton:disabled {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                opacity: 0.5;
            }
        """)
        self.export_button.clicked.connect(lambda: self.export_gpx_clicked.emit(self.history_data, self.export_button, self))
        # 初始状态为禁用
        self.export_button.setEnabled(False)
        layout.addWidget(self.export_button, 0, Qt.AlignVCenter)

        # 加载交通方式图标
        self._load_mode_icon()

    def set_selected(self, selected: bool):
        """设置选中状态"""
        self.is_selected = selected
        self._update_export_button_state()

    def set_route_data_available(self, available: bool):
        """设置路线数据是否可用"""
        self.has_route_data = available
        self._update_export_button_state()

    def _update_export_button_state(self):
        """更新导出按钮状态"""
        # 只有当记录被选中且有路线数据时才启用导出按钮
        should_enable = self.is_selected and self.has_route_data
        self.export_button.setEnabled(should_enable)

        # 更新图标
        self._update_export_button_icon()

        # 更新工具提示
        if self.is_selected:
            if self.has_route_data:
                self.export_button.setToolTip("导出GPX文件")
            else:
                self.export_button.setToolTip("该记录缺少路线数据，无法导出")
        else:
            self.export_button.setToolTip("请先选择此路线记录")

    def _update_export_button_icon(self):
        """更新导出按钮图标"""
        # 使用emoji作为图标，与右键菜单面板保持一致
        self.export_button.setText("📥")
        if self.export_button.isEnabled():
            # 启用状态
            self.export_button.setStyleSheet("""
                QPushButton {
                    font-size: 18px;
                    background-color: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 4px;
                }
                QPushButton:hover:enabled {
                    background-color: rgba(255, 255, 255, 0.2);
                    border: 1px solid rgba(255, 255, 255, 0.5);
                }
                QPushButton:pressed:enabled {
                    background-color: rgba(255, 255, 255, 0.3);
                    border: 1px solid rgba(255, 255, 255, 0.7);
                }
            """)
        else:
            # 禁用状态
            self.export_button.setStyleSheet("""
                QPushButton {
                    font-size: 18px;
                    background-color: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 4px;
                    opacity: 0.5;
                }
            """)

    def _load_mode_icon(self):
        """加载交通方式图标"""
        # 使用emoji作为图标，与右键菜单面板保持一致
        mode = self.history_data.get('mode', 'driving')
        icon_map = {
            'driving': '🚗',
            'cycling': '🚲',
            'walking': '🚶'
        }

        icon_text = icon_map.get(mode, '🚗')
        self.mode_icon_label.setText(icon_text)
        self.mode_icon_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                text-align: center;
                color: white;
            }
        """)


class RouteAlternativeItem(QWidget):
    """路线待选列表项"""

    export_gpx_clicked = pyqtSignal(dict, object, object)  # 导出GPX按钮点击信号：(路线数据, 按钮实例, 条目实例)

    def __init__(self, route_data: dict, index: int, is_selected: bool = False, parent=None):
        super().__init__(parent)
        self.route_data = route_data
        self.index = index
        self.is_selected = is_selected
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        # 使用水平布局作为主布局，以便将导出按钮放在右侧垂直居中
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(8)

        # 左侧内容容器
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(6)

        # 第一行：方案名称和时间
        first_row = QHBoxLayout()
        first_row.setSpacing(8)

        # 方案名称（如：推荐方案、距离最短、躲避拥堵）
        description = self.route_data.get('description', f'方案{self.index + 1}')
        name_label = QLabel(description)
        name_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 14px;
                font-weight: bold;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
        """)
        first_row.addWidget(name_label)

        first_row.addStretch()

        # 预计时间
        duration = self.route_data.get('duration', 0)
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        if hours > 0:
            time_text = f"约{hours}小时{minutes}分钟"
        else:
            time_text = f"约{minutes}分钟"

        time_label = QLabel(time_text)
        time_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.7);
                font-size: 12px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
        """)
        first_row.addWidget(time_label)

        content_layout.addLayout(first_row)

        # 第二行：距离、红绿灯、收费信息、路线点位数量
        second_row = QHBoxLayout()
        second_row.setSpacing(12)

        # 距离
        distance = self.route_data.get('distance', 0)
        distance_km = distance / 1000
        distance_label = QLabel(f"{distance_km:.1f}公里")
        distance_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.6);
                font-size: 11px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
        """)
        second_row.addWidget(distance_label)

        # 路线点位数量
        route_points = self.route_data.get('route_points', [])
        if route_points:
            # 计算有效点位数量（排除None分隔符）
            valid_points_count = len([p for p in route_points if p is not None])
            points_label = QLabel(f"{valid_points_count}个点位")
            points_label.setStyleSheet("""
                QLabel {
                    color: rgba(255, 255, 255, 0.6);
                    font-size: 11px;
                    font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                }
            """)
            second_row.addWidget(points_label)

        # 红绿灯数量（仅驾车模式）
        traffic_lights = self.route_data.get('traffic_lights', 0)
        if traffic_lights > 0:
            lights_label = QLabel(f"红绿灯{traffic_lights}个")
            lights_label.setStyleSheet("""
                QLabel {
                    color: rgba(255, 255, 255, 0.6);
                    font-size: 11px;
                    font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                }
            """)
            second_row.addWidget(lights_label)

        # 收费信息（仅驾车模式）
        tolls = self.route_data.get('tolls', 0)
        if tolls > 0:
            tolls_label = QLabel(f"收费{tolls}元")
            tolls_label.setStyleSheet("""
                QLabel {
                    color: rgba(255, 255, 255, 0.6);
                    font-size: 11px;
                    font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                }
            """)
            second_row.addWidget(tolls_label)

        second_row.addStretch()

        content_layout.addLayout(second_row)

        # 导出GPX按钮 - 使用Downloading图标
        from PyQt5.QtGui import QIcon
        from core.resource_path import resource_path

        self.export_button = QPushButton()
        self.export_button.setFixedSize(32, 32)  # 与地图设置按钮保持一致的大小

        # 使用emoji作为图标，与右键菜单面板保持一致
        self.export_button.setText("📥")
        self.export_button.setToolTip('导出GPX文件')
        self.export_button.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.5);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.7);
            }
        """)
        self.export_button.clicked.connect(lambda: self.export_gpx_clicked.emit(self.route_data, self.export_button, self))

        # 将内容布局添加到主布局
        main_layout.addLayout(content_layout, 1)
        # 将导出按钮添加到主布局，设置垂直居中对齐
        main_layout.addWidget(self.export_button, 0, Qt.AlignVCenter)

        # 导出图标已通过create_icon_button自动加载

        # 设置选中状态的背景色
        if self.is_selected:
            self.setStyleSheet("""
                RouteAlternativeItem {
                    background-color: rgba(255, 255, 255, 0.15);
                    border-radius: 4px;
                }
            """)

    def set_selected(self, selected: bool):
        """设置选中状态"""
        self.is_selected = selected
        if selected:
            self.setStyleSheet("""
                RouteAlternativeItem {
                    background-color: rgba(255, 255, 255, 0.15);
                    border-radius: 4px;
                }
            """)
        else:
            self.setStyleSheet("")


class AddressSuggestionItem(QWidget):
    """地址待选列表项"""

    confirm_clicked = pyqtSignal(dict)  # 确认按钮点击信号

    def __init__(self, address_data: dict, parent=None):
        super().__init__(parent)
        self.address_data = address_data
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)  # 减小内边距
        layout.setSpacing(8)  # 减小间距

        # 地址信息容器
        address_container = QVBoxLayout()
        address_container.setSpacing(2)  # 减小间距

        # 地址名称
        name_label = QLabel(self.address_data.get('name', ''))
        name_label.setStyleSheet("""
            QLabel {
                color: #333333;
                font-size: 13px;
                font-weight: bold;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
        """)
        name_label.setWordWrap(True)
        address_container.addWidget(name_label)

        # 详细地址
        address_label = QLabel(self.address_data.get('address', ''))
        address_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 11px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
        """)
        address_label.setWordWrap(True)
        address_container.addWidget(address_label)

        layout.addLayout(address_container, 1)

        # 确认按钮
        self.confirm_button = QPushButton()
        self.confirm_button.setFixedSize(32, 32)  # 减小按钮尺寸
        self.confirm_button.setToolTip("选择此地址")
        self.confirm_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(74, 144, 226, 0.15);
                border: 1px solid rgba(74, 144, 226, 0.4);
                border-radius: 16px;
            }
            QPushButton:hover {
                background-color: rgba(74, 144, 226, 0.25);
                border: 1px solid rgba(74, 144, 226, 0.6);
            }
            QPushButton:pressed {
                background-color: rgba(74, 144, 226, 0.35);
                border: 1px solid rgba(74, 144, 226, 0.8);
            }
        """)
        self.confirm_button.clicked.connect(lambda: self.confirm_clicked.emit(self.address_data))
        layout.addWidget(self.confirm_button, 0, Qt.AlignVCenter | Qt.AlignRight)

        # 加载确认图标
        self._load_icon()

    def _load_icon(self):
        """加载确认图标"""
        # 使用emoji作为图标，与右键菜单面板保持一致
        self.confirm_button.setText("✅")
        self.confirm_button.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                background-color: rgba(74, 144, 226, 0.15);
                border: 1px solid rgba(74, 144, 226, 0.4);
                border-radius: 16px;
            }
            QPushButton:hover {
                background-color: rgba(74, 144, 226, 0.25);
                border: 1px solid rgba(74, 144, 226, 0.6);
            }
            QPushButton:pressed {
                background-color: rgba(74, 144, 226, 0.35);
                border: 1px solid rgba(74, 144, 226, 0.8);
            }
        """)


class RoutePlanPanel(QWidget):
    """路线规划面板"""

    # 信号
    cancel_clicked = pyqtSignal()  # 取消按钮点击
    plan_route_clicked = pyqtSignal(str, str, str, list)  # 规划路线：(起点, 终点, 交通方式, 途径点列表)
    search_location_clicked = pyqtSignal(str, str)  # 搜索地点：(搜索文本, 类型: start/end/waypoint)
    history_selected = pyqtSignal(dict)  # 选择历史记录
    address_selected = pyqtSignal(dict, str, bool)  # 地址选中：(地址数据, 类型: start/end/waypoint, 是否缩放地图)
    clear_route_clicked = pyqtSignal()  # 清除路线按钮点击
    route_alternative_selected = pyqtSignal(int)  # 路线方案选中：(方案索引)
    export_gpx_clicked = pyqtSignal(dict, object, object)  # 导出GPX按钮点击：(路线数据, 按钮实例, 条目实例)
    history_export_gpx_clicked = pyqtSignal(dict, object, object)  # 历史记录导出GPX按钮点击：(历史记录数据, 按钮实例, 条目实例)

    def __init__(self, parent=None):
        """初始化路线规划面板"""
        super().__init__(parent)

        # 设置窗口标志 - 使用Tool而不是Popup，避免自动关闭
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)  # 不透明背景

        # 设置焦点策略以接收键盘事件
        self.setFocusPolicy(Qt.StrongFocus)

        # 当前交通方式
        self.current_transport_mode = "driving"  # driving, cycling, walking

        # 途径点列表
        self.waypoint_widgets = []

        # 地址搜索相关状态
        self.current_search_type = None  # 当前正在搜索的类型: start/end/waypoint
        self.current_search_input = None  # 当前正在搜索的输入框
        self.current_suggestions = []  # 当前的地址建议列表
        self.selected_suggestion_index = 0  # 当前选中的建议索引

        # 坐标存储（用于保存右键菜单设置的坐标）
        self.start_coords = None  # 起点坐标 (lat, lon)
        self.end_coords = None  # 终点坐标 (lat, lon)
        self.waypoint_coords = []  # 途径点坐标列表 [(lat, lon), ...]

        # 初始化UI
        self._init_ui()

        # 加载图标
        self._load_icons()

    def _init_ui(self):
        """初始化UI"""
        # 设置面板样式 - 使用 RoutePlanPanel 作为选择器确保背景色应用
        self.setStyleSheet("""
            RoutePlanPanel {
                background-color: #3b4453;
                border-radius: 6px;
                border: 1px solid rgba(0, 0, 0, 0.15);
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.9);
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 13px;
                color: #333333;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QLineEdit:focus {
                background-color: white;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.2);
            }
            /* 交通方式按钮特殊样式 - 无背景框 */
            QPushButton[transportMode="true"] {
                background-color: transparent;
                border: none;
            }
            QPushButton[transportMode="true"]:hover {
                background-color: rgba(255, 255, 255, 0.15);
            }
            QPushButton[transportMode="true"]:pressed {
                background-color: rgba(255, 255, 255, 0.25);
            }
            QPushButton[transportMode="true"][selected="true"] {
                background-color: rgba(255, 255, 255, 0.2);
                border: none;
            }
            /* 切换按钮特殊样式 - 无背景框 */
            QPushButton[switchButton="true"] {
                background-color: transparent;
                border: none;
            }
            QPushButton[switchButton="true"]:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton[switchButton="true"]:pressed {
                background-color: rgba(255, 255, 255, 0.15);
            }
            QLabel {
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QListWidget {
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
        """)

        # 设置自动填充背景
        self.setAutoFillBackground(True)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # 1. 顶部：交通方式选择和取消按钮
        top_layout = QHBoxLayout()
        top_layout.setSpacing(8)

        # 取消按钮（左侧，用于占位保持居中）
        cancel_spacer = QWidget()
        cancel_spacer.setFixedSize(36, 36)
        top_layout.addWidget(cancel_spacer)

        # 左侧弹簧（用于居中交通方式按钮）
        top_layout.addStretch(1)

        # 驾车按钮
        self.driving_button = QPushButton()
        self.driving_button.setFixedSize(36, 36)
        self.driving_button.setToolTip("驾车")
        self.driving_button.setProperty("transportMode", True)
        self.driving_button.clicked.connect(lambda: self._switch_transport_mode("driving"))
        top_layout.addWidget(self.driving_button)

        # 骑行按钮
        self.cycling_button = QPushButton()
        self.cycling_button.setFixedSize(36, 36)
        self.cycling_button.setToolTip("骑行")
        self.cycling_button.setProperty("transportMode", True)
        self.cycling_button.clicked.connect(lambda: self._switch_transport_mode("cycling"))
        top_layout.addWidget(self.cycling_button)

        # 步行按钮
        self.walking_button = QPushButton()
        self.walking_button.setFixedSize(36, 36)
        self.walking_button.setToolTip("步行")
        self.walking_button.setProperty("transportMode", True)
        self.walking_button.clicked.connect(lambda: self._switch_transport_mode("walking"))
        top_layout.addWidget(self.walking_button)

        # 右侧弹簧（用于居中交通方式按钮）
        top_layout.addStretch(1)

        # 取消按钮（右侧）
        self.cancel_button = QPushButton()
        self.cancel_button.setFixedSize(36, 36)
        self.cancel_button.setToolTip("取消")
        self.cancel_button.clicked.connect(self.cancel_clicked.emit)
        top_layout.addWidget(self.cancel_button)

        main_layout.addLayout(top_layout)

        # 2. 中部：起点、终点、途径点
        locations_layout = QVBoxLayout()
        locations_layout.setSpacing(8)

        # 主容器（包含切换按钮、起点终点途径点、添加按钮）
        main_locations_container = QWidget()
        main_locations_layout = QHBoxLayout(main_locations_container)
        main_locations_layout.setContentsMargins(0, 0, 0, 0)
        main_locations_layout.setSpacing(8)

        # 保存主容器引用，用于后续添加按钮位置调整
        self.main_locations_container = main_locations_container
        self.main_locations_layout = main_locations_layout

        # 切换按钮（左侧，垂直居中）
        self.switch_button = QPushButton()
        self.switch_button.setFixedSize(32, 32)
        self.switch_button.setToolTip("切换起点和终点")
        self.switch_button.setProperty("switchButton", True)
        self.switch_button.clicked.connect(self._switch_start_end)
        main_locations_layout.addWidget(self.switch_button, 0, Qt.AlignVCenter)

        # 中间的垂直容器（起点、途径点、终点）
        center_container = QWidget()
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(8)

        # 起点行
        self.start_layout = QHBoxLayout()
        self.start_layout.setSpacing(8)

        # 起点标签
        start_label = QLabel("起")
        start_label.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 0.3);
                color: white;
                font-size: 12px;
                font-weight: bold;
                border-radius: 12px;
                min-width: 24px;
                max-width: 24px;
                min-height: 24px;
                max-height: 24px;
            }
        """)
        start_label.setAlignment(Qt.AlignCenter)
        self.start_layout.addWidget(start_label)

        # 起点输入框
        self.start_input = QLineEdit()
        self.start_input.setPlaceholderText("请输入起点")
        self.start_input.returnPressed.connect(lambda: self._on_search_location("start"))
        self.start_input.focusInEvent = lambda e: self._on_input_focus_in(e, "start", self.start_input)
        self.start_layout.addWidget(self.start_input)

        # 起点右侧占位符（用于保持输入框宽度一致）
        self.start_spacer = QWidget()
        self.start_spacer.setFixedSize(32, 32)
        self.start_layout.addWidget(self.start_spacer)

        center_layout.addLayout(self.start_layout)

        # 途径点容器
        self.waypoints_container = QWidget()
        self.waypoints_layout = QVBoxLayout(self.waypoints_container)
        self.waypoints_layout.setContentsMargins(0, 0, 0, 0)
        self.waypoints_layout.setSpacing(8)
        # 初始化时隐藏，确保不占用空间
        self.waypoints_container.setVisible(False)
        center_layout.addWidget(self.waypoints_container)

        # 终点行（保存引用以便后续添加按钮）
        self.end_layout = QHBoxLayout()
        self.end_layout.setSpacing(8)

        # 终点标签
        end_label = QLabel("终")
        end_label.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 0.3);
                color: white;
                font-size: 12px;
                font-weight: bold;
                border-radius: 12px;
                min-width: 24px;
                max-width: 24px;
                min-height: 24px;
                max-height: 24px;
            }
        """)
        end_label.setAlignment(Qt.AlignCenter)
        self.end_layout.addWidget(end_label)

        # 终点输入框
        self.end_input = QLineEdit()
        self.end_input.setPlaceholderText("请输入终点")
        self.end_input.returnPressed.connect(lambda: self._on_search_location("end"))
        self.end_input.focusInEvent = lambda e: self._on_input_focus_in(e, "end", self.end_input)
        self.end_layout.addWidget(self.end_input)

        # 终点右侧占位符（用于保持输入框宽度一致）
        self.end_spacer = QWidget()
        self.end_spacer.setFixedSize(32, 32)
        self.end_layout.addWidget(self.end_spacer)

        center_layout.addLayout(self.end_layout)

        main_locations_layout.addWidget(center_container)

        # 添加途径点按钮（右侧，垂直居中）
        self.add_waypoint_button = QPushButton()
        self.add_waypoint_button.setFixedSize(32, 32)
        self.add_waypoint_button.setToolTip("添加途径点")
        self.add_waypoint_button.clicked.connect(self._add_waypoint)
        main_locations_layout.addWidget(self.add_waypoint_button, 0, Qt.AlignVCenter)

        locations_layout.addWidget(main_locations_container)

        main_layout.addLayout(locations_layout)

        # 3. 路线规划按钮和清除路线按钮
        # 使用与起点终点相同的布局结构，确保对齐
        buttons_container = QWidget()
        buttons_container_layout = QHBoxLayout(buttons_container)
        buttons_container_layout.setContentsMargins(0, 0, 0, 0)
        buttons_container_layout.setSpacing(8)

        # 左侧占位符（与切换按钮宽度一致）
        left_spacer = QWidget()
        left_spacer.setFixedSize(32, 32)
        buttons_container_layout.addWidget(left_spacer)

        # 清除路线按钮（左对齐）
        self.clear_button = QPushButton("清除路线")
        self.clear_button.setFixedWidth(110)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.7);
                color: #666666;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.85);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.6);
            }
        """)
        self.clear_button.clicked.connect(self._on_clear_route)
        buttons_container_layout.addWidget(self.clear_button)

        # 弹性空间，将开车去按钮推到右侧
        buttons_container_layout.addStretch()

        # 开车去按钮（右对齐，与终点文本框右对齐）
        self.plan_button = QPushButton("开车去")
        self.plan_button.setFixedWidth(110)
        self.plan_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.9);
                color: #4A90E2;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: white;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.8);
            }
        """)
        self.plan_button.clicked.connect(self._on_plan_route)
        buttons_container_layout.addWidget(self.plan_button)

        # 加载中按钮（默认隐藏，放在开车去右侧，但始终占据空间）
        self.loading_button = QLabel()
        self.loading_button.setFixedSize(32, 32)
        self.loading_button.setAlignment(Qt.AlignCenter)
        # 使用透明度隐藏，而不是setVisible，这样可以保持占据空间
        self.loading_button.setStyleSheet("QLabel { background: transparent; }")
        buttons_container_layout.addWidget(self.loading_button)

        # 加载Loading图标
        self._load_loading_icon()

        main_layout.addWidget(buttons_container)

        # 4. 地址待选列表（用于显示搜索结果）
        self.address_suggestions_container = QWidget()
        address_suggestions_layout = QVBoxLayout(self.address_suggestions_container)
        address_suggestions_layout.setContentsMargins(0, 0, 0, 0)
        address_suggestions_layout.setSpacing(4)

        # 地址待选列表标题
        suggestions_header_layout = QHBoxLayout()
        suggestions_header_layout.setSpacing(4)
        suggestions_header_layout.setContentsMargins(0, 8, 0, 8)

        # 搜索图标
        self.search_icon_label = QLabel()
        self.search_icon_label.setFixedSize(16, 16)
        suggestions_header_layout.addWidget(self.search_icon_label)

        # 地址待选标题
        self.suggestions_title_label = QLabel("地址待选")
        self.suggestions_title_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.7);
                font-size: 12px;
            }
        """)
        suggestions_header_layout.addWidget(self.suggestions_title_label)

        # 添加弹簧，使标签靠左
        suggestions_header_layout.addStretch(1)

        address_suggestions_layout.addLayout(suggestions_header_layout)

        # 地址待选列表
        self.address_suggestions_list = QListWidget()
        self.address_suggestions_list.setStyleSheet("""
            QListWidget {
                background-color: rgba(255, 255, 255, 0.95);
                border: none;
                border-radius: 4px;
                color: #333333;
            }
            QListWidget::item {
                padding: 0px;
                border-bottom: 1px solid rgba(0, 0, 0, 0.1);
            }
            QListWidget::item:hover {
                background-color: rgba(74, 144, 226, 0.05);
            }
            QListWidget::item:selected {
                background-color: rgba(74, 144, 226, 0.1);
            }
        """)
        self.address_suggestions_list.itemClicked.connect(self._on_address_suggestion_clicked)
        self.address_suggestions_list.itemDoubleClicked.connect(self._on_address_suggestion_double_clicked)
        address_suggestions_layout.addWidget(self.address_suggestions_list)

        # 初始隐藏地址待选列表
        self.address_suggestions_container.setVisible(False)
        main_layout.addWidget(self.address_suggestions_container)

        # 5. 路线搜索历史记录
        self.history_container = QWidget()
        history_container_layout = QVBoxLayout(self.history_container)
        history_container_layout.setContentsMargins(0, 0, 0, 0)
        history_container_layout.setSpacing(0)

        history_header_layout = QHBoxLayout()
        history_header_layout.setSpacing(4)
        history_header_layout.setContentsMargins(0, 8, 0, 8)

        # 历史记录图标
        self.history_icon_label = QLabel()
        self.history_icon_label.setFixedSize(16, 16)
        history_header_layout.addWidget(self.history_icon_label)

        # 历史记录文本
        history_label = QLabel("路线搜索记录")
        history_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.7);
                font-size: 12px;
            }
        """)
        history_header_layout.addWidget(history_label)

        # 添加弹簧，使标签靠左
        history_header_layout.addStretch(1)

        history_container_layout.addLayout(history_header_layout)

        # 历史记录列表
        self.history_list = QListWidget()
        self.history_list.setStyleSheet("""
            QListWidget {
                background-color: rgba(0, 0, 0, 0.3);
                border: none;
                border-radius: 4px;
                color: white;
            }
            QListWidget::item {
                padding: 0px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            QListWidget::item:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QListWidget::item:selected {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        self.history_list.itemClicked.connect(self._on_history_clicked)
        history_container_layout.addWidget(self.history_list)

        main_layout.addWidget(self.history_container)

        # 初始化交通方式
        self._update_transport_mode_ui()

    def _load_icons(self):
        """加载图标"""
        # 使用emoji作为图标，与右键菜单面板保持一致

        # 驾车图标
        self.driving_button.setText("🚗")
        self.driving_button.setStyleSheet("""
            QPushButton {
                font-size: 24px;
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.15);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.25);
            }
        """)

        # 骑行图标
        self.cycling_button.setText("🚲")
        self.cycling_button.setStyleSheet("""
            QPushButton {
                font-size: 24px;
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.15);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.25);
            }
        """)

        # 步行图标
        self.walking_button.setText("🚶")
        self.walking_button.setStyleSheet("""
            QPushButton {
                font-size: 24px;
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.15);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.25);
            }
        """)

        # 取消图标
        self.cancel_button.setText("❌")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                font-size: 20px;
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)

        # 切换图标
        self.switch_button.setText("🔄")
        self.switch_button.setStyleSheet("""
            QPushButton {
                font-size: 20px;
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)

        # 添加途径点图标
        self.add_waypoint_button.setText("➕")
        self.add_waypoint_button.setStyleSheet("""
            QPushButton {
                font-size: 20px;
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)

        # 历史记录图标
        self.history_icon_label.setText("📋")
        self.history_icon_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: white;
            }
        """)

        # 搜索图标
        self.search_icon_label.setText("🔍")
        self.search_icon_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: white;
            }
        """)

    def _load_loading_icon(self):
        """设置Loading图标为emoji"""
        # 使用emoji作为Loading图标
        self.loading_button.setText("🔄")
        self.loading_button.setStyleSheet("""
            QLabel {
                font-size: 24px;
                color: white;
                background: transparent;
            }
        """)

        # 创建定时器用于动画效果
        from PyQt5.QtCore import QTimer
        self.loading_timer = QTimer(self)
        self.loading_timer.timeout.connect(self._animate_loading_emoji)

        # 初始化动画状态
        self.loading_animation_state = 0

    def _animate_loading_emoji(self):
        """动画Loading emoji"""
        # 简单的动画效果，切换不同的加载emoji
        loading_emojis = ["🔄", "⏳", "⌛"]
        self.loading_animation_state = (self.loading_animation_state + 1) % len(loading_emojis)
        self.loading_button.setText(loading_emojis[self.loading_animation_state])

    def keyPressEvent(self, event: QKeyEvent):
        """处理键盘事件"""
        if event.key() == Qt.Key_Escape:
            # 检查是否有任何子弹出窗口正在显示
            parent_app = self.parent()
            while parent_app and not hasattr(parent_app, 'gpx_export_popup'):
                parent_app = parent_app.parent()

            if parent_app and hasattr(parent_app, 'gpx_export_popup'):
                if parent_app.gpx_export_popup and parent_app.gpx_export_popup.isVisible():
                    # 检查GPX面板是否有子弹出窗口（时间日期设置面板）
                    gpx_popup = parent_app.gpx_export_popup
                    has_child_popup = False
                    # 检查新的日期时间选择器
                    if hasattr(gpx_popup, 'picker_popup') and gpx_popup.picker_popup and gpx_popup.picker_popup.isVisible():
                        has_child_popup = True

                    if has_child_popup:
                        # 如果有子弹出窗口，不处理ESC键，让子窗口处理
                        print("[路线面板] 有子弹出窗口正在显示，ESC键由子窗口处理")
                        super().keyPressEvent(event)
                        return
                    else:
                        # 如果GPX面板显示但没有子窗口，不处理ESC键，让GPX面板处理
                        print("[路线面板] GPX导出面板正在显示，ESC键由GPX面板处理")
                        super().keyPressEvent(event)
                        return

            # 如果没有任何子弹出窗口显示，则关闭路线规划面板
            print("[路线面板] ESC键关闭路线规划面板")
            self.cancel_clicked.emit()
            event.accept()
        else:
            super().keyPressEvent(event)

    def show_loading(self):
        """显示加载中状态"""
        # 不使用setVisible，而是通过设置pixmap来显示
        if hasattr(self, 'loading_timer'):
            self.loading_timer.start(50)  # 每50ms旋转一次

    def hide_loading(self):
        """隐藏加载中状态"""
        # 清除pixmap来隐藏，但保持占据空间
        self.loading_button.clear()
        if hasattr(self, 'loading_timer'):
            self.loading_timer.stop()

    def show_search_error(self, location_type: str):
        """显示搜索失败提示"""
        if location_type == "start":
            input_widget = self.start_input
        elif location_type == "end":
            input_widget = self.end_input
        else:
            # 途径点
            return

        # 保存原始占位符
        original_placeholder = input_widget.placeholderText()

        # 设置错误提示
        input_widget.setPlaceholderText("搜索失败，请重试")
        input_widget.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid rgba(255, 100, 100, 0.5);
                border-radius: 4px;
                padding: 8px;
                font-size: 13px;
                color: #333333;
            }
            QLineEdit::placeholder {
                color: #ff6666;
            }
        """)

        # 3秒后恢复原始状态
        from PyQt5.QtCore import QTimer
        def restore_placeholder():
            input_widget.setPlaceholderText(original_placeholder)
            input_widget.setStyleSheet("""
                QLineEdit {
                    background-color: rgba(255, 255, 255, 0.9);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 4px;
                    padding: 8px;
                    font-size: 13px;
                    color: #333333;
                }
            """)

        QTimer.singleShot(3000, restore_placeholder)

    def show_route_plan_error(self, error_message: str = "路线规划失败，请重试"):
        """显示路线规划失败提示"""
        # 在历史记录区域显示错误提示
        self.history_list.clear()

        # 创建错误提示项
        error_widget = QWidget()
        error_layout = QVBoxLayout(error_widget)
        error_layout.setContentsMargins(16, 16, 16, 16)
        error_layout.setSpacing(8)

        # 错误图标和文字
        error_text = QLabel(error_message)
        error_text.setStyleSheet("""
            QLabel {
                color: rgba(255, 100, 100, 1);
                font-size: 13px;
                font-weight: bold;
            }
        """)
        error_text.setWordWrap(True)
        error_text.setAlignment(Qt.AlignCenter)
        error_layout.addWidget(error_text)

        # 添加到列表
        item = QListWidgetItem()
        item.setSizeHint(error_widget.sizeHint())
        self.history_list.addItem(item)
        self.history_list.setItemWidget(item, error_widget)

        # 3秒后恢复历史记录显示
        from PyQt5.QtCore import QTimer
        def restore_history():
            # 重新加载历史记录
            if hasattr(self, '_last_history_list'):
                self.load_history(self._last_history_list)

        QTimer.singleShot(3000, restore_history)

    def _switch_transport_mode(self, mode: str):
        """切换交通方式"""
        self.current_transport_mode = mode
        self._update_transport_mode_ui()

    def _update_transport_mode_ui(self):
        """更新交通方式UI"""
        # 更新按钮样式（使用property标记选中状态）
        self.driving_button.setProperty("selected", self.current_transport_mode == "driving")
        self.driving_button.style().unpolish(self.driving_button)
        self.driving_button.style().polish(self.driving_button)

        self.cycling_button.setProperty("selected", self.current_transport_mode == "cycling")
        self.cycling_button.style().unpolish(self.cycling_button)
        self.cycling_button.style().polish(self.cycling_button)

        self.walking_button.setProperty("selected", self.current_transport_mode == "walking")
        self.walking_button.style().unpolish(self.walking_button)
        self.walking_button.style().polish(self.walking_button)

        # 更新规划按钮文本
        mode_text = {
            "driving": "开车去",
            "cycling": "骑车去",
            "walking": "走路去"
        }
        self.plan_button.setText(mode_text.get(self.current_transport_mode, "开车去"))

        # 显示/隐藏添加途径点按钮（仅驾车模式）
        self.add_waypoint_button.setVisible(self.current_transport_mode == "driving")

        # 显示/隐藏途径点容器（仅驾车模式且有途径点时显示）
        is_driving = self.current_transport_mode == "driving"
        has_waypoints = len(self.waypoint_widgets) > 0
        self.waypoints_container.setVisible(is_driving and has_waypoints)

        # 更新占位符显示逻辑
        if self.current_transport_mode == "driving":
            # 驾车模式：根据途径点数量决定
            if len(self.waypoint_widgets) == 0:
                # 没有途径点时，添加按钮在右侧垂直居中，起点和终点都不需要占位符
                self.start_spacer.hide()
                self.end_spacer.hide()
            else:
                # 有途径点时，起点需要占位符保持宽度一致，终点不需要（添加按钮在终点右侧）
                self.start_spacer.show()
                self.end_spacer.hide()
        else:
            # 步行和骑行模式：起点和终点都显示占位符
            self.start_spacer.show()
            self.end_spacer.show()

    def _switch_start_end(self):
        """切换起点和终点"""
        start_text = self.start_input.text()
        end_text = self.end_input.text()

        self.start_input.setText(end_text)
        self.end_input.setText(start_text)

    def _add_waypoint(self):
        """添加途径点"""
        # 检查途径点数量限制（最多5个）
        if len(self.waypoint_widgets) >= 5:
            return

        # 创建途径点行
        waypoint_layout = QHBoxLayout()
        waypoint_layout.setSpacing(8)

        # 途径点标签
        waypoint_label = QLabel(f"经{len(self.waypoint_widgets) + 1}")
        waypoint_label.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 0.3);
                color: white;
                font-size: 12px;
                font-weight: bold;
                border-radius: 12px;
                min-width: 24px;
                max-width: 24px;
                min-height: 24px;
                max-height: 24px;
            }
        """)
        waypoint_label.setAlignment(Qt.AlignCenter)
        waypoint_layout.addWidget(waypoint_label)

        # 途径点输入框
        waypoint_input = QLineEdit()
        waypoint_input.setPlaceholderText(f"请输入途径点{len(self.waypoint_widgets) + 1}")
        waypoint_input.returnPressed.connect(lambda: self._on_search_location("waypoint"))
        waypoint_input.focusInEvent = lambda e: self._on_input_focus_in(e, "waypoint", waypoint_input)
        waypoint_layout.addWidget(waypoint_input)

        # 删除按钮
        delete_button = QPushButton()
        delete_button.setFixedSize(32, 32)
        delete_button.setToolTip("删除途径点")

        # 使用emoji作为图标，与缩放地图按钮保持一致
        delete_button.setText("➖")
        delete_button.setStyleSheet("""
            QPushButton {
                font-size: 20px;
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)

        # 创建途径点容器widget
        waypoint_widget = QWidget()
        waypoint_widget_layout = QHBoxLayout(waypoint_widget)
        waypoint_widget_layout.setContentsMargins(0, 0, 0, 0)
        waypoint_widget_layout.setSpacing(0)
        waypoint_widget_layout.addLayout(waypoint_layout)

        delete_button.clicked.connect(lambda: self._remove_waypoint(waypoint_widget))

        # 添加到途径点容器
        self.waypoints_layout.addWidget(waypoint_widget)
        self.waypoint_widgets.append({
            'container': waypoint_widget,
            'input': waypoint_input,
            'label': waypoint_label,
            'delete_button': delete_button,
            'delete_layout': waypoint_layout
        })

        # 将删除按钮添加到布局（在输入框右侧）
        waypoint_layout.addWidget(delete_button)

        # 显示途径点容器
        self.waypoints_container.setVisible(True)

        # 更新添加按钮位置
        self._update_add_button_position()

        # 如果达到5个途径点，禁用添加按钮
        if len(self.waypoint_widgets) >= 5:
            self.add_waypoint_button.setEnabled(False)
            self.add_waypoint_button.setToolTip("最多添加5个途径点")

    def _remove_waypoint(self, container):
        """删除途径点"""
        # 找到对应的widget
        for i, widget_dict in enumerate(self.waypoint_widgets):
            if widget_dict['container'] == container:
                # 从父布局中移除并删除容器
                self.waypoints_layout.removeWidget(container)
                container.deleteLater()

                # 从列表中移除
                self.waypoint_widgets.pop(i)

                # 从data_manager中删除对应途径点并重新渲染地图
                if self.parent() and hasattr(self.parent(), 'data_manager'):
                    # 确保索引有效
                    if i < len(self.parent().data_manager.waypoints_coords):
                        self.parent().data_manager.remove_waypoint(i)

                        # 重新渲染地图，清除已删除途径点的地址标识
                        if hasattr(self.parent(), 'map_manager'):
                            # 显示路线地图，不包含已删除的途径点标识
                            self.parent().map_manager.show_route_on_map()

                # 重新编号
                self._renumber_waypoints()

                # 如果没有途径点了，隐藏途径点容器
                if len(self.waypoint_widgets) == 0:
                    self.waypoints_container.setVisible(False)

                # 更新添加按钮位置
                self._update_add_button_position()

                # 重新启用添加按钮（如果之前被禁用）
                if len(self.waypoint_widgets) < 5:
                    self.add_waypoint_button.setEnabled(True)
                    self.add_waypoint_button.setToolTip("添加途径点")

                break

    def _renumber_waypoints(self):
        """重新编号途径点"""
        for i, widget_dict in enumerate(self.waypoint_widgets):
            widget_dict['label'].setText(f"经{i + 1}")
            widget_dict['input'].setPlaceholderText(f"请输入途径点{i + 1}")

    def _update_add_button_position(self):
        """更新添加途径点按钮的位置"""
        if len(self.waypoint_widgets) == 0:
            # 没有途径点时，添加按钮在主容器右侧垂直居中
            # 先从终点行移除（如果存在）
            if self.end_layout.indexOf(self.add_waypoint_button) >= 0:
                self.end_layout.removeWidget(self.add_waypoint_button)

            # 驾车模式下，起点和终点都不显示占位符（添加按钮在右侧垂直居中）
            # 步行和骑行模式下，终点显示占位符
            if self.current_transport_mode == "driving":
                self.start_spacer.hide()
                self.end_spacer.hide()
            else:
                self.end_spacer.show()

            # 添加到主容器右侧
            if self.main_locations_layout.indexOf(self.add_waypoint_button) < 0:
                self.main_locations_layout.addWidget(self.add_waypoint_button, 0, Qt.AlignVCenter)
        else:
            # 有途径点时，将添加按钮移到终点输入框右侧
            # 先从主容器移除（如果存在）
            if self.main_locations_layout.indexOf(self.add_waypoint_button) >= 0:
                self.main_locations_layout.removeWidget(self.add_waypoint_button)

            # 驾车模式下，起点显示占位符保持宽度一致，终点隐藏（添加按钮占据了这个位置）
            self.start_spacer.show()
            self.end_spacer.hide()

            # 添加到终点行（替换占位符位置）
            if self.end_layout.indexOf(self.add_waypoint_button) < 0:
                # 移除占位符
                self.end_layout.removeWidget(self.end_spacer)
                # 添加按钮
                self.end_layout.addWidget(self.add_waypoint_button)
                # 重新添加占位符（保持在最后）
                self.end_layout.addWidget(self.end_spacer)

    def _on_search_location(self, location_type: str):
        """搜索地点"""
        if location_type == "start":
            text = self.start_input.text().strip()
            input_widget = self.start_input
        elif location_type == "end":
            text = self.end_input.text().strip()
            input_widget = self.end_input
        else:  # waypoint
            # 找到当前焦点的输入框
            focused_widget = self.focusWidget()
            if isinstance(focused_widget, QLineEdit):
                text = focused_widget.text().strip()
                input_widget = focused_widget
            else:
                return

        # 如果地址待选列表可见且有结果，按回车时选择第一个地址
        if self.address_suggestions_container.isVisible() and self.current_suggestions:
            # 自动选择第一个地址
            first_address = self.current_suggestions[0]
            self._on_address_confirm_clicked(first_address)
            return

        if text:
            # 保存当前搜索文本（用于后续保存历史记录）
            self._current_search_text = text

            # 更新当前搜索状态
            self.current_search_type = location_type
            self.current_search_input = input_widget

            # 发送搜索信号
            self.search_location_clicked.emit(text, location_type)

    def _on_plan_route(self):
        """规划路线"""
        start = self.start_input.text().strip()
        end = self.end_input.text().strip()

        if not start or not end:
            return

        # 获取途径点
        waypoints = []
        for widget_dict in self.waypoint_widgets:
            waypoint_text = widget_dict['input'].text().strip()
            if waypoint_text:
                waypoints.append(waypoint_text)

        # 发送信号
        self.plan_route_clicked.emit(start, end, self.current_transport_mode, waypoints)

    def _on_clear_route(self):
        """清除路线"""
        # 清空起点和终点
        self.start_input.clear()
        self.end_input.clear()

        # 清空所有途径点
        while self.waypoint_widgets:
            widget_dict = self.waypoint_widgets[0]
            self._remove_waypoint(widget_dict['container'])

        # 恢复历史记录模式（关闭路线待选列表，显示历史记录）
        self.restore_history_mode()

        # 发送清除路线信号
        self.clear_route_clicked.emit()

    def _on_history_clicked(self, item: QListWidgetItem):
        """点击历史记录"""
        history_data = item.data(Qt.UserRole)
        if history_data:
            # 更新所有历史记录项的选中状态
            self._update_history_selection(item)

            # 检查选中的历史记录是否有路线数据
            self._check_and_update_route_data_status(history_data)

            # 发送历史记录选中信号
            self.history_selected.emit(history_data)

    def _update_history_selection(self, selected_item: QListWidgetItem):
        """更新历史记录选中状态"""
        if not hasattr(self, 'history_widgets'):
            return

        # 获取选中项的索引
        selected_row = self.history_list.row(selected_item)

        # 更新所有历史记录项的选中状态
        for i, widget in enumerate(self.history_widgets):
            is_selected = (i == selected_row)
            widget.set_selected(is_selected)

    def _check_and_update_route_data_status(self, history_data: dict):
        """检查并更新历史记录的路线数据状态"""
        # 检查历史记录是否有完整的路线数据
        route_points = history_data.get('route_points', [])
        has_route_data = bool(route_points and len(route_points) > 0)

        # 更新对应widget的路线数据状态
        for widget in self.history_widgets:
            if widget.history_data == history_data:
                widget.set_route_data_available(has_route_data)
                break

    def update_history_route_data_status(self, history_data: dict, has_route_data: bool):
        """更新历史记录的路线数据状态"""
        if not hasattr(self, 'history_widgets'):
            return

        # 根据历史记录数据找到对应的widget并更新状态
        for widget in self.history_widgets:
            if widget.history_data == history_data:
                widget.set_route_data_available(has_route_data)
                break

    def set_start_location(self, text: str):
        """设置起点"""
        self.start_input.setText(text)

    def set_end_location(self, text: str):
        """设置终点"""
        self.end_input.setText(text)

    def clear_all_inputs(self):
        """清空所有输入框（供外部调用）"""
        # 清空起点和终点
        self.start_input.clear()
        self.end_input.clear()

        # 清空所有途径点
        while self.waypoint_widgets:
            widget_dict = self.waypoint_widgets[0]
            self._remove_waypoint(widget_dict['container'])

    def load_history(self, history_list: list):
        """加载历史记录"""
        # 保存历史记录列表，以便错误提示后恢复
        self._last_history_list = history_list

        self.history_list.clear()

        # 存储历史记录项的引用，用于状态管理
        self.history_widgets = []

        for record in history_list:
            # 创建自定义历史记录项widget
            history_widget = RouteHistoryItem(record)

            # 确保初始状态：未选中，无路线数据（导出按钮禁用）
            history_widget.set_selected(False)
            history_widget.set_route_data_available(False)

            # 连接导出GPX信号
            history_widget.export_gpx_clicked.connect(self.history_export_gpx_clicked.emit)

            # 创建列表项
            item = QListWidgetItem()
            item.setData(Qt.UserRole, record)
            item.setSizeHint(QSize(history_widget.sizeHint().width(), max(40, history_widget.sizeHint().height())))

            self.history_list.addItem(item)
            self.history_list.setItemWidget(item, history_widget)

            # 保存widget引用
            self.history_widgets.append(history_widget)

    def _on_input_focus_in(self, event, location_type: str, input_widget):
        """输入框获得焦点时的处理"""
        # 如果之前有正在搜索的输入框，且不是当前输入框，则确认之前的选择
        if self.current_search_input and self.current_search_input != input_widget:
            self._confirm_current_selection()

        # 更新当前搜索状态
        self.current_search_type = location_type
        self.current_search_input = input_widget

        # 调用原始的focusInEvent
        QLineEdit.focusInEvent(input_widget, event)

    def _confirm_current_selection(self):
        """确认当前的地址选择"""
        if not self.current_search_input or not self.current_suggestions:
            # 如果没有选择地址，直接显示所有历史记录
            self.show_all_history()
            self.address_suggestions_container.setVisible(False)
            self.history_container.setVisible(True)
            return

        # 获取当前选中的地址
        if 0 <= self.selected_suggestion_index < len(self.current_suggestions):
            selected_address = self.current_suggestions[self.selected_suggestion_index]
            # 将地址名称回显到输入框
            address_name = selected_address.get('name', '')
            self.current_search_input.setText(address_name)

            # 如果是起点，根据起点过滤历史记录
            if self.current_search_type == "start" and address_name:
                self.filter_history_by_start(address_name)
            else:
                # 其他情况显示所有历史记录
                self.show_all_history()

        # 隐藏地址待选列表，显示历史记录
        self._hide_address_suggestions()
        self.history_container.setVisible(True)

    def _hide_address_suggestions(self):
        """隐藏地址待选列表"""
        self.address_suggestions_container.setVisible(False)
        self.current_suggestions = []
        self.selected_suggestion_index = 0

    def _on_address_suggestion_clicked(self, item: QListWidgetItem):
        """点击地址待选项"""
        # 获取地址数据
        address_data = item.data(Qt.UserRole)
        if not address_data:
            return

        # 更新选中索引
        self.selected_suggestion_index = self.address_suggestions_list.row(item)

        # 发送地址选中信号，通知父组件在地图上标识位置（需要缩放地图）
        self.address_selected.emit(address_data, self.current_search_type, True)

    def _on_address_suggestion_double_clicked(self, item: QListWidgetItem):
        """双击地址待选项"""
        # 获取地址数据
        address_data = item.data(Qt.UserRole)
        if not address_data:
            return

        # 双击时直接确认选择该地址
        self._on_address_confirm_clicked(address_data)

    def _on_address_confirm_clicked(self, address_data: dict):
        """点击地址确认按钮"""
        # 将地址名称回填到输入框
        if self.current_search_input:
            self.current_search_input.setText(address_data.get('name', ''))

        # 更新选中的地址
        for i in range(self.address_suggestions_list.count()):
            item = self.address_suggestions_list.item(i)
            if item.data(Qt.UserRole) == address_data:
                self.selected_suggestion_index = i
                break

        # 发送地址选中信号（包含搜索文本，用于保存历史记录）
        # 保存当前搜索的文本（用于历史记录）
        search_text = getattr(self, '_current_search_text', address_data.get('name', ''))

        # 发送地址选中信号，同时传递搜索文本，但不缩放地图（双击时不需要缩放）
        self.address_selected.emit(address_data, self.current_search_type, False)

        # 发送保存历史记录的信号（通过自定义属性传递）
        address_data['_search_text'] = search_text

        # 确认选择并关闭待选列表
        self._confirm_current_selection()

    def show_address_suggestions(self, suggestions: list):
        """显示地址搜索结果

        Args:
            suggestions: 地址列表，每个地址是一个字典，包含：
                - name: 地址名称
                - address: 详细地址
                - location: 经纬度 "lng,lat"
        """
        self.current_suggestions = suggestions
        self.selected_suggestion_index = 0

        # 清空列表
        self.address_suggestions_list.clear()

        if not suggestions:
            self._hide_address_suggestions()
            return

        # 添加地址到列表
        for i, addr in enumerate(suggestions):
            # 创建自定义列表项widget
            item_widget = AddressSuggestionItem(addr)
            item_widget.confirm_clicked.connect(self._on_address_confirm_clicked)

            # 创建列表项
            item = QListWidgetItem()
            item.setData(Qt.UserRole, addr)

            # 设置合适的高度以显示完整内容
            # 使用 sizeHint 并确保有足够的高度
            size_hint = item_widget.sizeHint()
            # 减小最小高度，让更多结果可以显示
            item.setSizeHint(QSize(size_hint.width(), max(55, size_hint.height())))

            self.address_suggestions_list.addItem(item)
            self.address_suggestions_list.setItemWidget(item, item_widget)

        # 显示地址待选列表，隐藏历史记录
        self.address_suggestions_container.setVisible(True)
        self.history_container.setVisible(False)

        # 默认选中第一项
        if self.address_suggestions_list.count() > 0:
            self.address_suggestions_list.setCurrentRow(0)

    def hide_address_suggestions_and_show_history(self):
        """隐藏地址待选列表，显示历史记录"""
        self._hide_address_suggestions()
        self.history_container.setVisible(True)

    def get_current_search_type(self):
        """获取当前正在搜索的类型"""
        return self.current_search_type

    def get_selected_address(self):
        """获取当前选中的地址"""
        if 0 <= self.selected_suggestion_index < len(self.current_suggestions):
            return self.current_suggestions[self.selected_suggestion_index]
        return None

    def filter_history_by_start(self, start_location: str):
        """根据起点过滤历史记录

        Args:
            start_location: 起点地址
        """
        # 遍历历史记录列表，只显示匹配起点的记录
        for i in range(self.history_list.count()):
            item = self.history_list.item(i)
            history_data = item.data(Qt.UserRole)
            if history_data:
                # 如果起点匹配，显示该项；否则隐藏
                if history_data.get('start', '') == start_location:
                    item.setHidden(False)
                else:
                    item.setHidden(True)

    def show_all_history(self):
        """显示所有历史记录"""
        for i in range(self.history_list.count()):
            item = self.history_list.item(i)
            item.setHidden(False)

    def show_route_alternatives(self, alternatives: list, selected_index: int = 0):
        """显示路线待选列表

        Args:
            alternatives: 路线方案列表，每个方案包含：
                - route_points: 路线点列表
                - duration: 预估时间（秒）
                - distance: 路线距离（米）
                - tolls: 收费金额（元）
                - traffic_lights: 红绿灯数量
                - description: 路线描述
            selected_index: 默认选中的方案索引
        """
        # 清空历史记录列表
        self.history_list.clear()

        if not alternatives:
            return

        # 添加路线方案到列表
        for i, route_data in enumerate(alternatives):
            # 创建自定义路线方案项widget
            is_selected = (i == selected_index)
            route_widget = RouteAlternativeItem(route_data, i, is_selected)

            # 连接导出GPX信号
            route_widget.export_gpx_clicked.connect(self.export_gpx_clicked.emit)

            # 创建列表项
            item = QListWidgetItem()
            item.setData(Qt.UserRole, {'index': i, 'route_data': route_data})

            # 设置合适的高度
            size_hint = route_widget.sizeHint()
            item.setSizeHint(QSize(size_hint.width(), max(60, size_hint.height())))

            self.history_list.addItem(item)
            self.history_list.setItemWidget(item, route_widget)

        # 默认选中第一项
        if self.history_list.count() > 0:
            self.history_list.setCurrentRow(selected_index)

        # 连接点击事件
        try:
            self.history_list.itemClicked.disconnect()  # 先断开之前的连接
        except:
            pass
        self.history_list.itemClicked.connect(self._on_route_alternative_clicked)

    def _on_route_alternative_clicked(self, item: QListWidgetItem):
        """点击路线方案"""
        data = item.data(Qt.UserRole)
        if data:
            index = data.get('index', 0)

            # 更新所有项的选中状态
            for i in range(self.history_list.count()):
                list_item = self.history_list.item(i)
                widget = self.history_list.itemWidget(list_item)
                if isinstance(widget, RouteAlternativeItem):
                    widget.set_selected(i == index)

            # 发送信号
            self.route_alternative_selected.emit(index)

    def restore_history_mode(self):
        """恢复历史记录模式"""
        # 清空列表
        self.history_list.clear()

        # 重新连接历史记录点击事件
        try:
            self.history_list.itemClicked.disconnect()
        except:
            pass
        self.history_list.itemClicked.connect(self._on_history_clicked)

        # 重新加载历史记录
        if hasattr(self, '_last_history_list') and self._last_history_list:
            self.load_history(self._last_history_list)
        else:
            # 如果没有保存的历史记录，从存储中加载
            from modules.routing.storage.route_history_storage import RouteHistoryStorage
            storage = RouteHistoryStorage()
            history_list = storage.get_history(10)
            self.load_history(history_list)

    def set_selected_history(self, selected_history_data: dict):
        """设置选中的历史记录"""
        if not hasattr(self, 'history_widgets') or not self.history_widgets:
            return

        # 找到匹配的历史记录并设置为选中状态
        for i, widget in enumerate(self.history_widgets):
            is_match = widget.history_data == selected_history_data

            if is_match:
                # 设置选中状态
                widget.set_selected(True)

                # 自动检查并设置路线数据状态
                route_points = selected_history_data.get('route_points', [])
                has_route_data = bool(route_points and len(route_points) > 0)
                widget.set_route_data_available(has_route_data)

                # 同时设置列表项为选中状态
                self.history_list.setCurrentRow(i)
            else:
                # 其他项设置为未选中状态
                widget.set_selected(False)
                widget.set_route_data_available(False)


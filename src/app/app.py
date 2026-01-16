"""
GPX Studio 主应用窗口 (重构版)
使用管理器模式，提高代码的可复用性、可维护性、可扩展性
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QListWidget, QFileDialog,
                             QMessageBox, QSplitter, QListWidgetItem, QScrollArea,
                             QApplication, QDialog, QTimeEdit, QMenuBar, QMenu, QAction,
                             QComboBox, QLineEdit)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile

import sys
import os
from typing import Optional

# 确保日志重定向生效 - 必须在其他导入之前执行
import core.logging_setup

# 导入信号管理器
from core.signals import SignalManager

# 导入模块
from modules.geolocation.geolocation import GeolocationHandler
from modules.map.webengine import ConsoleWebEnginePage
from modules.map.map_renderer import MapRenderer
from services.config.map_config import map_config

# 导入UI组件
from ui.styles import UIStyles
from ui.panels.panel_factory import PanelFactory
from ui.panels.log_panel import LogPanel, setup_logger
from ui.panels.scale_panel import ScalePanel
from ui.dialogs.map_config_dialog import MapConfigDialog
from ui.dialogs.about_dialog import AboutDialog
from ui.dialogs.map_context_menu import MapContextMenu
from ui.layout.layout_manager import LayoutManager

# 导入常量
from .constants import (
    WINDOW_TITLE, WINDOW_SIZE, MAP_LOAD_DELAY_MS
)

# 导入管理器
from .managers import (
    WindowManager, ServiceManager, DataManager,
    LocationManager, SearchManager, MapManager,
    RouteManager, TimeManager
)


class GpxStudio(QMainWindow):
    """GPX Studio 主应用窗口（重构版）"""

    def __init__(self, splash_screen=None):
        """
        初始化主窗口

        Args:
            splash_screen: 启动画面实例，用于更新加载进度
        """
        super().__init__()
        self.splash_screen = splash_screen

        print("=" * 80)
        print("GPX Studio 程序启动开始（重构版）")
        print("=" * 80)

        # 初始化数据目录（最先执行）
        from .data_paths import init_data_directories
        init_data_directories()

        # 初始化各个部分（进度范围：10-95，为启动和完成阶段留出空间）
        self._update_splash(15, "正在初始化管理器...")
        self._init_managers()

        self._update_splash(30, "正在设置窗口...")
        self._init_window()

        self._update_splash(45, "正在初始化服务...")
        self._init_services()

        self._update_splash(60, "正在初始化信号系统...")
        self._init_signals()

        self._update_splash(75, "正在加载用户界面...")
        self._init_ui()

        self._update_splash(90, "正在初始化日志系统...")
        self._init_logging()

        self._update_splash(95, "准备就绪...")

        # 启动完成
        self.logger.info("=" * 80)
        self.logger.info("GPX Studio 程序启动完成")
        self.logger.info("=" * 80)

        # 标记首次启动完成
        from core.logging_setup import mark_first_run_completed
        mark_first_run_completed()

    def _update_splash(self, progress: int, message: str = ""):
        """
        更新启动画面进度

        Args:
            progress: 进度值 (0-100)
            message: 状态消息
        """
        if self.splash_screen:
            self.splash_screen.update_progress(progress, message)
            # 强制处理事件，确保界面更新
            from PyQt5.QtWidgets import QApplication
            QApplication.processEvents()

    def _init_managers(self):
        """初始化所有管理器"""
        print("开始初始化管理器")

        # 数据管理器（独立，最先初始化）
        self.data_manager = DataManager()

        # 准备日志回调（稍后在logger初始化后连接）
        self.logger_callbacks = {
            'geocoding': self._log_to_geocoding,
            'routing': self._log_to_routing,
            'gpx': self._log_to_gpx,
            'service': self._log_to_service
        }

        # 服务管理器
        self.service_manager = ServiceManager(self.logger_callbacks)

        # 窗口管理器
        self.window_manager = WindowManager(self, WINDOW_TITLE, WINDOW_SIZE)

        # UI更新器回调（稍后在UI初始化后连接）
        self.ui_updater = {}

        # 任务管理器（延迟初始化，需要logger）
        self.task_manager = None

        print("管理器初始化完成")

    def _init_window(self):
        """初始化窗口设置"""
        print("开始初始化窗口设置")
        self.window_manager.setup_window()

        # 创建菜单栏
        self._create_menu_bar()

        print("窗口设置初始化完成")

    def _init_services(self):
        """初始化服务"""
        print("开始初始化服务")

        # 重新加载地图配置（确保使用正确的数据目录）
        from services.config.map_config import map_config
        map_config._load_config()

        self.service_manager.initialize_services()
        print("服务初始化完成")

    def _init_signals(self):
        """初始化信号系统"""
        print("开始初始化信号系统")
        self.signal_manager = SignalManager()
        self.geolocation_handler = GeolocationHandler(signal_manager=self.signal_manager)

        # 连接信号（稍后在各管理器初始化后连接具体处理）
        print("信号系统初始化完成")

    def _init_ui(self):
        """初始化用户界面"""
        print("开始初始化UI")
        self.init_ui()

        # 初始化地图右键菜单
        self.map_context_menu = MapContextMenu(self)
        self.map_context_menu.set_as_start.connect(self._on_context_menu_set_start)
        self.map_context_menu.add_as_waypoint.connect(self._on_context_menu_add_waypoint)
        self.map_context_menu.set_as_end.connect(self._on_context_menu_set_end)

        print("UI初始化完成")

    def _init_logging(self):
        """初始化日志系统"""
        print("开始初始化日志系统")
        self.logger = setup_logger(None, "GpxStudio")  # 不使用UI日志面板，只输出到文件

        # 初始化任务管理器（需要logger）
        from core.background_task import TaskManager
        self.task_manager = TaskManager(self.logger)

        # 连接任务管理器信号
        self._connect_task_manager_signals()

        # 初始化Windows定位服务（需要logger）
        self.service_manager.initialize_windows_location_service()

        # 初始化其他管理器（需要logger和UI组件）
        self._init_functional_managers()

        # 连接信号
        self._connect_signals()

        self.logger.debug("日志系统初始化完成")

    def _init_functional_managers(self):
        """初始化功能管理器（需要在UI和logger之后）"""
        print("开始初始化功能管理器")

        # 构建UI更新器回调
        self._build_ui_updater()

        # 初始化各个功能管理器
        self.location_manager = LocationManager(
            self.service_manager, self.data_manager,
            self.ui_updater, self.logger, self.task_manager
        )

        self.map_manager = MapManager(
            self.data_manager, self.map_view, self.logger
        )

        self.search_manager = SearchManager(
            self.service_manager, self.data_manager,
            self.ui_updater, self.logger, self.task_manager
        )

        self.route_manager = RouteManager(
            self.service_manager, self.data_manager,
            self.ui_updater, self.logger, self.task_manager
        )

        self.time_manager = TimeManager(
            self.data_manager, self.ui_updater, self.logger
        )

        print("功能管理器初始化完成")

    def _build_ui_updater(self):
        """构建UI更新器回调字典"""
        self.ui_updater = {
            # 窗口和对话框
            'main_window': self,
            'show_warning': self._show_warning,
            'show_info': self._show_info,

            # 进度条
            'set_progress_indeterminate': self._set_progress_indeterminate,
            'set_progress_complete': self._set_progress_complete,
            'set_progress': self._set_progress,

            # 结果列表
            'clear_results': self._clear_results,
            'clear_results_list': self._clear_results_list,
            'add_result': self._add_result,
            'set_results_title': self._set_results_title,

            # 搜索结果显示
            'show_search_results': self._show_search_results,
            'show_search_results_on_map': self._show_search_results_on_map,
            'show_search_results_dropdown': self._show_search_results_dropdown,  # 新增：显示搜索结果下拉列表

            # 位置显示
            'update_location_display': self._update_location_display,
            'update_start_from_search': self._update_start_from_search,
            'update_end_from_search': self._update_end_from_search,
            'add_waypoint_to_list': self._add_waypoint_to_list,

            # 地图
            'update_map_preview': self._update_map_preview,
            'preview_search_result': self._preview_search_result,
            'show_location_on_map': self._show_location_on_map,
            'show_route_on_map': self._show_route_on_map,
            'load_map_url': self._load_map_url,  # 新增：直接加载地图URL

            # 定位
            'trigger_browser_location': self._trigger_browser_location,

            # 时间
            'get_start_time': lambda: self.start_time_edit.dateTime(),
            'set_start_time': lambda dt: self.start_time_edit.setDateTime(dt),
            'get_end_time': lambda: self.end_time_edit.dateTime(),
            'set_end_time': lambda dt: self.end_time_edit.setDateTime(dt),
            'get_duration': lambda: self.duration_time_edit.text(),
            'set_duration': lambda text: self.duration_time_edit.setText(text),
            'get_transport_mode': lambda: self.transport_combo.currentText(),

            # 时间面板
            'hide_time_panel': lambda: self.time_panel.hide() if hasattr(self, 'time_panel') and self.time_panel.isVisible() else None,
            'hide_date_panel': lambda: self.date_panel.hide() if hasattr(self, 'date_panel') and self.date_panel.isVisible() else None,
            'setup_date_panel_callback': self._setup_date_panel_callback,
            'setup_time_panel_callback': self._setup_time_panel_callback,
            'show_date_panel': self._show_date_panel,
            'show_time_panel': self._show_time_panel,

            # 路线信息
            'add_route_time_info': self._add_route_time_info,
            'show_route_alternatives': self._show_route_alternatives,
            'save_route_history': self._save_route_history,
        }

    def _connect_signals(self):
        """连接信号"""
        self.signal_manager.geolocation_success.connect(self._on_geolocation_success)
        self.signal_manager.geolocation_error.connect(self._on_geolocation_error)
        self.signal_manager.map_zoom_changed.connect(self.on_map_zoom_changed)
        self.signal_manager.map_right_click.connect(self._on_map_right_click)

    def _connect_task_manager_signals(self):
        """连接任务管理器信号"""
        # 任务开始
        self.task_manager.task_started.connect(self._on_task_started)
        # 任务进度
        self.task_manager.task_progress.connect(self._on_task_progress)
        # 任务完成
        self.task_manager.task_completed.connect(self._on_task_completed)
        # 任务失败
        self.task_manager.task_failed.connect(self._on_task_failed)
        # 任务取消
        self.task_manager.task_cancelled.connect(self._on_task_cancelled)
        # 任务日志
        self.task_manager.task_log.connect(self._on_task_log)

    # ==================== 日志回调方法 ====================

    def _log_to_service(self, level: str, message: str):
        """将日志转发到WindowsLocationService"""
        self._log_with_prefix("Windows定位", level, message)

    def _log_to_geocoding(self, level: str, message: str):
        """将日志转发到GeocodingService"""
        self._log_with_prefix("地理编码", level, message)

    def _log_to_routing(self, level: str, message: str):
        """将日志转发到RoutingService"""
        self._log_with_prefix("路线规划", level, message)

    def _log_to_gpx(self, level: str, message: str):
        """将日志转发到GpxExportService"""
        self._log_with_prefix("GPX导出", level, message)

    def _log_with_prefix(self, prefix: str, level: str, message: str):
        """通用日志转发方法"""
        if not hasattr(self, 'logger'):
            return
        level_map = {
            "DEBUG": self.logger.debug,
            "INFO": self.logger.info,
            "WARNING": self.logger.warning,
            "ERROR": self.logger.error,
            "CRITICAL": self.logger.critical
        }
        log_func = level_map.get(level, self.logger.info)
        log_func(f"[{prefix}] {message}")

    # ==================== UI初始化方法 ====================

    def _create_menu_bar(self):
        """创建菜单栏"""
        # 暂时不创建任何菜单，为重新设计界面做准备
        pass

    def init_ui(self):
        """初始化用户界面 - 简化版，只显示地图"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 只创建地图面板，铺满整个界面
        map_panel = self.create_map_panel()
        main_layout.addWidget(map_panel)

        # 延迟加载初始地图
        QTimer.singleShot(MAP_LOAD_DELAY_MS, self._show_initial_map)

    def create_map_panel(self):
        """创建地图面板（铺满整个界面）"""
        map_widget = QWidget()
        layout = QVBoxLayout(map_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 创建地图视图
        self.map_view = QWebEngineView()
        self.web_page = ConsoleWebEnginePage(signal_manager=self.signal_manager)
        self.web_page.set_geolocation_handler(self.geolocation_handler)
        self.map_view.setPage(self.web_page)

        # 设置User Agent
        profile = QWebEngineProfile.defaultProfile()
        profile.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        # 创建一个容器来放置地图和浮动按钮
        map_container = QWidget()
        map_container_layout = QVBoxLayout(map_container)
        map_container_layout.setContentsMargins(0, 0, 0, 0)
        map_container_layout.setSpacing(0)
        map_container_layout.addWidget(self.map_view)

        # 获取项目根目录
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

        # 统一的控件高度（在使用前定义）
        control_height = 36

        # 创建右侧按钮容器（统一背景框，与搜索框样式一致）
        self.right_buttons_container = QWidget()
        self.right_buttons_container.setParent(map_container)
        self.right_buttons_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 6px;
                border: 1px solid rgba(0, 0, 0, 0.15);
            }
        """)
        right_buttons_layout = QVBoxLayout(self.right_buttons_container)
        right_buttons_layout.setContentsMargins(8, 6, 8, 6)  # 内边距，与搜索框一致
        right_buttons_layout.setSpacing(5)  # 按钮间距

        # 按钮样式（透明背景，无边框，与搜索框内按钮样式一致）
        right_button_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
            }
        """

        # 创建地图设置按钮
        self.map_settings_button = QPushButton()
        self.map_settings_button.setToolTip("地图设置")
        self.map_settings_button.clicked.connect(self.on_map_settings_clicked)
        self.map_settings_button.setFixedSize(control_height, control_height)  # 使用与搜索框按钮相同的大小
        settings_icon_path = os.path.join(project_root, 'res', 'Setting.png')
        if os.path.exists(settings_icon_path):
            from PyQt5.QtGui import QIcon
            self.map_settings_button.setIcon(QIcon(settings_icon_path))
            from PyQt5.QtCore import QSize
            self.map_settings_button.setIconSize(QSize(20, 20))  # 与搜索框按钮图标大小一致
        else:
            self.map_settings_button.setText("⚙️")
        self.map_settings_button.setStyleSheet(right_button_style)
        right_buttons_layout.addWidget(self.map_settings_button)

        # 创建日志设置按钮
        self.log_settings_button = QPushButton()
        self.log_settings_button.setToolTip("日志设置")
        self.log_settings_button.clicked.connect(self.on_log_settings_clicked)
        self.log_settings_button.setFixedSize(control_height, control_height)
        log_icon_path = os.path.join(project_root, 'res', 'Log.png')
        if os.path.exists(log_icon_path):
            from PyQt5.QtGui import QIcon
            self.log_settings_button.setIcon(QIcon(log_icon_path))
            from PyQt5.QtCore import QSize
            self.log_settings_button.setIconSize(QSize(20, 20))
        else:
            self.log_settings_button.setText("📋")
        self.log_settings_button.setStyleSheet(right_button_style)
        right_buttons_layout.addWidget(self.log_settings_button)

        # 创建关于按钮
        self.about_button = QPushButton()
        self.about_button.setToolTip("关于")
        self.about_button.clicked.connect(self.on_about_clicked)
        self.about_button.setFixedSize(control_height, control_height)
        about_icon_path = os.path.join(project_root, 'res', 'About.png')
        if os.path.exists(about_icon_path):
            from PyQt5.QtGui import QIcon
            self.about_button.setIcon(QIcon(about_icon_path))
            from PyQt5.QtCore import QSize
            self.about_button.setIconSize(QSize(20, 20))
        else:
            self.about_button.setText("ℹ️")
        self.about_button.setStyleSheet(right_button_style)
        right_buttons_layout.addWidget(self.about_button)

        # 创建放大按钮
        self.zoom_in_button = QPushButton()
        self.zoom_in_button.setToolTip("放大")
        self.zoom_in_button.clicked.connect(self.on_zoom_in_clicked)
        self.zoom_in_button.setFixedSize(control_height, control_height)
        zoom_in_icon_path = os.path.join(project_root, 'res', 'ZoomBig.png')
        if os.path.exists(zoom_in_icon_path):
            from PyQt5.QtGui import QIcon
            self.zoom_in_button.setIcon(QIcon(zoom_in_icon_path))
            from PyQt5.QtCore import QSize
            self.zoom_in_button.setIconSize(QSize(20, 20))
        else:
            self.zoom_in_button.setText("+")
        self.zoom_in_button.setStyleSheet(right_button_style)
        right_buttons_layout.addWidget(self.zoom_in_button)

        # 创建缩小按钮
        self.zoom_out_button = QPushButton()
        self.zoom_out_button.setToolTip("缩小")
        self.zoom_out_button.clicked.connect(self.on_zoom_out_clicked)
        self.zoom_out_button.setFixedSize(control_height, control_height)
        zoom_out_icon_path = os.path.join(project_root, 'res', 'ZoomSamll.png')
        if os.path.exists(zoom_out_icon_path):
            from PyQt5.QtGui import QIcon
            self.zoom_out_button.setIcon(QIcon(zoom_out_icon_path))
            from PyQt5.QtCore import QSize
            self.zoom_out_button.setIconSize(QSize(20, 20))
        else:
            self.zoom_out_button.setText("-")
        self.zoom_out_button.setStyleSheet(right_button_style)
        right_buttons_layout.addWidget(self.zoom_out_button)

        # 创建定位按钮
        self.locate_button = QPushButton()
        self.locate_button.setToolTip("定位到当前位置")
        self.locate_button.clicked.connect(self.on_locate_clicked)
        self.locate_button.setFixedSize(control_height, control_height)
        location_icon_path = os.path.join(project_root, 'res', 'Location.png')
        if os.path.exists(location_icon_path):
            from PyQt5.QtGui import QIcon
            self.locate_button.setIcon(QIcon(location_icon_path))
            from PyQt5.QtCore import QSize
            self.locate_button.setIconSize(QSize(20, 20))
        else:
            self.locate_button.setText("📍")
        self.locate_button.setStyleSheet(right_button_style)
        right_buttons_layout.addWidget(self.locate_button)

        # 创建比例尺信息标签（左下角）
        self.scale_info_label = QLabel()
        self.scale_info_label.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(0, 0, 0, 0.2);
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 12px;
                color: #333333;
            }
        """)
        self.scale_info_label.setText("缩放级别: 10")
        self.scale_info_label.setParent(map_container)

        # 创建搜索框容器（左上角）- 带统一背景
        self.search_container = QWidget()
        self.search_container.setParent(map_container)
        # 设置统一的背景样式（参考高德地图）
        self.search_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 6px;
                border: 1px solid rgba(0, 0, 0, 0.15);
            }
        """)
        search_layout = QHBoxLayout(self.search_container)
        search_layout.setContentsMargins(8, 6, 8, 6)  # 内边距
        search_layout.setSpacing(8)  # 控件间距

        # 搜索输入框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索地点...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #f5f5f5;
                border: none;
                border-radius: 4px;
                padding: 0px 12px;
                font-size: 13px;
                min-width: 250px;
                max-width: 250px;
            }
            QLineEdit:focus {
                background-color: #ebebeb;
            }
        """)
        self.search_input.setFixedHeight(control_height)
        # 按回车键触发搜索
        self.search_input.returnPressed.connect(self.on_search_button_clicked)
        # 文本改变时的处理
        self.search_input.textChanged.connect(self._on_search_input_text_changed)
        # 获得焦点时显示搜索历史
        self.search_input.focusInEvent = self._on_search_input_focus_in
        # 失去焦点时隐藏搜索历史（延迟处理以允许点击历史项）
        self.search_input.focusOutEvent = self._on_search_input_focus_out
        search_layout.addWidget(self.search_input)

        # 搜索按钮样式（方形按钮，无边框）
        search_button_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
            }
        """

        # 搜索按钮
        self.search_button = QPushButton()
        self.search_button.setToolTip("搜索")
        self.search_button.clicked.connect(self.on_search_button_clicked)
        self.search_button.setFixedSize(control_height, control_height)
        search_icon_path = os.path.join(project_root, 'res', 'Search.png')
        if os.path.exists(search_icon_path):
            from PyQt5.QtGui import QIcon
            self.search_button.setIcon(QIcon(search_icon_path))
            from PyQt5.QtCore import QSize
            self.search_button.setIconSize(QSize(20, 20))
        else:
            self.search_button.setText("🔍")
        self.search_button.setStyleSheet(search_button_style)
        search_layout.addWidget(self.search_button)

        # 路线按钮
        self.route_button = QPushButton()
        self.route_button.setToolTip("路线")
        self.route_button.clicked.connect(self.on_route_button_clicked)
        self.route_button.setFixedSize(control_height, control_height)
        route_icon_path = os.path.join(project_root, 'res', 'Route.png')
        if os.path.exists(route_icon_path):
            from PyQt5.QtGui import QIcon
            self.route_button.setIcon(QIcon(route_icon_path))
            from PyQt5.QtCore import QSize
            self.route_button.setIconSize(QSize(20, 20))
        else:
            self.route_button.setText("🗺️")
        self.route_button.setStyleSheet(search_button_style)
        search_layout.addWidget(self.route_button)

        # 关闭按钮（初始隐藏，显示搜索结果时替换路线按钮）
        self.cancel_button = QPushButton()
        self.cancel_button.setToolTip("关闭")
        self.cancel_button.clicked.connect(self.on_cancel_button_clicked)
        self.cancel_button.setFixedSize(control_height, control_height)
        cancel_icon_path = os.path.join(project_root, 'res', 'Cancel.png')
        if os.path.exists(cancel_icon_path):
            from PyQt5.QtGui import QIcon
            self.cancel_button.setIcon(QIcon(cancel_icon_path))
            from PyQt5.QtCore import QSize
            self.cancel_button.setIconSize(QSize(20, 20))
        else:
            self.cancel_button.setText("✕")
        self.cancel_button.setStyleSheet(search_button_style)
        search_layout.addWidget(self.cancel_button)
        self.cancel_button.hide()  # 初始隐藏

        self.scale_info_label.setParent(map_container)

        # 监听窗口大小变化，调整按钮位置
        map_container.resizeEvent = lambda event: self._update_button_positions(map_container)

        layout.addWidget(map_container)

        # 初始化必要的UI组件（用于后台逻辑，但不显示）
        self._init_hidden_ui_components()

        # 创建搜索历史下拉列表
        from modules.search import SearchHistoryPopup, SearchResultsPopup
        self.search_history_popup = SearchHistoryPopup(map_container)
        self.search_history_popup.history_selected.connect(self._on_history_selected)
        self.search_history_popup.hide()

        # 创建搜索结果下拉列表
        self.search_results_popup = SearchResultsPopup(map_container)
        self.search_results_popup.result_selected.connect(self._on_result_selected)
        self.search_results_popup.hide()

        # 创建路线规划面板
        from modules.routing import RoutePlanPanel, RouteHistoryStorage
        self.route_plan_panel = RoutePlanPanel(map_container)
        self.route_plan_panel.cancel_clicked.connect(self._on_route_panel_cancel)
        self.route_plan_panel.plan_route_clicked.connect(self._on_route_plan_clicked)
        self.route_plan_panel.search_location_clicked.connect(self._on_route_location_search)
        self.route_plan_panel.history_selected.connect(self._on_route_history_selected)
        self.route_plan_panel.address_selected.connect(self._on_route_address_selected)
        self.route_plan_panel.clear_route_clicked.connect(self._on_route_clear_clicked)
        self.route_plan_panel.route_alternative_selected.connect(self._on_route_alternative_selected)
        self.route_plan_panel.hide()

        # 初始化路线历史存储
        self.route_history_storage = RouteHistoryStorage()

        # 保存当前搜索文本（用于保存历史记录）
        self.current_search_text = ""

        # 创建设置弹出面板
        from ui.popups import MapSettingsPopup, LogSettingsPopup, AboutPopup
        self.map_settings_popup = MapSettingsPopup(map_container)
        self.map_settings_popup.config_saved.connect(self._on_map_config_saved)
        self.map_settings_popup.hide()

        self.log_settings_popup = LogSettingsPopup(map_container)
        self.log_settings_popup.hide()

        self.about_popup = AboutPopup(map_container)
        self.about_popup.hide()

        return map_widget

    def _update_button_positions(self, container):
        """更新浮动按钮的位置"""
        # 获取容器大小
        width = container.width()
        height = container.height()

        # 边距设置
        right_margin = 20
        bottom_margin = 20
        left_margin = 20
        top_margin = 20

        # 右侧按钮容器位置（右侧垂直居中）
        self.right_buttons_container.adjustSize()  # 自动调整大小
        buttons_x = width - self.right_buttons_container.width() - right_margin
        # 垂直居中：(容器高度 - 按钮容器高度) / 2
        buttons_y = (height - self.right_buttons_container.height()) // 2
        self.right_buttons_container.move(buttons_x, buttons_y)
        self.right_buttons_container.raise_()

        # 比例尺信息标签（左下角）
        self.scale_info_label.adjustSize()  # 自动调整大小
        scale_x = left_margin
        scale_y = height - self.scale_info_label.height() - bottom_margin
        self.scale_info_label.move(scale_x, scale_y)
        self.scale_info_label.raise_()

        # 搜索框容器（左上角）
        self.search_container.adjustSize()  # 自动调整大小
        search_x = left_margin
        search_y = top_margin
        self.search_container.move(search_x, search_y)
        self.search_container.raise_()

    def on_zoom_in_clicked(self):
        """放大按钮点击"""
        self.logger.info("[缩放] 放大按钮点击")
        # 通过JavaScript调用地图的放大方法
        js_code = """
        (function() {
            var map = null;

            // 方法1: 通过leaflet-container元素
            var mapElement = document.querySelector('.leaflet-container');
            if (mapElement && mapElement._leaflet_map) {
                map = mapElement._leaflet_map;
            }

            // 方法2: 查找全局地图对象
            if (!map) {
                for (var key in window) {
                    if (key.startsWith('map_') && window[key] && window[key].zoomIn) {
                        map = window[key];
                        break;
                    }
                }
            }

            if (map && map.zoomIn) {
                map.zoomIn();
                console.log('[缩放] 放大地图成功，当前级别: ' + map.getZoom());
            } else {
                console.log('[缩放] 未找到地图对象');
            }
        })();
        """
        if self.map_view and self.map_view.page():
            self.map_view.page().runJavaScript(js_code)
            self.logger.debug("[缩放] 已执行放大JavaScript代码")
        else:
            self.logger.warning("[缩放] 地图视图或页面不存在")

    def on_zoom_out_clicked(self):
        """缩小按钮点击"""
        self.logger.info("[缩放] 缩小按钮点击")
        # 通过JavaScript调用地图的缩小方法
        js_code = """
        (function() {
            var map = null;

            // 方法1: 通过leaflet-container元素
            var mapElement = document.querySelector('.leaflet-container');
            if (mapElement && mapElement._leaflet_map) {
                map = mapElement._leaflet_map;
            }

            // 方法2: 查找全局地图对象
            if (!map) {
                for (var key in window) {
                    if (key.startsWith('map_') && window[key] && window[key].zoomOut) {
                        map = window[key];
                        break;
                    }
                }
            }

            if (map && map.zoomOut) {
                map.zoomOut();
                console.log('[缩放] 缩小地图成功，当前级别: ' + map.getZoom());
            } else {
                console.log('[缩放] 未找到地图对象');
            }
        })();
        """
        if self.map_view and self.map_view.page():
            self.map_view.page().runJavaScript(js_code)
            self.logger.debug("[缩放] 已执行缩小JavaScript代码")
        else:
            self.logger.warning("[缩放] 地图视图或页面不存在")

    def on_search_button_clicked(self):
        """搜索按钮点击"""
        # 获取搜索框内容
        search_text = self.search_input.text().strip()

        # 如果输入框为空，不执行任何操作
        if not search_text:
            self.logger.debug("[搜索] 搜索框为空，不执行搜索")
            return

        self.logger.info(f"[搜索] 搜索地点: {search_text}")

        # 保存当前搜索文本
        self.current_search_text = search_text

        # 隐藏搜索历史下拉列表
        if hasattr(self, 'search_history_popup'):
            self.search_history_popup.hide()

        # 调用搜索管理器进行搜索
        # 搜索类型设为 "search"，表示通用搜索
        self.search_manager.search_location(search_text, "search")

    def _on_search_input_focus_in(self, event):
        """搜索框获得焦点"""
        # 调用原始的focusInEvent
        QLineEdit.focusInEvent(self.search_input, event)

        # 显示搜索历史
        self._show_search_history()

    def _on_search_input_focus_out(self, event):
        """搜索框失去焦点"""
        # 调用原始的focusOutEvent
        QLineEdit.focusOutEvent(self.search_input, event)

        # 延迟隐藏搜索历史，以允许点击历史项
        QTimer.singleShot(200, self._hide_search_history_if_needed)

    def _on_search_input_text_changed(self, text: str):
        """搜索框文本改变"""
        # 当用户开始输入时，自动关闭历史记录列表
        if text.strip():
            self.logger.debug("[搜索历史] 用户开始输入，关闭历史记录列表")
            if hasattr(self, 'search_history_popup'):
                self.search_history_popup.hide()

    def _show_search_history(self):
        """显示搜索历史下拉列表"""
        if not hasattr(self, 'search_history_popup'):
            return

        # 只有当搜索框为空时才显示历史记录
        if self.search_input.text().strip():
            self.logger.debug("[搜索历史] 搜索框有文字，不显示历史记录")
            self.search_history_popup.hide()
            return

        # 获取搜索历史
        history_list = self.search_manager.get_search_history(10)

        if history_list:
            self.logger.debug(f"[搜索历史] 显示 {len(history_list)} 条历史记录")
            # 使用搜索容器作为参考
            self.search_history_popup.show_history(history_list, self.search_container)

            # 使用QTimer延迟恢复焦点，确保在下拉列表显示后焦点回到搜索框
            QTimer.singleShot(10, lambda: self.search_input.setFocus())
            self.logger.debug("[搜索历史] 已设置延迟焦点恢复")
        else:
            self.logger.debug("[搜索历史] 没有历史记录")
            self.search_history_popup.hide()

    def _hide_search_history_if_needed(self):
        """如果需要，隐藏搜索历史下拉列表"""
        if not hasattr(self, 'search_history_popup'):
            return

        # 检查搜索框是否仍有焦点
        if not self.search_input.hasFocus():
            # 检查下拉列表是否有焦点
            if not self.search_history_popup.hasFocus():
                self.search_history_popup.hide()

    def _on_history_selected(self, record: dict):
        """处理历史记录选择"""
        self.logger.info(f"[搜索历史] 用户选择: {record.get('name')}")

        # 将地址名称回填到搜索框
        name = record.get('name', '')
        if hasattr(self, 'search_input'):
            self.search_input.setText(name)
            self.logger.debug(f"[搜索历史] 已回填地址到搜索框: {name}")

        # 隐藏下拉列表
        if hasattr(self, 'search_history_popup'):
            self.search_history_popup.hide()

        # 调用搜索管理器处理历史记录选择
        self.search_manager.select_history_result(record)

    def _on_result_selected(self, result: dict):
        """处理搜索结果选择"""
        self.logger.info(f"[搜索结果] 用户选择: {result.get('name')}")

        # 隐藏下拉列表
        if hasattr(self, 'search_history_popup'):
            self.search_history_popup.hide()

        # 调用搜索管理器处理搜索结果选择（会保存到历史记录）
        self.search_manager.select_result_from_dropdown(result, self.current_search_text)

    def on_route_button_clicked(self):
        """路线按钮点击"""
        self.logger.info("[路线] 路线按钮点击")

        # 显示路线规划面板
        self._show_route_plan_panel()

    def on_cancel_button_clicked(self):
        """关闭按钮点击"""
        self.logger.info("[搜索] ========== 关闭按钮点击 ==========")

        # 添加详细的调试信息
        self.logger.debug(f"[搜索] 关闭按钮可见性: {self.cancel_button.isVisible()}")
        self.logger.debug(f"[搜索] 关闭按钮启用状态: {self.cancel_button.isEnabled()}")
        self.logger.debug(f"[搜索] 关闭按钮位置: {self.cancel_button.pos()}")
        self.logger.debug(f"[搜索] 关闭按钮大小: {self.cancel_button.size()}")
        self.logger.debug(f"[搜索] 搜索结果下拉列表存在: {hasattr(self, 'search_results_popup')}")

        if hasattr(self, 'search_results_popup'):
            self.logger.debug(f"[搜索] 搜索结果下拉列表可见: {self.search_results_popup.isVisible()}")

        # 隐藏搜索结果下拉列表
        if hasattr(self, 'search_results_popup'):
            self.logger.debug("[搜索] 正在隐藏搜索结果下拉列表...")
            self.search_results_popup.hide()
            self.logger.debug("[搜索] 搜索结果下拉列表已隐藏")

        # 清空搜索框
        self.logger.debug("[搜索] 正在清空搜索框...")
        self.search_input.clear()
        self.logger.debug("[搜索] 搜索框已清空")

        # 切换回路线按钮
        self.logger.debug("[搜索] 正在切换回路线按钮...")
        self._switch_to_route_button()
        self.logger.debug("[搜索] 已切换回路线按钮")

        self.logger.info("[搜索] ========== 关闭按钮处理完成 ==========")

    def _switch_to_cancel_button(self):
        """切换到关闭按钮（显示搜索结果时）"""
        self.logger.debug("[按钮切换] 切换到关闭按钮")
        self.route_button.hide()
        self.cancel_button.show()
        self.cancel_button.raise_()  # 确保按钮在最上层
        self.logger.debug(f"[按钮切换] 关闭按钮可见: {self.cancel_button.isVisible()}")

    def _switch_to_route_button(self):
        """切换回路线按钮（关闭搜索结果时）"""
        self.logger.debug("[按钮切换] 切换回路线按钮")
        self.cancel_button.hide()
        self.route_button.show()
        self.route_button.raise_()  # 确保按钮在最上层
        self.logger.debug(f"[按钮切换] 路线按钮可见: {self.route_button.isVisible()}")

    def _init_hidden_ui_components(self):
        """初始化隐藏的UI组件（用于后台逻辑）"""
        # 创建隐藏的搜索结果列表
        self.search_results_list = QListWidget()
        self.search_results_list.itemClicked.connect(self.on_search_result_clicked)
        self.search_results_list.hide()

        # 创建隐藏的搜索结果标题
        self.search_results_title = QLabel("搜索结果")
        self.search_results_title.hide()

        # 创建隐藏的任务进度面板
        from ui.panels.task_progress_panel import TaskInfoPanel
        self.task_progress_panel = TaskInfoPanel()
        self.task_progress_panel.cancel_task_requested.connect(self._on_cancel_task_requested)
        self.task_progress_panel.hide()

        # 创建隐藏的地图缩放比例尺显示面板
        self.scale_panel = ScalePanel()
        self.scale_panel.hide()

        # 创建隐藏的输入框和列表（用于后台逻辑）
        self.start_input = QLineEdit()
        self.start_input.hide()
        self.start_label = QLineEdit()
        self.start_label.hide()
        self.start_list = QListWidget()
        self.start_list.hide()

        self.end_input = QLineEdit()
        self.end_input.hide()
        self.end_label = QLineEdit()
        self.end_label.hide()
        self.end_list = QListWidget()
        self.end_list.hide()

        self.waypoint_input = QLineEdit()
        self.waypoint_input.hide()
        self.waypoint_list = QListWidget()
        self.waypoint_list.hide()

        # 创建隐藏的交通方式选择框
        self.transport_combo = QComboBox()
        self.transport_combo.addItems(["驾车", "步行", "骑行", "公交"])
        self.transport_combo.hide()

        # 创建隐藏的时间编辑器
        from PyQt5.QtCore import QDateTime
        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setDateTime(QDateTime.currentDateTime())
        self.start_time_edit.hide()

        self.end_time_edit = QTimeEdit()
        self.end_time_edit.setDateTime(QDateTime.currentDateTime())
        self.end_time_edit.hide()

        self.duration_time_edit = QLineEdit()
        self.duration_time_edit.hide()

        # 创建隐藏的按钮
        self.plan_button = QPushButton("规划路线")
        self.plan_button.clicked.connect(self.on_plan_route_clicked)
        self.plan_button.hide()

        self.export_button = QPushButton("导出GPX")
        self.export_button.clicked.connect(self.on_export_gpx_clicked)
        self.export_button.hide()

        # 创建隐藏的日期和时间面板（如果需要）
        # 这些面板可能在后台逻辑中使用
        # 暂时不创建，如果需要可以后续添加

    # ==================== 原有面板创建方法（保留用于参考，暂时不使用）====================
    # 以下方法保留用于将来重新设计界面时参考，目前不被调用

    def _create_left_panel_original(self):
        """创建左侧控制面板"""
        left_widget = QWidget()
        left_widget.setMinimumWidth(LayoutManager.PANEL_SIZES[0])
        left_layout = QVBoxLayout(left_widget)

        # 顶部按钮 - 只保留地图配置按钮，并让它占满宽度
        config_button = QPushButton("⚙️ 地图配置")
        config_button.clicked.connect(self.show_map_config)
        config_button.setStyleSheet(UIStyles.LOCATE_BUTTON)
        left_layout.addWidget(config_button)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # 创建各个组
        start_group = PanelFactory.create_location_group("起点", "start", self)
        scroll_layout.addWidget(start_group)

        waypoint_group = PanelFactory.create_waypoint_group(self)
        scroll_layout.addWidget(waypoint_group)

        end_group = PanelFactory.create_location_group("终点", "end", self)
        scroll_layout.addWidget(end_group)

        transport_group = PanelFactory.create_transport_group(self)
        scroll_layout.addWidget(transport_group)

        time_group = PanelFactory.create_time_group(self)
        scroll_layout.addWidget(time_group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        left_layout.addWidget(scroll)

        # 底部按钮
        button_layout = QHBoxLayout()
        self.plan_button = QPushButton("规划路线")
        self.plan_button.clicked.connect(self.on_plan_route_clicked)
        self.plan_button.setStyleSheet(UIStyles.PLAN_BUTTON)

        self.export_button = QPushButton("导出GPX")
        self.export_button.clicked.connect(self.on_export_gpx_clicked)
        self.export_button.setStyleSheet(UIStyles.EXPORT_BUTTON)

        button_layout.addWidget(self.plan_button)
        button_layout.addWidget(self.export_button)
        left_layout.addLayout(button_layout)

        return left_widget

    def _create_middle_panel_original(self):
        """创建中间搜索结果面板"""
        middle_widget = QWidget()
        middle_widget.setMinimumWidth(LayoutManager.PANEL_SIZES[1])
        layout = QVBoxLayout(middle_widget)
        layout.setSpacing(10)  # 设置组件间距
        layout.setContentsMargins(5, 5, 5, 5)  # 设置边距

        # 标题
        self.search_results_title = QLabel("搜索结果")
        self.search_results_title.setStyleSheet(UIStyles.TITLE_LABEL)
        layout.addWidget(self.search_results_title)

        # 搜索结果列表 - 设置更大的高度
        self.search_results_list = QListWidget()
        self.search_results_list.itemClicked.connect(self.on_search_result_clicked)
        self.search_results_list.setMinimumHeight(300)  # 增加最小高度
        # 设置列表项支持多行显示
        self.search_results_list.setWordWrap(True)
        self.search_results_list.setSpacing(2)
        # 设置合适的最小项高度以显示多行文本
        self.search_results_list.setStyleSheet("""
            QListWidget::item {
                padding: 5px;
                min-height: 60px;
                color: #333333;
            }
            QListWidget::item:selected {
                background-color: #4A90E2;
                color: white;
                border: none;
            }
            QListWidget::item:hover {
                background-color: #E8F4FD;
                color: #333333;
            }
            QListWidget {
                outline: none;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                background-color: white;
            }
        """)
        layout.addWidget(self.search_results_list, 1)  # 设置伸展因子，占据更多空间

        # 任务进度面板
        from ui.panels.task_progress_panel import TaskInfoPanel
        self.task_progress_panel = TaskInfoPanel()
        self.task_progress_panel.cancel_task_requested.connect(self._on_cancel_task_requested)
        layout.addWidget(self.task_progress_panel)

        # 地图缩放比例尺显示面板
        self.scale_panel = ScalePanel()
        layout.addWidget(self.scale_panel)

        return middle_widget

    def _create_right_panel_original(self):
        """创建右侧地图面板"""
        right_widget = QWidget()
        right_widget.setMinimumWidth(LayoutManager.PANEL_SIZES[2])
        layout = QVBoxLayout(right_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 创建地图视图
        self.map_view = QWebEngineView()
        self.web_page = ConsoleWebEnginePage(signal_manager=self.signal_manager)
        self.web_page.set_geolocation_handler(self.geolocation_handler)
        self.map_view.setPage(self.web_page)

        # 设置User Agent
        profile = QWebEngineProfile.defaultProfile()
        profile.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        # 创建一个容器来放置地图和浮动按钮
        map_container = QWidget()
        map_container_layout = QVBoxLayout(map_container)
        map_container_layout.setContentsMargins(0, 0, 0, 0)
        map_container_layout.setSpacing(0)
        map_container_layout.addWidget(self.map_view)

        # 创建定位按钮（浮动在地图上）
        self.locate_button = QPushButton()
        self.locate_button.setToolTip("定位到当前位置")
        self.locate_button.clicked.connect(self.on_locate_clicked)

        # 加载图标
        import os
        # __file__ 是 src/app/app.py，需要向上三级到达项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        icon_path = os.path.join(project_root, 'res', 'Location.png')

        if os.path.exists(icon_path):
            from PyQt5.QtGui import QIcon
            self.locate_button.setIcon(QIcon(icon_path))
            from PyQt5.QtCore import QSize
            self.locate_button.setIconSize(QSize(18, 18))
        else:
            self.locate_button.setText("📍")

        # 设置按钮样式，与 leaflet 的缩放按钮保持一致
        self.locate_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 2px solid rgba(0, 0, 0, 0.2);
                border-radius: 2px;
                padding: 0px;
                min-width: 30px;
                min-height: 30px;
                max-width: 30px;
                max-height: 30px;
            }
            QPushButton:hover {
                background-color: #f4f4f4;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
            }
        """)

        self.locate_button.setParent(map_container)
        # 放置在左上角，放大缩小按钮下方
        # leaflet 的缩放控件默认位置是 top-left，距离顶部10px，左侧10px
        # 每个按钮高度约30px，加上1px边框，所以第三个按钮应该在 10 + 30 + 30 = 70px 处
        self.locate_button.move(10, 70)
        self.locate_button.raise_()

        layout.addWidget(map_container)

        return right_widget

    # ==================== UI更新回调方法 ====================

    def _show_warning(self, title: str, message: str):
        """显示警告对话框"""
        QMessageBox.warning(self, title, message)

    def _show_info(self, title: str, message: str):
        """显示信息对话框"""
        QMessageBox.information(self, title, message)

    def _set_progress_indeterminate(self):
        """设置进度条为不确定模式"""
        # 使用任务进度面板的进度条
        self.task_progress_panel.progress_widget.progress_bar.setRange(0, 0)
        QApplication.processEvents()

    def _set_progress_complete(self):
        """设置进度条为完成状态"""
        # 使用任务进度面板的进度条
        self.task_progress_panel.progress_widget.progress_bar.setRange(0, 100)
        self.task_progress_panel.progress_widget.progress_bar.setValue(100)
        QApplication.processEvents()

    def _set_progress(self, value: int):
        """设置进度条值"""
        # 使用任务进度面板的进度条
        self.task_progress_panel.progress_widget.progress_bar.setRange(0, 100)
        self.task_progress_panel.progress_widget.progress_bar.setValue(value)
        QApplication.processEvents()

    def _clear_results(self):
        """清空搜索结果"""
        self.search_results_list.clear()
        QApplication.processEvents()

    def _clear_results_list(self):
        """清空搜索结果列表"""
        self.search_results_list.clear()

    def _add_result(self, text: str):
        """添加结果项"""
        self.search_results_list.addItem(text)

    def _set_results_title(self, title: str):
        """设置结果标题"""
        self.search_results_title.setText(title)

    def _show_search_results(self, locations: list):
        """显示搜索结果"""
        for i, location in enumerate(locations):
            if isinstance(location, dict):
                name = location.get('name', '')
                address = location.get('address', '')
                lat = location.get('lat', 0)
                lon = location.get('lon', 0)
                level = location.get('level', None)
                type_info = location.get('type', None)
                radius = location.get('radius', None)  # 提取POI半径

                # 构建详细的显示文本
                display_parts = []
                display_parts.append(f"{i+1}. {name}")

                # 如果有地址信息且与名称不同，添加地址
                if address and address != name:
                    display_parts.append(f"   地址: {address}")

                # 如果有类型信息，添加类型
                if type_info:
                    display_parts.append(f"   类型: {type_info}")

                # 添加坐标信息（可选，让用户知道精确位置）
                display_parts.append(f"   坐标: {lat:.6f}, {lon:.6f}")

                item_text = "\n".join(display_parts)

                # 用于选择的完整名称（包含地址）
                full_name = f"{name}"
                if address and address != name:
                    full_name = f"{name} ({address})"

            else:
                # OSM数据结构
                name = location.address
                lat = location.latitude
                lon = location.longitude
                level = None
                type_info = location.type if hasattr(location, 'type') else None
                radius = None  # OSM暂不支持半径

                display_parts = []
                display_parts.append(f"{i+1}. {name}")

                if type_info:
                    display_parts.append(f"   类型: {type_info}")

                display_parts.append(f"   坐标: {lat:.6f}, {lon:.6f}")

                item_text = "\n".join(display_parts)
                full_name = name

            item = QListWidgetItem(item_text)
            # 保存完整名称用于后续选择，包含radius信息
            item.setData(Qt.UserRole, (full_name, lat, lon, level, type_info, radius))
            self.search_results_list.addItem(item)

    def _show_search_results_on_map(self, locations: list, location_type: str):
        """在地图上显示搜索结果"""
        self.map_manager.show_search_results_on_map(locations, location_type)

    def _show_search_results_dropdown(self, results: list):
        """
        显示搜索结果下拉列表

        参数:
            results: 格式化后的搜索结果列表
        """
        self.logger.debug(f"[搜索结果] 显示 {len(results)} 条搜索结果")

        if hasattr(self, 'search_results_popup') and results:
            # 使用搜索容器（包含输入框和两个按钮）作为参考
            self.search_results_popup.show_results(results, self.search_container)

            # 切换到关闭按钮
            self._switch_to_cancel_button()

            # 确保关闭按钮在最上层，不被下拉列表遮挡
            QTimer.singleShot(50, lambda: self.cancel_button.raise_())
            self.logger.debug("[搜索结果] 已提升关闭按钮层级")

    def _update_location_display(self, location_type: str, name: str, data: tuple):
        """更新位置显示"""
        if location_type == "start":
            if hasattr(self, 'start_label'):
                self.start_label.setText(name)
                self.start_label.setCursorPosition(0)  # 将光标移到开头
                self.start_label.setProperty('userData', data)
        elif location_type == "end":
            if hasattr(self, 'end_label'):
                self.end_label.setText(name)
                self.end_label.setCursorPosition(0)  # 将光标移到开头
                self.end_label.setProperty('userData', data)

    def _update_start_from_search(self, name: str, data: tuple):
        """从搜索结果更新起点"""
        if hasattr(self, 'start_label'):
            self.start_label.setText(name)
            self.start_label.setCursorPosition(0)  # 将光标移到开头
            self.start_label.setProperty('userData', data)
        if hasattr(self, 'start_list'):
            self.start_list.clear()
            self.start_list.addItem(name)
            self.start_list.item(0).setData(Qt.UserRole, data)

    def _update_end_from_search(self, name: str, data: tuple):
        """从搜索结果更新终点"""
        if hasattr(self, 'end_label'):
            self.end_label.setText(name)
            self.end_label.setCursorPosition(0)  # 将光标移到开头
            self.end_label.setProperty('userData', data)
        if hasattr(self, 'end_list'):
            self.end_list.clear()
            self.end_list.addItem(name)
            self.end_list.item(0).setData(Qt.UserRole, data)

    def _add_waypoint_to_list(self, name: str, data: tuple, level: Optional[str]):
        """添加途径点到列表"""
        waypoint_item = QListWidgetItem(
            f"{len(self.data_manager.waypoints_coords)}. {name}"
        )
        level_data = level if level else None
        waypoint_item.setData(Qt.UserRole, (name, data[1], data[2], level_data, None))
        self.waypoint_list.addItem(waypoint_item)

    def _update_map_preview(self):
        """更新地图预览"""
        self.map_manager.update_map_preview()

    def _preview_search_result(self, coords, name, level=None, type_info=None, radius=None):
        """预览搜索结果"""
        self.map_manager.preview_search_result(coords, name, level, type_info, radius)

    def _show_location_on_map(self, lat: float, lon: float, popup_text: str):
        """在地图上显示位置"""
        self.logger.debug(f"[UI回调] 收到显示位置请求: {lat}, {lon}")
        self.map_manager.show_location_on_map(lat, lon, popup_text)
        self.logger.debug("[UI回调] 地图管理器显示位置完成")

    def _show_route_on_map(self):
        """在地图上显示路线"""
        self.map_manager.show_route_on_map()

    def _load_map_url(self, url: str):
        """直接加载地图URL（用于后台渲染完成后）

        参数:
            url: 地图HTML的URL
        """
        from PyQt5.QtCore import QUrl
        self.logger.debug(f"加载地图URL: {url}")
        self.map_view.setUrl(QUrl(url))

    def _trigger_browser_location(self):
        """触发浏览器定位"""
        geolocation_script = """
        if (navigator.geolocation) {
            console.log('[定位] 正在调用浏览器定位API...');
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    var result = {
                        lat: position.coords.latitude,
                        lon: position.coords.longitude,
                        accuracy: position.coords.accuracy
                    };
                    console.log('[定位] 浏览器定位成功: ' + result.lat + ', ' + result.lon + ', 精度: ' + result.accuracy + 'm');
                    console.log('定位成功:' + result.lat + ',' + result.lon + ',' + result.accuracy);
                },
                function(error) {
                    var errorMsg = '';
                    switch(error.code) {
                        case error.PERMISSION_DENIED:
                            errorMsg = '用户拒绝定位请求';
                            break;
                        case error.POSITION_UNAVAILABLE:
                            errorMsg = '位置信息不可用';
                            break;
                        case error.TIMEOUT:
                            errorMsg = '定位请求超时';
                            break;
                        default:
                            errorMsg = '未知错误: ' + error.message;
                    }
                    console.log('[定位] 浏览器定位失败: ' + errorMsg);
                    console.log('定位失败:' + errorMsg);
                },
                {
                    enableHighAccuracy: true,
                    timeout: 15000,
                    maximumAge: 0
                }
            );
        } else {
            console.log('[定位] 浏览器不支持Geolocation API');
            console.log('定位失败: 浏览器不支持定位');
        }
        """
        if self.map_view and self.map_view.page():
            self.map_view.page().runJavaScript(geolocation_script)

    def _setup_date_panel_callback(self, callback):
        """设置日期面板回调"""
        try:
            self.date_panel.date_selected.disconnect()
        except TypeError:
            pass
        self.date_panel.date_selected.connect(callback)

    def _setup_time_panel_callback(self, callback):
        """设置时间面板回调"""
        try:
            self.time_panel.time_selected.disconnect()
        except TypeError:
            pass
        self.time_panel.time_selected.connect(callback)

    def _show_date_panel(self, current_date):
        """显示日期面板"""
        panel_rect = self.middle_panel.rect()
        panel_pos = self.middle_panel.mapToGlobal(panel_rect.topLeft())
        panel_size = self.middle_panel.size()
        self.date_panel.show_panel(current_date, panel_pos, 0, panel_size)

    def _show_time_panel(self, current_time):
        """显示时间面板"""
        panel_rect = self.middle_panel.rect()
        panel_pos = self.middle_panel.mapToGlobal(panel_rect.topLeft())
        panel_size = self.middle_panel.size()
        self.time_panel.show_panel(current_time, panel_pos, 0, panel_size)

    def _add_route_time_info(self):
        """添加路线时间信息到结果列表"""
        # 起始时间
        start_datetime = self.start_time_edit.dateTime()
        start_time_str = start_datetime.toString("yyyy-MM-dd HH:mm")
        self.search_results_list.addItem(f"起始时间: {start_time_str}")

        # 途径时间
        duration_hours = self.data_manager.estimated_duration_seconds // 3600
        duration_minutes = (self.data_manager.estimated_duration_seconds % 3600) // 60
        self.search_results_list.addItem(f"途径时间: {int(duration_hours)}小时{duration_minutes}分钟")

        # 结束时间
        end_datetime = self.end_time_edit.dateTime()
        end_time_str = end_datetime.toString("yyyy-MM-dd HH:mm")
        self.search_results_list.addItem(f"结束时间: {end_time_str}")

    def _show_initial_map(self):
        """显示初始地图"""
        self.map_manager.show_initial_map()
        self.scale_panel.update_zoom(10)

    # ==================== 事件处理方法 ====================

    def on_locate_clicked(self):
        """定位按钮点击"""
        self.location_manager.get_current_location()

    def on_map_settings_clicked(self):
        """地图设置按钮点击"""
        self.logger.info("[设置] 打开地图设置面板")

        # 隐藏其他popup
        if hasattr(self, 'log_settings_popup'):
            self.log_settings_popup.hide()
        if hasattr(self, 'about_popup'):
            self.about_popup.hide()

        # 显示地图设置popup
        if hasattr(self, 'map_settings_popup'):
            self.map_settings_popup.show_popup(self.map_settings_button)

    def on_log_settings_clicked(self):
        """日志设置按钮点击"""
        self.logger.info("[设置] 打开日志设置面板")

        # 隐藏其他popup
        if hasattr(self, 'map_settings_popup'):
            self.map_settings_popup.hide()
        if hasattr(self, 'about_popup'):
            self.about_popup.hide()

        # 显示日志设置popup
        if hasattr(self, 'log_settings_popup'):
            self.log_settings_popup.show_popup(self.log_settings_button)

    def on_about_clicked(self):
        """关于按钮点击"""
        self.logger.info("[设置] 打开关于面板")

        # 隐藏其他popup
        if hasattr(self, 'map_settings_popup'):
            self.map_settings_popup.hide()
        if hasattr(self, 'log_settings_popup'):
            self.log_settings_popup.hide()

        # 显示关于popup
        if hasattr(self, 'about_popup'):
            self.about_popup.show_popup(self.about_button)

    def _on_map_config_saved(self):
        """地图配置保存后的处理"""
        self.logger.info("[设置] 地图配置已保存，重新加载地图")

        # 重新加载配置
        from services.config.map_config import map_config
        map_config._load_config()

        # 重新初始化服务（使用新的API Key）
        self.service_manager.initialize_services()

        # 重新加载地图
        self._show_initial_map()

    def on_plan_route_clicked(self):
        """规划路线按钮点击"""
        transport_mode = self.transport_combo.currentText()
        self.route_manager.plan_route(transport_mode)

    def on_export_gpx_clicked(self):
        """导出GPX按钮点击"""
        self.route_manager.export_gpx()

    def on_search_result_clicked(self, item):
        """搜索结果点击"""
        data = item.data(Qt.UserRole)
        self.search_manager.select_search_result(data)

    def on_clear_search_clicked(self):
        """清空搜索结果按钮点击"""
        self.search_manager.clear_search_results()

    def on_map_zoom_changed(self, zoom_level: int):
        """处理地图缩放变化事件"""
        self.logger.info(f"地图缩放级别变化: {zoom_level}")

        # 更新隐藏的比例尺面板（用于后台逻辑）
        self.scale_panel.update_zoom(zoom_level)

        # 更新显示的比例尺信息标签
        if hasattr(self, 'scale_info_label'):
            # 根据缩放级别计算比例尺
            scale_text = self._get_scale_text(zoom_level)
            self.scale_info_label.setText(f"缩放级别: {zoom_level}  {scale_text}")
            self.scale_info_label.adjustSize()  # 调整标签大小以适应文本

    def _get_scale_text(self, zoom_level: int) -> str:
        """根据缩放级别获取比例尺文本

        Args:
            zoom_level: 地图缩放级别 (1-20)

        Returns:
            str: 比例尺文本，如 "比例尺: 1:50000"
        """
        # 高德地图缩放级别对应的比例尺（近似值）
        # zoom 3:  1:40000000 (全球)
        # zoom 10: 1:300000 (城市)
        # zoom 15: 1:10000 (街道)
        # zoom 18: 1:1250 (建筑)

        scale_map = {
            3: "1:40000000",
            4: "1:20000000",
            5: "1:10000000",
            6: "1:5000000",
            7: "1:2500000",
            8: "1:1250000",
            9: "1:625000",
            10: "1:300000",
            11: "1:150000",
            12: "1:75000",
            13: "1:40000",
            14: "1:20000",
            15: "1:10000",
            16: "1:5000",
            17: "1:2500",
            18: "1:1250",
            19: "1:625",
            20: "1:300"
        }

        scale = scale_map.get(zoom_level, "1:100000")
        return f"比例尺: {scale}"

    def _on_geolocation_success(self, lat: float, lon: float, accuracy: float):
        """处理浏览器定位成功信号"""
        self.logger.info(f"[主应用] 收到浏览器定位成功信号: {lat}, {lon}, 精度: {accuracy}m")
        self.logger.debug(f"[主应用] location_manager存在: {hasattr(self, 'location_manager')}")
        if hasattr(self, 'location_manager'):
            self.logger.debug("[主应用] 调用location_manager.handle_browser_location_success...")
            self.location_manager.handle_browser_location_success(lat, lon, accuracy)
            self.logger.debug("[主应用] location_manager.handle_browser_location_success 调用完成")
        else:
            self.logger.error("[主应用] location_manager未初始化！")

    def _on_geolocation_error(self, error_msg: str):
        """处理浏览器定位失败信号"""
        self.logger.warning(f"浏览器定位失败: {error_msg}")
        self.location_manager.handle_browser_location_error(error_msg)

    def _on_map_right_click(self, lat: float, lon: float):
        """处理地图右键点击事件"""
        self.logger.info(f"[地图右键] 收到右键点击信号: {lat}, {lon}")

        # 使用地理编码服务获取位置信息
        self.logger.debug("[地图右键] 开始反向地理编码...")

        # 创建后台任务获取位置信息
        def get_location_info(progress_callback, log_callback, cancel_check):
            """后台任务：获取位置信息"""
            try:
                log_callback("INFO", "开始获取位置信息")

                from services.config.map_config import map_config
                map_source = map_config.get_map_source()

                # 获取对应的地理编码服务
                geocoding_service = self.service_manager.get_geocoding_service(map_source)

                if map_source == "gaode":
                    # 使用高德地理编码服务
                    log_callback("DEBUG", "使用高德地图反向地理编码")
                    result = geocoding_service.reverse_geocode(lat, lon)
                    if result:
                        # 高德地图返回格式：{'city': '...', 'full_address': '...', 'level': '...', 'type': '...'}
                        name = result.get('full_address', '未知位置')
                        type_info = result.get('type', '')
                        level = result.get('level', None)

                        log_callback("INFO", f"获取位置信息成功: {name}, level: {level}, type: {type_info}")
                        return {
                            'success': True,
                            'name': name,
                            'lat': lat,
                            'lon': lon,
                            'type': type_info,
                            'level': level
                        }
                else:
                    # 使用OSM地理编码服务
                    log_callback("DEBUG", "使用OSM反向地理编码")
                    result = geocoding_service.reverse_geocode(lat, lon)
                    if result:
                        # OSM返回格式：{'name': '...', 'address': '...', 'type': '...'}
                        name = result.get('name', '未知位置')
                        type_info = result.get('type', '')

                        log_callback("INFO", f"获取位置信息成功: {name}")
                        return {
                            'success': True,
                            'name': name,
                            'lat': lat,
                            'lon': lon,
                            'type': type_info,
                            'level': None
                        }

                # 如果获取失败，返回基本信息
                log_callback("WARNING", "获取位置信息失败，使用坐标格式")
                return {
                    'success': False,
                    'name': f'位置 ({lat:.6f}, {lon:.6f})',
                    'lat': lat,
                    'lon': lon,
                    'type': '',
                    'level': None
                }

            except Exception as e:
                log_callback("ERROR", f"获取位置信息失败: {e}")
                return {
                    'success': False,
                    'name': f'位置 ({lat:.6f}, {lon:.6f})',
                    'lat': lat,
                    'lon': lon,
                    'type': '',
                    'level': None
                }

        # 提交后台任务
        task_id = self.task_manager.submit_task(
            task_type='context_menu',
            task_func=get_location_info
        )

        # 保存任务ID，用于在任务完成时识别
        self._context_menu_task_id = task_id

    def _show_context_menu(self, location_info: dict):
        """显示右键菜单"""
        self.logger.debug(f"[地图右键] 显示右键菜单: {location_info}")

        # 保存位置信息，供右键菜单处理方法使用
        self._context_menu_location_info = location_info

        # 获取鼠标当前位置
        from PyQt5.QtGui import QCursor
        cursor_pos = QCursor.pos()

        # 显示菜单
        self.map_context_menu.show_menu(
            cursor_pos,
            location_info['name'],
            location_info['lat'],
            location_info['lon'],
            location_info.get('type', '')
        )

    def _on_context_menu_set_start(self, name: str, lat: float, lon: float):
        """右键菜单：设为起点"""
        self.logger.info(f"[右键菜单] 设为起点: {name} ({lat}, {lon})")

        # 获取位置信息（包括level和type）
        location_info = getattr(self, '_context_menu_location_info', {})
        level = location_info.get('level', None)
        type_info = location_info.get('type', None)

        # 使用DataManager的方法保存起点信息（包括名称）
        self.data_manager.set_start_location((lat, lon), name)

        # 更新UI显示
        data = (name, lat, lon, None, None, None)
        self._update_start_from_search(name, data)

        # 检查是否有搜索结果需要清除
        has_search_results = len(self.data_manager.search_results) > 0

        # 清除搜索结果（数据和UI）
        self.search_manager.clear_search_results()

        # 智能更新地图：
        all_coords = self.map_manager._get_all_selected_coords()
        if len(all_coords) >= 2:
            # 多点：自动适应所有点
            self.map_manager.update_map_preview(auto_fit=True)
        else:
            # 单点：根据地址级别智能缩放
            zoom_level = MapRenderer.get_zoom_by_level(level, type_info)
            self.logger.info(f"[右键菜单] 单点缩放: level={level}, type={type_info}, zoom={zoom_level}")
            self.map_manager.update_map_preview_simple((lat, lon), zoom_level=zoom_level)

    def _on_context_menu_add_waypoint(self, name: str, lat: float, lon: float):
        """右键菜单：添加途径点"""
        self.logger.info(f"[右键菜单] 添加途径点: {name} ({lat}, {lon})")

        # 获取位置信息（包括level和type）
        location_info = getattr(self, '_context_menu_location_info', {})
        level = location_info.get('level', None)
        type_info = location_info.get('type', None)

        # 使用DataManager的方法添加途径点（包括名称）
        self.data_manager.add_waypoint((lat, lon), name)

        # 更新UI显示
        data = (name, lat, lon, None, None, None)
        self._add_waypoint_to_list(name, data, None)

        # 检查是否有搜索结果需要清除
        has_search_results = len(self.data_manager.search_results) > 0

        # 清除搜索结果（数据和UI）
        self.search_manager.clear_search_results()

        # 智能更新地图：
        all_coords = self.map_manager._get_all_selected_coords()
        if len(all_coords) >= 2:
            # 多点：自动适应所有点
            self.map_manager.update_map_preview(auto_fit=True)
        else:
            # 单点：根据地址级别智能缩放
            zoom_level = MapRenderer.get_zoom_by_level(level, type_info)
            self.logger.info(f"[右键菜单] 单点缩放: level={level}, type={type_info}, zoom={zoom_level}")
            self.map_manager.update_map_preview_simple((lat, lon), zoom_level=zoom_level)

    def _on_context_menu_set_end(self, name: str, lat: float, lon: float):
        """右键菜单：设为终点"""
        self.logger.info(f"[右键菜单] 设为终点: {name} ({lat}, {lon})")

        # 获取位置信息（包括level和type）
        location_info = getattr(self, '_context_menu_location_info', {})
        level = location_info.get('level', None)
        type_info = location_info.get('type', None)

        # 使用DataManager的方法保存终点信息（包括名称）
        self.data_manager.set_end_location((lat, lon), name)

        # 更新UI显示
        data = (name, lat, lon, None, None, None)
        self._update_end_from_search(name, data)

        # 检查是否有搜索结果需要清除
        has_search_results = len(self.data_manager.search_results) > 0

        # 清除搜索结果（数据和UI）
        self.search_manager.clear_search_results()

        # 智能更新地图：
        all_coords = self.map_manager._get_all_selected_coords()
        if len(all_coords) >= 2:
            # 多点：自动适应所有点
            self.map_manager.update_map_preview(auto_fit=True)
        else:
            # 单点：根据地址级别智能缩放
            zoom_level = MapRenderer.get_zoom_by_level(level, type_info)
            self.logger.info(f"[右键菜单] 单点缩放: level={level}, type={type_info}, zoom={zoom_level}")
            self.map_manager.update_map_preview_simple((lat, lon), zoom_level=zoom_level)

    # ==================== 公共方法（由PanelFactory调用）====================

    def search_location(self, location_type: str):
        """搜索地点（起点/终点）"""
        search_text = getattr(self, f"{location_type}_input").text()
        if search_text:
            self.search_manager.search_location(search_text, location_type)

    def search_waypoint(self):
        """搜索途径点"""
        search_text = self.waypoint_input.text()
        if search_text:
            self.search_manager.search_location(search_text, "waypoint")

    def select_location(self, item, location_type: str):
        """选择地点（从下拉框）"""
        data = item.data(Qt.UserRole)
        self.search_manager.select_location_from_list(data, location_type)

    def remove_waypoint(self):
        """删除途径点"""
        current_row = self.waypoint_list.currentRow()
        if current_row >= 0:
            self.waypoint_list.takeItem(current_row)
            self.data_manager.remove_waypoint(current_row)

            # 重新编号
            for i in range(self.waypoint_list.count()):
                item = self.waypoint_list.item(i)
                data = item.data(Qt.UserRole)
                item.setText(f"{i+1}. {data[0]}")

            self.map_manager.update_map_preview()

    def clear_all_waypoints(self):
        """清空所有途径点"""
        self.waypoint_list.clear()
        self.data_manager.clear_waypoints()
        self.map_manager.update_map_preview()

    def show_date_panel(self, time_type: str):
        """显示日期选择面板"""
        self.time_manager.show_date_panel(time_type)

    def show_time_panel(self, time_type: str):
        """显示时间选择面板"""
        self.time_manager.show_time_panel(time_type)

    def calculate_times(self):
        """计算时间"""
        self.time_manager.calculate_times()

    def show_map_config(self):
        """显示地图配置对话框"""
        dialog = MapConfigDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            map_source = map_config.get_map_source()
            self.logger.info(f"地图数据源已更新: {map_source}")

            # 更新服务配置
            if map_source == "gaode":
                api_key = map_config.get_api_key()
                security_key = map_config.get_security_key()
                self.service_manager.update_gaode_config(api_key, security_key)
                self.logger.info("高德地图API配置已更新")

            # 清空路线数据并重新加载地图
            self.clear_route_data()
            self._show_initial_map()

    def clear_route_data(self):
        """清空所有路线相关数据"""
        self.data_manager.clear_all_route_data()

        # 清空UI显示
        if hasattr(self, 'start_label'):
            self.start_label.setText('')
        if hasattr(self, 'end_label'):
            self.end_label.setText('')
        if hasattr(self, 'start_list'):
            self.start_list.clear()
        if hasattr(self, 'end_list'):
            self.end_list.clear()
        if hasattr(self, 'waypoint_list'):
            self.waypoint_list.clear()
        if hasattr(self, 'search_results_list'):
            self.search_results_list.clear()
        if hasattr(self, 'search_results_title'):
            self.search_results_title.setText("搜索结果")

        self.logger.info("已清空所有路线相关数据")

    def show_about_dialog(self):
        """显示关于对话框"""
        dialog = AboutDialog(self)
        dialog.exec_()

    def closeEvent(self, event):
        """重写关闭事件"""
        self.window_manager.handle_close_event(event)

    # ==================== 任务管理器事件处理方法 ====================

    def _on_task_started(self, task_id: str, task_type: str):
        """任务开始事件"""
        self.logger.info(f"[任务] 开始: {task_id} ({task_type})")

        # 任务类型到显示名称的映射
        task_name_map = {
            'location': '定位',
            'search': '搜索',
            'routing': '路线规划',
            'map_render': '地图渲染'
        }
        task_name = task_name_map.get(task_type, task_type)

        # 在任务进度面板显示任务开始
        self.task_progress_panel.start_task(task_id, task_type, task_name)

    def _on_task_progress(self, task_id: str, percent: int, message: str):
        """任务进度更新事件"""
        # 更新任务进度面板
        self.task_progress_panel.update_progress(percent, message)

    def _on_task_completed(self, task_id: str, result):
        """任务完成事件"""
        self.logger.info(f"[任务] 完成: {task_id}")

        # 根据任务ID判断任务类型并处理结果
        if task_id.startswith('location_'):
            self.location_manager.on_location_task_completed(task_id, result)
            self.task_progress_panel.task_completed("定位完成")
        elif task_id.startswith('search_'):
            self.search_manager.on_search_task_completed(task_id, result)
            self.task_progress_panel.task_completed("搜索完成")
        elif task_id.startswith('routing_'):
            self.route_manager.on_route_task_completed(task_id, result)
            self.task_progress_panel.task_completed("路线规划完成")
        elif task_id.startswith('map_render_'):
            self.route_manager.on_map_render_task_completed(task_id, result)
            self.task_progress_panel.task_completed("地图渲染完成")
            # 地图渲染完成后隐藏加载状态
            if hasattr(self, 'route_plan_panel') and self.route_plan_panel.isVisible():
                self.route_plan_panel.hide_loading()
        elif task_id.startswith('context_menu_'):
            # 处理右键菜单任务完成
            self._show_context_menu(result)
            self.task_progress_panel.task_completed("位置信息获取完成")
        else:
            self.task_progress_panel.task_completed("任务完成")

        # 延迟重置任务进度面板
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(3000, self.task_progress_panel.reset)

    def _on_task_failed(self, task_id: str, error: str):
        """任务失败事件"""
        self.logger.error(f"[任务] 失败: {task_id} - {error}")

        # 根据任务ID判断任务类型并处理错误
        if task_id.startswith('location_'):
            self.location_manager.on_location_task_failed(task_id, error)
        elif task_id.startswith('search_'):
            self.search_manager.on_search_task_failed(task_id, error)
        elif task_id.startswith('routing_'):
            self.route_manager.on_route_task_failed(task_id, error)
            # 路线规划失败时隐藏加载状态并显示错误提示
            if hasattr(self, 'route_plan_panel') and self.route_plan_panel.isVisible():
                self.route_plan_panel.hide_loading()
                self.route_plan_panel.show_route_plan_error("路线规划失败，请重试")
        elif task_id.startswith('map_render_'):
            self.route_manager.on_map_render_task_failed(task_id, error)
            # 地图渲染失败时隐藏加载状态并显示错误提示
            if hasattr(self, 'route_plan_panel') and self.route_plan_panel.isVisible():
                self.route_plan_panel.hide_loading()
                self.route_plan_panel.show_route_plan_error("地图渲染失败，请重试")
        elif task_id.startswith('context_menu_'):
            # 处理右键菜单任务失败
            self.logger.error(f"[地图右键] 任务失败: {error}")

        # 在任务进度面板显示失败
        self.task_progress_panel.task_failed(error)

        # 延迟重置任务进度面板
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(5000, self.task_progress_panel.reset)

    def _on_task_cancelled(self, task_id: str):
        """任务取消事件"""
        self.logger.warning(f"[任务] 已取消: {task_id}")

        # 在任务进度面板显示取消
        self.task_progress_panel.task_cancelled()

        # 延迟重置任务进度面板
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(2000, self.task_progress_panel.reset)

    def _on_task_log(self, task_id: str, level: str, message: str):
        """任务日志事件"""
        # 转发到任务进度面板
        self.task_progress_panel.add_log(level, message)

        # 同时记录到主日志
        level_map = {
            "DEBUG": self.logger.debug,
            "INFO": self.logger.info,
            "WARNING": self.logger.warning,
            "ERROR": self.logger.error,
            "CRITICAL": self.logger.critical
        }
        log_func = level_map.get(level, self.logger.info)
        log_func(f"[任务 {task_id}] {message}")

    def _on_cancel_task_requested(self, task_id: str):
        """请求取消任务"""
        self.logger.info(f"[任务] 用户请求取消: {task_id}")
        self.task_manager.cancel_task(task_id)

    # ==================== 路线规划面板相关方法 ====================

    def _show_route_plan_panel(self):
        """显示路线规划面板"""
        self.logger.info("[路线面板] 显示路线规划面板")

        # 隐藏搜索相关的下拉列表
        if hasattr(self, 'search_history_popup'):
            self.search_history_popup.hide()
        if hasattr(self, 'search_results_popup'):
            self.search_results_popup.hide()

        # 设置面板位置和大小（覆盖搜索容器）
        if hasattr(self, 'search_container') and hasattr(self, 'route_plan_panel'):
            # 获取搜索容器的全局位置
            container_rect = self.search_container.rect()
            container_global_pos = self.search_container.mapToGlobal(container_rect.topLeft())

            # 设置路线规划面板的位置和大小
            self.route_plan_panel.setGeometry(
                container_global_pos.x(),
                container_global_pos.y(),
                self.search_container.width(),
                400  # 固定高度
            )

            # 加载路线搜索历史
            history_list = self.route_history_storage.get_history(10)
            self.route_plan_panel.load_history(history_list)

            # 显示面板
            self.route_plan_panel.show()
            self.route_plan_panel.raise_()

            self.logger.debug(f"[路线面板] 面板位置: ({container_global_pos.x()}, {container_global_pos.y()})")
            self.logger.debug(f"[路线面板] 面板大小: {self.search_container.width()} x 400")

            self.logger.debug("[路线面板] 路线规划面板已显示")

    def _on_route_panel_cancel(self):
        """路线规划面板取消按钮点击"""
        self.logger.info("[路线面板] 取消路线规划")

        # 恢复历史记录模式（关闭路线待选列表，显示历史记录）
        if hasattr(self, 'route_plan_panel'):
            self.route_plan_panel.restore_history_mode()

        # 隐藏路线规划面板
        if hasattr(self, 'route_plan_panel'):
            self.route_plan_panel.hide()

    def _on_route_plan_clicked(self, start: str, end: str, mode: str, waypoints: list):
        """路线规划按钮点击"""
        self.logger.info(f"[路线规划] 开始规划路线: {start} → {end}, 方式: {mode}")
        self.logger.info(f"[路线规划] 途径点: {waypoints}")

        # 检查起点和终点是否已设置
        if not start or not end:
            self.route_plan_panel.show_route_plan_error("请先设置起点和终点")
            return

        # 检查是否已经有起点和终点的坐标
        if not self.data_manager.has_start_end():
            self.route_plan_panel.show_route_plan_error("请先搜索并选择起点和终点位置")
            return

        # 保存当前的路线信息（用于后续保存历史记录）
        self._current_route_info = {
            'start': start,
            'end': end,
            'mode': mode,
            'waypoints': waypoints,
            'start_coords': self.data_manager.start_coords,
            'end_coords': self.data_manager.end_coords,
            'waypoint_coords': self.data_manager.waypoints_coords
        }

        # 显示加载中状态
        self.route_plan_panel.show_loading()

        # 调用路线管理器进行路线规划
        self.route_manager.plan_route(mode)

    def _on_route_clear_clicked(self):
        """清除路线按钮点击"""
        self.logger.info("[路线面板] 清除路线")

        # 清除 data_manager 中的所有路线数据
        self.data_manager.clear_all_route_data()

        # 清除路线面板中的输入框内容
        self.route_plan_panel.clear_all_inputs()

        # 清除地图上的路线显示
        self.map_manager.update_map_preview(auto_fit=False)

        self.logger.info("[路线面板] 路线已清除")

    def _on_route_location_search(self, search_text: str, location_type: str):
        """路线面板中的地点搜索"""
        self.logger.info(f"[路线面板] 搜索地点: {search_text}, 类型: {location_type}")

        # 显示加载状态
        self.route_plan_panel.show_loading()

        # 获取当前地图源
        from services.config.map_config import map_config
        map_source = map_config.get_map_source()

        # 获取对应的地理编码服务
        geocoding_service = self.service_manager.get_geocoding_service(map_source)

        if not geocoding_service:
            self.logger.warning(f"未找到地图源 {map_source} 的地理编码服务")
            self.route_plan_panel.hide_loading()
            self.route_plan_panel.show_search_error(location_type)
            return

        try:
            # 执行搜索
            results = geocoding_service.search_location(search_text)

            # 隐藏加载状态
            self.route_plan_panel.hide_loading()

            if results:
                # 转换为地址待选列表格式
                suggestions = []
                for result in results:
                    # 根据不同服务的返回格式进行转换
                    name = result.get('name', '')
                    address = result.get('address', result.get('formatted_address', ''))

                    # 获取坐标
                    if 'location' in result:
                        location = result['location']
                    elif 'lat' in result and 'lon' in result:
                        location = f"{result['lon']},{result['lat']}"
                    elif 'lng' in result and 'lat' in result:
                        location = f"{result['lng']},{result['lat']}"
                    else:
                        location = ''

                    # 保留原始结果中的级别、类型、半径信息
                    suggestions.append({
                        'name': name,
                        'address': address,
                        'location': location,
                        'level': result.get('level'),
                        'type': result.get('type'),
                        'radius': result.get('radius')
                    })

                # 显示搜索结果
                self.route_plan_panel.show_address_suggestions(suggestions)

                # 在地图上预览第一个地址（使用 preview_search_result 以支持级别缩放）
                if suggestions and suggestions[0].get('location'):
                    first_addr = suggestions[0]
                    location = first_addr['location']
                    if ',' in location:
                        try:
                            lng, lat = location.split(',')
                            # 使用 preview_search_result 方法，支持根据级别、类型、半径自动缩放
                            self.map_manager.preview_search_result(
                                coords=(float(lat), float(lng)),
                                name=f"{first_addr['name']}\n{first_addr['address']}",
                                level=first_addr.get('level'),
                                type_info=first_addr.get('type'),
                                radius=first_addr.get('radius')
                            )
                        except (ValueError, IndexError) as e:
                            self.logger.error(f"无效的坐标格式: {location}, 错误: {e}")
            else:
                # 没有搜索结果
                self.route_plan_panel.hide_address_suggestions_and_show_history()
                self.route_plan_panel.show_search_error(location_type)
                self.logger.warning(f"未找到地址: {search_text}")

        except Exception as e:
            self.logger.error(f"搜索地址失败: {e}")
            self.route_plan_panel.hide_loading()
            self.route_plan_panel.hide_address_suggestions_and_show_history()
            self.route_plan_panel.show_search_error(location_type)

    def _on_route_address_selected(self, address_data: dict, location_type: str, should_zoom: bool = True):
        """处理地址选中事件

        Args:
            address_data: 地址数据字典
            location_type: 位置类型（start/end/waypoint）
            should_zoom: 是否缩放地图（默认True，双击时为False）
        """
        self.logger.info(f"[路线面板] 地址选中: {address_data.get('name', '')}, 类型: {location_type}, 缩放: {should_zoom}")

        # 获取坐标
        location = address_data.get('location', '')
        if not location or ',' not in location:
            self.logger.warning(f"地址缺少坐标信息: {address_data}")
            return

        try:
            lng, lat = location.split(',')
            lat_float = float(lat)
            lng_float = float(lng)

            # 根据地址类型设置到 data_manager
            name = address_data.get('name', '')
            level = address_data.get('level')

            if location_type == "start":
                self.data_manager.set_start_location((lat_float, lng_float), name, level)
                self.logger.info(f"[路线面板] 设置起点: {name} ({lat_float}, {lng_float})")
            elif location_type == "end":
                self.data_manager.set_end_location((lat_float, lng_float), name, level)
                self.logger.info(f"[路线面板] 设置终点: {name} ({lat_float}, {lng_float})")
            elif location_type == "waypoint":
                self.data_manager.add_waypoint((lat_float, lng_float), name)
                self.logger.info(f"[路线面板] 添加途径点: {name} ({lat_float}, {lng_float})")

            # 保存到搜索历史记录
            search_text = address_data.get('_search_text', name)  # 获取原始搜索文本
            if search_text:
                # 构建标准格式的结果字典
                result_dict = {
                    'name': name,
                    'address': address_data.get('address', ''),
                    'lat': lat_float,
                    'lon': lng_float,
                    'type': address_data.get('type', ''),
                    'level': address_data.get('level', ''),
                    'radius': address_data.get('radius', None)
                }
                # 调用搜索管理器保存历史记录
                self.search_manager._save_to_history(search_text, result_dict)
                self.logger.info(f"[路线面板] 已保存到搜索历史: {search_text} -> {name}")

            # 只有在需要缩放时才调用 preview_search_result
            if should_zoom:
                # 使用 preview_search_result 在地图上标识位置（带箭头标记）
                # 支持根据级别、类型、半径自动缩放
                address = address_data.get('address', '')
                display_name = f"{name}\n{address}" if address else name

                self.map_manager.preview_search_result(
                    coords=(lat_float, lng_float),
                    name=display_name,
                    level=address_data.get('level'),
                    type_info=address_data.get('type'),
                    radius=address_data.get('radius')
                )

                self.logger.info(f"[路线面板] 地图已缩放到: {name} ({lat_float}, {lng_float})")
            else:
                self.logger.info(f"[路线面板] 跳过地图缩放（双击确认）")

        except (ValueError, IndexError) as e:
            self.logger.error(f"无效的坐标格式: {location}, 错误: {e}")

    def _on_route_history_selected(self, history_data: dict):
        """选择路线搜索历史"""
        start = history_data.get('start', '')
        end = history_data.get('end', '')
        mode = history_data.get('mode', 'driving')

        # 获取坐标信息
        start_coords = history_data.get('start_coords')
        end_coords = history_data.get('end_coords')
        waypoint_coords = history_data.get('waypoint_coords', [])

        # 获取保存的路线点数据
        route_points = history_data.get('route_points', [])
        distance = history_data.get('distance', 0)
        duration = history_data.get('duration', 0)

        self.logger.info(f"[路线面板] 选择历史记录: {start} → {end}")
        self.logger.info(f"[路线面板] 起点坐标: {start_coords}, 终点坐标: {end_coords}")
        self.logger.info(f"[路线面板] 路线点数量: {len(route_points)}, 距离: {distance}m, 时长: {duration}s")

        # 清除旧的路线数据（重要：避免显示上一次的路线）
        self.data_manager.clear_all_route_data()

        # 清除旧的途径点数据
        self.data_manager.clear_waypoints()

        # 恢复历史记录模式（关闭路线待选列表，显示历史记录）
        if hasattr(self, 'route_plan_panel'):
            self.route_plan_panel.restore_history_mode()

            # 清空所有输入框（重要：清除旧数据）
            self.route_plan_panel.clear_all_inputs()

        # 填充到输入框
        if hasattr(self, 'route_plan_panel'):
            self.route_plan_panel.set_start_location(start)
            self.route_plan_panel.set_end_location(end)

            # 切换交通方式
            self.route_plan_panel._switch_transport_mode(mode)

        # 如果历史记录中有坐标，直接恢复
        has_coords = False
        if start_coords and isinstance(start_coords, (list, tuple)) and len(start_coords) == 2:
            self.data_manager.set_start_location(tuple(start_coords), start)
            self.logger.info(f"[路线面板] 已恢复起点坐标: {start_coords}")
            has_coords = True

        if end_coords and isinstance(end_coords, (list, tuple)) and len(end_coords) == 2:
            self.data_manager.set_end_location(tuple(end_coords), end)
            self.logger.info(f"[路线面板] 已恢复终点坐标: {end_coords}")
            has_coords = has_coords and True
        else:
            has_coords = False

        # 恢复途径点坐标和UI
        if waypoint_coords:
            waypoints = history_data.get('waypoints', [])
            for i, coords in enumerate(waypoint_coords):
                if coords and isinstance(coords, (list, tuple)) and len(coords) == 2:
                    waypoint_name = waypoints[i] if i < len(waypoints) else f"途径点{i+1}"
                    # 添加到data_manager
                    self.data_manager.add_waypoint(tuple(coords), waypoint_name)
                    # 添加到UI
                    if hasattr(self, 'route_plan_panel'):
                        self.route_plan_panel._add_waypoint()
                        # 设置途径点文本
                        if i < len(self.route_plan_panel.waypoint_widgets):
                            self.route_plan_panel.waypoint_widgets[i]['input'].setText(waypoint_name)
                    self.logger.info(f"[路线面板] 已恢复途径点{i+1}坐标: {coords}")

        # 如果没有坐标，自动搜索起点和终点
        if not has_coords:
            self.logger.info(f"[路线面板] 历史记录缺少坐标，开始自动搜索...")
            self._auto_search_history_locations(start, end, mode)
        else:
            # 恢复路线点数据到data_manager
            if route_points and len(route_points) > 0:
                # 将路线点转换为元组格式 (lat, lon) 或 (lat, lon, elevation)
                converted_route_points = []
                for point in route_points:
                    if isinstance(point, (list, tuple)) and len(point) >= 2:
                        # 保留原始格式（可能包含海拔）
                        converted_route_points.append(tuple(point))

                if converted_route_points:
                    # 设置路线点数据
                    self.data_manager.route_points = converted_route_points
                    self.data_manager.estimated_duration_seconds = duration
                    # 注意：distance 在 data_manager 中没有直接存储，但可以通过 route_points 计算

                    self.logger.info(f"[路线面板] 已恢复路线点数据: {len(converted_route_points)} 个点")

                    # 在地图上渲染路线
                    self.map_manager.show_route_on_map()
                    self.logger.info(f"[路线面板] 路线已渲染到地图")
            else:
                # 如果没有路线点数据，只显示起点和终点
                self.logger.info(f"[路线面板] 历史记录中没有路线点数据，只显示起点和终点")
                # 在地图上预览起点和终点
                if self.data_manager.start_coords and self.data_manager.end_coords:
                    # 更新地图预览，显示起点和终点
                    self.map_manager.update_map_preview(auto_fit=True)

    def _auto_search_history_locations(self, start: str, end: str, mode: str):
        """自动搜索历史记录中的起点和终点坐标

        Args:
            start: 起点名称
            end: 终点名称
            mode: 交通方式
        """
        from services.config.map_config import map_config

        # 获取地理编码服务
        map_source = map_config.get_map_source()
        geocoding_service = self.service_manager.get_geocoding_service(map_source)

        if not geocoding_service:
            self.logger.warning(f"未找到地图源 {map_source} 的地理编码服务")
            return

        try:
            # 搜索起点
            self.logger.info(f"[路线面板] 搜索起点: {start}")
            start_results = geocoding_service.search_location(start)
            if start_results and len(start_results) > 0:
                # 使用第一个结果
                first_result = start_results[0]
                location = first_result.get('location', '')
                if location and ',' in location:
                    lng, lat = location.split(',')
                    start_coords = (float(lat), float(lng))
                    self.data_manager.set_start_location(
                        start_coords,
                        start,
                        first_result.get('level')
                    )
                    self.logger.info(f"[路线面板] 起点坐标已找到: {start_coords}")

            # 搜索终点
            self.logger.info(f"[路线面板] 搜索终点: {end}")
            end_results = geocoding_service.search_location(end)
            if end_results and len(end_results) > 0:
                # 使用第一个结果
                first_result = end_results[0]
                location = first_result.get('location', '')
                if location and ',' in location:
                    lng, lat = location.split(',')
                    end_coords = (float(lat), float(lng))
                    self.data_manager.set_end_location(
                        end_coords,
                        end,
                        first_result.get('level')
                    )
                    self.logger.info(f"[路线面板] 终点坐标已找到: {end_coords}")

            # 在地图上预览起点和终点
            if self.data_manager.start_coords and self.data_manager.end_coords:
                self.map_manager.update_map_preview(auto_fit=True)
                self.logger.info(f"[路线面板] 已在地图上显示起点和终点")

                # 更新历史记录中的坐标（下次就不用再搜索了）
                self.route_history_storage.add_record(
                    start, end, mode, [],
                    start_coords=self.data_manager.start_coords,
                    end_coords=self.data_manager.end_coords,
                    waypoint_coords=[]
                )
                self.logger.info(f"[路线面板] 已更新历史记录中的坐标")
            else:
                self.logger.warning(f"[路线面板] 未能找到起点或终点的坐标")

        except Exception as e:
            self.logger.error(f"[路线面板] 自动搜索坐标失败: {e}")

    def _on_route_alternative_selected(self, index: int):
        """用户选择路线方案"""
        self.logger.info(f"[路线面板] 用户选择路线方案: {index}")

        # 隐藏加载状态
        self.route_plan_panel.hide_loading()

        # 调用路线管理器选择路线方案
        self.route_manager.select_route_alternative(index)

    def _show_route_alternatives(self, alternatives: list, selected_index: int = 0):
        """显示路线待选列表"""
        self.logger.info(f"[路线面板] 显示路线待选列表，共 {len(alternatives)} 个方案")

        # 隐藏加载状态
        self.route_plan_panel.hide_loading()

        # 在路线规划面板中显示路线待选列表
        self.route_plan_panel.show_route_alternatives(alternatives, selected_index)

    def _save_route_history(self, distance: float = None, duration: int = None):
        """保存路线历史记录（在路线规划成功后调用）

        Args:
            distance: 路线总距离（米）
            duration: 路线总时长（秒）
        """
        if not hasattr(self, '_current_route_info'):
            self.logger.warning("[路线面板] 没有当前路线信息，无法保存历史记录")
            return

        info = self._current_route_info

        # 从data_manager获取完整路线点数据（包含海拔）
        route_points = self.data_manager.route_points if hasattr(self.data_manager, 'route_points') else None

        # 记录路线点数量
        if route_points:
            valid_points = [p for p in route_points if p is not None]
            self.logger.debug(f"[路线面板] 准备保存路线点数据，共 {len(valid_points)} 个有效点")
        else:
            self.logger.warning("[路线面板] 没有路线点数据")

        # 保存到历史记录（包含完整信息）
        self.route_history_storage.add_record(
            info['start'],
            info['end'],
            info['mode'],
            info['waypoints'],
            start_coords=info['start_coords'],
            end_coords=info['end_coords'],
            waypoint_coords=info['waypoint_coords'],
            distance=distance,
            duration=duration,
            route_points=route_points
        )

        self.logger.info(f"[路线面板] 已保存历史记录: {info['start']} → {info['end']}, "
                        f"距离: {distance}米, 时长: {duration}秒")

        # 重新加载历史记录
        history_list = self.route_history_storage.get_history(10)
        self.route_plan_panel.load_history(history_list)

        # 清除临时信息
        delattr(self, '_current_route_info')

    def _get_mode_text(self, mode: str) -> str:
        """获取交通方式文本"""
        mode_map = {
            'driving': '驾车',
            'cycling': '骑行',
            'walking': '步行'
        }
        return mode_map.get(mode, '驾车')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GpxStudio()
    window.show()
    sys.exit(app.exec_())

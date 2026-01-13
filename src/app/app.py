"""
GPX Studio 主应用窗口 (重构版)
使用管理器模式，提高代码的可复用性、可维护性、可扩展性
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QListWidget, QFileDialog,
                             QMessageBox, QSplitter, QListWidgetItem, QScrollArea,
                             QApplication, QDialog, QTimeEdit)
from PyQt5.QtCore import Qt, QTimer
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
        print("窗口设置初始化完成")

    def _init_services(self):
        """初始化服务"""
        print("开始初始化服务")
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
        }

    def _connect_signals(self):
        """连接信号"""
        self.signal_manager.geolocation_success.connect(self._on_geolocation_success)
        self.signal_manager.geolocation_error.connect(self._on_geolocation_error)
        self.signal_manager.map_zoom_changed.connect(self.on_map_zoom_changed)

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

    def init_ui(self):
        """初始化用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)

        # 创建三个主面板
        left_panel = self.create_left_panel()
        middle_panel = self.create_middle_panel()
        right_panel = self.create_right_panel()

        splitter.addWidget(left_panel)
        splitter.addWidget(middle_panel)
        splitter.addWidget(right_panel)

        # 使用布局管理器设置布局
        LayoutManager.setup_layout(splitter)

        main_layout.addWidget(splitter)

        # 延迟加载初始地图
        QTimer.singleShot(MAP_LOAD_DELAY_MS, self._show_initial_map)

    def create_left_panel(self):
        """创建左侧控制面板"""
        left_widget = QWidget()
        left_widget.setMinimumWidth(LayoutManager.PANEL_SIZES[0])
        left_layout = QVBoxLayout(left_widget)

        # 顶部按钮
        top_button_layout = QHBoxLayout()

        locate_button = QPushButton("📍 定位")
        locate_button.clicked.connect(self.on_locate_clicked)
        locate_button.setStyleSheet(UIStyles.LOCATE_BUTTON)
        top_button_layout.addWidget(locate_button)

        config_button = QPushButton("⚙️ 地图配置")
        config_button.clicked.connect(self.show_map_config)
        config_button.setStyleSheet(UIStyles.LOCATE_BUTTON)
        top_button_layout.addWidget(config_button)

        about_button = QPushButton("ℹ️ 关于")
        about_button.clicked.connect(self.show_about_dialog)
        about_button.setStyleSheet(UIStyles.LOCATE_BUTTON)
        top_button_layout.addWidget(about_button)

        left_layout.addLayout(top_button_layout)

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

    def create_middle_panel(self):
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

        # 清空按钮
        clear_button = QPushButton("清空搜索结果")
        clear_button.clicked.connect(self.on_clear_search_clicked)
        clear_button.setStyleSheet(UIStyles.CLEAR_BUTTON)
        layout.addWidget(clear_button)

        # 任务进度面板
        from ui.panels.task_progress_panel import TaskInfoPanel
        self.task_progress_panel = TaskInfoPanel()
        self.task_progress_panel.cancel_task_requested.connect(self._on_cancel_task_requested)
        layout.addWidget(self.task_progress_panel)

        # 地图缩放比例尺显示面板
        self.scale_panel = ScalePanel()
        layout.addWidget(self.scale_panel)

        # 进度条
        self.progress_bar = PanelFactory.create_progress_bar()
        layout.addWidget(self.progress_bar)

        return middle_widget

    def create_right_panel(self):
        """创建右侧地图面板"""
        right_widget = QWidget()
        right_widget.setMinimumWidth(LayoutManager.PANEL_SIZES[2])
        layout = QVBoxLayout(right_widget)

        # 创建地图视图
        self.map_view = QWebEngineView()
        self.web_page = ConsoleWebEnginePage(signal_manager=self.signal_manager)
        self.web_page.set_geolocation_handler(self.geolocation_handler)
        self.map_view.setPage(self.web_page)

        # 设置User Agent
        profile = QWebEngineProfile.defaultProfile()
        profile.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        layout.addWidget(self.map_view)

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
        self.progress_bar.setMaximum(0)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(0)
        QApplication.processEvents()

    def _set_progress_complete(self):
        """设置进度条为完成状态"""
        self.progress_bar.setMaximum(100)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(100)
        QApplication.processEvents()

    def _set_progress(self, value: int):
        """设置进度条值"""
        self.progress_bar.setMaximum(100)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(value)
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

    def _update_location_display(self, location_type: str, name: str, data: tuple):
        """更新位置显示"""
        if location_type == "start":
            if hasattr(self, 'start_label'):
                self.start_label.setText(name)
                self.start_label.setProperty('userData', data)
        elif location_type == "end":
            if hasattr(self, 'end_label'):
                self.end_label.setText(name)
                self.end_label.setProperty('userData', data)

    def _update_start_from_search(self, name: str, data: tuple):
        """从搜索结果更新起点"""
        if hasattr(self, 'start_label'):
            self.start_label.setText(name)
            self.start_label.setProperty('userData', data)
        if hasattr(self, 'start_list'):
            self.start_list.clear()
            self.start_list.addItem(name)
            self.start_list.item(0).setData(Qt.UserRole, data)

    def _update_end_from_search(self, name: str, data: tuple):
        """从搜索结果更新终点"""
        if hasattr(self, 'end_label'):
            self.end_label.setText(name)
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
        log_rect = self.log_panel.rect()
        log_pos = self.log_panel.mapToGlobal(log_rect.topLeft())
        log_size = self.log_panel.size()
        self.date_panel.show_panel(current_date, log_pos, 0, log_size)

    def _show_time_panel(self, current_time):
        """显示时间面板"""
        log_rect = self.log_panel.rect()
        log_pos = self.log_panel.mapToGlobal(log_rect.topLeft())
        log_size = self.log_panel.size()
        self.time_panel.show_panel(current_time, log_pos, 0, log_size)

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
        self.scale_panel.update_zoom(zoom_level)

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
        elif task_id.startswith('map_render_'):
            self.route_manager.on_map_render_task_failed(task_id, error)

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GpxStudio()
    window.show()
    sys.exit(app.exec_())

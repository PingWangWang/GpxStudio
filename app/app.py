"""
GPX Studio 主应用窗口
整合所有模块，实现完整的路线规划功能
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QListWidget, QFileDialog,
                             QMessageBox, QSplitter, QListWidgetItem, QScrollArea,
                             QApplication, QDialog, QTimeEdit)
from PyQt5.QtCore import Qt, QTimer, QTime
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile

import sys
import os
from typing import Optional

# 确保日志重定向生效 - 必须在其他导入之前执行
import core.logging_setup

# 导入信号管理器
from core.signals import SignalManager

from modules.geolocation.geolocation import GeolocationHandler
from modules.map.webengine import ConsoleWebEnginePage
from services.gaode.gaode_geocoding import GaodeGeocodingService
from services.gaode.gaode_routing import GaodeRoutingService
from services.osm.osm_geocoding import OsmGeocodingService
from services.osm.osm_routing import OsmRoutingService
from modules.gpx.gpx_export import GpxExportService
from modules.geolocation.windows_location import WindowsLocationService
from services.config.map_config import map_config
from modules.map.map_renderer import MapRenderer
from modules.geolocation.location_helper import LocationHelper
from ui.styles import UIStyles
from ui.panels.panel_factory import PanelFactory
from ui.panels.log_panel import LogPanel, setup_logger
from ui.panels.scale_panel import ScalePanel
from ui.dialogs.map_config_dialog import MapConfigDialog
from ui.dialogs.about_dialog import AboutDialog
from ui.layout.layout_manager import LayoutManager
from .constants import (
    WINDOW_TITLE, WINDOW_SIZE, SEARCH_TYPE_START, SEARCH_TYPE_END, SEARCH_TYPE_WAYPOINT,
    COLOR_INFO, COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR, COLOR_ORANGE, ICON_INFO, ICON_SUCCESS,
    ICON_WARNING, ICON_ERROR, GEOLOCATION_ERROR_MESSAGES,
    MAP_LOAD_DELAY_MS, SEARCH_RESULTS_TITLE, SEARCH_LIST_TITLES
)


class GpxStudio(QMainWindow):
    """GPX Studio 主应用窗口"""

    def __init__(self):
        super().__init__()
        # 添加启动标记日志
        print("=" * 80)
        print("GPX Studio 程序启动开始")
        print("=" * 80)
        
        # 先初始化基本组件，然后再初始化日志系统
        print("开始初始化窗口设置")
        self._init_window()
        print("窗口设置初始化完成")
        
        print("开始初始化服务")
        self._init_services()
        print("服务初始化完成")
        
        print("开始初始化数据状态")
        self._init_data_state()
        print("数据状态初始化完成")
        
        print("开始初始化定位和信号系统")
        self._init_geolocation_and_signals()
        print("定位和信号系统初始化完成")
        
        print("开始初始化UI")
        self._init_ui()
        print("UI初始化完成")
        
        print("开始初始化日志系统")
        self._init_logging()
        print("日志系统初始化完成")
        
        # 添加启动完成标记日志
        self.logger.info("=" * 80)
        self.logger.info("GPX Studio 程序启动完成")
        self.logger.info("=" * 80)
        self.logger.info("所有初始化步骤已完成")
        
        # 记录初始化完成后的状态
        self.logger.debug("程序启动完成，开始记录初始化状态")
        self.logger.debug(f"窗口标题: {self.windowTitle()}")
        self.logger.debug(f"窗口大小: {self.size()}")
        self.logger.debug("程序启动状态: 正常")

    def _init_window(self):
        """初始化窗口设置"""
        print(f"设置窗口标题: {WINDOW_TITLE}")
        self.setWindowTitle(WINDOW_TITLE)
        
        print(f"设置窗口大小: {WINDOW_SIZE}")
        self.resize(*WINDOW_SIZE)

        # 窗口居中
        print("开始窗口居中操作")
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        print(f"屏幕几何信息: {screen_geometry}")
        
        window_geometry = self.frameGeometry()
        center_point = screen_geometry.center()
        print(f"屏幕中心点: {center_point}")
        
        window_geometry.moveCenter(center_point)
        print(f"窗口居中后的位置: {window_geometry.topLeft()}")
        self.move(window_geometry.topLeft())
        print("窗口居中操作完成")

    def _init_services(self):
        """初始化服务"""
        print("开始初始化服务")
        
        # 获取配置信息
        api_key = map_config.get_api_key()
        security_key = map_config.get_security_key()
        print(f"API Key 配置: {'已配置' if api_key else '未配置'}")
        print(f"Security Key 配置: {'已配置' if security_key else '未配置'}")
        
        # 初始化高德地理编码服务
        print("初始化高德地理编码服务")
        self.gaode_geocoding_service = GaodeGeocodingService(
            api_key=api_key,
            security_key=security_key,
            logger=self._log_to_geocoding
        )
        
        # 初始化高德路线规划服务
        print("初始化高德路线规划服务")
        self.gaode_routing_service = GaodeRoutingService(
            api_key=api_key,
            security_key=security_key,
            logger=self._log_to_routing
        )
        
        # 初始化OSM地理编码服务
        print("初始化OSM地理编码服务")
        self.osm_geocoding_service = OsmGeocodingService(
            logger=self._log_to_geocoding
        )
        
        # 初始化OSM路线规划服务
        print("初始化OSM路线规划服务")
        self.osm_routing_service = OsmRoutingService(
            logger=self._log_to_routing
        )
        
        # 初始化GPX导出服务
        print("初始化GPX导出服务")
        self.gpx_service = GpxExportService(logger=self._log_to_gpx)
        
        print("服务初始化完成")

    def _init_data_state(self):
        """初始化数据状态"""
        print("开始初始化数据状态")
        
        self.start_coords = None
        self.start_name = None
        self.end_coords = None
        self.end_name = None
        self.waypoints_coords = []
        self.waypoints_names = []
        self.current_route = None
        self.route_points = []
        self.current_location = None
        self.search_results = []
        self.searching_for = None
        self.selected_search_result_coords = None
        self.estimated_duration_seconds = 0
        self.last_selected_coords = None
        self.last_selected_level = None
        self.last_selected_type = None
        self.last_selected_from_search = False
        
        print("数据状态初始化完成")
        print(f"初始数据状态: start_coords={self.start_coords}, end_coords={self.end_coords}, waypoints_coords={self.waypoints_coords}")

    def _init_geolocation_and_signals(self):
        """初始化定位和信号系统"""
        print("开始初始化定位和信号系统")
        
        print("创建地理定位处理器")
        self.geolocation_handler = GeolocationHandler()
        
        print("创建信号管理器")
        self.signal_manager = SignalManager()

        # 使用信号管理器连接地理定位信号
        print("连接地理定位成功信号")
        self.signal_manager.geolocation_success.connect(self._on_geolocation_success)
        
        print("连接地理定位错误信号")
        self.signal_manager.geolocation_error.connect(self._on_geolocation_error)
        
        print("定位和信号系统初始化完成")

    def _init_ui(self):
        """初始化UI"""
        print("开始初始化UI")
        self.init_ui()
        print("UI初始化完成")

    def _init_logging(self):
        """初始化日志系统"""
        print("开始初始化日志系统")
        self.logger = setup_logger(self.log_panel, "GpxStudio")
        self.logger.debug("创建Windows定位服务")
        self.windows_location_service = WindowsLocationService(logger=self._log_to_service)
        self.logger.debug("日志系统初始化完成")

    def show_map_config(self):
        """显示地图配置对话框"""
        dialog = MapConfigDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # 获取地图数据源
            map_source = map_config.get_map_source()
            self.logger.info(f"地图数据源已更新: {map_source}")
            
            # 如果是高德地图，更新API Key
            if map_source == "gaode":
                api_key = map_config.get_api_key()
                security_key = map_config.get_security_key()
                self.gaode_geocoding_service.api_key = api_key
                self.gaode_geocoding_service.security_key = security_key
                self.gaode_routing_service.api_key = api_key
                self.gaode_routing_service.security_key = security_key
                self.logger.info("高德地图API配置已更新")
            
            # 清空所有路线相关数据
            self.clear_route_data()
            
            # 重新加载地图
            self.show_initial_map()
    
    def clear_route_data(self):
        """清空所有路线相关数据"""
        # 清空起点终点数据
        self.start_coords = None
        self.start_name = None
        self.end_coords = None
        self.end_name = None
        
        # 清空途径点数据
        self.waypoints_coords = []
        self.waypoints_names = []
        
        # 清空路线数据
        self.current_route = None
        self.route_points = []
        self.estimated_duration_seconds = 0
        
        # 清空搜索相关数据
        self.search_results = []
        self.searching_for = None
        self.selected_search_result_coords = None
        
        # 清空最后选中位置数据
        self.last_selected_coords = None
        self.last_selected_level = None
        self.last_selected_type = None
        self.last_selected_from_search = False
        
        # 清空UI显示
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
        level_map = {
            "DEBUG": self.logger.debug,
            "INFO": self.logger.info,
            "WARNING": self.logger.warning,
            "ERROR": self.logger.error,
            "CRITICAL": self.logger.critical
        }
        log_func = level_map.get(level, self.logger.info)
        log_func(f"[{prefix}] {message}")

    def _init_ui(self):
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

        # 延迟加载初始地图，确保UI完全初始化后再显示地图
        QTimer.singleShot(MAP_LOAD_DELAY_MS, self.show_initial_map)

    def create_left_panel(self):
        """创建左侧控制面板"""
        left_widget = QWidget()
        left_widget.setMinimumWidth(LayoutManager.PANEL_SIZES[0])
        left_layout = QVBoxLayout(left_widget)

        # 顶部按钮布局
        top_button_layout = QHBoxLayout()

        locate_button = QPushButton("📍 定位")
        locate_button.clicked.connect(self.get_current_location)
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
        self.plan_button.clicked.connect(self.plan_route)
        self.plan_button.setStyleSheet(UIStyles.PLAN_BUTTON)

        self.export_button = QPushButton("导出GPX")
        self.export_button.clicked.connect(self.export_gpx)
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

        # 标题
        self.search_results_title = QLabel("搜索结果")
        self.search_results_title.setStyleSheet(UIStyles.TITLE_LABEL)
        layout.addWidget(self.search_results_title)

        # 搜索结果列表
        self.search_results_list = QListWidget()
        self.search_results_list.itemClicked.connect(self.select_search_result)
        layout.addWidget(self.search_results_list)

        # 清空按钮
        clear_button = QPushButton("清空搜索结果")
        clear_button.clicked.connect(self.clear_search_results)
        clear_button.setStyleSheet(UIStyles.CLEAR_BUTTON)
        layout.addWidget(clear_button)

        # 日志显示面板
        self.log_panel = LogPanel()
        layout.addWidget(self.log_panel)

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

        # 使用信号管理器连接地图缩放信号
        self.signal_manager.map_zoom_changed.connect(self.on_map_zoom_changed)

        self.map_view.setPage(self.web_page)

        # 设置User Agent
        profile = QWebEngineProfile.defaultProfile()
        profile.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        layout.addWidget(self.map_view)

        # 注意：初始地图现在通过定时器延迟加载，确保UI完全初始化

        return right_widget

    def show_initial_map(self):
        """显示初始地图（北京中心）"""
        map_source = map_config.get_map_source()
        m = MapRenderer.create_base_map([39.9042, 116.4074], zoom_start=10, map_source=map_source)
        url = MapRenderer.save_and_get_url(m)
        self.map_view.setUrl(url)
        # 初始化比例尺显示
        self.scale_panel.update_zoom(10)

    def on_map_zoom_changed(self, zoom_level: int):
        """处理地图缩放变化事件"""
        self.logger.info(f"地图缩放级别变化: {zoom_level}")
        self.scale_panel.update_zoom(zoom_level)

    # ========== 搜索相关方法 ==========

    def search_location(self, location_type):
        """搜索地点（起点/终点）"""
        search_text = getattr(self, f"{location_type}_input").text()
        self._perform_generic_search(search_text, location_type)

    def search_waypoint(self):
        """搜索途径点"""
        search_text = self.waypoint_input.text()
        self._perform_generic_search(search_text, "waypoint")

    def _perform_generic_search(self, search_text, location_type):
        """执行通用搜索"""
        if not search_text:
            return

        # 恢复信息展示框标题
        self.search_results_title.setText("搜索结果")
        self.search_results_list.clear()
        self.progress_bar.setMaximum(0)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(0)
        QApplication.processEvents()

        self._perform_search(search_text, location_type)

    def _perform_search(self, search_text, location_type):
        """执行搜索"""
        map_source = map_config.get_map_source()
        
        # 检查地图源是否已设置
        if not map_source:
            QMessageBox.warning(self, "警告", "请先在地图配置中设置地图数据源")
            return
        
        if map_source == "gaode":
            if map_config.is_gaode_configured():
                locations = self.gaode_geocoding_service.search_location(search_text)
            else:
                locations = []
                self.logger.warning("高德地图API未配置，无法进行地点搜索。请先配置高德地图API密钥。")
        else:
            # OSM地图使用OSM搜索服务
            locations = self.osm_geocoding_service.search_location(search_text)

        self.progress_bar.setMaximum(100)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(100)
        QApplication.processEvents()

        if locations:
            self.search_results = locations
            self.searching_for = location_type

            self.search_results_title.setText(SEARCH_LIST_TITLES.get(location_type, SEARCH_RESULTS_TITLE))

            for i, location in enumerate(locations):
                if isinstance(location, dict):
                    name = location.get('name', '')
                    address = location.get('address', '')
                    level = location.get('level', '')
                    type_info = location.get('type', '')

                    display_text = f"{i+1}. {name}"
                    if address and address != name:
                        display_text += f"\n    地址: {address}"
                    if level:
                        display_text += f"\n    地点类型: {level}"
                    if type_info:
                        display_text += f"\n    POI分类: {type_info}"

                    item = QListWidgetItem(display_text)
                    item.setData(Qt.UserRole, (
                        name,
                        location.get('lat'),
                        location.get('lon'),
                        level,
                        type_info
                    ))
                else:
                    name = getattr(location, 'name', location.address)
                    address = location.address
                    display_text = f"{i+1}. {name}"
                    if address and address != name:
                        display_text += f"\n    地址: {address}"
                    item = QListWidgetItem(display_text)
                    item.setData(Qt.UserRole, (name, location.latitude, location.longitude, None, None))
                self.search_results_list.addItem(item)

            self.show_search_results_on_map(locations, location_type)
        else:
            QMessageBox.warning(
                self,
                "搜索失败",
                f"未找到: {search_text}\n\n建议：\n"
                "1. 尝试使用更具体的地址（如：陕西省西安市）\n"
                "2. 尝试使用英文搜索（如：Xi'an）\n"
                "3. 检查网络连接\n"
                "4. 稍后再试（可能是服务暂时不可用）\n\n"
                "提示：某些城市名可能需要加上省份名称才能找到更多结果"
            )

    def select_location(self, item, location_type):
        """选择地点（从下拉框或地图点击）"""
        data = item.data(Qt.UserRole)
        if not data:
            return

        name = data[0]
        coords = (data[1], data[2])
        level = data[3] if len(data) > 3 else None
        type_info = data[4] if len(data) > 4 else None

        self.last_selected_coords = coords
        self.last_selected_level = level
        self.last_selected_type = type_info
        self.last_selected_from_search = False

        if location_type == "start":
            self.start_coords = coords
            self.start_name = name
            self.start_level = level
            self.start_list.clear()
            self.start_list.addItem(name)
            self.start_list.item(0).setData(Qt.UserRole, data)
        elif location_type == "end":
            self.end_coords = coords
            self.end_name = name
            self.end_level = level
            self.end_list.clear()
            self.end_list.addItem(name)
            self.end_list.item(0).setData(Qt.UserRole, data)
        elif location_type == "waypoint":
            waypoint_index = self.waypoint_list.row(item)
            if waypoint_index >= 0 and waypoint_index < len(self.waypoints_coords):
                self.waypoints_coords[waypoint_index] = coords
                self.waypoints_names[waypoint_index] = name

        self.update_map_preview()

    def select_search_result(self, item):
        """从搜索结果中选择"""
        data = item.data(Qt.UserRole)
        if not data:
            return
        name = data[0]
        coords = (data[1], data[2])
        level = data[3] if len(data) > 3 else None
        type_info = data[4] if len(data) > 4 else None

        self.last_selected_coords = coords
        self.last_selected_level = level
        self.last_selected_type = type_info
        self.last_selected_from_search = True

        # 设置选中的搜索结果坐标，用于在地图上区分
        self.selected_search_result_coords = coords

        if self.searching_for == "start":
            self.start_coords = coords
            self.start_name = name
            self.start_level = level
            self.start_list.clear()
            self.start_list.addItem(name)
            self.start_list.item(0).setData(Qt.UserRole, data)
        elif self.searching_for == "end":
            self.end_coords = coords
            self.end_name = name
            self.end_level = level
            self.end_list.clear()
            self.end_list.addItem(name)
            self.end_list.item(0).setData(Qt.UserRole, data)
        elif self.searching_for == "waypoint":
            self.waypoints_coords.append(coords)
            self.waypoints_names.append(name)
            waypoint_item = QListWidgetItem(
                f"{len(self.waypoints_coords)}. {name}"
            )
            waypoint_item.setData(Qt.UserRole, (name, coords[0], coords[1], level, None))
            self.waypoint_list.addItem(waypoint_item)

        self.update_map_preview()

    def clear_search_results(self):
        """清空搜索结果"""
        self.search_results = []
        self.searching_for = None
        self.selected_search_result_coords = None
        self.search_results_list.clear()
        self.search_results_title.setText("搜索结果")

    def remove_waypoint(self):
        """删除途径点"""
        current_row = self.waypoint_list.currentRow()

        if current_row >= 0:
            self.waypoint_list.takeItem(current_row)
            self.waypoints_coords.pop(current_row)
            self.waypoints_names.pop(current_row)

            # 重新编号
            for i in range(self.waypoint_list.count()):
                item = self.waypoint_list.item(i)
                data = item.data(Qt.UserRole)
                if len(data) == 3:
                    name = data[0]
                    item.setText(f"{i + 1}. {name}")
                else:
                    coords = data
                    item.setText(f"{i + 1}. {coords[0]:.4f}, {coords[1]:.4f}")

            self.update_map_preview()

    def clear_all_waypoints(self):
        """清空所有途径点"""
        # 清空列表
        self.waypoint_list.clear()
        # 清空数据
        self.waypoints_coords.clear()
        self.waypoints_names.clear()
        # 更新地图预览
        self.update_map_preview()

    # ========== 地图显示相关方法 ==========

    def show_search_results_on_map(self, locations, location_type):
        """在地图上显示搜索结果"""
        if not locations:
            return

        def get_lat(loc):
            return loc.get('lat') if isinstance(loc, dict) else loc.latitude
        def get_lon(loc):
            return loc.get('lon') if isinstance(loc, dict) else loc.longitude
        def get_address(loc):
            return loc.get('address', '') if isinstance(loc, dict) else loc.address

        center_lat = sum(get_lat(loc) for loc in locations) / len(locations)
        center_lon = sum(get_lon(loc) for loc in locations) / len(locations)

        map_source = map_config.get_map_source()
        m = MapRenderer.create_base_map([center_lat, center_lon], zoom_start=12, map_source=map_source)

        colors = {"start": "green", "end": "red", "waypoint": "blue"}
        color = colors.get(location_type, "orange")

        for i, location in enumerate(locations):
            MapRenderer.add_marker(
                m, [get_lat(location), get_lon(location)],
                f"{i+1}. {get_address(location)}",
                color=color, icon='info-sign'
            )

        self._add_selected_points_to_map(m)

        if self.route_points:
            MapRenderer.add_route(m, self.route_points)

        url = MapRenderer.save_and_get_url(m)
        self.map_view.setUrl(url)

    def update_map_preview(self):
        """更新地图预览"""
        center_lat, center_lon = 39.9042, 116.4074
        center_level = None
        center_type = None

        if hasattr(self, 'last_selected_coords') and self.last_selected_coords:
            center_lat, center_lon = self.last_selected_coords
            center_level = getattr(self, 'last_selected_level', None)
            center_type = getattr(self, 'last_selected_type', None)
        elif self.start_coords:
            center_lat, center_lon = self.start_coords
            center_level = getattr(self, 'start_level', None)
        elif self.end_coords:
            center_lat, center_lon = self.end_coords
            center_level = getattr(self, 'end_level', None)
        elif self.waypoints_coords:
            center_lat, center_lon = self.waypoints_coords[0]

        zoom_level = MapRenderer.get_zoom_by_level(center_level, center_type)
        map_source = map_config.get_map_source()

        m = MapRenderer.create_base_map([center_lat, center_lon], zoom_start=zoom_level, map_source=map_source)

        # 添加已选择的点
        self._add_selected_points_to_map(m)

        # 添加搜索结果
        if self.search_results and self.searching_for:
            colors = {"start": "green", "end": "red", "waypoint": "blue"}
            color = colors.get(self.searching_for, "orange")

            for i, location in enumerate(self.search_results):
                def get_lat(loc):
                    return loc.get('lat') if isinstance(loc, dict) else loc.latitude
                def get_lon(loc):
                    return loc.get('lon') if isinstance(loc, dict) else loc.longitude
                def get_address(loc):
                    return loc.get('address', '') if isinstance(loc, dict) else loc.address

                is_selected = (self.selected_search_result_coords and
                              abs(get_lat(location) - self.selected_search_result_coords[0]) < 0.0001 and
                              abs(get_lon(location) - self.selected_search_result_coords[1]) < 0.0001)
                MapRenderer.add_marker(
                    m, [get_lat(location), get_lon(location)],
                    f"{i+1}. {get_address(location)}",
                    color=color, icon='info-sign'
                )
                if is_selected:
                    MapRenderer.add_marker(
                        m, [get_lat(location), get_lon(location)],
                        "已选择",
                        color=COLOR_WARNING, icon=ICON_WARNING
                    )

        url = MapRenderer.save_and_get_url(m)
        self.map_view.setUrl(url)

    def _add_selected_points_to_map(self, map_obj):
        """添加已选择的点到地图"""
        start_name = self.start_name if self.start_name else "起点"
        if self.start_coords:
            MapRenderer.add_marker(
                map_obj, self.start_coords, start_name,
                color=COLOR_SUCCESS, icon=ICON_SUCCESS
            )

        for i, (waypoint, name) in enumerate(zip(self.waypoints_coords, self.waypoints_names)):
            display_name = name if name else f"途径点 {i + 1}"
            MapRenderer.add_marker(
                map_obj, waypoint, display_name,
                color=COLOR_INFO, icon=ICON_INFO
            )

        end_name = self.end_name if self.end_name else "终点"
        if self.end_coords:
            MapRenderer.add_marker(
                map_obj, self.end_coords, end_name,
                color=COLOR_ERROR, icon=ICON_ERROR
            )

    # ========== 路线规划相关方法 ==========

    def plan_route(self):
        """规划路线"""
        self.logger.info("=" * 80)
        self.logger.info("开始执行路线规划")
        self.logger.info("=" * 80)
        
        if not self.start_coords or not self.end_coords:
            self.logger.warning("路线规划失败：未设置起点或终点")
            QMessageBox.warning(self, "错误", "请先设置起点和终点")
            return
        
        # 检查地图源是否已设置
        map_source = map_config.get_map_source()
        if not map_source:
            self.logger.warning("路线规划失败：未设置地图数据源")
            QMessageBox.warning(self, "警告", "请先在地图配置中设置地图数据源")
            return

        transport_mode = self.transport_combo.currentText()
        points = [self.start_coords] + self.waypoints_coords + [self.end_coords]

        self.logger.info(f"开始规划路线，方式: {transport_mode}")
        self.logger.debug(f"起点: {self.start_coords}, 终点: {self.end_coords}")
        self.logger.debug(f"途径点数量: {len(self.waypoints_coords)}")
        self.logger.debug(f"总点数: {len(points)}")
        
        if self.waypoints_coords:
            self.logger.debug(f"途径点: {self.waypoints_coords}")

        try:
            self.progress_bar.setMaximum(0)
            self.progress_bar.setMinimum(0)
            self.progress_bar.setValue(0)
            QApplication.processEvents()

            self.search_results_list.clear()
            self.search_results_list.addItem("正在规划路线...")
            self.search_results_list.addItem(f"方式: {transport_mode}")

            self.logger.debug("正在调用路线规划服务...")
            map_source = map_config.get_map_source()
            
            if map_source == "gaode":
                if map_config.is_gaode_configured():
                    self.route_points, estimated_duration = self.gaode_routing_service.plan_route(points, transport_mode)
                    self.estimated_duration_seconds = estimated_duration

                    from datetime import datetime
                    current_time = datetime.now()
                    current_time_zero_sec = current_time.replace(second=0)

                    from PyQt5.QtCore import QDateTime
                    qt_current_datetime = QDateTime.fromString(current_time_zero_sec.strftime("%Y-%m-%d %H:%M:%S"), "yyyy-MM-dd hh:mm:ss")
                    self.start_time_edit.setDateTime(qt_current_datetime)

                    # 计算途径时间（小时，支持小数）
                    duration_hours = estimated_duration / 3600
                    self.duration_time_edit.setText(f"{duration_hours:.1f}")

                    end_time = current_time_zero_sec.timestamp() + estimated_duration
                    end_datetime = datetime.fromtimestamp(end_time)
                    qt_end_datetime = QDateTime.fromString(end_datetime.strftime("%Y-%m-%d %H:%M:%S"), "yyyy-MM-dd hh:mm:ss")
                    self.end_time_edit.setDateTime(qt_end_datetime)

                    duration_minutes = (estimated_duration % 3600) // 60
                    self.search_results_list.addItem(f"预估时间: {int(duration_hours)}小时{duration_minutes}分钟")
                else:
                    self.route_points = []
                    self.logger.warning("高德地图API未配置，无法进行路线规划。请先配置高德地图API密钥。")
            else:
                # OSM地图使用OSM路线规划服务
                self.route_points, estimated_duration = self.osm_routing_service.plan_route(points, transport_mode)
                self.estimated_duration_seconds = estimated_duration

                from datetime import datetime
                current_time = datetime.now()
                current_time_zero_sec = current_time.replace(second=0)

                from PyQt5.QtCore import QDateTime
                qt_current_datetime = QDateTime.fromString(current_time_zero_sec.strftime("%Y-%m-%d %H:%M:%S"), "yyyy-MM-dd hh:mm:ss")
                self.start_time_edit.setDateTime(qt_current_datetime)

                # 计算途径时间（小时，支持小数）
                duration_hours = estimated_duration / 3600
                self.duration_time_edit.setText(f"{duration_hours:.1f}")

                end_time = current_time_zero_sec.timestamp() + estimated_duration
                end_datetime = datetime.fromtimestamp(end_time)
                qt_end_datetime = QDateTime.fromString(end_datetime.strftime("%Y-%m-%d %H:%M:%S"), "yyyy-MM-dd hh:mm:ss")
                self.end_time_edit.setDateTime(qt_end_datetime)

                duration_minutes = (estimated_duration % 3600) // 60
                self.search_results_list.addItem(f"预估时间: {int(duration_hours)}小时{duration_minutes}分钟")

            self.progress_bar.setMaximum(100)
            self.progress_bar.setMinimum(0)
            self.progress_bar.setValue(100)
            QApplication.processEvents()

            if self.route_points:
                self.logger.info(f"路线规划成功，共 {len(self.route_points)} 个点")
                self.search_results_list.clear()

                # 修改信息展示框标题
                self.search_results_title.setText("路线信息")

                # 显示路线详细信息
                self.search_results_list.addItem("路线规划成功！")
                self.search_results_list.addItem("=" * 30)

                # 起点、途径点、终点
                self.search_results_list.addItem(f"起点: {self.start_name or '未命名'}")

                # 显示途径点
                if self.waypoints_coords:
                    for i, waypoint in enumerate(self.waypoints_coords):
                        if waypoint and i < len(self.waypoints_names):
                            waypoint_name = self.waypoints_names[i] or f"途径点{i+1}"
                            self.search_results_list.addItem(f"途径点{i+1}: {waypoint_name}")

                self.search_results_list.addItem(f"终点: {self.end_name or '未命名'}")
                self.search_results_list.addItem("=" * 30)

                # 交通方式
                transport_mode = self.transport_combo.currentText()
                self.search_results_list.addItem(f"交通方式: {transport_mode}")

                # 起始时间
                start_datetime = self.start_time_edit.dateTime()
                start_time_str = start_datetime.toString("yyyy-MM-dd HH:mm")
                self.search_results_list.addItem(f"起始时间: {start_time_str}")

                # 途径时间
                duration_hours = self.estimated_duration_seconds // 3600
                duration_minutes = (self.estimated_duration_seconds % 3600) // 60
                self.search_results_list.addItem(f"途径时间: {int(duration_hours)}小时{duration_minutes}分钟")

                # 结束时间
                end_datetime = self.end_time_edit.dateTime()
                end_time_str = end_datetime.toString("yyyy-MM-dd HH:mm")
                self.search_results_list.addItem(f"结束时间: {end_time_str}")

                # 总距离
                if self.gaode_routing_service:
                    total_distance = self.gaode_routing_service.calculate_distance(self.route_points)
                    self.search_results_list.addItem(f"总距离: {total_distance:.2f} 公里")

                self.search_results_list.addItem("=" * 30)

                self.show_route_on_map()
            else:
                self.logger.warning("路线规划失败，未返回路线点")
                self.search_results_list.clear()
                self.search_results_list.addItem("路线规划失败")
                QMessageBox.warning(self, "错误", "路线规划失败")

        except Exception as e:
            self.logger.exception(f"路线规划出错: {str(e)}")
            self.progress_bar.setMaximum(100)
            self.progress_bar.setMinimum(0)
            self.progress_bar.setValue(100)
            QApplication.processEvents()
            self.search_results_list.clear()
            self.search_results_list.addItem("路线规划出错")
            self.search_results_list.addItem(f"错误信息: {str(e)}")
            QMessageBox.warning(self, "错误", f"路线规划出错: {str(e)}")
        
        self.logger.info("路线规划流程完成")
        self.logger.info("=" * 80)

    def show_route_on_map(self):
        """在地图上显示路线"""
        if not self.route_points:
            return

        valid_points = [p for p in self.route_points if p is not None]

        if not valid_points:
            return

        all_coords = []
        if self.start_coords:
            all_coords.append(self.start_coords)
        all_coords.extend(valid_points)
        if self.end_coords:
            all_coords.append(self.end_coords)
        for wp in self.waypoints_coords:
            if wp:
                all_coords.append(wp)

        # 确保所有路线点都包含在边界计算中，避免遗漏
        all_route_points = [p for p in self.route_points if p is not None]

        # 创建一个包含所有相关点的列表
        combined_coords = []
        # 添加起点、终点和途径点
        if self.start_coords and self.start_coords not in combined_coords:
            combined_coords.append(self.start_coords)
        for wp in self.waypoints_coords:
            if wp and wp not in combined_coords:
                combined_coords.append(wp)
        if self.end_coords and self.end_coords not in combined_coords:
            combined_coords.append(self.end_coords)
        # 添加所有路线点
        for rp in all_route_points:
            if rp and rp not in combined_coords:
                combined_coords.append(rp)

        # 更新地图显示，使用MapRenderer的fit_bounds方法进行边界计算和调整
        map_source = map_config.get_map_source()
        m = MapRenderer.create_base_map(self.start_coords or combined_coords[0], zoom_start=12, map_source=map_source)  # 使用适中的初始缩放

        self._add_selected_points_to_map(m)

        MapRenderer.add_route(m, self.route_points)

        # 使用所有坐标点进行边界调整，确保完整显示
        MapRenderer.fit_bounds(m, combined_coords)

        url = MapRenderer.save_and_get_url(m)
        self.map_view.setUrl(url)

    # ========== GPX导出相关方法 ==========

    def export_gpx(self):
        """导出GPX文件"""
        self.logger.info("=" * 80)
        self.logger.info("开始执行GPX文件导出")
        self.logger.info("=" * 80)
        
        if not self.route_points:
            self.logger.warning("GPX导出失败：未规划路线")
            QMessageBox.warning(self, "错误", "请先规划路线")
            return

        # 生成默认文件名
        start_name = self.start_name if self.start_name else "起点"
        end_name = self.end_name if self.end_name else "终点"
        transport_mode = self.transport_combo.currentText()
        start_datetime = self.start_time_edit.dateTime()
        start_time_str = start_datetime.toString("yyyyMMdd_hhmm")

        # 格式化途径时间（小时和分钟）
        duration_hours = self.estimated_duration_seconds // 3600
        duration_minutes = (self.estimated_duration_seconds % 3600) // 60
        duration_str = f"{duration_hours}小时{duration_minutes}分钟"

        # 生成默认文件名
        default_filename = f"{start_name}_{end_name}_{transport_mode}_{start_time_str}_{duration_str}.gpx"
        self.logger.debug(f"生成默认文件名: {default_filename}")

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存GPX文件", default_filename, "GPX文件 (*.gpx);;所有文件 (*.*)"
        )

        if not file_path:
            self.logger.info("GPX导出取消：用户未选择文件路径")
            return

        self.logger.info(f"开始导出GPX文件: {file_path}")
        self.logger.debug(f"路线点数量: {len(self.route_points)}")
        self.logger.debug(f"起始时间: {start_datetime.toString()}")

        try:
            self.progress_bar.setMaximum(0)
            self.progress_bar.setMinimum(0)
            self.progress_bar.setValue(0)
            QApplication.processEvents()

            self.search_results_list.clear()
            self.search_results_list.addItem("正在导出GPX文件...")

            self.logger.debug("正在调用GPX导出服务...")
            start_datetime = self.start_time_edit.dateTime()

            self.progress_bar.setMaximum(100)
            self.progress_bar.setMinimum(0)
            self.progress_bar.setValue(50)
            QApplication.processEvents()

            self.logger.debug("执行GPX导出操作...")
            success = self.gpx_service.export_to_gpx(
                self.route_points, start_datetime, file_path
            )

            self.progress_bar.setMaximum(100)
            self.progress_bar.setMinimum(0)
            self.progress_bar.setValue(100)
            QApplication.processEvents()

            if success:
                self.logger.info("GPX文件导出成功")
                self.search_results_list.clear()
                self.search_results_list.addItem("导出成功！")
                self.search_results_list.addItem(f"文件: {file_path}")
                QMessageBox.information(self, "成功", f"GPX文件已导出到: {file_path}")
            else:
                self.logger.warning("GPX文件导出失败")
                self.search_results_list.clear()
                self.search_results_list.addItem("导出失败")
                QMessageBox.warning(self, "错误", "导出GPX文件失败")

        except Exception as e:
            self.logger.exception(f"导出GPX文件出错: {str(e)}")
            self.progress_bar.setMaximum(100)
            self.progress_bar.setMinimum(0)
            self.progress_bar.setValue(100)
            QApplication.processEvents()
            self.search_results_list.clear()
            self.search_results_list.addItem("导出出错")
            self.search_results_list.addItem(f"错误信息: {str(e)}")
            QMessageBox.warning(self, "错误", f"导出GPX文件出错: {str(e)}")
        
        self.logger.info("GPX导出流程完成")
        self.logger.info("=" * 80)

    # ========== 时间计算相关方法 ==========

    def show_date_panel(self, time_type):
        """显示日期选择面板

        Args:
            time_type: "start"，表示起始时间
        """
        # 自动关闭已打开的时间选择面板
        if self.time_panel.isVisible():
            self.time_panel.hide()

        self.time_type = time_type
        # 连接日期选择信号
        try:
            self.date_panel.date_selected.disconnect()
        except TypeError:
            pass  # 没有连接时忽略错误
        self.date_panel.date_selected.connect(self.on_date_selected)

        # 设置当前选中的日期（只处理起始时间）
        current_date = self.start_time_edit.dateTime().date()

        # 获取日志面板的全局位置和大小
        log_rect = self.log_panel.rect()
        log_pos = self.log_panel.mapToGlobal(log_rect.topLeft())
        log_size = self.log_panel.size()

        self.date_panel.show_panel(current_date, log_pos, 0, log_size)

    def on_date_selected(self, selected_date):
        """日期选择回调

        Args:
            selected_date: 选择的日期（datetime对象）
        """
        from PyQt5.QtCore import QDateTime, QTime

        # 只处理起始时间
        if hasattr(self, 'time_type') and self.time_type == "start":
            # 更新起始日期
            current_time = self.start_time_edit.dateTime().time()
            new_datetime = QDateTime(
                selected_date.year, selected_date.month, selected_date.day,
                current_time.hour(), current_time.minute()
            )
            self.start_time_edit.setDateTime(new_datetime)

            # 自动计算结束时间
            self.calculate_times()

    def show_time_panel(self, time_type):
        """显示时间选择面板

        Args:
            time_type: "start"，表示起始时间
        """
        # 自动关闭已打开的日期选择面板
        if self.date_panel.isVisible():
            self.date_panel.hide()

        self.time_type = time_type
        # 连接时间选择信号
        try:
            self.time_panel.time_selected.disconnect()
        except TypeError:
            pass  # 没有连接时忽略错误
        self.time_panel.time_selected.connect(self.on_time_selected)

        # 设置当前选中的时间（只处理起始时间）
        current_time = self.start_time_edit.dateTime().time()

        # 获取日志面板的全局位置和大小
        log_rect = self.log_panel.rect()
        log_pos = self.log_panel.mapToGlobal(log_rect.topLeft())
        log_size = self.log_panel.size()

        self.time_panel.show_panel(current_time, log_pos, 0, log_size)

    def on_time_selected(self, selected_time):
        """时间选择回调

        Args:
            selected_time: 选择的时间（datetime对象）
        """
        from PyQt5.QtCore import QDateTime, QTime

        # 只处理起始时间
        if hasattr(self, 'time_type') and self.time_type == "start":
            # 更新起始时间
            current_date = self.start_time_edit.dateTime().date()
            new_datetime = QDateTime(
                current_date.year(), current_date.month(), current_date.day(),
                selected_time.hour, selected_time.minute
            )
            self.start_time_edit.setDateTime(new_datetime)

            # 自动计算结束时间
            self.calculate_times()

    def calculate_times(self):
        """计算时间（根据起始时间和经历时间自动计算结束时间）"""
        from PyQt5.QtCore import QDateTime

        try:
            # 获取起始时间
            start_datetime = self.start_time_edit.dateTime()

            # 从文本框获取经历小时数
            duration_text = self.duration_time_edit.text().strip()
            if not duration_text:
                duration_hours = 1  # 默认1小时
            else:
                try:
                    duration_hours = float(duration_text)
                    if duration_hours < 0:
                        duration_hours = 0
                except ValueError:
                    duration_hours = 1  # 无效输入时默认1小时

            # 计算结束时间（支持小数小时）
            duration_seconds = int(duration_hours * 3600)
            end_datetime = start_datetime.addSecs(duration_seconds)

            # 更新结束时间显示
            self.end_time_edit.setDateTime(end_datetime)

        except Exception as e:
            self.logger.warning(f"计算时间时出错: {str(e)}")

    # ========== 定位相关方法 ==========

    def get_current_location(self):
        """获取当前位置（优先使用：Windows原生 → 高德在线定位 → 高德IP定位 → 公共IP定位）"""
        self.logger.info("=" * 80)
        self.logger.info("开始执行定位流程")
        self.logger.info("=" * 80)
        
        # 检查地图源是否已设置
        map_source = map_config.get_map_source()
        if not map_source:
            self.logger.warning("定位失败：未设置地图数据源")
            QMessageBox.warning(self, "警告", "请先在地图配置中设置地图数据源")
            return
        
        self.logger.info("开始定位流程")

        try:
            self.progress_bar.setMaximum(0)
            self.progress_bar.setMinimum(0)
            self.progress_bar.setValue(0)
            QApplication.processEvents()

            self.search_results_list.clear()
            self.search_results_list.addItem("正在定位...")

            self.logger.debug(f"Windows位置服务可用: {self.windows_location_service.is_available()}")

            if self.windows_location_service.is_available():
                self.search_results_list.addItem("正在使用Windows原生定位...")
                self.logger.info("尝试使用Windows原生位置服务...")

                location_info = self.windows_location_service.get_location(timeout=10)

                if location_info:
                    self.handle_native_location_success(location_info)
                    return

            self.search_results_list.clear()
            self.search_results_list.addItem("Windows定位不可用")

            if map_config.is_gaode_configured():
                self.search_results_list.addItem("正在使用高德地图在线定位...")
                self.logger.info("尝试使用高德地图在线定位...")

                location_info = self.get_gaode_online_location()

                if location_info:
                    self.handle_gaode_online_location_success(location_info)
                    return

                self.search_results_list.clear()
                self.search_results_list.addItem("高德在线定位不可用")
                self.search_results_list.addItem("正在使用高德地图IP定位...")
                self.logger.warning("高德地图在线定位失败，尝试高德IP定位")

                def gaode_ip_log(level: str, message: str):
                    level_map = {
                        "DEBUG": self.logger.debug,
                        "INFO": self.logger.info,
                        "WARNING": self.logger.warning,
                        "ERROR": self.logger.error,
                        "CRITICAL": self.logger.critical
                    }
                    log_func = level_map.get(level, self.logger.info)
                    log_func(f"[高德IP定位] {message}")

                location_info = LocationHelper.get_ip_location(
                    use_gaode=True,
                    api_key=map_config.get_api_key() if map_config.is_gaode_configured() else None,
                    logger=gaode_ip_log
                )

                if location_info:
                    self.progress_bar.setMaximum(100)
                    self.progress_bar.setMinimum(0)
                    self.progress_bar.setValue(100)
                    QApplication.processEvents()
                    self.handle_ip_location_success(location_info, source="高德IP定位")
                    return

                self.search_results_list.clear()
                self.search_results_list.addItem("高德IP定位不可用")
                self.logger.warning("高德IP定位失败，尝试公共IP定位")

            self.search_results_list.addItem("正在使用公共IP定位...")

            self.logger.warning("所有定位方式不可使用，使用公共IP定位作为备选方案")

            def ip_log(level: str, message: str):
                level_map = {
                    "DEBUG": self.logger.debug,
                    "INFO": self.logger.info,
                    "WARNING": self.logger.warning,
                    "ERROR": self.logger.error,
                    "CRITICAL": self.logger.critical
                }
                log_func = level_map.get(level, self.logger.info)
                log_func(f"[公共IP定位] {message}")

            location_info = LocationHelper.get_ip_location(logger=ip_log)

            self.progress_bar.setMaximum(100)
            self.progress_bar.setMinimum(0)
            self.progress_bar.setValue(100)
            QApplication.processEvents()

            if location_info:
                self.handle_ip_location_success(location_info, source="公共IP定位")
            else:
                self.search_results_list.clear()
                self.search_results_list.addItem("定位失败")
                self.search_results_list.addItem("无法获取您的位置信息")
                self.logger.error("定位失败：无法获取您的位置信息")
                QMessageBox.warning(self, "定位失败", "无法获取您的位置信息\n\n建议：\n1. 检查网络连接\n2. 确认Windows位置服务已开启（如适用）")

        except Exception as e:
            self.logger.exception(f"定位流程异常: {str(e)}")

            self.progress_bar.setMaximum(100)
            self.progress_bar.setMinimum(0)
            self.progress_bar.setValue(100)
            QApplication.processEvents()

            self.search_results_list.clear()
            self.search_results_list.addItem("定位出错")
            self.search_results_list.addItem(f"错误信息: {str(e)}")
            QMessageBox.warning(self, "错误", f"定位出错: {str(e)}\n\n请检查网络连接")
        
        self.logger.info("定位流程完成")
        self.logger.info("=" * 80)

    def get_gaode_online_location(self) -> Optional[dict]:
        """
        使用浏览器Geolocation API + 高德逆地理编码获取当前位置

        Returns:
            dict: 定位信息 {'lat': float, 'lon': float, 'city': str, 'source': str}
        """
        def log_cb(level, message):
            if self.logger:
                level_map = {
                    "DEBUG": self.logger.debug,
                    "INFO": self.logger.info,
                    "WARNING": self.logger.warning,
                    "ERROR": self.logger.error,
                    "CRITICAL": self.logger.critical
                }
                log_func = level_map.get(level, self.logger.info)
                log_func(message)

        if not map_config.is_gaode_configured():
            log_cb("WARNING", "高德API未配置，无法使用在线定位")
            return None

        log_cb("DEBUG", "正在通过浏览器Geolocation API获取位置...")

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
            log_cb("DEBUG", "已发起浏览器定位请求")
        else:
            log_cb("WARNING", "地图视图未初始化，无法执行定位")

        return None

    def _on_geolocation_success(self, lat, lon, accuracy):
        """处理浏览器定位成功信号"""
        self.logger.info(f"浏览器定位成功: {lat}, {lon}, 精度: {accuracy}m")

        location_info = {
            'lat': lat,
            'lon': lon,
            'accuracy': accuracy
        }
        self.handle_gaode_online_location_success(location_info)

    def _on_geolocation_error(self, error_msg):
        """处理浏览器定位失败信号"""
        self.logger.warning(f"浏览器定位失败: {error_msg}")
        self.handle_gaode_location_error({'code': -1, 'message': error_msg})

    def handle_gaode_online_location_success(self, location_info):
        """处理高德在线定位成功（浏览器Geolocation + 高德逆地理编码）"""
        self.logger.info("高德在线定位成功")

        lat = location_info['lat']
        lon = location_info['lon']
        accuracy = location_info.get('accuracy', 0)

        self.logger.debug(f"纬度: {lat}, 经度: {lon}, 精度: {accuracy}m")

        if map_config.is_gaode_configured():
            self.logger.debug("正在进行逆地理编码...")
            address_info = self.gaode_geocoding_service.reverse_geocode(lat, lon)

            if address_info:
                city = address_info.get('city', '')
                full_address = address_info.get('full_address', '')

                self.logger.debug(f"逆地理编码成功: {full_address}")

                self.progress_bar.setMaximum(100)
                self.progress_bar.setMinimum(0)
                self.progress_bar.setValue(100)
                QApplication.processEvents()

                self.search_results_list.clear()
                self.search_results_list.addItem("定位成功！")
                self.search_results_list.addItem("定位方式: 高德地图在线定位（精准定位）")
                self.search_results_list.addItem(f"位置: {city}")

                self.current_location = (lat, lon)

                popup_text = f"我的位置\n{full_address}\n定位方式: 高德在线定位\n精度: 约{accuracy:.0f}米"
                MapRenderer.add_marker(self.map_view.current_map, [lat, lon], popup_text, 'green', 'user')
                self.map_view.current_map.fit_bounds([[lat, lon], [lat, lon]])

                self.show_location_on_map(lat, lon, city, full_address)
                return

            self.logger.warning("逆地理编码失败，仅显示坐标")

        self.progress_bar.setMaximum(100)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(100)
        QApplication.processEvents()

        self.search_results_list.clear()
        self.search_results_list.addItem("定位成功！")
        self.search_results_list.addItem("定位方式: 浏览器Geolocation API")
        self.search_results_list.addItem(f"坐标: {lat:.4f}, {lon:.4f}")

        self.current_location = (lat, lon)

        popup_text = f"我的位置\n坐标: {lat:.4f}, {lon:.4f}\n定位方式: 浏览器定位\n精度: 约{accuracy:.0f}米"
        self.show_location_on_map(lat, lon, "", popup_text)

    def handle_gaode_location_error(self, error):
        """处理高德在线定位失败"""
        error_code = error.get('code', -1)
        error_msg = error.get('message', '未知错误')

        self.logger.warning(f"高德在线定位失败: {error_msg} (代码: {error_code})")

        self.search_results_list.clear()
        self.search_results_list.addItem("在线定位失败")

        if error_code in GEOLOCATION_ERROR_MESSAGES:
            error_text = GEOLOCATION_ERROR_MESSAGES[error_code]
            self.search_results_list.addItem(f"原因: {error_text}")
            self.logger.warning(error_text)
        else:
            self.search_results_list.addItem(f"原因: {error_msg}")

    def handle_gaode_location_success(self, location_info):
        """处理高德地图定位成功"""
        self.logger.info("高德地图定位成功")

        lat = location_info['lat']
        lon = location_info['lon']
        city = location_info.get('city', '')
        province = location_info.get('province', '')

        self.logger.debug(f"纬度: {lat}, 经度: {lon}, 城市: {city}")

        try:
            if map_config.is_gaode_configured():
                address_info = self.gaode_geocoding_service.reverse_geocode(lat, lon)
            else:
                address_info = None

            self.current_location = (lat, lon)

            self.progress_bar.setMaximum(100)
            self.progress_bar.setMinimum(0)
            self.progress_bar.setValue(100)
            QApplication.processEvents()

            self.search_results_list.clear()
            self.search_results_list.addItem("定位成功！")
            self.search_results_list.addItem("定位方式: 高德地图IP定位")

            full_address = f"{province}{city}" if province and city else (city or province)
            if full_address:
                self.search_results_list.addItem(f"位置: {full_address}")
                popup_text = f"我的位置\n{full_address}\n定位方式: 高德地图IP定位"
            else:
                popup_text = f"我的位置\n坐标: {lat:.4f}, {lon:.4f}\n定位方式: 高德地图IP定位"

            self.search_results_list.addItem(f"坐标: {lat:.6f}, {lon:.6f}")

            self.logger.info(f"位置信息: {full_address}")
            self.show_location_on_map(lat, lon, popup_text)

        except Exception as e:
            self.logger.exception(f"高德定位处理异常: {str(e)}")
            self.show_location_on_map(lat, lon, f"我的位置\n坐标: {lat:.4f}, {lon:.4f}")

    def handle_native_location_success(self, location_info):
        """处理Windows原生定位成功"""
        self.logger.info("Windows原生定位成功")

        lat = location_info['latitude']
        lon = location_info['longitude']
        accuracy = location_info.get('accuracy', 0)

        self.logger.debug(f"纬度: {lat}, 经度: {lon}, 精度: {accuracy}米")

        try:
            if map_config.is_gaode_configured():
                address_info = self.gaode_geocoding_service.reverse_geocode(lat, lon)
            else:
                address_info = None
                self.logger.warning("高德地图API未配置，无法获取地址信息")

            self.current_location = (lat, lon)

            self.progress_bar.setMaximum(100)
            self.progress_bar.setMinimum(0)
            self.progress_bar.setValue(100)
            QApplication.processEvents()

            self.search_results_list.clear()
            self.search_results_list.addItem("定位成功！")
            self.search_results_list.addItem("定位方式: Windows原生定位（高精度）")

            if address_info:
                city = address_info.get('city', '')
                country = address_info.get('country', '')
                self.search_results_list.addItem(f"位置: {city}, {country}")
                popup_text = f"我的位置\n{city}, {country}\n定位方式: Windows原生定位\n精度: 约{accuracy:.0f}米"
            else:
                popup_text = f"我的位置\n坐标: {lat:.4f}, {lon:.4f}\n定位方式: Windows原生定位\n精度: 约{accuracy:.0f}米"

            self.search_results_list.addItem(f"坐标: {lat:.6f}, {lon:.6f}")
            self.search_results_list.addItem(f"精度: 约{accuracy:.0f}米")

            self.logger.info(f"位置信息: {address_info}")
            self.show_location_on_map(lat, lon, popup_text)

        except Exception as e:
            self.logger.exception(f"处理异常: {str(e)}")

    def handle_ip_location_success(self, location_info, source: str = "IP地址定位"):
        """处理IP定位成功"""
        self.logger.info(f"{source}成功")

        lat = location_info.get('lat')
        lon = location_info.get('lon')
        city = location_info.get('city', '')
        country = location_info.get('country', '')
        region = location_info.get('region', '')
        isp = location_info.get('isp', '')
        source_key = location_info.get('source', '')

        if lat is None or lon is None:
            self.search_results_list.clear()
            self.search_results_list.addItem("定位成功！")
            self.search_results_list.addItem(f"定位方式: {source}（仅城市级别）")
            self.search_results_list.addItem(f"位置: {city}")

            if source_key == 'gaode_ip_city':
                self.logger.info(f"高德IP定位成功（城市级别）: {city}")
                QMessageBox.information(self, "定位成功", f"定位成功！\n\n位置: {city}\n定位方式: {source}（仅城市级别）")
            return

        self.logger.debug(f"纬度: {lat}, 经度: {lon}")
        self.logger.info(f"位置: {city}, {region}, {country}")

        self.current_location = (lat, lon)

        self.search_results_list.clear()
        self.search_results_list.addItem("定位成功！")

        if source_key == 'gaode_ip':
            self.search_results_list.addItem("定位方式: 高德IP定位（城市级精度）")
        else:
            self.search_results_list.addItem(f"定位方式: {source}（城市级精度）")

        location_text = ", ".join(filter(None, [city, region, country]))
        self.search_results_list.addItem(f"位置: {location_text}")
        self.search_results_list.addItem(f"坐标: {lat:.4f}, {lon:.4f}")

        if isp:
            self.search_results_list.addItem(f"运营商: {isp}")
            popup_text = f"我的位置\n{location_text}\n定位方式: {source}\n运营商: {isp}"
        else:
            popup_text = f"我的位置\n{location_text}\n定位方式: {source}"

        self.show_location_on_map(lat, lon, popup_text)

    def show_location_on_map(self, lat, lon, popup_text):
        """在地图上显示定位"""
        map_source = map_config.get_map_source()
        m = MapRenderer.create_base_map([lat, lon], zoom_start=13, map_source=map_source)

        MapRenderer.add_marker(
            m, [lat, lon], popup_text,
            color=COLOR_ORANGE, icon=ICON_WARNING
        )

        # 添加已选择的点
        self._add_selected_points_to_map(m)

        # 添加路线
        if self.route_points:
            MapRenderer.add_route(m, self.route_points)

        url = MapRenderer.save_and_get_url(m)
        self.map_view.setUrl(url)

    def test_geolocation(self):
        """测试定位功能"""
        self.logger.info("开始测试定位功能")
        self.logger.debug("="*50)

        self.search_results_list.clear()
        self.search_results_list.addItem("=== 定位功能测试 ===")
        self.search_results_list.addItem("1. 检查定位处理器...")
        self.search_results_list.addItem(
            f"   状态: {'✓ 已初始化' if self.geolocation_handler else '✗ 未初始化'}"
        )
        self.logger.debug(f"定位处理器状态: {self.geolocation_handler is not None}")

        self.search_results_list.addItem("2. 检查地图视图...")
        self.search_results_list.addItem(
            f"   状态: {'✓ 已创建' if self.map_view else '✗ 未创建'}"
        )
        self.logger.debug(f"地图视图状态: {self.map_view is not None}")

        self.search_results_list.addItem("3. 检查当前位置...")
        self.search_results_list.addItem(
            f"   状态: {'✓ 已定位' if self.current_location else '✗ 未定位'}"
        )
        if self.current_location:
            self.search_results_list.addItem(
                f"   坐标: {self.current_location[0]:.4f}, {self.current_location[1]:.4f}"
            )
            self.logger.debug(f"当前位置: {self.current_location[0]:.4f}, {self.current_location[1]:.4f}")
        else:
            self.logger.debug("当前位置: 未定位")

        self.search_results_list.addItem("4. 测试信号连接...")
        try:
            self.geolocation_handler.test_geolocation()
            self.search_results_list.addItem("   状态: ✓ 信号连接正常")
            self.logger.debug("测试结果: 信号连接正常")
        except Exception as e:
            self.search_results_list.addItem(f"   状态: ✗ 信号连接失败: {e}")
            self.logger.error(f"信号连接测试失败: {e}")

        self.search_results_list.addItem("=== 测试完成 ===")
        self.logger.info("定位功能测试完成")
        self.logger.debug("="*50)

    def show_about_dialog(self):
        """显示关于对话框"""
        dialog = AboutDialog(self)
        dialog.exec_()

    def closeEvent(self, event):
        """关闭事件"""
        event.accept()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = GpxStudio()
    window.show()
    sys.exit(app.exec_())

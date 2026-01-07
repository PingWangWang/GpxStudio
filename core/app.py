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
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from handlers.geolocation import GeolocationHandler
from handlers.webengine import ConsoleWebEnginePage
from services.gaode_geocoding import GaodeGeocodingService
from services.gaode_routing import GaodeRoutingService
from services.gpx_export import GpxExportService
from services.windows_location import WindowsLocationService
from services.gaode_config import gaode_config
from utils.map_renderer import MapRenderer
from utils.location_helper import LocationHelper
from ui.styles import UIStyles
from ui.panels import PanelFactory
from ui.log_panel import LogPanel, setup_logger
from ui.gaode_config_dialog import GaodeConfigDialog


class GpxStudio(QMainWindow):
    """GPX Studio 主应用窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("GPX Studio - 路线规划工具")
        self.resize(1400, 800)

        # 窗口居中
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        window_geometry = self.frameGeometry()
        center_point = screen_geometry.center()
        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())

        # 初始化服务
        self.gaode_geocoding_service = GaodeGeocodingService(
            api_key=gaode_config.get_api_key(),
            security_key=gaode_config.get_security_key(),
            logger=self._log_to_geocoding
        )
        self.gaode_routing_service = GaodeRoutingService(
            api_key=gaode_config.get_api_key(),
            security_key=gaode_config.get_security_key(),
            logger=self._log_to_routing
        )
        self.gpx_service = GpxExportService(logger=self._log_to_gpx)

        # 数据状态
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
        self.last_selected_coords = None
        self.last_selected_level = None
        self.last_selected_type = None
        self.last_selected_from_search = False

        # 定位处理器
        self.geolocation_handler = GeolocationHandler()

        self.geolocation_handler.geolocation_success.connect(self._on_geolocation_success)
        self.geolocation_handler.geolocation_error.connect(self._on_geolocation_error)

        # 初始化UI
        self.init_ui()

        # 初始化日志系统
        self.logger = setup_logger(self.log_panel, "GpxStudio")

        # 初始化Windows位置服务（需要logger）
        self.windows_location_service = WindowsLocationService(logger=self._log_to_service)

        self.logger.info("程序启动完成")

    def show_gaode_config(self):
        """显示高德地图配置对话框"""
        dialog = GaodeConfigDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            api_key = gaode_config.get_api_key()
            security_key = gaode_config.get_security_key()
            self.gaode_geocoding_service.api_key = api_key
            self.gaode_geocoding_service.security_key = security_key
            self.gaode_routing_service.api_key = api_key
            self.gaode_routing_service.security_key = security_key
            self.logger.info("高德地图配置已更新")

    def _log_to_service(self, level: str, message: str):
        """将日志转发到WindowsLocationService"""
        level_map = {
            "DEBUG": self.logger.debug,
            "INFO": self.logger.info,
            "WARNING": self.logger.warning,
            "ERROR": self.logger.error,
            "CRITICAL": self.logger.critical
        }
        log_func = level_map.get(level, self.logger.info)
        log_func(f"[Windows定位] {message}")

    def _log_to_geocoding(self, level: str, message: str):
        """将日志转发到GeocodingService"""
        level_map = {
            "DEBUG": self.logger.debug,
            "INFO": self.logger.info,
            "WARNING": self.logger.warning,
            "ERROR": self.logger.error,
            "CRITICAL": self.logger.critical
        }
        log_func = level_map.get(level, self.logger.info)
        log_func(f"[地理编码] {message}")

    def _log_to_routing(self, level: str, message: str):
        """将日志转发到RoutingService"""
        level_map = {
            "DEBUG": self.logger.debug,
            "INFO": self.logger.info,
            "WARNING": self.logger.warning,
            "ERROR": self.logger.error,
            "CRITICAL": self.logger.critical
        }
        log_func = level_map.get(level, self.logger.info)
        log_func(f"[路线规划] {message}")

    def _log_to_gpx(self, level: str, message: str):
        """将日志转发到GpxExportService"""
        level_map = {
            "DEBUG": self.logger.debug,
            "INFO": self.logger.info,
            "WARNING": self.logger.warning,
            "ERROR": self.logger.error,
            "CRITICAL": self.logger.critical
        }
        log_func = level_map.get(level, self.logger.info)
        log_func(f"[GPX导出] {message}")

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
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 6)

        # 设置初始尺寸分配，让地图列更宽
        splitter.setSizes([300, 250, 1000])

        main_layout.addWidget(splitter)

        # 延迟加载初始地图，确保UI完全初始化后再显示地图
        QTimer.singleShot(500, self.show_initial_map)

    def create_left_panel(self):
        """创建左侧控制面板"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # 顶部按钮布局
        top_button_layout = QHBoxLayout()

        locate_button = QPushButton("📍 定位")
        locate_button.clicked.connect(self.get_current_location)
        locate_button.setStyleSheet(UIStyles.LOCATE_BUTTON)
        top_button_layout.addWidget(locate_button)

        config_button = QPushButton("⚙️ 地图配置")
        config_button.clicked.connect(self.show_gaode_config)
        config_button.setStyleSheet(UIStyles.LOCATE_BUTTON)
        top_button_layout.addWidget(config_button)

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

        # 进度条
        self.progress_bar = PanelFactory.create_progress_bar()
        layout.addWidget(self.progress_bar)

        return middle_widget

    def create_right_panel(self):
        """创建右侧地图面板"""
        right_widget = QWidget()
        layout = QVBoxLayout(right_widget)

        # 创建地图视图
        self.map_view = QWebEngineView()
        web_page = ConsoleWebEnginePage()
        web_page.set_geolocation_handler(self.geolocation_handler)
        self.map_view.setPage(web_page)

        # 设置User Agent
        profile = QWebEngineProfile.defaultProfile()
        profile.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        layout.addWidget(self.map_view)

        # 注意：初始地图现在通过定时器延迟加载，确保UI完全初始化

        return right_widget

    def show_initial_map(self):
        """显示初始地图（北京中心）"""
        m = MapRenderer.create_base_map([39.9042, 116.4074], zoom_start=10)
        url = MapRenderer.save_and_get_url(m)
        self.map_view.setUrl(url)

    # ========== 搜索相关方法 ==========

    def search_location(self, location_type):
        """搜索地点（起点/终点）"""
        search_text = getattr(self, f"{location_type}_input").text()

        if not search_text:
            return

        self.search_results_list.clear()
        self.progress_bar.setMaximum(0)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(0)
        QApplication.processEvents()

        self._perform_search(search_text, location_type)

    def search_waypoint(self):
        """搜索途径点"""
        search_text = self.waypoint_input.text()

        if not search_text:
            return

        self.search_results_list.clear()
        self.progress_bar.setMaximum(0)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(0)
        QApplication.processEvents()

        self._perform_search(search_text, "waypoint")

    def _perform_search(self, search_text, location_type):
        """执行搜索"""
        if gaode_config.is_configured and gaode_config.get_api_key():
            locations = self.gaode_geocoding_service.search_location(search_text)
        else:
            locations = []
            self.logger.warning("高德地图API未配置，无法进行地点搜索。请先配置高德地图API密钥。")

        self.progress_bar.setMaximum(100)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(100)
        QApplication.processEvents()

        if locations:
            self.search_results = locations
            self.searching_for = location_type

            titles = {
                "start": "起点搜索列表",
                "end": "终点搜索列表",
                "waypoint": "途径点搜索列表"
            }

            self.search_results_title.setText(titles.get(location_type, "搜索结果"))

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

        m = MapRenderer.create_base_map([center_lat, center_lon], zoom_start=12)

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

        m = MapRenderer.create_base_map([center_lat, center_lon], zoom_start=zoom_level)

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
                        color='purple', icon='star'
                    )

        url = MapRenderer.save_and_get_url(m)
        self.map_view.setUrl(url)

    def _add_selected_points_to_map(self, map_obj):
        """添加已选择的点到地图"""
        start_name = self.start_name if self.start_name else "起点"
        if self.start_coords:
            MapRenderer.add_marker(
                map_obj, self.start_coords, start_name,
                color='green', icon='play'
            )

        for i, (waypoint, name) in enumerate(zip(self.waypoints_coords, self.waypoints_names)):
            display_name = name if name else f"途径点 {i + 1}"
            MapRenderer.add_marker(
                map_obj, waypoint, display_name,
                color='blue', icon='info-sign'
            )

        end_name = self.end_name if self.end_name else "终点"
        if self.end_coords:
            MapRenderer.add_marker(
                map_obj, self.end_coords, end_name,
                color='red', icon='stop'
            )

    # ========== 路线规划相关方法 ==========

    def plan_route(self):
        """规划路线"""
        if not self.start_coords or not self.end_coords:
            QMessageBox.warning(self, "错误", "请先设置起点和终点")
            return

        transport_mode = self.transport_combo.currentText()
        points = [self.start_coords] + self.waypoints_coords + [self.end_coords]

        self.logger.info(f"开始规划路线，方式: {transport_mode}")
        self.logger.debug(f"起点: {self.start_coords}, 终点: {self.end_coords}")

        try:
            self.progress_bar.setMaximum(0)
            self.progress_bar.setMinimum(0)
            self.progress_bar.setValue(0)
            QApplication.processEvents()

            self.search_results_list.clear()
            self.search_results_list.addItem("正在规划路线...")
            self.search_results_list.addItem(f"方式: {transport_mode}")

            self.logger.debug("正在调用路线规划服务...")
            if gaode_config.is_configured and gaode_config.get_api_key():
                self.route_points, estimated_duration = self.gaode_routing_service.plan_route(points, transport_mode)

                from datetime import datetime
                current_time = datetime.now()
                current_time_zero_sec = current_time.replace(second=0)
                self.start_time_edit.setTime(QTime(current_time.hour, current_time.minute))

                duration_hours = estimated_duration // 3600
                duration_minutes = (estimated_duration % 3600) // 60
                self.duration_time_edit.setTime(QTime(duration_hours, duration_minutes))

                end_time = current_time_zero_sec.timestamp() + estimated_duration
                end_datetime = datetime.fromtimestamp(end_time)
                end_hour = end_datetime.hour
                end_minute = end_datetime.minute
                self.end_time_edit.setTime(QTime(end_hour, end_minute))

                self.search_results_list.addItem(f"预估时间: {duration_hours}小时{duration_minutes}分钟")
            else:
                self.route_points = []
                self.logger.warning("高德地图API未配置，无法进行路线规划。请先配置高德地图API密钥。")

            self.progress_bar.setMaximum(100)
            self.progress_bar.setMinimum(0)
            self.progress_bar.setValue(100)
            QApplication.processEvents()

            if self.route_points:
                self.logger.info(f"路线规划成功，共 {len(self.route_points)} 个点")
                self.search_results_list.clear()
                self.search_results_list.addItem("路线规划成功！")
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

        min_lat = min(p[0] for p in all_coords)
        max_lat = max(p[0] for p in all_coords)
        min_lon = min(p[1] for p in all_coords)
        max_lon = max(p[1] for p in all_coords)

        lat_diff = max_lat - min_lat
        lon_diff = max_lon - min_lon
        max_diff = max(lat_diff, lon_diff)

        if max_diff < 0.01:
            initial_zoom = 18
        elif max_diff < 0.05:
            initial_zoom = 17
        elif max_diff < 0.1:
            initial_zoom = 16
        elif max_diff < 0.5:
            initial_zoom = 15
        elif max_diff < 1:
            initial_zoom = 12
        elif max_diff < 3:
            initial_zoom = 10
        elif max_diff < 5:
            initial_zoom = 8
        elif max_diff < 10:
            initial_zoom = 6
        else:
            initial_zoom = 4

        center_lat = sum(p[0] for p in all_coords) / len(all_coords)
        center_lon = sum(p[1] for p in all_coords) / len(all_coords)

        m = MapRenderer.create_base_map([center_lat, center_lon], zoom_start=initial_zoom)

        self._add_selected_points_to_map(m)

        MapRenderer.add_route(m, self.route_points)

        MapRenderer.fit_bounds(m, all_coords)

        url = MapRenderer.save_and_get_url(m)
        self.map_view.setUrl(url)

    # ========== GPX导出相关方法 ==========

    def export_gpx(self):
        """导出GPX文件"""
        if not self.route_points:
            QMessageBox.warning(self, "错误", "请先规划路线")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存GPX文件", "", "GPX文件 (*.gpx);;所有文件 (*.*)"
        )

        if not file_path:
            return

        self.logger.info(f"开始导出GPX文件: {file_path}")

        try:
            self.progress_bar.setMaximum(0)
            self.progress_bar.setMinimum(0)
            self.progress_bar.setValue(0)
            QApplication.processEvents()

            self.search_results_list.clear()
            self.search_results_list.addItem("正在导出GPX文件...")

            self.logger.debug("正在调用GPX导出服务...")
            start_time = self.start_time_edit.time()

            self.progress_bar.setMaximum(100)
            self.progress_bar.setMinimum(0)
            self.progress_bar.setValue(50)
            QApplication.processEvents()

            success = self.gpx_service.export_to_gpx(
                self.route_points, start_time, file_path
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

    # ========== 时间计算相关方法 ==========

    def calculate_times(self):
        """计算时间（起始/经历/结束时间联动）"""
        from PyQt5.QtCore import QTime

        sender = self.sender()

        if sender == self.start_time_edit:
            start_time = self.start_time_edit.time()
            duration_time = self.duration_time_edit.time()

            end_time = QTime(start_time.hour(), start_time.minute())
            end_time = end_time.addSecs(
                duration_time.hour() * 3600 + duration_time.minute() * 60
            )

            self.end_time_edit.blockSignals(True)
            self.end_time_edit.setTime(end_time)
            self.end_time_edit.blockSignals(False)

        elif sender == self.duration_time_edit:
            start_time = self.start_time_edit.time()
            duration_time = self.duration_time_edit.time()

            end_time = QTime(start_time.hour(), start_time.minute())
            end_time = end_time.addSecs(
                duration_time.hour() * 3600 + duration_time.minute() * 60
            )

            self.end_time_edit.blockSignals(True)
            self.end_time_edit.setTime(end_time)
            self.end_time_edit.blockSignals(False)

        elif sender == self.end_time_edit:
            start_time = self.start_time_edit.time()
            end_time = self.end_time_edit.time()

            duration = start_time.secsTo(end_time)
            duration_hours = duration // 3600
            duration_minutes = (duration % 3600) // 60

            self.duration_time_edit.blockSignals(True)
            self.duration_time_edit.setTime(QTime(duration_hours, duration_minutes))
            self.duration_time_edit.blockSignals(False)

    # ========== 定位相关方法 ==========

    def get_current_location(self):
        """获取当前位置（优先使用：Windows原生 → 高德在线定位 → 高德IP定位 → 公共IP定位）"""
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

            if gaode_config.is_configured and gaode_config.get_api_key():
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
                    api_key=gaode_config.get_api_key() if gaode_config.is_configured else None,
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

        if not gaode_config.is_configured or not gaode_config.get_api_key():
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

        if gaode_config.is_configured and gaode_config.get_api_key():
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

        if error_code == 1:
            self.search_results_list.addItem("原因: 用户拒绝定位请求")
            self.logger.warning("用户拒绝了定位请求")
        elif error_code == 2:
            self.search_results_list.addItem("原因: 位置信息不可用")
            self.logger.warning("位置信息不可用")
        elif error_code == 3:
            self.search_results_list.addItem("原因: 定位请求超时")
            self.logger.warning("定位请求超时")
        elif error_code == -1:
            self.search_results_list.addItem("原因: 浏览器不支持定位")
            self.logger.warning("浏览器不支持Geolocation API")
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
            if gaode_config.is_configured and gaode_config.get_api_key():
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
            if gaode_config.is_configured and gaode_config.get_api_key():
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
        m = MapRenderer.create_base_map([lat, lon], zoom_start=13)

        MapRenderer.add_marker(
            m, [lat, lon], popup_text,
            color='orange', icon='star'
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


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = GpxStudio()
    window.show()
    sys.exit(app.exec_())

    def closeEvent(self, event):
        """关闭事件"""
        event.accept()

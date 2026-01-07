"""
GPX Studio 主应用窗口
整合所有模块，实现完整的路线规划功能
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QListWidget, QFileDialog,
                             QMessageBox, QSplitter, QListWidgetItem, QScrollArea,
                             QApplication)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile

import sys
import os
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from handlers.geolocation import GeolocationHandler
from handlers.webengine import ConsoleWebEnginePage
from services.geocoding import GeocodingService
from services.routing import RoutingService
from services.gpx_export import GpxExportService
from utils.map_renderer import MapRenderer
from utils.location_helper import LocationHelper
from ui.styles import UIStyles
from ui.panels import PanelFactory


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
        self.geocoding_service = GeocodingService()
        self.routing_service = RoutingService()
        self.gpx_service = GpxExportService()

        # 数据状态
        self.start_coords = None
        self.end_coords = None
        self.waypoints_coords = []
        self.current_route = None
        self.route_points = []
        self.current_location = None
        self.search_results = []
        self.searching_for = None

        # 定位处理器
        self.geolocation_handler = GeolocationHandler()
        self.geolocation_handler.geolocation_success.connect(self.handle_geolocation_success)
        self.geolocation_handler.geolocation_error.connect(
            lambda msg: self.fallback_to_ip_geolocation(msg)
        )

        # 初始化UI
        self.init_ui()

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

        # 定位按钮
        locate_button = QPushButton("📍 定位我的位置")
        locate_button.clicked.connect(self.get_current_location)
        locate_button.setStyleSheet(UIStyles.LOCATE_BUTTON)
        left_layout.addWidget(locate_button)

        # 测试按钮
        test_button = QPushButton("🧪 测试定位功能")
        test_button.clicked.connect(self.test_geolocation)
        test_button.setStyleSheet(UIStyles.TEST_BUTTON)
        left_layout.addWidget(test_button)

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

        layout.addStretch()

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
        locations = self.geocoding_service.search_location(search_text)

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
                item = QListWidgetItem(f"{i+1}. {location.address}")
                item.setData(Qt.UserRole, (location.latitude, location.longitude))
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
        """选择地点（起点/终点）"""
        coords = item.data(Qt.UserRole)

        if location_type == "start":
            self.start_coords = coords
            self.start_list.clear()
            self.start_list.addItem(f"起点: {coords[0]:.4f}, {coords[1]:.4f}")
        elif location_type == "end":
            self.end_coords = coords
            self.end_list.clear()
            self.end_list.addItem(f"终点: {coords[0]:.4f}, {coords[1]:.4f}")

        self.update_map_preview()

    def select_search_result(self, item):
        """从搜索结果中选择"""
        coords = item.data(Qt.UserRole)

        if self.searching_for == "start":
            self.start_coords = coords
            self.start_list.clear()
            self.start_list.addItem(f"起点: {coords[0]:.4f}, {coords[1]:.4f}")
        elif self.searching_for == "end":
            self.end_coords = coords
            self.end_list.clear()
            self.end_list.addItem(f"终点: {coords[0]:.4f}, {coords[1]:.4f}")
        elif self.searching_for == "waypoint":
            self.waypoints_coords.append(coords)
            waypoint_item = QListWidgetItem(
                f"途径点 {len(self.waypoints_coords)}: {coords[0]:.4f}, {coords[1]:.4f}"
            )
            waypoint_item.setData(Qt.UserRole, coords)
            self.waypoint_list.addItem(waypoint_item)

        self.update_map_preview()

    def clear_search_results(self):
        """清空搜索结果"""
        self.search_results = []
        self.searching_for = None
        self.search_results_list.clear()
        self.search_results_title.setText("搜索结果")

    def remove_waypoint(self):
        """删除途径点"""
        current_row = self.waypoint_list.currentRow()

        if current_row >= 0:
            self.waypoint_list.takeItem(current_row)
            self.waypoints_coords.pop(current_row)

            # 重新编号
            for i in range(self.waypoint_list.count()):
                item = self.waypoint_list.item(i)
                coords = item.data(Qt.UserRole)
                item.setText(f"途径点 {i + 1}: {coords[0]:.4f}, {coords[1]:.4f}")

            self.update_map_preview()

    # ========== 地图显示相关方法 ==========

    def show_search_results_on_map(self, locations, location_type):
        """在地图上显示搜索结果"""
        if not locations:
            return

        center_lat = sum(loc.latitude for loc in locations) / len(locations)
        center_lon = sum(loc.longitude for loc in locations) / len(locations)

        m = MapRenderer.create_base_map([center_lat, center_lon], zoom_start=12)

        # 搜索结果标记颜色
        colors = {"start": "green", "end": "red", "waypoint": "blue"}
        color = colors.get(location_type, "orange")

        # 添加搜索结果标记
        for i, location in enumerate(locations):
            MapRenderer.add_marker(
                m, [location.latitude, location.longitude],
                f"{i+1}. {location.address}",
                color=color, icon='info-sign'
            )

        # 添加已选择的点
        self._add_selected_points_to_map(m)

        # 添加路线
        if self.route_points:
            MapRenderer.add_route(m, self.route_points)

        url = MapRenderer.save_and_get_url(m)
        self.map_view.setUrl(url)

    def update_map_preview(self):
        """更新地图预览"""
        # 确定中心点
        center_lat, center_lon = 39.9042, 116.4074

        if self.start_coords:
            center_lat, center_lon = self.start_coords
        elif self.end_coords:
            center_lat, center_lon = self.end_coords
        elif self.waypoints_coords:
            center_lat, center_lon = self.waypoints_coords[0]

        m = MapRenderer.create_base_map([center_lat, center_lon], zoom_start=10)

        # 添加已选择的点
        self._add_selected_points_to_map(m)

        # 添加搜索结果
        if self.search_results and self.searching_for:
            colors = {"start": "green", "end": "red", "waypoint": "blue"}
            color = colors.get(self.searching_for, "orange")

            for i, location in enumerate(self.search_results):
                MapRenderer.add_marker(
                    m, [location.latitude, location.longitude],
                    f"{i+1}. {location.address}",
                    color=color, icon='info-sign'
                )

        url = MapRenderer.save_and_get_url(m)
        self.map_view.setUrl(url)

    def _add_selected_points_to_map(self, map_obj):
        """添加已选择的点到地图"""
        if self.start_coords:
            MapRenderer.add_marker(
                map_obj, self.start_coords, "起点",
                color='green', icon='play'
            )

        for i, waypoint in enumerate(self.waypoints_coords):
            MapRenderer.add_marker(
                map_obj, waypoint, f"途径点 {i + 1}",
                color='blue', icon='info-sign'
            )

        if self.end_coords:
            MapRenderer.add_marker(
                map_obj, self.end_coords, "终点",
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

        try:
            self.route_points = self.routing_service.plan_route(points, transport_mode)

            if self.route_points:
                self.show_route_on_map()
            else:
                QMessageBox.warning(self, "错误", "路线规划失败")

        except Exception as e:
            QMessageBox.warning(self, "错误", f"路线规划出错: {str(e)}")

    def show_route_on_map(self):
        """在地图上显示路线"""
        if not self.route_points:
            return

        valid_points = [p for p in self.route_points if p is not None]

        if not valid_points:
            return

        # 计算中心点和缩放级别
        center_lat = sum(p[0] for p in valid_points) / len(valid_points)
        center_lon = sum(p[1] for p in valid_points) / len(valid_points)
        zoom_level = MapRenderer.calculate_zoom_level(self.route_points)

        m = MapRenderer.create_base_map([center_lat, center_lon], zoom_start=zoom_level)

        # 添加标记点
        self._add_selected_points_to_map(m)

        # 添加路线
        MapRenderer.add_route(m, self.route_points)

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

        try:
            start_time = self.start_time_edit.time()
            success = self.gpx_service.export_to_gpx(
                self.route_points, start_time, file_path
            )

            if success:
                QMessageBox.information(self, "成功", f"GPX文件已导出到: {file_path}")
            else:
                QMessageBox.warning(self, "错误", "导出GPX文件失败")

        except Exception as e:
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
        """获取当前位置"""
        print("\n" + "="*50)
        print("[定位] 开始定位流程")
        print("="*50)

        try:
            self.progress_bar.setMaximum(0)
            self.progress_bar.setMinimum(0)
            self.progress_bar.setValue(0)
            QApplication.processEvents()

            self.search_results_list.clear()
            self.search_results_list.addItem("正在尝试使用电脑定位服务...")

            # 创建带定位脚本的地图
            m = MapRenderer.create_base_map([39.9042, 116.4074], zoom_start=10)
            MapRenderer.add_geolocation_script(m)

            url = MapRenderer.save_and_get_url(m)
            self.map_view.setUrl(url)
            print("[定位] 地图加载完成，等待定位结果...")
            print("="*50 + "\n")

        except Exception as e:
            print(f"[定位] 定位流程异常: {str(e)}")
            import traceback
            traceback.print_exc()

            self.progress_bar.setMaximum(100)
            self.progress_bar.setMinimum(0)
            self.progress_bar.setValue(100)
            QApplication.processEvents()

            self.search_results_list.clear()
            self.search_results_list.addItem("定位出错")
            self.search_results_list.addItem(f"错误信息: {str(e)}")
            QMessageBox.warning(self, "错误", f"定位出错: {str(e)}\n\n请检查网络连接")

    def handle_geolocation_success(self, lat, lon, accuracy):
        """处理定位成功"""
        print("\n" + "="*50)
        print("[定位成功] 开始处理定位结果")
        print("="*50)
        print(f"[定位成功] 纬度: {lat}, 经度: {lon}, 精度: {accuracy}")

        try:
            address_info = self.geocoding_service.reverse_geocode(lat, lon)

            self.current_location = (lat, lon)

            self.progress_bar.setMaximum(100)
            self.progress_bar.setMinimum(0)
            self.progress_bar.setValue(100)
            QApplication.processEvents()

            self.search_results_list.clear()
            self.search_results_list.addItem("定位成功！")
            self.search_results_list.addItem(f"定位方式: 电脑定位服务")

            if address_info:
                city = address_info.get('city', '')
                country = address_info.get('country', '')
                self.search_results_list.addItem(f"位置: {city}, {country}")
                popup_text = f"我的位置\n{city}, {country}\n定位方式: 电脑定位服务"
            else:
                popup_text = f"我的位置\n坐标: {lat:.4f}, {lon:.4f}\n定位方式: 电脑定位服务"

            self.search_results_list.addItem(f"坐标: {lat:.4f}, {lon:.4f}")

            self.show_location_on_map(lat, lon, popup_text)
            print("="*50 + "\n")

        except Exception as e:
            print(f"[定位成功] 处理异常: {str(e)}")
            import traceback
            traceback.print_exc()

    def fallback_to_ip_geolocation(self, error_msg):
        """回退到IP定位"""
        try:
            self.search_results_list.clear()
            self.search_results_list.addItem(f"电脑定位失败: {error_msg}")
            self.search_results_list.addItem("正在使用IP地址定位...")

            location_info = LocationHelper.get_ip_location()

            self.progress_bar.setMaximum(100)
            self.progress_bar.setMinimum(0)
            self.progress_bar.setValue(100)
            QApplication.processEvents()

            if location_info:
                lat = location_info['lat']
                lon = location_info['lon']
                city = location_info['city']
                country = location_info['country']

                self.current_location = (lat, lon)

                self.search_results_list.clear()
                self.search_results_list.addItem("定位成功！")
                self.search_results_list.addItem(f"定位方式: IP地址定位")
                self.search_results_list.addItem(f"位置: {city}, {country}")
                self.search_results_list.addItem(f"坐标: {lat:.4f}, {lon:.4f}")

                self.show_location_on_map(
                    lat, lon,
                    f"我的位置\n{city}, {country}\n定位方式: IP地址定位"
                )
            else:
                self.search_results_list.clear()
                self.search_results_list.addItem("定位失败")
                self.search_results_list.addItem("无法获取您的位置信息")
                QMessageBox.warning(self, "定位失败", "无法获取您的位置信息")

        except Exception as e:
            self.progress_bar.setMaximum(100)
            self.progress_bar.setMinimum(0)
            self.progress_bar.setValue(100)
            QApplication.processEvents()

            self.search_results_list.clear()
            self.search_results_list.addItem("定位出错")
            self.search_results_list.addItem(f"错误信息: {str(e)}")
            QMessageBox.warning(self, "错误", f"定位出错: {str(e)}\n\n请检查网络连接")

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
        print("\n" + "="*50)
        print("[测试] 开始测试定位功能")
        print("="*50)

        self.search_results_list.clear()
        self.search_results_list.addItem("=== 定位功能测试 ===")
        self.search_results_list.addItem("1. 检查定位处理器...")
        self.search_results_list.addItem(
            f"   状态: {'✓ 已初始化' if self.geolocation_handler else '✗ 未初始化'}"
        )

        self.search_results_list.addItem("2. 检查地图视图...")
        self.search_results_list.addItem(
            f"   状态: {'✓ 已创建' if self.map_view else '✗ 未创建'}"
        )

        self.search_results_list.addItem("3. 检查当前位置...")
        self.search_results_list.addItem(
            f"   状态: {'✓ 已定位' if self.current_location else '✗ 未定位'}"
        )
        if self.current_location:
            self.search_results_list.addItem(
                f"   坐标: {self.current_location[0]:.4f}, {self.current_location[1]:.4f}"
            )

        self.search_results_list.addItem("4. 测试信号连接...")
        try:
            self.geolocation_handler.test_geolocation()
            self.search_results_list.addItem("   状态: ✓ 信号连接正常")
        except Exception as e:
            self.search_results_list.addItem(f"   状态: ✗ 信号连接失败: {e}")

        self.search_results_list.addItem("=== 测试完成 ===")
        print("[测试] 测试完成")
        print("="*50 + "\n")


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = GpxStudio()
    window.show()
    sys.exit(app.exec_())

    def closeEvent(self, event):
        """关闭事件"""
        event.accept()

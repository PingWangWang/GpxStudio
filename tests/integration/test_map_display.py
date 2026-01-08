"""
GPX Studio 简化测试版本
仅测试地图显示功能，不运行完整的定位测试
"""

import sys
import os
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QListWidget, QFileDialog,
                             QMessageBox, QSplitter, QListWidgetItem, QScrollArea,
                             QApplication, QLineEdit)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile

from modules.geolocation.geolocation import GeolocationHandler
from modules.map.webengine import ConsoleWebEnginePage
from services.gaode_geocoding import GaodeGeocodingService
from services.gaode_routing import GaodeRoutingService
from modules.gpx.gpx_export import GpxExportService
from modules.map.map_renderer import MapRenderer
from modules.geolocation.location_helper import LocationHelper
from ui.styles import UIStyles
from ui.panels.panel_factory import PanelFactory


class GpxStudio(QMainWindow):
    """GPX Studio 主应用窗口 - 简化测试版本"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("GPX Studio - 地图显示测试")
        self.resize(1400, 800)

        # 窗口居中
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        window_geometry = self.frameGeometry()
        center_point = screen_geometry.center()
        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())

        # 初始化服务（简化）
        self.gaode_geocoding_service = GaodeGeocodingService()
        self.gaode_routing_service = GaodeRoutingService()
        self.gpx_service = GpxExportService()

        # 初始化处理器
        self.geolocation_handler = GeolocationHandler()

        # 初始化UI
        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建主布局
        main_layout = QHBoxLayout(central_widget)

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # 左侧面板（占12.5%）
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)

        # 中间面板（占12.5%）
        middle_panel = self.create_middle_panel()
        splitter.addWidget(middle_panel)

        # 右侧地图面板（占75%）
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        # 设置分割器比例
        splitter.setSizes([175, 175, 1050])  # 1400 * 0.125 = 175, 1400 * 0.75 = 1050

        # 延迟加载初始地图
        QTimer.singleShot(500, self.show_initial_map)

    def create_left_panel(self):
        """创建左侧面板"""
        left_widget = QWidget()
        layout = QVBoxLayout(left_widget)

        # 起点搜索
        start_label = QLabel("起点搜索")
        start_label.setStyleSheet(UIStyles.TITLE_LABEL)
        layout.addWidget(start_label)

        self.start_input = QLineEdit()
        self.start_input.setPlaceholderText("输入起点...")
        layout.addWidget(self.start_input)

        # 途径点搜索
        waypoint_label = QLabel("途径点搜索")
        waypoint_label.setStyleSheet(UIStyles.TITLE_LABEL)
        layout.addWidget(waypoint_label)

        self.waypoint_input = QLineEdit()
        self.waypoint_input.setPlaceholderText("输入途径点...")
        layout.addWidget(self.waypoint_input)

        # 终点搜索
        end_label = QLabel("终点搜索")
        end_label.setStyleSheet(UIStyles.TITLE_LABEL)
        layout.addWidget(end_label)

        self.end_input = QLineEdit()
        self.end_input.setPlaceholderText("输入终点...")
        layout.addWidget(self.end_input)

        layout.addStretch()
        return left_widget

    def create_middle_panel(self):
        """创建中间面板"""
        middle_widget = QWidget()
        layout = QVBoxLayout(middle_widget)

        # 搜索结果
        results_label = QLabel("搜索结果")
        results_label.setStyleSheet(UIStyles.TITLE_LABEL)
        layout.addWidget(results_label)

        self.search_results_list = QListWidget()
        # 使用默认样式
        layout.addWidget(self.search_results_list)

        # 按钮面板
        button_layout = QVBoxLayout()

        self.plan_button = QPushButton("规划路线")
        self.plan_button.setStyleSheet(UIStyles.PLAN_BUTTON)
        button_layout.addWidget(self.plan_button)

        self.export_button = QPushButton("导出GPX")
        self.export_button.setStyleSheet(UIStyles.EXPORT_BUTTON)
        button_layout.addWidget(self.export_button)

        layout.addLayout(button_layout)
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
        print("[地图测试] 开始显示初始地图...")
        try:
            m = MapRenderer.create_base_map([39.9042, 116.4074], zoom_start=10)
            url = MapRenderer.save_and_get_url(m)
            self.map_view.setUrl(url)
            print("[地图测试] 地图显示成功！")
        except Exception as e:
            print(f"[地图测试] 地图显示失败: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GpxStudio()
    window.show()
    print("[程序] GPX Studio 地图测试版本已启动")
    sys.exit(app.exec_())
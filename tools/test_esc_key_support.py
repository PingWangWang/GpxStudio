#!/usr/bin/env python3
"""
测试所有弹出面板的ESC键支持功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QDateTime
from ui.popups.gpx_export_popup import GpxExportPopup
from ui.popups.settings_popup import MapSettingsPopup, LogSettingsPopup, AboutPopup, RouteSettingsPopup
from modules.search.ui.search_history_popup import SearchHistoryPopup
from modules.search.ui.search_results_popup import SearchResultsPopup


class TestMainWindow(QMainWindow):
    """测试主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ESC键支持测试")
        self.setGeometry(100, 100, 400, 300)
        
        # 创建中央控件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 创建测试按钮
        self.create_test_buttons(layout)
        
        # 初始化弹出面板
        self.init_popups()
        
    def create_test_buttons(self, layout):
        """创建测试按钮"""
        # GPX导出弹出面板测试
        gpx_btn = QPushButton("测试GPX导出弹出面板 (ESC关闭)")
        gpx_btn.clicked.connect(self.test_gpx_export_popup)
        layout.addWidget(gpx_btn)
        
        # 地图设置弹出面板测试
        map_btn = QPushButton("测试地图设置弹出面板 (ESC关闭)")
        map_btn.clicked.connect(self.test_map_settings_popup)
        layout.addWidget(map_btn)
        
        # 日志设置弹出面板测试
        log_btn = QPushButton("测试日志设置弹出面板 (ESC关闭)")
        log_btn.clicked.connect(self.test_log_settings_popup)
        layout.addWidget(log_btn)
        
        # 关于弹出面板测试
        about_btn = QPushButton("测试关于弹出面板 (ESC关闭)")
        about_btn.clicked.connect(self.test_about_popup)
        layout.addWidget(about_btn)
        
        # 路线设置弹出面板测试
        route_btn = QPushButton("测试路线设置弹出面板 (ESC关闭)")
        route_btn.clicked.connect(self.test_route_settings_popup)
        layout.addWidget(route_btn)
        
        # 搜索历史弹出面板测试
        history_btn = QPushButton("测试搜索历史弹出面板 (ESC关闭)")
        history_btn.clicked.connect(self.test_search_history_popup)
        layout.addWidget(history_btn)
        
        # 搜索结果弹出面板测试
        results_btn = QPushButton("测试搜索结果弹出面板 (ESC关闭)")
        results_btn.clicked.connect(self.test_search_results_popup)
        layout.addWidget(results_btn)
        
    def init_popups(self):
        """初始化弹出面板"""
        # 模拟路线数据
        route_data = {
            'description': '测试路线',
            'distance': 5000,
            'duration': 1800
        }
        
        self.gpx_popup = GpxExportPopup(route_data, self)
        self.map_popup = MapSettingsPopup(self)
        self.log_popup = LogSettingsPopup(self)
        self.about_popup = AboutPopup(self)
        self.route_popup = RouteSettingsPopup(self)
        self.history_popup = SearchHistoryPopup(self)
        self.results_popup = SearchResultsPopup(self)
        
    def test_gpx_export_popup(self):
        """测试GPX导出弹出面板"""
        pos = self.mapToGlobal(self.rect().center())
        self.gpx_popup.show_at_position(pos)
        print("GPX导出弹出面板已显示，按ESC键测试关闭功能")
        
    def test_map_settings_popup(self):
        """测试地图设置弹出面板"""
        self.map_popup.show_popup(self)
        print("地图设置弹出面板已显示，按ESC键测试关闭功能")
        
    def test_log_settings_popup(self):
        """测试日志设置弹出面板"""
        self.log_popup.show_popup(self)
        print("日志设置弹出面板已显示，按ESC键测试关闭功能")
        
    def test_about_popup(self):
        """测试关于弹出面板"""
        self.about_popup.show_popup(self)
        print("关于弹出面板已显示，按ESC键测试关闭功能")
        
    def test_route_settings_popup(self):
        """测试路线设置弹出面板"""
        self.route_popup.show_popup(self)
        print("路线设置弹出面板已显示，按ESC键测试关闭功能")
        
    def test_search_history_popup(self):
        """测试搜索历史弹出面板"""
        # 模拟历史数据
        history_data = [
            {'name': '北京天安门', 'address': '北京市东城区天安门广场'},
            {'name': '上海外滩', 'address': '上海市黄浦区中山东一路'},
            {'name': '广州塔', 'address': '广州市海珠区阅江西路222号'}
        ]
        self.history_popup.show_history(history_data, self)
        print("搜索历史弹出面板已显示，按ESC键测试关闭功能")
        
    def test_search_results_popup(self):
        """测试搜索结果弹出面板"""
        # 模拟搜索结果数据
        results_data = [
            {'name': '北京大学', 'address': '北京市海淀区颐和园路5号'},
            {'name': '清华大学', 'address': '北京市海淀区清华园1号'},
            {'name': '中国人民大学', 'address': '北京市海淀区中关村大街59号'}
        ]
        self.results_popup.show_results(results_data, self)
        print("搜索结果弹出面板已显示，按ESC键测试关闭功能")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    window = TestMainWindow()
    window.show()
    
    print("ESC键支持测试程序已启动")
    print("点击按钮显示各种弹出面板，然后按ESC键测试关闭功能")
    print("所有弹出面板都应该支持ESC键关闭")
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
"""
搜索管理器
负责地点搜索功能
"""

from typing import List, Optional
from PyQt5.QtWidgets import QMessageBox, QListWidgetItem, QApplication
from PyQt5.QtCore import Qt
from services.config.map_config import map_config


class SearchManager:
    """搜索管理器

    负责地点搜索和地理编码功能：
    - 支持多种地图源的地点搜索
    - 处理搜索结果的展示和选择
    - 管理搜索结果与地图的交互
    - 根据搜索类型（起点/终点/途径点）处理搜索结果
    """

    def __init__(self, service_manager, data_manager, ui_updater, logger):
        """
        初始化搜索管理器

        参数:
            service_manager: 服务管理器实例，提供地理编码服务
            data_manager: 数据管理器实例，用于存储和获取搜索相关数据
            ui_updater: UI更新回调函数字典，用于更新界面显示
            logger: 日志器，用于记录搜索操作日志
        """
        self.service_manager = service_manager
        self.data_manager = data_manager
        self.ui_updater = ui_updater
        self.logger = logger

    def search_location(self, search_text: str, location_type: str):
        """
        搜索地点

        参数:
            search_text: 搜索文本，用户输入的地点名称或地址
            location_type: 位置类型（start/end/waypoint），指定搜索结果的用途
        """
        if not search_text:
            return

        # 检查地图源是否已设置
        map_source = map_config.get_map_source()
        if not map_source:
            self.ui_updater['show_warning']("警告", "请先在地图配置中设置地图数据源")
            return

        # 恢复信息展示框标题
        self.ui_updater['set_results_title']("搜索结果")
        self.ui_updater['clear_results_list']()
        self.ui_updater['set_progress_indeterminate']()
        QApplication.processEvents()

        # 执行搜索
        self._perform_search(search_text, location_type, map_source)

    def _perform_search(self, search_text: str, location_type: str, map_source: str):
        """执行搜索（内部方法）

        根据地图源选择对应的地理编码服务，并执行实际的地点搜索。

        参数:
            search_text: 搜索文本
            location_type: 位置类型
            map_source: 地图源（如：gaode、osm等）
        """
        # 根据地图源选择服务
        geocoding_service = self.service_manager.get_geocoding_service(map_source)

        # 检查高德API配置
        if map_source == "gaode" and not map_config.is_gaode_configured():
            self.logger.warning("高德地图API未配置，无法进行地点搜索。请先配置高德地图API密钥。")
            locations = []
        else:
            locations = geocoding_service.search_location(search_text)

        self.ui_updater['set_progress_complete']()
        QApplication.processEvents()

        if locations:
            self._handle_search_success(locations, location_type)
        else:
            self._handle_search_failure(search_text)

    def _handle_search_success(self, locations: List, location_type: str):
        """处理搜索成功（内部方法）

        搜索成功后，更新数据管理器中的搜索结果，并在界面和地图上显示结果。

        参数:
            locations: 搜索结果列表，包含地点名称、坐标等信息
            location_type: 位置类型
        """
        self.data_manager.set_search_results(locations, location_type)

        # 更新标题
        from app.constants import SEARCH_LIST_TITLES, SEARCH_RESULTS_TITLE
        title = SEARCH_LIST_TITLES.get(location_type, SEARCH_RESULTS_TITLE)
        self.ui_updater['set_results_title'](title)

        # 显示搜索结果
        self.ui_updater['show_search_results'](locations)

        # 在地图上显示搜索结果
        self.ui_updater['show_search_results_on_map'](locations, location_type)

    def _handle_search_failure(self, search_text: str):
        """处理搜索失败（内部方法）

        搜索失败后，向用户显示失败提示和建议。

        参数:
            search_text: 搜索文本
        """
        self.ui_updater['show_warning'](
            "搜索失败",
            f"未找到: {search_text}\n\n建议：\n"
            "1. 尝试使用更具体的地址（如：陕西省西安市）\n"
            "2. 尝试使用英文搜索（如：Xi'an）\n"
            "3. 检查网络连接\n"
            "4. 稍后再试（可能是服务暂时不可用）\n\n"
            "提示：某些城市名可能需要加上省份名称才能找到更多结果"
        )

    def select_location_from_list(self, data: tuple, location_type: str):
        """
        从下拉框选择地点

        参数:
            data: 地点数据 (name, lat, lon, level, type_info)，包含地点名称、坐标和其他信息
            location_type: 位置类型（start/end/waypoint）
        """
        if not data:
            return

        name = data[0]
        coords = (data[1], data[2])
        level = data[3] if len(data) > 3 else None
        type_info = data[4] if len(data) > 4 else None

        # 更新数据
        if location_type == "start":
            self.data_manager.set_start_location(coords, name, level)
        elif location_type == "end":
            self.data_manager.set_end_location(coords, name, level)
        elif location_type == "waypoint":
            # 由UI层处理途径点的更新
            pass

        # 更新UI和地图
        self.ui_updater['update_location_display'](location_type, name, data)
        self.ui_updater['update_map_preview']()

    def select_search_result(self, data: tuple):
        """
        从搜索结果中选择

        参数:
            data: 地点数据 (name, lat, lon, level, type_info)，包含地点名称、坐标和其他信息
        """
        if not data:
            return

        # 提取数据
        full_name = data[0]
        coords = (data[1], data[2])
        level = data[3] if len(data) > 3 else None
        type_info = data[4] if len(data) > 4 else None

        # 提取纯地址名称（去除地址后缀）
        # 格式如 "name (address)" 只保留 name 部分
        clean_name = full_name.split(' (')[0] if ' (' in full_name else full_name

        searching_for = self.data_manager.searching_for

        # 设置选中的搜索结果坐标
        self.data_manager.set_selected_search_result(coords, level, type_info)

        # 根据搜索类型更新数据
        if searching_for == "start":
            self.data_manager.set_start_location(coords, clean_name, level)
            self.ui_updater['update_start_from_search'](clean_name, data)
        elif searching_for == "end":
            self.data_manager.set_end_location(coords, clean_name, level)
            self.ui_updater['update_end_from_search'](clean_name, data)
        elif searching_for == "waypoint":
            self.data_manager.add_waypoint(coords, clean_name)
            self.ui_updater['add_waypoint_to_list'](clean_name, data, level)

        # 预览选中的搜索结果
        self.ui_updater['preview_search_result'](coords, clean_name, level)

        # 更新地图
        self.ui_updater['update_map_preview']()

    def clear_search_results(self):
        """清空搜索结果

        清除所有搜索结果，并重置界面显示。
        """
        self.data_manager.clear_search_results()
        self.ui_updater['clear_results_list']()
        self.ui_updater['set_results_title']("搜索结果")

"""
地图管理器
负责地图显示和更新
"""

from typing import List, Tuple, Optional
from PyQt5.QtCore import QUrl
from modules.map.map_renderer import MapRenderer
from services.config.map_config import map_config


class MapManager:
    """地图管理器

    负责地图的显示、更新和管理，提供以下功能：
    - 显示初始地图
    - 在地图上显示搜索结果
    - 更新地图预览
    - 预览单个搜索结果
    - 在地图上显示路线
    - 在地图上显示定位结果
    - 管理地图上的标记和路线
    """

    def __init__(self, data_manager, map_view, logger):
        """
        初始化地图管理器

        参数:
            data_manager: 数据管理器实例，用于获取地图相关数据
            map_view: 地图视图组件，用于显示地图
            logger: 日志器，用于记录地图操作日志
        """
        self.data_manager = data_manager  # 数据管理器实例
        self.map_view = map_view  # 地图视图组件
        self.logger = logger  # 日志器

    def show_initial_map(self):
        """显示初始地图（默认北京中心）"""
        # 获取当前配置的地图数据源
        map_source = map_config.get_map_source()

        # 创建以北京为中心的基础地图
        m = MapRenderer.create_base_map([39.9042, 116.4074], zoom_start=10, map_source=map_source)

        # 保存地图并获取URL
        url = MapRenderer.save_and_get_url(m)

        # 在地图视图中加载地图
        self.map_view.setUrl(url)
        self.logger.info("初始地图已加载")

    def show_search_results_on_map(self, locations: List, location_type: str):
        """在地图上显示搜索结果

        参数:
            locations: 搜索结果列表，包含地点信息
            location_type: 地点类型（start/end/waypoint）
        """
        if not locations:
            return

        # 获取纬度的辅助函数，处理不同格式的地点数据
        def get_lat(loc):
            return loc.get('lat') if isinstance(loc, dict) else loc.latitude

        # 获取经度的辅助函数，处理不同格式的地点数据
        def get_lon(loc):
            return loc.get('lon') if isinstance(loc, dict) else loc.longitude

        # 获取地图标记显示文本的辅助函数
        def get_display_text(loc, index):
            """获取地图标记的显示文本"""
            if isinstance(loc, dict):
                name = loc.get('name', '')  # 地点名称
                address = loc.get('address', '')  # 地点地址
                type_info = loc.get('type', '')  # 地点类型

                # 构建详细的标记文本
                parts = [f"{index}. {name}"]
                if address and address != name:
                    parts.append(f"地址: {address}")
                if type_info:
                    parts.append(f"类型: {type_info}")

                return "<br>".join(parts)
            else:
                # OSM数据格式
                return f"{index}. {loc.address}"

        # 获取当前配置的地图数据源
        map_source = map_config.get_map_source()

        # 根据搜索结果数量决定缩放策略
        if len(locations) == 1:
            # 单个地址：使用智能缩放级别
            first_location = locations[0]
            if isinstance(first_location, dict):
                level = first_location.get('level', None)
                type_info = first_location.get('type', None)
                radius = first_location.get('radius', None)
                center_lat = first_location.get('lat')
                center_lon = first_location.get('lon')
            else:
                # OSM数据格式
                level = getattr(first_location, 'level', None) if hasattr(first_location, 'level') else None
                type_info = getattr(first_location, 'type', None) if hasattr(first_location, 'type') else None
                radius = None
                center_lat = first_location.latitude
                center_lon = first_location.longitude

            # 使用智能缩放级别计算
            zoom_level = MapRenderer.get_zoom_by_level(level, type_info, radius)
            # 保存缩放级别
            self.data_manager.last_map_zoom_level = zoom_level

            # 创建基础地图，使用智能缩放级别
            m = MapRenderer.create_base_map([center_lat, center_lon], zoom_start=zoom_level, map_source=map_source)
        else:
            # 多个地址：计算中心点，稍后使用fit_bounds自动适应
            center_lat = sum(get_lat(loc) for loc in locations) / len(locations)
            center_lon = sum(get_lon(loc) for loc in locations) / len(locations)

            # 创建基础地图，使用默认缩放级别（稍后会被fit_bounds覆盖）
            m = MapRenderer.create_base_map([center_lat, center_lon], zoom_start=12, map_source=map_source)
            # fit_bounds会改变缩放级别，但我们无法获取新的级别，所以清除保存的值
            self.data_manager.last_map_zoom_level = None

        # 为每个搜索结果添加标记，统一使用灰色图标（尚未选中）
        for i, location in enumerate(locations):
            MapRenderer.add_marker(
                m, [get_lat(location), get_lon(location)],
                get_display_text(location, i+1),
                color="gray", icon='info-sign'
            )

        # 添加已选择的点（起点、终点、途径点）
        self._add_selected_points_to_map(m)

        # 如果有路线数据，添加路线到地图
        if self.data_manager.route_points:
            MapRenderer.add_route(m, self.data_manager.route_points)

        # 多个地址时，自动适应所有搜索结果
        if len(locations) > 1:
            all_search_coords = [(get_lat(loc), get_lon(loc)) for loc in locations]
            MapRenderer.fit_bounds(m, all_search_coords)

        # 保存地图并获取URL
        url = MapRenderer.save_and_get_url(m)

        # 在地图视图中加载地图
        self.map_view.setUrl(url)

    def update_map_preview(self, auto_fit=False, keep_zoom=False):
        """更新地图预览，根据当前选中的点和搜索结果更新地图显示

        参数:
            auto_fit: 是否自动调整地图以适应所有点（默认False）
            keep_zoom: 是否保持上次的缩放级别（默认False）
        """
        # 默认地图中心（北京）
        center_lat, center_lon = 39.9042, 116.4074
        center_level = None  # 中心点精度级别
        center_type = None  # 中心点类型

        # 确定地图中心，优先级：最后选中的点 > 起点 > 终点 > 第一个途径点
        if self.data_manager.last_selected_coords:
            center_lat, center_lon = self.data_manager.last_selected_coords
            center_level = self.data_manager.last_selected_level
            center_type = self.data_manager.last_selected_type
        elif self.data_manager.start_coords:
            center_lat, center_lon = self.data_manager.start_coords
            center_level = self.data_manager.start_level
        elif self.data_manager.end_coords:
            center_lat, center_lon = self.data_manager.end_coords
            center_level = getattr(self.data_manager, 'end_level', None)
        elif self.data_manager.waypoints_coords:
            center_lat, center_lon = self.data_manager.waypoints_coords[0]

        # 确定缩放级别
        if keep_zoom and self.data_manager.last_map_zoom_level is not None:
            # 使用上次保存的缩放级别
            calculated_zoom_level = self.data_manager.last_map_zoom_level
        else:
            # 根据中心点的精度级别和类型计算缩放级别
            calculated_zoom_level = MapRenderer.get_zoom_by_level(center_level, center_type)
            # 保存缩放级别
            self.data_manager.last_map_zoom_level = calculated_zoom_level

        # 获取当前配置的地图数据源
        map_source = map_config.get_map_source()

        # 创建基础地图
        m = MapRenderer.create_base_map([center_lat, center_lon], zoom_start=calculated_zoom_level, map_source=map_source)

        # 添加已选择的点（起点、终点、途径点）
        self._add_selected_points_to_map(m)

        # 添加搜索结果
        self._add_search_results_to_map(m)

        # 如果需要自动适应所有点，调整地图边界
        if auto_fit:
            all_coords = self._get_all_selected_coords()
            if len(all_coords) >= 2:
                MapRenderer.fit_bounds(m, all_coords)
                # fit_bounds会改变缩放级别，但我们无法获取新的级别，所以清除保存的值
                self.data_manager.last_map_zoom_level = None

        # 保存地图并获取URL
        url = MapRenderer.save_and_get_url(m)

        # 在地图视图中加载地图
        self.map_view.setUrl(url)

    def update_map_preview_simple(self, center_coords: Tuple[float, float], zoom_level: int = 13):
        """简单更新地图预览，不改变缩放级别

        参数:
            center_coords: 地图中心坐标 (纬度, 经度)
            zoom_level: 缩放级别（默认13）
        """
        # 获取当前配置的地图数据源
        map_source = map_config.get_map_source()

        # 创建基础地图，使用指定的缩放级别
        m = MapRenderer.create_base_map([center_coords[0], center_coords[1]], zoom_start=zoom_level, map_source=map_source)

        # 添加已选择的点（起点、终点、途径点）
        self._add_selected_points_to_map(m)

        # 添加搜索结果
        self._add_search_results_to_map(m)

        # 保存地图并获取URL
        url = MapRenderer.save_and_get_url(m)

        # 在地图视图中加载地图
        self.map_view.setUrl(url)

    def _get_all_selected_coords(self):
        """获取所有已选择的坐标点

        返回:
            list: 所有坐标点的列表 [(lat, lon), ...]
        """
        coords = []
        if self.data_manager.start_coords:
            coords.append(self.data_manager.start_coords)
        coords.extend(self.data_manager.waypoints_coords)
        if self.data_manager.end_coords:
            coords.append(self.data_manager.end_coords)
        return coords

    def preview_search_result(self, coords: Tuple[float, float], name: str, level: Optional[str] = None, type_info: Optional[str] = None, radius: Optional[float] = None):
        """
        预览单个搜索结果，高亮显示该结果

        参数:
            coords: 坐标 (纬度, 经度)
            name: 地点名称
            level: 地点级别（可选）
            type_info: 地点类型信息（可选）
            radius: POI半径（可选，单位：米）
        """
        # 导入常量
        from app.constants import COLOR_SUCCESS, ICON_SUCCESS

        # 根据地点级别、类型和实际范围计算缩放级别
        zoom_level = MapRenderer.get_zoom_by_level(level, type_info, radius)

        # 获取当前配置的地图数据源
        map_source = map_config.get_map_source()

        # 创建地图，聚焦到选中的位置
        m = MapRenderer.create_base_map([coords[0], coords[1]], zoom_start=zoom_level, map_source=map_source)

        # 添加高亮标记（使用绿色颜色和图标表示选中）
        MapRenderer.add_marker(
            m, [coords[0], coords[1]],
            f"<b>已选中: {name}</b>",
            color=COLOR_SUCCESS, icon=ICON_SUCCESS
        )

        # 添加已选择的点（使用普通样式）
        self._add_selected_points_to_map(m)

        # 添加其他搜索结果（使用普通样式，跳过当前预览的结果）
        self._add_search_results_to_map(m, preview_coords=coords)

        # 保存地图并获取URL
        url = MapRenderer.save_and_get_url(m)

        # 在地图视图中加载地图
        self.map_view.setUrl(url)
        self.logger.debug(f"预览搜索结果: {name} at {coords}, zoom_level: {zoom_level}")

    def show_route_on_map(self):
        """在地图上显示路线"""
        if not self.data_manager.route_points:
            return

        # 过滤掉无效的路线点
        valid_points = [p for p in self.data_manager.route_points if p is not None]
        if not valid_points:
            return

        # 收集所有坐标点（起点、途径点、终点）
        combined_coords = []
        if self.data_manager.start_coords:
            combined_coords.append(self.data_manager.start_coords)
        combined_coords.extend(self.data_manager.waypoints_coords)
        if self.data_manager.end_coords:
            combined_coords.append(self.data_manager.end_coords)

        # 添加所有有效的路线点
        for rp in valid_points:
            if rp and rp not in combined_coords:
                combined_coords.append(rp)

        # 获取当前配置的地图数据源
        map_source = map_config.get_map_source()

        # 确定地图中心（优先使用起点，否则使用第一个坐标点）
        center = self.data_manager.start_coords or combined_coords[0]

        # 创建基础地图
        m = MapRenderer.create_base_map(center, zoom_start=12, map_source=map_source)

        # 添加已选择的点（起点、终点、途径点）
        self._add_selected_points_to_map(m)

        # 添加路线到地图（使用配置的优化设置）
        # 计算最优缩放级别
        from modules.map.route_optimizer import RouteOptimizer
        
        valid_coords = [(p[0], p[1]) for p in valid_points if len(p) >= 2]
        optimal_zoom = None
        if map_config.is_auto_zoom_calculation_enabled():
            optimal_zoom = RouteOptimizer.calculate_optimal_zoom(valid_coords)
        
        # 记录优化信息
        original_count = len([p for p in self.data_manager.route_points if p is not None])
        self.logger.info(f"[路线渲染] 原始路线点数: {original_count}")
        if optimal_zoom:
            self.logger.info(f"[路线渲染] 建议缩放级别: {optimal_zoom}")
        
        MapRenderer.add_route(
            m, 
            self.data_manager.route_points, 
            zoom_level=optimal_zoom
        )

        # 调整地图边界以显示完整路线
        MapRenderer.fit_bounds(m, combined_coords)

        # 保存地图并获取URL
        url = MapRenderer.save_and_get_url(m)

        # 在地图视图中加载地图
        self.map_view.setUrl(url)

    def show_location_on_map(self, lat: float, lon: float, popup_text: str):
        """在地图上显示定位结果

        参数:
            lat: 纬度
            lon: 经度
            popup_text: 弹出窗口显示的文本
        """
        # 导入常量
        from app.constants import COLOR_ORANGE, ICON_WARNING

        self.logger.debug(f"[MapManager] 开始在地图上显示位置: {lat}, {lon}")

        # 获取当前配置的地图数据源
        map_source = map_config.get_map_source()
        self.logger.debug(f"[MapManager] 地图数据源: {map_source}")

        # 创建基础地图
        m = MapRenderer.create_base_map([lat, lon], zoom_start=13, map_source=map_source)
        self.logger.debug("[MapManager] 基础地图创建完成")

        # 添加定位标记
        MapRenderer.add_marker(
            m, [lat, lon], popup_text,
            color=COLOR_ORANGE, icon=ICON_WARNING
        )

        # 添加已选择的点（起点、终点、途径点）
        self._add_selected_points_to_map(m)

        # 如果有路线数据，添加路线到地图
        if self.data_manager.route_points:
            self.logger.debug("[MapManager] 添加路线到地图")
            MapRenderer.add_route(m, self.data_manager.route_points)

        self.logger.debug("[MapManager] 保存地图并获取URL")

        # 保存地图并获取URL
        url = MapRenderer.save_and_get_url(m)
        self.logger.debug(f"[MapManager] 地图URL: {url}")

        # 在地图视图中加载地图
        self.logger.debug("[MapManager] 设置地图视图URL")
        self.map_view.setUrl(url)
        self.logger.info(f"[MapManager] 地图显示完成: {lat}, {lon}")

    def _add_selected_points_to_map(self, map_obj):
        """添加已选择的点到地图（内部方法）

        添加起点、终点和途径点到地图上，使用不同的颜色和图标区分。

        参数:
            map_obj: 地图对象
        """
        # 导入常量
        from app.constants import (COLOR_INFO, COLOR_SUCCESS, COLOR_ERROR,
                                   ICON_INFO, ICON_SUCCESS, ICON_ERROR)

        # 添加起点（绿色标记）
        if self.data_manager.start_coords:
            start_name = self.data_manager.start_name or "起点"
            MapRenderer.add_marker(
                map_obj, self.data_manager.start_coords, start_name,
                color=COLOR_SUCCESS, icon=ICON_SUCCESS
            )

        # 添加途径点（蓝色标记）
        for i, (waypoint, name) in enumerate(zip(
            self.data_manager.waypoints_coords,
            self.data_manager.waypoints_names
        )):
            display_name = name if name else f"途径点 {i + 1}"
            MapRenderer.add_marker(
                map_obj, waypoint, display_name,
                color=COLOR_INFO, icon=ICON_INFO
            )

        # 添加终点（红色标记）
        if self.data_manager.end_coords:
            end_name = self.data_manager.end_name or "终点"
            MapRenderer.add_marker(
                map_obj, self.data_manager.end_coords, end_name,
                color=COLOR_ERROR, icon=ICON_ERROR
            )

    def _add_search_results_to_map(self, map_obj, preview_coords: Optional[Tuple[float, float]] = None):
        """
        添加搜索结果到地图（内部方法）

        参数:
            map_obj: 地图对象
            preview_coords: 预览坐标（如果指定，则该坐标的标记会被跳过，因为已经用高亮样式显示）
        """
        if not self.data_manager.search_results or not self.data_manager.searching_for:
            return

        for i, location in enumerate(self.data_manager.search_results):
            # 获取纬度的辅助函数
            def get_lat(loc):
                return loc.get('lat') if isinstance(loc, dict) else loc.latitude

            # 获取经度的辅助函数
            def get_lon(loc):
                return loc.get('lon') if isinstance(loc, dict) else loc.longitude

            # 获取地址的辅助函数
            def get_address(loc):
                return loc.get('address', '') if isinstance(loc, dict) else loc.address

            # 如果正在预览某个结果，跳过该结果（避免重复标记）
            if preview_coords:
                if (abs(get_lat(location) - preview_coords[0]) < 0.0001 and
                    abs(get_lon(location) - preview_coords[1]) < 0.0001):
                    continue

            # 检查是否为选中的结果
            is_selected = (
                self.data_manager.selected_search_result_coords and
                abs(get_lat(location) - self.data_manager.selected_search_result_coords[0]) < 0.0001 and
                abs(get_lon(location) - self.data_manager.selected_search_result_coords[1]) < 0.0001
            )

            # 根据是否选中选择颜色和图标：选中用绿色，其他用灰色
            if is_selected:
                color = "green"
                icon = "ok-sign"
            else:
                color = "gray"
                icon = "info-sign"

            # 添加搜索结果标记
            MapRenderer.add_marker(
                map_obj, [get_lat(location), get_lon(location)],
                f"{i+1}. {get_address(location)}",
                color=color, icon=icon
            )

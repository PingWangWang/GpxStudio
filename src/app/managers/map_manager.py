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

    def __init__(self, data_manager, map_view, logger, recreate_callback=None):
        """
        初始化地图管理器

        参数:
            data_manager: 数据管理器实例，用于获取地图相关数据
            map_view: 地图视图组件，用于显示地图
            logger: 日志器，用于记录地图操作日志
            recreate_callback: 重新创建地图视图的回调函数
        """
        self.data_manager = data_manager  # 数据管理器实例
        self.map_view = map_view  # 地图视图组件
        self.logger = logger  # 日志器
        self._recreate_map_view = recreate_callback  # 重新创建回调

    def show_initial_map(self):
        """显示初始地图（默认北京中心）"""
        # 获取当前配置的地图数据源
        map_source = map_config.get_map_source()

        # 创建以北京为中心的基础地图
        m = MapRenderer.create_base_map([39.9042, 116.4074], zoom_start=10, map_source=map_source)

        # 保存地图并获取URL
        url = MapRenderer.save_and_get_url(m)

        # 在地图视图中加载地图
        try:
            if self.map_view and not self.map_view.isVisible():
                self.logger.warning("地图视图不可见，尝试显示")
                self.map_view.show()

            if self.map_view:
                self.map_view.setUrl(url)
                self.logger.info("初始地图已加载")
            else:
                self.logger.error("地图视图为None，无法加载地图")
        except RuntimeError as e:
            self.logger.error(f"地图视图已被删除: {e}")
            self.logger.info("尝试重新创建地图视图")
            # 尝试重新创建地图视图
            if self._recreate_map_view and self._recreate_map_view():
                # 重新尝试加载地图
                try:
                    self.map_view.setUrl(url)
                    self.logger.info("重新创建地图视图成功，初始地图已加载")
                except RuntimeError as e2:
                    self.logger.error(f"重新创建的地图视图也被删除: {e2}")
            else:
                self.logger.error("无法重新创建地图视图")
            return

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
            # 处理坐标转换：根据地图源和路线来源决定是否需要转换
            route_points_to_render = self.data_manager.route_points

            # 检查路线来源：如果存在路线替代方案，说明是通过路线规划服务获取的
            is_route_planned = hasattr(self.data_manager, 'route_alternatives') and self.data_manager.route_alternatives

            if map_source == 'gaode':
                # 当前地图源是高德地图
                has_original_gcj02 = False
                if is_route_planned:
                    # 路线是通过路线规划服务获取的，检查是否有原始GCJ-02坐标
                    try:
                        selected_route = self.data_manager.route_alternatives[self.data_manager.selected_route_index]
                        if selected_route and 'gcj02_route_points' in selected_route:
                            # 使用原始GCJ-02坐标直接渲染，避免双重转换
                            route_points_to_render = selected_route['gcj02_route_points']
                            self.logger.info(f"[路线预览] 使用原始GCJ-02坐标直接渲染，共{len(route_points_to_render)}个坐标点")
                            has_original_gcj02 = True
                    except (IndexError, AttributeError):
                        # 没有选中的路线方案或索引无效，使用默认转换逻辑
                        self.logger.warning("[路线预览] 无法获取选中的路线方案，使用默认坐标转换")

                # 如果没有原始GCJ-02坐标，将WGS-84坐标转换为GCJ-02坐标
                if not has_original_gcj02:
                    from modules.geolocation.coordinate_transform import CoordinateTransform
                    transformed_route_points = []
                    for point in route_points_to_render:
                        if point is not None:
                            # 提取坐标部分（忽略海拔）
                            lat, lon = point[0], point[1]
                            # 转换坐标
                            gcj_lat, gcj_lon = CoordinateTransform.wgs84_to_gcj02(lat, lon)
                            # 保留原始格式（可能包含海拔）
                            if len(point) > 2:
                                transformed_point = (gcj_lat, gcj_lon, point[2])
                            else:
                                transformed_point = (gcj_lat, gcj_lon)
                            transformed_route_points.append(transformed_point)
                        else:
                            transformed_route_points.append(None)
                    route_points_to_render = transformed_route_points
                    self.logger.info(f"[路线预览] 已将{len(transformed_route_points)}个WGS-84坐标转换为GCJ-02坐标")

            MapRenderer.add_route(m, route_points_to_render)

        # 多个地址时，自动适应所有搜索结果
        if len(locations) > 1:
            all_search_coords = [(get_lat(loc), get_lon(loc)) for loc in locations]
            MapRenderer.fit_bounds(m, all_search_coords)

        # 保存地图并获取URL
        url = MapRenderer.save_and_get_url(m)

        # 在地图视图中加载地图
        try:
            if self.map_view:
                self.map_view.setUrl(url)
            else:
                self.logger.error("地图视图为None，无法显示搜索结果")
        except RuntimeError as e:
            self.logger.error(f"地图视图已被删除，无法显示搜索结果: {e}")

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

        # 确定地图中心，优先级：保存的地图中心 > 最后选中的点 > 起点 > 终点 > 第一个途径点
        if self.data_manager.last_map_center:
            center_lat, center_lon = self.data_manager.last_map_center
        elif self.data_manager.last_selected_coords:
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

        # 保存当前地图中心和缩放级别
        self.data_manager.last_map_center = (center_lat, center_lon)
        self.data_manager.last_map_zoom_level = calculated_zoom_level

        # 获取当前配置的地图数据源
        map_source = map_config.get_map_source()

        # 检查路线来源：如果存在路线替代方案，说明是通过路线规划服务获取的
        is_route_planned = hasattr(self.data_manager, 'route_alternatives') and self.data_manager.route_alternatives

        # 处理坐标转换：当使用高德地图时，需要将WGS-84坐标转换为GCJ-02坐标
        if map_source == 'gaode':
            # 如果路线是通过路线规划服务获取的，那么中心点坐标已经是GCJ-02坐标，不需要转换
            # 只有当路线是通过其他方式获取的（如历史记录），才需要将WGS-84坐标转换为GCJ-02坐标
            if not is_route_planned:
                from modules.geolocation.coordinate_transform import CoordinateTransform
                # 转换地图中心点坐标
                center_lat, center_lon = CoordinateTransform.wgs84_to_gcj02(center_lat, center_lon)

        # 创建基础地图
        m = MapRenderer.create_base_map([center_lat, center_lon], zoom_start=calculated_zoom_level, map_source=map_source)

        # 添加已选择的点（起点、终点、途径点）
        self._add_selected_points_to_map(m)

        # 添加搜索结果
        self._add_search_results_to_map(m)

        # 如果有路线数据，添加路线到地图
        if self.data_manager.route_points:
            # 处理坐标转换：根据地图源和路线来源决定是否需要转换
            route_points_to_render = self.data_manager.route_points

            # 检查路线来源：如果存在路线替代方案，说明是通过路线规划服务获取的
            is_route_planned = hasattr(self.data_manager, 'route_alternatives') and self.data_manager.route_alternatives

            if map_source == 'gaode':
                # 当前地图源是高德地图
                has_original_gcj02 = False
                if is_route_planned:
                    # 路线是通过路线规划服务获取的，检查是否有原始GCJ-02坐标
                    try:
                        selected_route = self.data_manager.route_alternatives[self.data_manager.selected_route_index]
                        if selected_route and 'gcj02_route_points' in selected_route:
                            # 使用原始GCJ-02坐标直接渲染，避免双重转换
                            route_points_to_render = selected_route['gcj02_route_points']
                            self.logger.info(f"[路线预览] 使用原始GCJ-02坐标直接渲染，共{len(route_points_to_render)}个坐标点")
                            has_original_gcj02 = True
                    except (IndexError, AttributeError):
                        # 没有选中的路线方案或索引无效，使用默认转换逻辑
                        self.logger.warning("[路线预览] 无法获取选中的路线方案，使用默认坐标转换")

                # 如果没有原始GCJ-02坐标，将WGS-84坐标转换为GCJ-02坐标
                if not has_original_gcj02:
                    from modules.geolocation.coordinate_transform import CoordinateTransform
                    transformed_route_points = []
                    for point in route_points_to_render:
                        if point is not None:
                            # 提取坐标部分（忽略海拔）
                            lat, lon = point[0], point[1]
                            # 转换坐标
                            gcj_lat, gcj_lon = CoordinateTransform.wgs84_to_gcj02(lat, lon)
                            # 保留原始格式（可能包含海拔）
                            if len(point) > 2:
                                transformed_point = (gcj_lat, gcj_lon, point[2])
                            else:
                                transformed_point = (gcj_lat, gcj_lon)
                            transformed_route_points.append(transformed_point)
                        else:
                            transformed_route_points.append(None)
                    route_points_to_render = transformed_route_points
                    self.logger.info(f"[路线预览] 已将{len(transformed_route_points)}个WGS-84坐标转换为GCJ-02坐标")

            MapRenderer.add_route(m, route_points_to_render)

        # 如果需要自动适应所有点，调整地图边界
        if auto_fit:
            all_coords = self._get_all_selected_coords()
            if len(all_coords) >= 2:
                # 处理坐标转换：当使用高德地图时，需要将WGS-84坐标转换为GCJ-02坐标
                bounds_coords = all_coords
                if map_source == 'gaode':
                    # 如果路线是通过路线规划服务获取的，那么边界点坐标已经是GCJ-02坐标，不需要转换
                    # 只有当路线是通过其他方式获取的（如历史记录），才需要将WGS-84坐标转换为GCJ-02坐标
                    if not is_route_planned:
                        from modules.geolocation.coordinate_transform import CoordinateTransform
                        # 转换边界点坐标
                        transformed_bounds_coords = []
                        for coords in bounds_coords:
                            if coords:
                                lat, lon = coords
                                gcj_lat, gcj_lon = CoordinateTransform.wgs84_to_gcj02(lat, lon)
                                transformed_bounds_coords.append((gcj_lat, gcj_lon))
                        bounds_coords = transformed_bounds_coords
                MapRenderer.fit_bounds(m, bounds_coords)
                # fit_bounds会改变缩放级别，但我们无法获取新的级别，所以清除保存的值
                self.data_manager.last_map_zoom_level = None

        # 保存地图并获取URL
        url = MapRenderer.save_and_get_url(m)

        # 在地图视图中加载地图
        try:
            if self.map_view:
                self.map_view.setUrl(url)
            else:
                self.logger.error("地图视图为None，无法更新地图预览")
        except RuntimeError as e:
            self.logger.error(f"地图视图已被删除，无法更新地图预览: {e}")

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

        # 如果有路线数据，添加路线到地图
        if self.data_manager.route_points:
            # 处理坐标转换：根据地图源和路线来源决定是否需要转换
            route_points_to_render = self.data_manager.route_points

            # 检查路线来源：如果存在路线替代方案，说明是通过路线规划服务获取的
            is_route_planned = hasattr(self.data_manager, 'route_alternatives') and self.data_manager.route_alternatives

            if map_source == 'gaode':
                # 当前地图源是高德地图
                has_original_gcj02 = False
                if is_route_planned:
                    # 路线是通过路线规划服务获取的，检查是否有原始GCJ-02坐标
                    try:
                        selected_route = self.data_manager.route_alternatives[self.data_manager.selected_route_index]
                        if selected_route and 'gcj02_route_points' in selected_route:
                            # 使用原始GCJ-02坐标直接渲染，避免双重转换
                            route_points_to_render = selected_route['gcj02_route_points']
                            self.logger.info(f"[路线预览] 使用原始GCJ-02坐标直接渲染，共{len(route_points_to_render)}个坐标点")
                            has_original_gcj02 = True
                    except (IndexError, AttributeError):
                        # 没有选中的路线方案或索引无效，使用默认转换逻辑
                        self.logger.warning("[路线预览] 无法获取选中的路线方案，使用默认坐标转换")

                # 如果没有原始GCJ-02坐标，将WGS-84坐标转换为GCJ-02坐标
                if not has_original_gcj02:
                    from modules.geolocation.coordinate_transform import CoordinateTransform
                    transformed_route_points = []
                    for point in route_points_to_render:
                        if point is not None:
                            # 提取坐标部分（忽略海拔）
                            lat, lon = point[0], point[1]
                            # 转换坐标
                            gcj_lat, gcj_lon = CoordinateTransform.wgs84_to_gcj02(lat, lon)
                            # 保留原始格式（可能包含海拔）
                            if len(point) > 2:
                                transformed_point = (gcj_lat, gcj_lon, point[2])
                            else:
                                transformed_point = (gcj_lat, gcj_lon)
                            transformed_route_points.append(transformed_point)
                        else:
                            transformed_route_points.append(None)
                    route_points_to_render = transformed_route_points
                    self.logger.info(f"[路线预览] 已将{len(transformed_route_points)}个WGS-84坐标转换为GCJ-02坐标")

            MapRenderer.add_route(m, route_points_to_render)

        # 保存地图并获取URL
        url = MapRenderer.save_and_get_url(m)

        # 在地图视图中加载地图
        try:
            if self.map_view:
                self.map_view.setUrl(url)
            else:
                self.logger.error("地图视图为None，无法更新简单地图预览")
        except RuntimeError as e:
            self.logger.error(f"地图视图已被删除，无法更新简单地图预览: {e}")

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
        try:
            if self.map_view:
                self.map_view.setUrl(url)
                self.logger.debug(f"预览搜索结果: {name} at {coords}, zoom_level: {zoom_level}")
            else:
                self.logger.error("地图视图为None，无法预览搜索结果")
        except RuntimeError as e:
            self.logger.error(f"地图视图已被删除，无法预览搜索结果: {e}")

    def show_route_on_map(self):
        """在地图上显示路线"""
        import time
        start_time = time.time()

        if not self.data_manager.route_points:
            self.logger.info(f"[路线渲染] 路线点为空，耗时: {(time.time() - start_time) * 1000:.2f}ms")
            return

        # 快速过滤无效路线点
        valid_points = []
        for p in self.data_manager.route_points:
            if p is not None:
                valid_points.append(p)
        if not valid_points:
            self.logger.info(f"[路线渲染] 有效路线点为空，耗时: {(time.time() - start_time) * 1000:.2f}ms")
            return

        # 优化：只收集关键坐标点，避免处理所有路线点
        combined_coords = []
        if self.data_manager.start_coords:
            combined_coords.append(self.data_manager.start_coords)
        combined_coords.extend(self.data_manager.waypoints_coords)
        if self.data_manager.end_coords:
            combined_coords.append(self.data_manager.end_coords)

        # 获取当前配置的地图数据源
        map_source = map_config.get_map_source()

        # 确定地图中心（优先使用起点，否则使用第一个坐标点）
        center = self.data_manager.start_coords or valid_points[0]

        # 创建基础地图
        map_create_start = time.time()
        m = MapRenderer.create_base_map(center, zoom_start=12, map_source=map_source)
        map_create_time = (time.time() - map_create_start) * 1000

        # 添加已选择的点（起点、终点、途径点）
        points_add_start = time.time()
        self._add_selected_points_to_map(m)
        points_add_time = (time.time() - points_add_start) * 1000

        # 添加路线到地图
        route_add_start = time.time()

        # 处理坐标转换：根据地图源和路线来源决定是否需要转换
        route_points_to_render = self.data_manager.route_points

        # 检查路线来源：如果存在路线替代方案，说明是通过路线规划服务获取的
        is_route_planned = hasattr(self.data_manager, 'route_alternatives') and self.data_manager.route_alternatives

        if map_source == 'gaode':
            # 当前地图源是高德地图
            has_original_gcj02 = False
            if is_route_planned:
                # 路线是通过路线规划服务获取的，检查是否有原始GCJ-02坐标
                try:
                    selected_route = self.data_manager.route_alternatives[self.data_manager.selected_route_index]
                    if selected_route and 'gcj02_route_points' in selected_route:
                        # 使用原始GCJ-02坐标直接渲染，避免双重转换
                        route_points_to_render = selected_route['gcj02_route_points']
                        self.logger.info(f"[路线渲染] 使用原始GCJ-02坐标直接渲染，共{len(route_points_to_render)}个坐标点")
                        has_original_gcj02 = True
                except (IndexError, AttributeError):
                    # 没有选中的路线方案或索引无效，使用默认转换逻辑
                    self.logger.warning("[路线渲染] 无法获取选中的路线方案，使用默认坐标转换")

            # 如果没有原始GCJ-02坐标，将WGS-84坐标转换为GCJ-02坐标
            if not has_original_gcj02:
                from modules.geolocation.coordinate_transform import CoordinateTransform
                transformed_route_points = []
                for point in route_points_to_render:
                    if point is not None:
                        # 提取坐标部分（忽略海拔）
                        lat, lon = point[0], point[1]
                        # 转换坐标
                        gcj_lat, gcj_lon = CoordinateTransform.wgs84_to_gcj02(lat, lon)
                        # 保留原始格式（可能包含海拔）
                        if len(point) > 2:
                            transformed_point = (gcj_lat, gcj_lon, point[2])
                        else:
                            transformed_point = (gcj_lat, gcj_lon)
                        transformed_route_points.append(transformed_point)
                    else:
                        transformed_route_points.append(None)
                route_points_to_render = transformed_route_points
                self.logger.info(f"[路线渲染] 已将{len(transformed_route_points)}个WGS-84坐标转换为GCJ-02坐标")

        MapRenderer.add_route(m, route_points_to_render)
        route_add_time = (time.time() - route_add_start) * 1000

        # 调整地图边界以显示完整路线
        fit_bounds_start = time.time()

        # 处理坐标转换：当使用高德地图时，需要将WGS-84坐标转换为GCJ-02坐标
        bounds_points = valid_points
        if map_source == 'gaode':
            # 当前地图源是高德地图，所有存储的路线数据都是WGS-84坐标，需要转换为GCJ-02坐标
            from modules.geolocation.coordinate_transform import CoordinateTransform
            # 转换边界点坐标
            transformed_bounds_points = []
            for point in bounds_points:
                if point is not None:
                    # 提取坐标部分（忽略海拔）
                    lat, lon = point[0], point[1]
                    # 转换坐标
                    gcj_lat, gcj_lon = CoordinateTransform.wgs84_to_gcj02(lat, lon)
                    transformed_bounds_points.append((gcj_lat, gcj_lon))
            bounds_points = transformed_bounds_points

        MapRenderer.fit_bounds(m, bounds_points)
        fit_bounds_time = (time.time() - fit_bounds_start) * 1000

        # 保存地图并获取URL
        save_map_start = time.time()
        url = MapRenderer.save_and_get_url(m)
        save_map_time = (time.time() - save_map_start) * 1000

        # 在地图视图中加载地图
        view_load_start = time.time()
        try:
            if self.map_view:
                self.map_view.setUrl(url)
            else:
                self.logger.error("地图视图为None，无法显示路线")
        except RuntimeError as e:
            self.logger.error(f"地图视图已被删除，无法显示路线: {e}")
        view_load_time = (time.time() - view_load_start) * 1000

        total_time = (time.time() - start_time) * 1000
        self.logger.info(f"[路线渲染] 总耗时: {total_time:.2f}ms (创建地图: {map_create_time:.2f}ms, 添加点: {points_add_time:.2f}ms, 添加路线: {route_add_time:.2f}ms, 调整边界: {fit_bounds_time:.2f}ms, 保存地图: {save_map_time:.2f}ms, 加载视图: {view_load_time:.2f}ms)")

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
            # 处理坐标转换：根据地图源和路线来源决定是否需要转换
            route_points_to_render = self.data_manager.route_points

            # 检查路线来源：如果存在路线替代方案，说明是通过路线规划服务获取的
            is_route_planned = hasattr(self.data_manager, 'route_alternatives') and self.data_manager.route_alternatives

            if map_source == 'gaode':
                # 当前地图源是高德地图
                has_original_gcj02 = False
                if is_route_planned:
                    # 路线是通过路线规划服务获取的，检查是否有原始GCJ-02坐标
                    try:
                        selected_route = self.data_manager.route_alternatives[self.data_manager.selected_route_index]
                        if selected_route and 'gcj02_route_points' in selected_route:
                            # 使用原始GCJ-02坐标直接渲染，避免双重转换
                            route_points_to_render = selected_route['gcj02_route_points']
                            self.logger.info(f"[路线预览] 使用原始GCJ-02坐标直接渲染，共{len(route_points_to_render)}个坐标点")
                            has_original_gcj02 = True
                    except (IndexError, AttributeError):
                        # 没有选中的路线方案或索引无效，使用默认转换逻辑
                        self.logger.warning("[路线预览] 无法获取选中的路线方案，使用默认坐标转换")

                # 如果没有原始GCJ-02坐标，将WGS-84坐标转换为GCJ-02坐标
                if not has_original_gcj02:
                    from modules.geolocation.coordinate_transform import CoordinateTransform
                    transformed_route_points = []
                    for point in route_points_to_render:
                        if point is not None:
                            # 提取坐标部分（忽略海拔）
                            lat, lon = point[0], point[1]
                            # 转换坐标
                            gcj_lat, gcj_lon = CoordinateTransform.wgs84_to_gcj02(lat, lon)
                            # 保留原始格式（可能包含海拔）
                            if len(point) > 2:
                                transformed_point = (gcj_lat, gcj_lon, point[2])
                            else:
                                transformed_point = (gcj_lat, gcj_lon)
                            transformed_route_points.append(transformed_point)
                        else:
                            transformed_route_points.append(None)
                    route_points_to_render = transformed_route_points
                    self.logger.info(f"[路线预览] 已将{len(transformed_route_points)}个WGS-84坐标转换为GCJ-02坐标")

            MapRenderer.add_route(m, route_points_to_render)

        self.logger.debug("[MapManager] 保存地图并获取URL")

        # 保存地图并获取URL
        url = MapRenderer.save_and_get_url(m)
        self.logger.debug(f"[MapManager] 地图URL: {url}")

        # 在地图视图中加载地图
        self.logger.debug("[MapManager] 设置地图视图URL")
        try:
            if self.map_view:
                self.map_view.setUrl(url)
                self.logger.info(f"[MapManager] 地图显示完成: {lat}, {lon}")
            else:
                self.logger.error("[MapManager] 地图视图为None，无法显示位置")
        except RuntimeError as e:
            self.logger.error(f"[MapManager] 地图视图已被删除，无法显示位置: {e}")

    def _add_selected_points_to_map(self, map_obj):
        """添加已选择的点到地图（内部方法）

        添加起点、终点和途径点到地图上，使用不同的颜色和图标区分。

        参数:
            map_obj: 地图对象
        """
        # 导入常量
        from app.constants import (COLOR_INFO, COLOR_SUCCESS, COLOR_ERROR,
                                   ICON_INFO, ICON_SUCCESS, ICON_ERROR)

        # 获取当前配置的地图数据源
        from services.config.map_config import map_config
        map_source = map_config.get_map_source()

        # 检查路线来源：如果存在路线替代方案，说明是通过路线规划服务获取的
        is_route_planned = hasattr(self.data_manager, 'route_alternatives') and self.data_manager.route_alternatives

        # 处理坐标转换：当使用高德地图时，需要将WGS-84坐标转换为GCJ-02坐标
        def transform_coords(coords):
            if map_source == 'gaode':
                # 如果路线是通过路线规划服务获取的，那么起点、终点和途径点的坐标已经是GCJ-02坐标，不需要转换
                # 只有当路线是通过其他方式获取的（如历史记录），才需要将WGS-84坐标转换为GCJ-02坐标
                if not is_route_planned:
                    from modules.geolocation.coordinate_transform import CoordinateTransform
                    if coords:
                        lat, lon = coords
                        gcj_lat, gcj_lon = CoordinateTransform.wgs84_to_gcj02(lat, lon)
                        return (gcj_lat, gcj_lon)
            return coords

        # 添加起点（绿色标记）
        if self.data_manager.start_coords:
            start_name = self.data_manager.start_name or "起点"
            start_coords_transformed = transform_coords(self.data_manager.start_coords)
            MapRenderer.add_marker(
                map_obj, start_coords_transformed, start_name,
                color=COLOR_SUCCESS, icon=ICON_SUCCESS
            )

        # 添加途径点（蓝色标记）
        for i, (waypoint, name) in enumerate(zip(
            self.data_manager.waypoints_coords,
            self.data_manager.waypoints_names
        )):
            display_name = name if name else f"途径点 {i + 1}"
            waypoint_transformed = transform_coords(waypoint)
            MapRenderer.add_marker(
                map_obj, waypoint_transformed, display_name,
                color=COLOR_INFO, icon=ICON_INFO
            )

        # 添加终点（红色标记）
        if self.data_manager.end_coords:
            end_name = self.data_manager.end_name or "终点"
            end_coords_transformed = transform_coords(self.data_manager.end_coords)
            MapRenderer.add_marker(
                map_obj, end_coords_transformed, end_name,
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

    def on_map_zoom_changed(self, new_zoom_level: int):
        """
        地图缩放级别变化时的处理方法
        只更新缩放级别记录，不重新优化路线（让Leaflet自己处理渲染）

        参数:
            new_zoom_level: 新的缩放级别
        """
        # 更新当前缩放级别记录
        self.data_manager.current_zoom_level = new_zoom_level
        # 同时更新last_map_zoom_level，以便在清除路线时保持缩放级别
        self.data_manager.last_map_zoom_level = new_zoom_level
        self.logger.debug(f"[MapManager] 缩放级别更新: {new_zoom_level}")

        # 不再进行动态路线优化，原因：
        # 1. Leaflet的Canvas渲染器可以高效渲染数千个点
        # 2. 避免每次缩放都重新计算导致的卡顿（1-2秒）
        # 3. 参考官方GPXStudio，缩放时无延迟，体验流畅

    def _rerender_route_on_map(self):
        """
        重新渲染地图上的路线（内部方法）
        使用JavaScript直接更新现有地图上的路线层，避免重新创建地图导致的卡顿和视图重置
        """
        import time
        start_time = time.time()

        if not self.data_manager.route_points:
            self.logger.debug("[路线重渲染] 无路线数据（route_points为空），跳过")
            return

        if not self.map_view:
            self.logger.debug("[路线重渲染] 地图视图不存在，跳过")
            return

        route_point_count = len([p for p in self.data_manager.route_points if p is not None])
        self.logger.debug(f"[路线重渲染] 开始更新路线: 路线点数={route_point_count}, 缩放级别={self.data_manager.current_zoom_level}")

        # 构建路线坐标数据（只包含有效点）
        valid_route_points = [p for p in self.data_manager.route_points if p is not None]
        route_coords = [[p[0], p[1]] for p in valid_route_points if len(p) >= 2]

        if not route_coords:
            self.logger.debug("[路线重渲染] 无有效路线坐标，跳过")
            return

        # 将坐标数据转换为JavaScript数组字符串
        coords_js = str(route_coords).replace("'", '"')

        # 构建JavaScript代码来更新路线
        update_route_js = f"""
        (function() {{
            try {{
                // 多种方法获取地图对象
                var map = null;

                // 方法1: 通过.leaflet-container元素的_leaflet_map属性
                var mapElement = document.querySelector('.leaflet-container');
                if (mapElement && mapElement._leaflet_map) {{
                    map = mapElement._leaflet_map;
                    console.log('[路线更新] 通过.leaflet-container._leaflet_map获取到地图');
                }} else {{
                    // 方法2: 查找window上以map_开头的全局变量
                    for (var key in window) {{
                        if (key.startsWith('map_') && window[key] && typeof window[key].getZoom === 'function') {{
                            map = window[key];
                            console.log('[路线更新] 通过window.' + key + '获取到地图');
                            break;
                        }}
                    }}
                }}

                if (!map) {{
                    console.log('[路线更新] 错误: 无法获取地图对象，稍后会自动重试');
                    return false;
                }}

                // 检查Leaflet库
                if (typeof L === 'undefined') {{
                    console.log('[路线更新] 错误: Leaflet库(L)未定义');
                    return false;
                }}

                // 保存当前地图的中心和缩放级别（关键：确保位置不变）
                var currentCenter = map.getCenter();
                var currentZoom = map.getZoom();
                console.log('[路线更新] 保存当前视图 - 中心: [' + currentCenter.lat.toFixed(6) + ', ' + currentCenter.lng.toFixed(6) + '], 缩放: ' + currentZoom);

                // 删除所有Polyline类型的层（路线），保留Marker（标记点）和TileLayer（地图瓦片）
                var layersToRemove = [];
                map.eachLayer(function(layer) {{
                    if (layer instanceof L.Polyline) {{
                        layersToRemove.push(layer);
                    }}
                }});

                console.log('[路线更新] 找到 ' + layersToRemove.length + ' 个Polyline层，准备删除');
                layersToRemove.forEach(function(layer) {{
                    map.removeLayer(layer);
                }});

                // 添加新的路线层
                var routeCoords = {coords_js};
                if (!Array.isArray(routeCoords) || routeCoords.length === 0) {{
                    console.log('[路线更新] 错误: 路线坐标无效');
                    return false;
                }}

                var routeLine = L.polyline(routeCoords, {{
                    color: 'blue',
                    weight: 5,
                    opacity: 0.7,
                    smoothFactor: 1.0
                }});
                routeLine.addTo(map);

                // 强制恢复视图位置（不使用动画，立即恢复）
                map.setView(currentCenter, currentZoom, {{animate: false}});
                console.log('[路线更新] 已恢复视图位置');

                console.log('[路线更新] ✅ 成功更新路线: ' + routeCoords.length + ' 个点');
                return true;
            }} catch (e) {{
                console.log('[路线更新] ❌ 异常: ' + e.name + ' - ' + e.message);
                console.log('[路线更新] 堆栈: ' + e.stack);
                return false;
            }}
        }})();
        """

        # 执行JavaScript代码（带重试机制）
        self._js_update_success = None  # 用于存储结果
        self._retry_count = 0
        max_retries = 3

        def try_update_route():
            self._retry_count += 1

            def handle_result(result):
                elapsed = (time.time() - start_time) * 1000
                self._js_update_success = result
                if result:
                    self.logger.info(f"[路线重渲染] ✅ JavaScript更新成功: {route_point_count}点, 耗时={elapsed:.2f}ms (尝试{self._retry_count}次)")
                else:
                    if self._retry_count < max_retries:
                        self.logger.debug(f"[路线重渲染] 第{self._retry_count}次尝试失败，{100}ms后重试...")
                        # 延迟后重试
                        from PyQt5.QtCore import QTimer
                        QTimer.singleShot(100, try_update_route)
                    else:
                        self.logger.warning(f"[路线重渲染] ⚠️ JavaScript更新失败（已重试{max_retries}次），放弃更新")

            try:
                page = self.map_view.page()
                page.runJavaScript(update_route_js, handle_result)
            except Exception as e:
                self.logger.error(f"[路线重渲染] ❌ JavaScript执行异常: {e}")
                import traceback
                traceback.print_exc()

        # 开始第一次尝试
        try_update_route()

    def _fallback_rerender_route(self, route_point_count):
        """
        降级的路线重渲染方案
        当JavaScript更新失败时，快速重建地图但保持当前视图
        """
        import time
        from modules.map.map_renderer import MapRenderer
        from services.config.map_config import map_config

        start_time = time.time()
        self.logger.info(f"[路线重渲染-降级] 开始快速重建: {route_point_count}点")

        # 获取当前地图中心（如果可能）
        # 注意：由于是异步的，这里只能使用data_manager中的数据
        valid_route_points = [p for p in self.data_manager.route_points if p is not None]
        if valid_route_points:
            center_lat = sum(p[0] for p in valid_route_points) / len(valid_route_points)
            center_lon = sum(p[1] for p in valid_route_points) / len(valid_route_points)
        else:
            center_lat, center_lon = 39.9042, 116.4074

        # 创建地图（使用当前缩放级别）
        map_source = map_config.get_map_source()
        m = MapRenderer.create_base_map(
            [center_lat, center_lon],
            zoom_start=self.data_manager.current_zoom_level,
            map_source=map_source
        )

        # 添加标记点（起点、终点、途径点）
        self._add_selected_points_to_map(m)

        # 添加优化后的路线（不再优化）
        MapRenderer.add_route(
            m,
            self.data_manager.route_points
        )

        # 不调用fitBounds，保持当前缩放级别和中心
        # 这是关键：避免视图跳转

        # 保存并加载地图
        url = MapRenderer.save_and_get_url(m)

        if self.map_view:
            self.map_view.setUrl(url)
            elapsed = (time.time() - start_time) * 1000
            self.logger.info(f"[路线重渲染-降级] ✅ 完成: 耗时={elapsed:.2f}ms")
        else:
            self.logger.error("[路线重渲染-降级] 地图视图为None")

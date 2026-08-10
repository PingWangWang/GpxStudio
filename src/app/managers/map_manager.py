"""
地图管理器
负责地图显示和更新
"""

from typing import List, Tuple, Optional
from PyQt5.QtCore import QUrl
from modules.map import MapRenderer
from modules.geolocation import CoordinateTransform
from services.config.map_config import map_config
from services.storage.favorites_storage import FavoritesStorage
from .map_view_state_manager import MapViewStateManager


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

    # 多路线同时渲染配色（8 色循环，色差分明，与路线管理库 color_index 对应）
    ROUTE_COLORS = ['#459c50', '#1890ff', '#ff7a45', '#9254de',
                    '#13c2c2', '#f5222d', '#a0d911', '#eb2f96']

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
        # 路线管理库中已 toggle 渲染的路线记录（全量重建时叠加渲染）
        self._library_rendered_records = []

        # 收藏点存储（本地 JSON 持久化，统一 WGS-84 坐标）
        self.favorites_storage = FavoritesStorage()
        
        # 创建视图状态管理器（使用lambda获取最新的map_view引用）
        self.view_state_manager = MapViewStateManager(lambda: self.map_view, logger)
        
        # 记录当前地图源，用于判断坐标系
        self._current_map_source = None

    def show_initial_map(self):
        """显示初始地图（优先恢复上次浏览位置，否则使用北京默认）"""
        # 获取当前配置的地图数据源
        map_source = map_config.get_map_source()
        # 获取地图模式
        map_mode = map_config.get_map_mode()

        # 尝试从配置文件恢复上次的地图视口
        saved = map_config.get_last_view_center()  # (lat, lon, saved_map_source) or None
        saved_zoom = map_config.get_last_view_zoom()
        if saved is not None:
            saved_lat, saved_lon, saved_map_source = saved
            # 校验地图源一致性：仅当保存时的地图源与当前一致时才能复用坐标
            # 不一致（用户切换了地图源）时丢弃，因为坐标系可能不同
            if saved_map_source is not None and saved_map_source == map_source:
                init_center = [saved_lat, saved_lon]
                init_zoom = saved_zoom if saved_zoom is not None else 10
                # 根据地图源确定传入的坐标系
                init_coord_system = CoordinateTransform.coord_system_for_map_source(map_source)
                self.logger.info(f"恢复上次地图视口: center=({saved_lat:.6f}, {saved_lon:.6f}), "
                                f"zoom={init_zoom}, coord_system={init_coord_system}")
            else:
                # 地图源不匹配或未记录，降级到北京默认
                init_center = [39.9042, 116.4074]
                init_zoom = 10
                init_coord_system = 'WGS-84'
                reason = "地图源不匹配" if saved_map_source is not None else "无地图源记录"
                self.logger.info(f"保存的视口与当前地图源{reason}，使用默认北京中心")
        else:
            init_center = [39.9042, 116.4074]  # 北京默认
            init_zoom = 10
            init_coord_system = 'WGS-84'
            self.logger.info("无保存的地图视口，使用默认北京中心")

        # 创建基础地图（传递正确的坐标系，避免重复转换）
        m = MapRenderer.create_base_map(init_center, zoom_start=init_zoom,
                                        map_type=map_mode, map_source=map_source,
                                        coord_system=init_coord_system)

        # 添加收藏点（受 show_favorites 开关控制，双地图源通用）
        self._add_favorites_to_map(m)

        # 保存地图并获取URL
        url = MapRenderer.save_and_get_url(m)

        # 在地图视图中加载地图
        try:
            if self.map_view and not self.map_view.isVisible():
                self.logger.warning("地图视图不可见，尝试显示")
                self.map_view.show()

            if self.map_view:
                self.map_view.setUrl(url)
                # 保存当前中心和缩放级别
                self.current_center = init_center
                self.current_zoom = init_zoom
                # 同步到 DataManager，确保后续预览操作一致
                self.data_manager.last_map_center = tuple(init_center)
                self.data_manager.last_map_zoom_level = init_zoom
                # 记录当前地图源
                self._current_map_source = map_source
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
                    # 保存当前中心和缩放级别
                    self.current_center = init_center
                    self.current_zoom = init_zoom
                    # 同步到 DataManager
                    self.data_manager.last_map_center = tuple(init_center)
                    self.data_manager.last_map_zoom_level = init_zoom
                    # 记录当前地图源
                    self._current_map_source = map_source
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
        
        # 获取坐标系统（从第一个搜索结果提取，所有结果应该使用相同的坐标系统）
        coord_system = 'WGS-84'  # 默认值
        if locations and isinstance(locations[0], dict):
            coord_system = locations[0].get('coord_system', 'WGS-84')

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

            # 获取地图模式
            map_mode = map_config.get_map_mode()
            # 创建基础地图，使用智能缩放级别，传递坐标系统
            m = MapRenderer.create_base_map([center_lat, center_lon], zoom_start=zoom_level, map_type=map_mode, map_source=map_source, coord_system=coord_system)
        else:
            # 多个地址：计算中心点，稍后使用fit_bounds自动适应
            center_lat = sum(get_lat(loc) for loc in locations) / len(locations)
            center_lon = sum(get_lon(loc) for loc in locations) / len(locations)

            # 获取地图模式
            map_mode = map_config.get_map_mode()
            # 创建基础地图，使用默认缩放级别（稍后会被fit_bounds覆盖），传递坐标系统
            m = MapRenderer.create_base_map([center_lat, center_lon], zoom_start=12, map_type=map_mode, map_source=map_source, coord_system=coord_system)
            # fit_bounds会改变缩放级别，但我们无法获取新的级别，所以清除保存的值
            self.data_manager.last_map_zoom_level = None

        # 为每个搜索结果添加标记，统一使用灰色图标（尚未选中），传递坐标系统
        for i, location in enumerate(locations):
            MapRenderer.add_marker(
                m, [get_lat(location), get_lon(location)],
                get_display_text(location, i+1),
                color="gray", icon='info-sign',
                map_source=map_source,
                coord_system=coord_system
            )

        # 添加已选择的点（起点、终点、途径点）
        self._add_selected_points_to_map(m)

        # 添加收藏点（受 show_favorites 开关控制，双地图源通用）
        self._add_favorites_to_map(m)

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
                    transformed_route_points = []
                    for point in route_points_to_render:
                        if point is not None:
                            # 提取坐标部分（忽略海拔）
                            lat, lon = point[0], point[1]
                            # 转换坐标
                            gcj_lat, gcj_lon = CoordinateTransform.convert(lat, lon, 'WGS-84', 'GCJ-02')
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

            MapRenderer.add_route(m, route_points_to_render, color='#459c50', weight=5, opacity=0.8)

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
                # 保存当前中心和缩放级别
                self.current_center = [center_lat, center_lon]
                self.current_zoom = zoom_level if len(locations) == 1 else 12
                # 记录当前地图源
                self._current_map_source = map_source
                self.logger.debug(f"[地图] 保存当前视图 - 中心: {self.current_center}, 缩放: {self.current_zoom}")
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
            center_source = "last_map_center"
        elif self.data_manager.last_selected_coords:
            center_lat, center_lon = self.data_manager.last_selected_coords
            center_source = "last_selected_coords"
            center_level = self.data_manager.last_selected_level
            center_type = self.data_manager.last_selected_type
        elif self.data_manager.start_coords:
            center_lat, center_lon = self.data_manager.start_coords
            center_source = "start_coords"
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

        # 保存当前地图中心和缩放级别（但不覆盖已经明确设置的值）
        # 如果 last_map_center 已经被设置且等于当前中心点，说明是外部明确设置的，不要覆盖
        should_update_state = True
        if self.data_manager.last_map_center:
            # 检查是否完全相同（表示是刚设置的）
            if abs(self.data_manager.last_map_center[0] - center_lat) < 0.0001 and \
               abs(self.data_manager.last_map_center[1] - center_lon) < 0.0001:
                # 坐标相同，不要覆盖，使用已设置的缩放级别
                if self.data_manager.last_map_zoom_level is not None:
                    calculated_zoom_level = self.data_manager.last_map_zoom_level
                should_update_state = False
        
        if should_update_state:
            self.data_manager.last_map_center = (center_lat, center_lon)
            self.data_manager.last_map_zoom_level = calculated_zoom_level

        # 获取当前配置的地图数据源
        map_source = map_config.get_map_source()

        # 检查路线来源：如果存在路线替代方案，说明是通过路线规划服务获取的
        is_route_planned = hasattr(self.data_manager, 'route_alternatives') and self.data_manager.route_alternatives

        # 处理坐标转换：当使用高德地图时，需要将WGS-84坐标转换为GCJ-02坐标
        # 同时确定最终的坐标系（用于传递给create_base_map，避免二次转换）
        center_coord_system = 'WGS-84'  # 默认坐标系
        
        if map_source == 'gaode':
            # 检查坐标系标记：如果已经设置了坐标系且为GCJ-02，说明坐标已经转换过了
            has_correct_coord_system = False
            self.logger.info(f"[DEBUG漂移] 5a_update_map_preview_enter: center_source={center_source}, "
                            f"center=({center_lat:.10f},{center_lon:.10f}), "
                            f"last_map_center={self.data_manager.last_map_center}, "
                            f"last_selected_coords={self.data_manager.last_selected_coords}")
            if self.data_manager.last_map_center:
                # 检查是否从路线规划或已标记的起点/终点/途径点来的坐标
                if is_route_planned:
                    has_correct_coord_system = True
                    center_coord_system = 'GCJ-02'
                elif hasattr(self.data_manager, 'start_coord_system') and self.data_manager.start_coords == self.data_manager.last_map_center:
                    # 中心点来自起点，检查起点坐标系
                    has_correct_coord_system = (self.data_manager.start_coord_system == 'GCJ-02')
                    center_coord_system = self.data_manager.start_coord_system
                elif hasattr(self.data_manager, 'end_coord_system') and self.data_manager.end_coords == self.data_manager.last_map_center:
                    # 中心点来自终点，检查终点坐标系
                    has_correct_coord_system = (self.data_manager.end_coord_system == 'GCJ-02')
                    center_coord_system = self.data_manager.end_coord_system
                else:
                    # 检查是否来自途径点
                    if hasattr(self.data_manager, 'waypoint_coord_systems'):
                        for i, waypoint_coords in enumerate(self.data_manager.waypoints_coords):
                            if waypoint_coords == self.data_manager.last_map_center:
                                if i < len(self.data_manager.waypoint_coord_systems):
                                    has_correct_coord_system = (self.data_manager.waypoint_coord_systems[i] == 'GCJ-02')
                                    center_coord_system = self.data_manager.waypoint_coord_systems[i]
                                break
            
            # 只有当坐标系不正确时才进行转换
            if not has_correct_coord_system:
                # 转换地图中心点坐标
                _before_lat, _before_lon = center_lat, center_lon
                center_lat, center_lon = CoordinateTransform.convert(center_lat, center_lon, 'WGS-84', 'GCJ-02')
                center_coord_system = 'GCJ-02'  # 转换后坐标系为GCJ-02
                self.logger.info(f"[DEBUG漂移] 5b_update_map_preview: center_source={center_source}, "
                                f"has_correct_sys=False → 已转换, before=({_before_lat:.10f},{_before_lon:.10f}), "
                                f"after=({center_lat:.10f},{center_lon:.10f})")
                self.logger.debug(f"[地图预览] 转换坐标系 WGS-84 -> GCJ-02: ({self.data_manager.last_map_center}) -> ({center_lat}, {center_lon})")
            else:
                self.logger.info(f"[DEBUG漂移] 5b_update_map_preview: center_source={center_source}, "
                                f"has_correct_sys=True → 跳过转换, center=({center_lat:.10f},{center_lon:.10f}), "
                                f"center_coord_system={center_coord_system}")
                self.logger.debug(f"[地图预览] 坐标已是GCJ-02，跳过转换")

        # 获取地图模式
        map_mode = map_config.get_map_mode()
        
        self.logger.info(f"[DEBUG漂移] 5c_create_base_map: center=({center_lat:.10f},{center_lon:.10f}), "
                        f"coord_system={center_coord_system}, map_source={map_source}, auto_fit={auto_fit}, zoom={calculated_zoom_level}")

        # 创建基础地图（传递正确的坐标系信息，避免重复转换）
        # center_coord_system 表示当前 center_lat, center_lon 的坐标系
        # 传递给 create_base_map 后，它会根据 map_source 和 coord_system 判断是否需要再次转换
        m = MapRenderer.create_base_map([center_lat, center_lon], 
                                       zoom_start=calculated_zoom_level, 
                                       map_type=map_mode, 
                                       map_source=map_source,
                                       coord_system=center_coord_system)

        # 添加已选择的点（起点、终点、途径点）
        self._add_selected_points_to_map(m)

        # 添加收藏点（受 show_favorites 开关控制，双地图源通用）
        self._add_favorites_to_map(m)

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
                    transformed_route_points = []
                    for point in route_points_to_render:
                        if point is not None:
                            # 提取坐标部分（忽略海拔）
                            lat, lon = point[0], point[1]
                            # 转换坐标
                            gcj_lat, gcj_lon = CoordinateTransform.convert(lat, lon, 'WGS-84', 'GCJ-02')
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

            MapRenderer.add_route(m, route_points_to_render, color='#4CAF50', weight=3, opacity=0.6)

        # 如果需要自动适应所有点，调整地图边界
        if auto_fit:
            all_coords = self._get_all_selected_coords()
            if len(all_coords) >= 2:
                # 直接使用原始坐标传递给 fit_bounds，与标记坐标保持一致
                # 高德地图下标记以原始坐标渲染（WGS-84），此处不应做额外 GCJ-02 转换
                bounds_coords = all_coords
                self.logger.info(f"[DEBUG漂移] 5d_auto_fit: bounds_coords={bounds_coords}")
                MapRenderer.fit_bounds(m, bounds_coords)
                # fit_bounds会改变缩放级别，但我们无法获取新的级别，所以清除保存的值
                self.data_manager.last_map_zoom_level = None

        # 保存地图并获取URL
        url = MapRenderer.save_and_get_url(m)

        # 在地图视图中加载地图
        try:
            if self.map_view:
                self.map_view.setUrl(url)
                # 保存当前中心和缩放级别
                self.current_center = [center_lat, center_lon]
                self.current_zoom = calculated_zoom_level
                # 记录当前地图源
                self._current_map_source = map_source
                self.logger.debug(f"[地图] 保存当前视图 - 中心: {self.current_center}, 缩放: {self.current_zoom}")
            else:
                self.logger.error("地图视图为None，无法更新地图预览")
        except RuntimeError as e:
            self.logger.error(f"地图视图已被删除，无法更新地图预览: {e}")

    def reload_map(self, keep_view=True, keep_route=True, keep_points=True, keep_search_results=True, keep_location=True):
        """
        统一的地图刷新方法
        
        Args:
            keep_view: 是否保持当前视图（中心点和缩放级别）
            keep_route: 是否保留路线
            keep_points: 是否保留起点、终点、途径点
            keep_search_results: 是否保留搜索结果
            keep_location: 是否保留定位标记（"我的位置"）
        """
        self.logger.info(f"[重载地图] ========== 开始重载地图 ==========")
        self.logger.info(f"[重载地图] 参数: keep_view={keep_view}, keep_route={keep_route}, "
                        f"keep_points={keep_points}, keep_search_results={keep_search_results}, keep_location={keep_location}")
        
        # 1. 获取地图配置
        map_source = map_config.get_map_source()
        map_mode = map_config.get_map_mode()
        self.logger.info(f"[重载地图] 目标配置: map_source={map_source}, map_mode={map_mode}")
        self.logger.info(f"[重载地图] 当前地图源: {self._current_map_source}")
        
        # 2. 获取视图状态
        if keep_view:
            view_state = self.view_state_manager.get_current_view()
            center = view_state['center']
            zoom = view_state['zoom']
            self.logger.info(f"[重载地图] 保持视图: center={center}, zoom={zoom}, source={view_state['source']}")

            # 降级链加固：JS/缓存均失败（默认北京值）时，用运行时记录的真实位置兜底，
            # 避免在 webengine console 回调栈内重建（视图读取超时）时地图跳回默认中心
            if view_state.get('source') == 'default' and self.data_manager.last_map_center:
                center = list(self.data_manager.last_map_center)
                zoom = self.data_manager.last_map_zoom_level or 10
                self.logger.warning(f"[重载地图] 视图获取失败，使用运行时记录位置兜底: center={center}, zoom={zoom}")
            
            # 关键：判断JavaScript返回坐标的坐标系
            # JavaScript返回的坐标系 = 当前显示的地图源的坐标系（切换前的）
            # 而不是目标地图源的坐标系（切换后的）
            if self._current_map_source == 'gaode':
                # 当前是高德地图，JavaScript返回的是GCJ-02坐标
                coord_system = 'GCJ-02'
                self.logger.debug(f"[重载地图] JavaScript返回坐标系: GCJ-02 (当前是高德地图)")
            elif self._current_map_source == 'osm':
                # 当前是OSM地图，JavaScript返回的是WGS-84坐标
                coord_system = 'WGS-84'
                self.logger.debug(f"[重载地图] JavaScript返回坐标系: WGS-84 (当前是OSM地图)")
            else:
                # 首次加载或未知，根据目标地图源推测
                coord_system = CoordinateTransform.coord_system_for_map_source(map_source)
                self.logger.warning(f"[重载地图] 无法确定当前坐标系，根据目标地图源推测: {coord_system}")
        else:
            # 不保持视图，使用默认中心点
            center = [39.9042, 116.4074]
            zoom = 10
            coord_system = 'WGS-84'  # 默认使用WGS-84
            self.logger.info(f"[重载地图] 使用默认视图: center={center}, zoom={zoom}")
        
        # 3. 创建基础地图（传入正确的坐标系信息）
        # MapRenderer会根据coord_system和map_source自动进行必要的坐标转换
        m = MapRenderer.create_base_map(center, zoom_start=zoom, map_type=map_mode, 
                                       map_source=map_source, coord_system=coord_system)
        
        # 4. 添加元素
        if keep_points:
            self._add_selected_points_to_map(m)

        # 添加收藏点（受 show_favorites 开关控制，双地图源通用）
        self._add_favorites_to_map(m)

        # 添加定位标记（"我的位置"）
        if keep_location:
            self._add_location_marker_to_map(m)
        
        if keep_search_results:
            # 添加调试日志，确认搜索结果状态
            has_search_results = hasattr(self.data_manager, 'search_results') and self.data_manager.search_results
            self.logger.info(f"[重载地图] keep_search_results=True, 实际有搜索结果: {has_search_results}")
            if has_search_results:
                self.logger.info(f"[重载地图] 搜索结果数量: {len(self.data_manager.search_results)}")
                self.logger.info(f"[重载地图] 第一个搜索结果: {self.data_manager.search_results[0]}")
            self._add_search_results_to_map(m)
        
        if keep_route and (self.data_manager.route_points
                           or self._library_rendered_records):
            # 统一渲染入口（多路线渲染开关/库渲染叠加在此生效）
            self._add_route_to_map(m)

        # 5. 保存并加载地图
        url = MapRenderer.save_and_get_url(m)
        
        try:
            if self.map_view:
                self.logger.info(f"[重载地图] 开始加载地图到浏览器")
                self.map_view.setUrl(url)
                # 更新视图状态管理器的缓存
                self.view_state_manager.set_cache(center, zoom)
                # 保持旧属性以兼容旧代码
                self.current_center = center
                self.current_zoom = zoom
                # 记录当前地图源，用于下次判断坐标系
                self._current_map_source = map_source
                self.logger.info(f"[重载地图] ========== 地图已成功重新加载 ==========")
            else:
                self.logger.error("[重载地图] 地图视图为None")
        except RuntimeError as e:
            self.logger.error(f"[重载地图] 地图视图已被删除: {e}")

    def clear_map_and_keep_view(self):
        """清空地图上的所有元素（路线、起止点、途径点等），但保持当前显示区域和缩放级别"""
        self.logger.info("[清空地图] 使用统一刷新方法清空地图并保持视图")
        # 同步清除定位标记数据（与 keep_location=False 参数意图一致），
        # 防止后续全量重建（如收藏后刷新）时残留的标记"复活"
        if getattr(self.data_manager, 'location_marker', None):
            self.logger.debug("[清空地图] 清除定位标记数据")
            self.data_manager.location_marker = None
        # 使用统一的刷新方法，不保留任何元素但保持视图
        self.reload_map(keep_view=True, keep_route=False, keep_points=False, keep_search_results=False, keep_location=False)

    def update_map_preview_simple(self, center_coords: Tuple[float, float], zoom_level: int = 13):
        """简单更新地图预览，不改变缩放级别

        参数:
            center_coords: 地图中心坐标 (纬度, 经度)
            zoom_level: 缩放级别（默认13）
        """
        # 获取当前配置的地图数据源
        map_source = map_config.get_map_source()

        # 推断坐标系：右键菜单传入的坐标与当前地图源一致
        # 高德地图：GCJ-02，OSM地图：WGS-84
        coord_system = CoordinateTransform.coord_system_for_map_source(map_source)
        self.logger.info(f"[DEBUG漂移] 4_update_map_preview_simple: center=({center_coords[0]:.10f}, {center_coords[1]:.10f}), "
                        f"coord_system={coord_system}, map_source={map_source}, zoom={zoom_level}")

        # 获取地图模式
        map_mode = map_config.get_map_mode()
        # 创建基础地图，使用指定的缩放级别和坐标系
        m = MapRenderer.create_base_map([center_coords[0], center_coords[1]], 
                                       zoom_start=zoom_level, 
                                       map_type=map_mode, 
                                       map_source=map_source,
                                       coord_system=coord_system)

        # 添加已选择的点（起点、终点、途径点）
        self._add_selected_points_to_map(m)

        # 添加收藏点（受 show_favorites 开关控制，双地图源通用）
        self._add_favorites_to_map(m)

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
                    transformed_route_points = []
                    for point in route_points_to_render:
                        if point is not None:
                            # 提取坐标部分（忽略海拔）
                            lat, lon = point[0], point[1]
                            # 转换坐标
                            gcj_lat, gcj_lon = CoordinateTransform.convert(lat, lon, 'WGS-84', 'GCJ-02')
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

            MapRenderer.add_route(m, route_points_to_render, color='#459c50', weight=5, opacity=0.8)

        # 保存地图并获取URL
        url = MapRenderer.save_and_get_url(m)

        # 在地图视图中加载地图
        try:
            if self.map_view:
                self.map_view.setUrl(url)
                # 保存当前中心和缩放级别
                self.current_center = [center_coords[0], center_coords[1]]
                self.current_zoom = zoom_level
                self.logger.debug(f"[地图] 保存当前视图 - 中心: {self.current_center}, 缩放: {self.current_zoom}")
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

    @staticmethod
    def _to_wgs84_coords(coords, coord_system):
        """将坐标按其坐标系转换为 WGS-84（自动缩放边界计算统一坐标系用）

        参数:
            coords: 坐标 (纬度, 经度)
            coord_system: 坐标系（'WGS-84'/'GCJ-02' 等，None/空按 WGS-84 处理）

        返回:
            tuple: WGS-84 坐标，或 None（coords 为空）
        """
        if not coords:
            return None
        if coord_system in (None, '', 'WGS-84'):
            return (coords[0], coords[1])
        return CoordinateTransform.convert(coords[0], coords[1], coord_system, 'WGS-84')

    def get_all_visible_element_coords(self):
        """获取自动缩放所需的全部可见元素坐标

        元素全集：起点/终点/途径点、路线点、当前位置标识（若显示中）、
        历史/搜索点击的当前地址标识（preview_location，若存在）。
        起点/终点/途径点/预览标识按其各自保存的坐标系统一转 WGS-84
        （高德源下路线规划面板设置的起终点为 GCJ-02），路线点为 WGS-84
        存储约定，统一坐标系后参与边界计算，避免中心点双重转换导致视野偏移。
        收藏点不参与自动缩放范围计算（地图显示保持原样，仅缩放边界排除）。

        返回:
            list: WGS-84 坐标点列表 [(lat, lon), ...]
        """
        coords = []

        # 起点/终点/途径点（按其各自坐标系统一转 WGS-84）
        if self.data_manager.start_coords:
            wgs = self._to_wgs84_coords(
                self.data_manager.start_coords,
                getattr(self.data_manager, 'start_coord_system', 'WGS-84'))
            if wgs:
                coords.append(wgs)
        for i, wp in enumerate(self.data_manager.waypoints_coords):
            wp_systems = getattr(self.data_manager, 'waypoint_coord_systems', None)
            wp_system = 'WGS-84'
            if wp_systems and i < len(wp_systems):
                wp_system = wp_systems[i]
            wgs = self._to_wgs84_coords(wp, wp_system)
            if wgs:
                coords.append(wgs)
        if self.data_manager.end_coords:
            wgs = self._to_wgs84_coords(
                self.data_manager.end_coords,
                getattr(self.data_manager, 'end_coord_system', 'WGS-84'))
            if wgs:
                coords.append(wgs)

        # 路线点（WGS-84 存储约定，忽略海拔，仅取前两个元素）
        if self.data_manager.route_points:
            # 多路线渲染开启时纳入全部规划方案点，否则仅当前选中路线
            from services.config.map_config import map_config
            if map_config.get_multi_route_render() \
                    and getattr(self.data_manager, 'route_alternatives', None):
                for alt in self.data_manager.route_alternatives:
                    coords.extend([(p[0], p[1]) for p in (alt.get('route_points') or [])
                                   if p is not None])
            else:
                coords.extend([(p[0], p[1]) for p in self.data_manager.route_points if p is not None])

        # 路线管理库已渲染路线点（自动缩放边界包含 toggle 渲染的库路线）
        for rec in self._library_rendered_records or []:
            coords.extend([(p[0], p[1]) for p in (rec.get('route_points') or [])
                           if p is not None])

        # 当前位置标识（数据存在即视为地图上显示中）
        if self.data_manager.location_marker:
            coords.append((self.data_manager.location_marker['lat'],
                           self.data_manager.location_marker['lon']))

        # 历史/搜索点击的当前地址标识（preview_location，按保存的坐标系统一转 WGS-84）
        preview = getattr(self.data_manager, 'preview_location', None)
        if preview and preview.get('coords'):
            wgs = self._to_wgs84_coords(
                preview['coords'],
                preview.get('coord_system', 'WGS-84'))
            if wgs:
                coords.append(wgs)

        return coords

    def preview_search_result(self, coords: Tuple[float, float], name: str, level: Optional[str] = None, type_info: Optional[str] = None, radius: Optional[float] = None, result_data: Optional[dict] = None):
        """
        预览单个搜索结果，高亮显示该结果

        参数:
            coords: 坐标 (纬度, 经度)
            name: 地点名称
            level: 地点级别（可选）
            type_info: 地点类型信息（可选）
            radius: POI半径（可选，单位：米）
            result_data: 完整的搜索结果字典，包含coord_system和data_source信息（可选）
        """
        # 导入常量
        from app.constants import COLOR_SUCCESS, ICON_DOT
        
        # 提取坐标系统信息（向后兼容：默认为WGS-84）
        coord_system = 'WGS-84'  # 默认值
        if result_data and isinstance(result_data, dict):
            coord_system = result_data.get('coord_system', 'WGS-84')
        
        # 保存预览信息到data_manager，以便切换地图模式时能恢复
        self.data_manager.preview_location = {
            'coords': coords,
            'name': name,
            'level': level,
            'type': type_info,
            'radius': radius,
            'coord_system': coord_system  # 保存坐标系统信息
        }
        
        # 【关键修复】确保 search_results 中包含当前预览的结果
        # 这样切换地图模式时才能保留标识
        if not self.data_manager.search_results:
            # 如果 search_results 为空，自动创建一个
            search_result = {
                'name': name,
                'address': name,
                'lat': coords[0],
                'lon': coords[1],
                'level': level,
                'type': type_info,
                'radius': radius,
                'coord_system': coord_system,
                'data_source': 'preview'
            }
            self.data_manager.search_results = [search_result]
            self.data_manager.selected_search_result_coords = coords
            self.logger.warning(f"[地图预览] search_results 为空，自动创建: {name}")
        else:
            self.logger.debug(f"[地图预览] search_results 已存在，长度: {len(self.data_manager.search_results)}")

        # 根据地点级别、类型和实际范围计算缩放级别
        zoom_level = MapRenderer.get_zoom_by_level(level, type_info, radius)

        # 获取当前配置的地图数据源
        map_source = map_config.get_map_source()

        # 获取地图模式
        map_mode = map_config.get_map_mode()
        # 创建地图，聚焦到选中的位置，传递坐标系统信息
        m = MapRenderer.create_base_map(
            [coords[0], coords[1]], 
            zoom_start=zoom_level, 
            map_type=map_mode, 
            map_source=map_source,
            coord_system=coord_system
        )

        # 添加当前选中地址标识（绿色纯气泡，无内部图形，与起点 play / 终点 stop 区分）
        MapRenderer.add_marker(
            m, [coords[0], coords[1]],
            f"<b>已选中: {name}</b>",
            color=COLOR_SUCCESS, icon=ICON_DOT,
            map_source=map_source,
            coord_system=coord_system
        )

        # 添加已选择的点（起点/终点/途径点）
        self._add_selected_points_to_map(m)

        # 添加收藏点（受 show_favorites 开关控制，双地图源通用）
        self._add_favorites_to_map(m)

        # 添加已规划的路线（点击地址后保留已渲染的路线，与路线渲染逻辑互不影响）
        self._add_route_to_map(m)

        # 添加其他搜索结果（点击选择场景已由 _add_search_results_to_map 内部处理）
        self._add_search_results_to_map(m, preview_coords=coords)

        # 保存地图并获取URL
        url = MapRenderer.save_and_get_url(m)

        # 在地图视图中加载地图
        try:
            if self.map_view:
                # setUrl 为原子导航，直接替换当前页面（含旧地图的全部标记）
                self.map_view.setUrl(url)
                # 保存当前中心和缩放级别
                self.current_center = [coords[0], coords[1]]
                self.current_zoom = zoom_level
                self.logger.debug(f"预览搜索结果: {name} at {coords}, zoom_level: {zoom_level}")
                self.logger.debug(f"[地图] 保存当前视图 - 中心: {self.current_center}, 缩放: {self.current_zoom}")
            else:
                self.logger.error("地图视图为None，无法预览搜索结果")
        except RuntimeError as e:
            self.logger.error(f"地图视图已被删除，无法预览搜索结果: {e}")

    def show_route_on_map(self):
        """在地图上显示路线"""
        import time
        start_time = time.time()

        # 路线点与库渲染路线均无 → 直接返回（库渲染路线叠加在 _add_route_to_map 内）
        if not self.data_manager.route_points and not self._library_rendered_records:
            self.logger.info(f"[路线渲染] 路线点为空，耗时: {(time.time() - start_time) * 1000:.2f}ms")
            return

        # 快速过滤无效路线点
        valid_points = []
        for p in self.data_manager.route_points:
            if p is not None:
                valid_points.append(p)

        # 优化：只收集关键坐标点，避免处理所有路线点
        combined_coords = []
        if self.data_manager.start_coords:
            combined_coords.append(self.data_manager.start_coords)
        combined_coords.extend(self.data_manager.waypoints_coords)
        if self.data_manager.end_coords:
            combined_coords.append(self.data_manager.end_coords)

        # 获取当前配置的地图数据源
        map_source = map_config.get_map_source()

        # 确定地图中心（优先使用起点，否则使用第一个坐标点；库渲染时用库路线首点兜底）
        if self.data_manager.start_coords:
            center = self.data_manager.start_coords
        elif valid_points:
            center = valid_points[0]
        elif self._library_rendered_records:
            first = self._library_rendered_records[0].get('route_points') or []
            center = next((p for p in first if p is not None), (30.0, 110.0))
        else:
            center = (30.0, 110.0)

        # 获取地图模式
        map_mode = map_config.get_map_mode()
        # 创建基础地图
        map_create_start = time.time()
        m = MapRenderer.create_base_map(center, zoom_start=12, map_type=map_mode, map_source=map_source)
        map_create_time = (time.time() - map_create_start) * 1000

        # 添加已选择的点（起点、终点、途径点）
        points_add_start = time.time()
        self._add_selected_points_to_map(m)

        # 添加收藏点（受 show_favorites 开关控制，双地图源通用）
        self._add_favorites_to_map(m)
        points_add_time = (time.time() - points_add_start) * 1000

        # 添加路线到地图（坐标系转换与渲染统一在 _add_route_to_map 处理）
        route_add_start = time.time()
        self._add_route_to_map(m)
        route_add_time = (time.time() - route_add_start) * 1000

        # 调整地图边界以显示完整路线
        fit_bounds_start = time.time()

        # 处理坐标转换：当使用高德地图时，需要将WGS-84坐标转换为GCJ-02坐标
        # 边界点 = 规划路线点 + 库渲染路线点（库渲染时保证完整可见）
        bounds_points = list(valid_points)
        for rec in self._library_rendered_records or []:
            bounds_points.extend([p for p in (rec.get('route_points') or [])
                                  if p is not None])
        if map_source == 'gaode':
            # 当前地图源是高德地图，所有存储的路线数据都是WGS-84坐标，需要转换为GCJ-02坐标
            # 转换边界点坐标
            transformed_bounds_points = []
            for point in bounds_points:
                if point is not None:
                    # 提取坐标部分（忽略海拔）
                    lat, lon = point[0], point[1]
                    # 转换坐标
                    gcj_lat, gcj_lon = CoordinateTransform.convert(lat, lon, 'WGS-84', 'GCJ-02')
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
                # 保存当前中心和缩放级别
                self.current_center = center
                self.current_zoom = 12
                self.logger.debug(f"[地图] 保存当前视图 - 中心: {self.current_center}, 缩放: {self.current_zoom}")
            else:
                self.logger.error("地图视图为None，无法显示路线")
        except RuntimeError as e:
            self.logger.error(f"地图视图已被删除，无法显示路线: {e}")
        view_load_time = (time.time() - view_load_start) * 1000

        total_time = (time.time() - start_time) * 1000
        self.logger.info(f"[路线渲染] 总耗时: {total_time:.2f}ms (创建地图: {map_create_time:.2f}ms, 添加点: {points_add_time:.2f}ms, 添加路线: {route_add_time:.2f}ms, 调整边界: {fit_bounds_time:.2f}ms, 保存地图: {save_map_time:.2f}ms, 加载视图: {view_load_time:.2f}ms)")

    def _add_route_to_map(self, map_obj):
        """添加路线到地图（内部方法）

        按地图源处理坐标系（高德：优先使用路线方案的原始 GCJ-02 坐标，
        否则将 WGS-84 转换为 GCJ-02），再渲染路线折线。
        多路线同时渲染开启时遍历全部规划方案渲染（颜色按索引区分）。
        与 show_route_on_map、preview_search_result 共用，
        保证任何地图构建路径都完整渲染已规划的路线。
        """
        # 规划路线与库渲染路线均无 → 跳过（库渲染叠加在下方统一处理）
        if not self.data_manager.route_points and not self._library_rendered_records:
            return

        # 获取当前配置的地图数据源
        from services.config.map_config import map_config
        map_source = map_config.get_map_source()
        multi_render = map_config.get_multi_route_render()

        # 渲染集合：多路线 → 全部规划方案（每条独立颜色）；单路线 → 当前选中（保持现有行为）
        if multi_render and getattr(self.data_manager, 'route_alternatives', None):
            render_list = []
            for i, alt in enumerate(self.data_manager.route_alternatives):
                pts = alt.get('route_points') or alt.get('gcj02_route_points')
                if pts:
                    render_list.append((pts, i))
        else:
            render_list = ([(self.data_manager.route_points, None)]
                           if self.data_manager.route_points else [])

        # 检查路线来源：如果存在路线替代方案，说明是通过路线规划服务获取的
        is_route_planned = hasattr(self.data_manager, 'route_alternatives') and self.data_manager.route_alternatives

        for route_points, index in render_list:
            color = self.ROUTE_COLORS[index % len(self.ROUTE_COLORS)] \
                if index is not None else '#459c50'
            route_points_to_render = route_points

            if map_source == 'gaode':
                # 当前地图源是高德地图
                has_original_gcj02 = False
                if is_route_planned:
                    # 路线是通过路线规划服务获取的，检查是否有原始GCJ-02坐标
                    try:
                        if index is not None:
                            # 多路线：取该方案的原始 GCJ-02 坐标
                            alt = self.data_manager.route_alternatives[index]
                            if alt and 'gcj02_route_points' in alt:
                                route_points_to_render = alt['gcj02_route_points']
                                has_original_gcj02 = True
                        else:
                            selected_route = self.data_manager.route_alternatives[
                                self.data_manager.selected_route_index]
                            if selected_route and 'gcj02_route_points' in selected_route:
                                # 使用原始GCJ-02坐标直接渲染，避免双重转换
                                route_points_to_render = selected_route['gcj02_route_points']
                                has_original_gcj02 = True
                    except (IndexError, AttributeError):
                        # 没有选中的路线方案或索引无效，使用默认转换逻辑
                        self.logger.warning("[路线渲染] 无法获取选中的路线方案，使用默认坐标转换")

                # 如果没有原始GCJ-02坐标，将WGS-84坐标转换为GCJ-02坐标
                if not has_original_gcj02:
                    transformed_route_points = []
                    for point in route_points_to_render:
                        if point is not None:
                            # 提取坐标部分（忽略海拔）
                            lat, lon = point[0], point[1]
                            # 转换坐标
                            gcj_lat, gcj_lon = CoordinateTransform.convert(lat, lon, 'WGS-84', 'GCJ-02')
                            # 保留原始格式（可能包含海拔）
                            if len(point) > 2:
                                transformed_point = (gcj_lat, gcj_lon, point[2])
                            else:
                                transformed_point = (gcj_lat, gcj_lon)
                            transformed_route_points.append(transformed_point)
                        else:
                            transformed_route_points.append(None)
                    route_points_to_render = transformed_route_points

            MapRenderer.add_route(map_obj, route_points_to_render, color=color,
                                  weight=5, opacity=0.8)

        # 路线管理库渲染路线不再写入 HTML：由 JS 增量注入（map_library_routes.js，
        # LayerGroup 管理），渲染/取消切换不重建页面，避免卡顿；
        # 页面重建后经 _on_map_loaded 恢复注入（_library_rendered_records 数据源）

    def set_library_rendered_records(self, records: list):
        """设置路线管理库中已渲染的路线记录（全量重建时叠加渲染）

        Args:
            records: 已渲染的库路线记录列表
        """
        self._library_rendered_records = list(records or [])

    def show_location_on_map(self, lat: float, lon: float, popup_text: str):
        """在地图上显示定位结果

        参数:
            lat: 纬度
            lon: 经度
            popup_text: 弹出窗口显示的文本
        """
        self.logger.debug(f"[MapManager] 开始在地图上显示位置: {lat}, {lon}")

        # 保存定位标记信息到 data_manager，以便地图切换时能够恢复
        self.data_manager.location_marker = {
            'lat': lat,
            'lon': lon,
            'popup_text': popup_text
        }
        self.logger.debug(f"[MapManager] 定位标记信息已保存到 data_manager")

        # 获取当前配置的地图数据源
        map_source = map_config.get_map_source()
        self.logger.debug(f"[MapManager] 地图数据源: {map_source}")

        # 获取地图模式
        map_mode = map_config.get_map_mode()
        # 创建基础地图
        m = MapRenderer.create_base_map([lat, lon], zoom_start=13, map_type=map_mode, map_source=map_source)
        self.logger.debug("[MapManager] 基础地图创建完成")

        # 添加定位标记（统一走公共渲染方法：格式化面板 + 隐藏按钮 + markerType，
        # 与各全量重建入口的恢复渲染保持一致，避免两条路径样式分叉）
        self._add_location_marker_to_map(m)

        # 添加已选择的点（起点、终点、途径点）
        self._add_selected_points_to_map(m)

        # 添加收藏点（受 show_favorites 开关控制，双地图源通用）
        self._add_favorites_to_map(m)

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
                    transformed_route_points = []
                    for point in route_points_to_render:
                        if point is not None:
                            # 提取坐标部分（忽略海拔）
                            lat, lon = point[0], point[1]
                            # 转换坐标
                            gcj_lat, gcj_lon = CoordinateTransform.convert(lat, lon, 'WGS-84', 'GCJ-02')
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

            MapRenderer.add_route(m, route_points_to_render, color='#459c50', weight=5, opacity=0.8)

        self.logger.debug("[MapManager] 保存地图并获取URL")

        # 保存地图并获取URL
        url = MapRenderer.save_and_get_url(m)
        self.logger.debug(f"[MapManager] 地图URL: {url}")

        # 在地图视图中加载地图
        self.logger.debug("[MapManager] 设置地图视图URL")
        try:
            if self.map_view:
                self.map_view.setUrl(url)
                # 保存当前中心和缩放级别
                self.current_center = [lat, lon]
                self.current_zoom = 13
                self.logger.debug(f"[地图] 保存当前视图 - 中心: {self.current_center}, 缩放: {self.current_zoom}")
                self.logger.info(f"[MapManager] 地图显示完成: {lat}, {lon}")
            else:
                self.logger.error("[MapManager] 地图视图为None，无法显示位置")
        except RuntimeError as e:
            self.logger.error(f"[MapManager] 地图视图已被删除，无法显示位置: {e}")

    def add_favorite(self, lat: float, lon: float, name: str, address: str = '',
                     coord_system: str = 'WGS-84', type_text: str = '') -> tuple:
        """
        添加收藏点

        参数:
            lat: 纬度
            lon: 经度
            name: 收藏点名称
            address: 收藏点地址
            coord_system: 传入坐标的坐标系统（统一转为 WGS-84 存储）
            type_text: 地址类型（高德 type/type_info，用于列表条目图标）

        返回:
            (success, message): 是否成功及结果消息
        """
        # 坐标统一转为 WGS-84 存储（渲染时再按地图源自动转换）
        if coord_system != 'WGS-84':
            lat, lon = CoordinateTransform.convert(lat, lon, coord_system, 'WGS-84')

        success, message = self.favorites_storage.add_favorite(
            name, address, lat, lon, type_text=type_text)
        if success:
            self.logger.info(f"[收藏点] 已添加收藏: {name} ({lat:.6f}, {lon:.6f})")
            # 保持当前视图刷新地图，显示新收藏点
            self.reload_map()
        else:
            self.logger.warning(f"[收藏点] 添加收藏失败: {message}")
        return success, message

    def is_favorited(self, lat: float, lon: float, coord_system: str = 'WGS-84') -> bool:
        """
        查询坐标是否已收藏

        参数:
            lat: 纬度
            lon: 经度
            coord_system: 传入坐标的坐标系统（统一转 WGS-84 后与存储比对）

        返回:
            bool: True 已收藏
        """
        if coord_system != 'WGS-84':
            lat, lon = CoordinateTransform.convert(lat, lon, coord_system, 'WGS-84')
        return self.favorites_storage.is_favorited(lat, lon)

    def toggle_favorite(self, lat: float, lon: float, name: str, address: str = '',
                        coord_system: str = 'WGS-84', type_text: str = '') -> str:
        """
        切换收藏状态：未收藏则收藏，已收藏则取消收藏

        参数:
            lat: 纬度
            lon: 经度
            name: 收藏点名称
            address: 收藏点地址
            coord_system: 传入坐标的坐标系统（统一转 WGS-84 存储）
            type_text: 地址类型（高德 type/type_info，用于列表条目图标）

        返回:
            str: 'added' 已收藏 / 'removed' 已取消收藏 / 'failed' 操作失败
        """
        # 坐标统一转为 WGS-84 存储（渲染时再按地图源自动转换）
        wgs_lat, wgs_lon = lat, lon
        if coord_system != 'WGS-84':
            wgs_lat, wgs_lon = CoordinateTransform.convert(lat, lon, coord_system, 'WGS-84')

        if self.favorites_storage.is_favorited(wgs_lat, wgs_lon):
            # 已收藏 → 取消收藏
            if self.favorites_storage.delete_by_coords(wgs_lat, wgs_lon):
                self.logger.info(f"[收藏点] 已取消收藏: {name} ({wgs_lat:.6f}, {wgs_lon:.6f})")
                self.reload_map()  # 保持当前视图刷新，移除星形标记
                return 'removed'
            self.logger.warning(f"[收藏点] 取消收藏失败: {name}")
            return 'failed'
        else:
            # 未收藏 → 收藏
            success, message = self.favorites_storage.add_favorite(
                name, address, wgs_lat, wgs_lon, type_text=type_text)
            if success:
                self.logger.info(f"[收藏点] 已收藏: {name} ({wgs_lat:.6f}, {wgs_lon:.6f})")
                self.reload_map()  # 保持当前视图刷新，显示星形标记
                return 'added'
            self.logger.warning(f"[收藏点] 收藏失败: {message}")
            return 'failed'

    def delete_favorite(self, fav_id: int) -> bool:
        """
        删除收藏点

        优先通过 JavaScript 增量移除星标（不重载页面，视图位置不变）；
        仅当 JS 移除失败（页面不可用或未找到星标）时，延后到下一事件循环
        重建地图兜底——脱离 webengine console 回调栈后再读取视图，
        避免视图获取超时导致地图跳回默认中心。

        参数:
            fav_id: 收藏点ID

        返回:
            bool: 是否删除成功
        """
        success = self.favorites_storage.delete_favorite(fav_id)
        if not success:
            self.logger.warning(f"[收藏点] 删除收藏点失败: id={fav_id}")
            return False

        self.logger.info(f"[收藏点] 已删除收藏点: id={fav_id}")
        # 增量移除星标（尽力而为）：回调在正常事件循环中执行，可安全读取 JS 结果
        self._remove_favorite_marker_js(fav_id)
        return True

    def _remove_favorite_marker_js(self, fav_id: int):
        """通过 JavaScript 增量移除收藏星标（内部方法）

        移除成功则不再重建地图；失败时延后重建兜底。
        延后使用 QTimer 而非同步调用：删除请求源自 webengine console 回调栈，
        在回调栈内直接 reload_map 会导致视图状态 JS 读取超时（跳默认中心）。

        参数:
            fav_id: 收藏点ID
        """
        if not self.map_view or not self.map_view.page():
            self._schedule_reload_after_delete()
            return

        from modules.map import MapJsBridge
        from PyQt5.QtCore import QTimer

        def on_js_result(result):
            if result and result.get('success'):
                self.logger.debug(f"[收藏点] JS 增量移除星标成功: id={fav_id}，保持当前视图")
            else:
                msg = result.get('message') if isinstance(result, dict) else 'JS返回空结果'
                self.logger.warning(f"[收藏点] JS 增量移除星标失败（{msg}），延后重建地图兜底")
                self._schedule_reload_after_delete()

        try:
            MapJsBridge.remove_favorite(self.map_view.page(), fav_id, on_js_result)
        except Exception as e:
            self.logger.error(f"[收藏点] JS 增量移除星标异常: {e}")
            self._schedule_reload_after_delete()

    def _schedule_reload_after_delete(self):
        """延后重建地图（脱离 console 回调栈后执行，保证视图读取正常）"""
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(50, self.reload_map)

    def hide_location_marker(self) -> bool:
        """
        隐藏当前位置标识（清数据 + JS 增量移除，视图位置不变）

        与删除收藏同构：优先 JS 增量移除标记（页面不重载），
        失败时延后重建地图兜底（脱离 console 回调栈后执行）。

        返回:
            bool: 是否存在已隐藏的定位标识
        """
        if not self.data_manager.location_marker:
            self.logger.debug("[定位标识] 无定位标识可隐藏")
            return False

        self.data_manager.location_marker = None
        self.logger.info("[定位标识] 已隐藏当前位置标识")
        self._hide_location_marker_js()
        return True

    def _hide_location_marker_js(self):
        """通过 JavaScript 增量隐藏定位标识（内部方法）

        移除成功则不再重建地图；失败时延后重建兜底
        （调用上下文为 webengine console 回调栈，直接重建会导致视图读取超时）。

        参数:
            无
        """
        if not self.map_view or not self.map_view.page():
            self._schedule_reload_after_delete()
            return

        from modules.map import MapJsBridge

        def on_js_result(result):
            if result and result.get('success'):
                self.logger.debug("[定位标识] JS 增量隐藏成功，保持当前视图")
            else:
                msg = result.get('message') if isinstance(result, dict) else 'JS返回空结果'
                self.logger.warning(f"[定位标识] JS 增量隐藏失败（{msg}），延后重建地图兜底")
                self._schedule_reload_after_delete()

        try:
            MapJsBridge.hide_location_marker(self.map_view.page(), on_js_result)
        except Exception as e:
            self.logger.error(f"[定位标识] JS 增量隐藏异常: {e}")
            self._schedule_reload_after_delete()

    def _add_favorites_to_map(self, map_obj):
        """添加收藏点标记到地图（内部方法）

        受 map_config.show_favorites 开关控制；开关关闭或收藏为空时不添加。

        参数:
            map_obj: 地图对象
        """
        if not map_config.get_show_favorites():
            return

        favorites = self.favorites_storage.get_all()
        if not favorites:
            return

        map_source = map_config.get_map_source()
        MapRenderer.add_favorites_markers(map_obj, favorites, map_source=map_source, visible=True)

    def _add_location_marker_to_map(self, map_obj):
        """添加当前位置标识到地图（内部方法）

        定位标记数据（data_manager.location_marker）存在即渲染，
        供所有全量重建入口统一调用，避免个别入口遗漏导致标识丢失。

        popup 格式与收藏点面板一致：加粗标题 + 灰色标签行 + 底部操作按钮；
        marker 携带 marker_type='location'（写入 Leaflet options.markerType），
        供 JS 增量移除"隐藏标识"时按类型定位。

        参数:
            map_obj: 地图对象
        """
        marker_info = self.data_manager.location_marker
        if not marker_info:
            return

        from app.constants import COLOR_ORANGE, ICON_WARNING
        self.logger.info(f"[地图] 恢复定位标记: lat={marker_info['lat']}, lon={marker_info['lon']}")

        lat = marker_info['lat']
        lon = marker_info['lon']
        # 收藏状态（marker 存储坐标 WGS-84，直接查询）
        is_fav = self.is_favorited(lat, lon)

        # 收藏名称：popup 标题文本（首行）；JS 注入需转义单引号/反斜杠/换行
        raw_lines = [line for line in (marker_info['popup_text'] or '').split('\n') if line.strip()]
        name = raw_lines[0] if raw_lines else '当前位置'
        name_js = name.replace('\\', '\\\\').replace("'", "\\'").replace('\n', ' ')

        # 注入定位标识交互脚本（供 popup 内"收藏位置/隐藏标识"按钮调用）
        location_script = f"""
        <script>
        // 定位标识交互全局对象：供定位 popup 内的收藏/隐藏按钮调用
        window.GPXLocation = {{
            lat: {lat}, lon: {lon}, name: '{name_js}', isFav: {'true' if is_fav else 'false'},
            hide: function() {{
                console.log('隐藏定位标识');
            }},
            favorite: function() {{
                // 乐观切换收藏按钮外观（实际增删由后端处理）
                var btn = document.getElementById('gpx-loc-fav-btn');
                if (btn) {{
                    this.isFav = !this.isFav;
                    btn.textContent = (this.isFav ? '★' : '☆') + ' 收藏位置';
                    btn.style.color = this.isFav ? '#FFD700' : '#888888';
                    btn.style.borderColor = this.isFav ? '#FFD700' : '#888888';
                }}
                console.log('收藏位置:' + this.lat + ',' + this.lon + ',' + this.name);
            }}
        }};
        </script>
        """
        from folium import Element  # 与 MapRenderer.fit_bounds 的局部导入模式一致
        map_obj.get_root().html.add_child(Element(location_script))

        # 格式化 popup：行分隔转 <br>，首行加粗为标题，其余为灰色标签行
        popup_lines = []
        for i, line in enumerate(raw_lines):
            line_esc = MapRenderer._escape_popup_html(line)
            if i == 0:
                popup_lines.append(f'<b>{line_esc}</b>')
            else:
                popup_lines.append(f'<span style="color:#888;">{line_esc}</span>')

        # 收藏按钮状态样式（金色已收藏 / 灰色未收藏）
        # 文案与"隐藏标识"同 4 字，保证两按钮宽度一致
        fav_btn_text = ('★' if is_fav else '☆') + ' 收藏位置'
        fav_btn_color = '#FFD700' if is_fav else '#888888'

        popup_html = f"""
        <div style="font-family:'Microsoft YaHei','微软雅黑',sans-serif; font-size:13px; min-width:180px;">
            {'<br>'.join(popup_lines)}
            <br>
            <div style="margin-top:6px; display:flex; gap:6px;">
                <button id="gpx-loc-fav-btn" onclick="window.GPXLocation.favorite()" style="
                    background-color:transparent; color:{fav_btn_color};
                    border:1px solid {fav_btn_color}; border-radius:3px; padding:3px 10px; cursor:pointer;">
                    {fav_btn_text}
                </button>
                <button onclick="window.GPXLocation.hide()" style="
                    background-color:#f5222d; color:white;
                    border:none; border-radius:3px; padding:3px 10px; cursor:pointer;">
                    隐藏标识
                </button>
            </div>
        </div>
        """

        MapRenderer.add_marker(
            map_obj,
            [marker_info['lat'], marker_info['lon']],
            popup_html,
            color=COLOR_ORANGE,
            icon=ICON_WARNING,
            map_source=map_config.get_map_source(),
            marker_type='location'  # 写入 Leaflet options（markerType），供 JS 增量移除定位
        )

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

        # 推断坐标系统：优先使用保存的坐标系统，其次根据路线点判断
        def infer_coord_system(coords, default='WGS-84'):
            if not coords or map_source != 'gaode':
                return default
            if is_route_planned:
                return 'GCJ-02'
            if not self.data_manager.route_points:
                return default
            # 使用路线点（WGS-84）与GCJ->WGS转换后距离判断

            # 取路线起终点作为参考
            route_points = [p for p in self.data_manager.route_points if p is not None]
            if not route_points:
                return default
            first_point = route_points[0]
            last_point = route_points[-1]

            def diff(a, b):
                return abs(a[0] - b[0]) + abs(a[1] - b[1])

            raw_min = min(diff(coords, first_point), diff(coords, last_point))
            wgs_lat, wgs_lon = CoordinateTransform.convert(coords[0], coords[1], 'GCJ-02', 'WGS-84')
            conv_min = min(diff((wgs_lat, wgs_lon), first_point), diff((wgs_lat, wgs_lon), last_point))

            return 'GCJ-02' if conv_min + 1e-6 < raw_min else 'WGS-84'

        # 添加起点（绿色标记）
        if self.data_manager.start_coords:
            start_name = self.data_manager.start_name or "起点"
            start_coord_system = getattr(self.data_manager, 'start_coord_system', None)
            start_coord_system = start_coord_system or infer_coord_system(self.data_manager.start_coords)
            MapRenderer.add_marker(
                map_obj, self.data_manager.start_coords, start_name,
                color=COLOR_SUCCESS, icon=ICON_SUCCESS,
                map_source=map_source,
                coord_system=start_coord_system
            )

        # 添加途径点（蓝色标记）
        for i, (waypoint, name) in enumerate(zip(
            self.data_manager.waypoints_coords,
            self.data_manager.waypoints_names
        )):
            display_name = name if name else f"途径点 {i + 1}"
            # 优先使用保存的坐标系信息
            wp_coord_systems = getattr(self.data_manager, 'waypoint_coord_systems', None)
            waypoint_coord_system = None
            if wp_coord_systems and i < len(wp_coord_systems):
                waypoint_coord_system = wp_coord_systems[i]
            
            # 如果没有保存的坐标系信息，则推断
            if not waypoint_coord_system:
                waypoint_coord_system = infer_coord_system(waypoint)
            
            self.logger.info(f"[DEBUG漂移] 6_add_marker_wp{i}: coord={waypoint}, "
                            f"coord_system={waypoint_coord_system}, map_source={map_source}")
            
            MapRenderer.add_marker(
                map_obj, waypoint, display_name,
                color=COLOR_INFO, icon=ICON_INFO,
                map_source=map_source,
                coord_system=waypoint_coord_system,
                number=i + 1  # 添加序号显示
            )

        # 添加终点（红色标记）
        if self.data_manager.end_coords:
            end_name = self.data_manager.end_name or "终点"
            end_coord_system = getattr(self.data_manager, 'end_coord_system', None)
            end_coord_system = end_coord_system or infer_coord_system(self.data_manager.end_coords)
            MapRenderer.add_marker(
                map_obj, self.data_manager.end_coords, end_name,
                color=COLOR_ERROR, icon=ICON_ERROR,
                map_source=map_source,
                coord_system=end_coord_system
            )

    def _add_search_results_to_map(self, map_obj, preview_coords: Optional[Tuple[float, float]] = None):
        """
        添加搜索结果到地图（内部方法）

        只渲染"选中的"搜索结果（绿色 ok-sign），非选中结果一律不渲染，
        保证地图上始终只显示当前选中的地址标识（与预览高亮语义一致）。

        参数:
            map_obj: 地图对象
            preview_coords: 预览坐标（非 None 表示点击选择场景，当前点已由
                            preview_search_result 高亮为绿色 play，直接跳过整个渲染）
        """
        # 只要有搜索结果就处理，不强制要求 searching_for（历史记录等也可保留）
        if not self.data_manager.search_results:
            return

        # 点击选择场景（preview_coords 非 None）：当前点已由预览高亮渲染，
        # 此处不再渲染任何 search_results，避免地图上出现多个地址标识
        if preview_coords:
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

            # 只渲染选中的结果（地图模式切换等非预览场景，保留当前选中标识）
            is_selected = (
                self.data_manager.selected_search_result_coords and
                abs(get_lat(location) - self.data_manager.selected_search_result_coords[0]) < 0.0001 and
                abs(get_lon(location) - self.data_manager.selected_search_result_coords[1]) < 0.0001
            )
            if not is_selected:
                continue

            # 获取地图数据源
            from services.config.map_config import map_config
            map_source = map_config.get_map_source()

            # 获取坐标系统（搜索结果若为字典，优先使用其标记）
            coord_system = location.get('coord_system', 'WGS-84') if isinstance(location, dict) else 'WGS-84'

            # 添加选中的搜索结果标记（绿色 ok-sign）
            MapRenderer.add_marker(
                map_obj, [get_lat(location), get_lon(location)],
                f"{i+1}. {get_address(location)}",
                color="green", icon="ok-sign",
                map_source=map_source,
                coord_system=coord_system
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

    def on_map_center_changed(self, lat: float, lon: float):
        """
        地图中心点变化时的处理方法
        用户拖拽/平移地图时由前端 moveend 事件触发，更新运行时记录的中心坐标。
        该坐标将在退出时由 _save_map_view_state 持久化到 map_config.json。

        参数:
            lat: 新中心点纬度
            lon: 新中心点经度
        """
        self.data_manager.last_map_center = (lat, lon)
        self.current_center = [lat, lon]
        self.logger.debug(f"[MapManager] 地图中心更新: ({lat:.6f}, {lon:.6f})")

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

        # 构建路线数据（保留分段结构，支持多段线）
        route_segments = []
        current_segment = []

        for p in self.data_manager.route_points:
            if p is None:
                if len(current_segment) > 1:
                    route_segments.append(current_segment)
                current_segment = []
            else:
                # 提取点的前两个元素（纬度和经度）
                if len(p) >= 2:
                    current_segment.append([p[0], p[1]])
        
        # 添加最后一段
        if len(current_segment) > 1:
            route_segments.append(current_segment)

        if not route_segments:
            self.logger.debug("[路线重渲染] 无有效路线段，跳过")
            return

        # 将坐标数据转换为JavaScript数组字符串
        coords_js = str(route_segments).replace("'", '"')

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
                        from PyQt5.QtCore import QTimer
                        QTimer.singleShot(100, try_update_route)
                    else:
                        self.logger.warning(f"[路线重渲染] ⚠️ JavaScript更新失败（已重试{max_retries}次），放弃更新")

            try:
                from modules.map import MapJsBridge
                page = self.map_view.page()
                MapJsBridge.update_route(page, coords_js, handle_result)
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
        from modules.map import MapRenderer
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

        # 获取地图模式
        map_mode = map_config.get_map_mode()
        # 创建地图（使用当前缩放级别）
        map_source = map_config.get_map_source()
        m = MapRenderer.create_base_map(
            [center_lat, center_lon],
            zoom_start=self.data_manager.current_zoom_level,
            map_type=map_mode,
            map_source=map_source
        )

        # 添加标记点（起点、终点、途径点）
        self._add_selected_points_to_map(m)

        # 添加收藏点（受 show_favorites 开关控制，双地图源通用）
        self._add_favorites_to_map(m)

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

    def show_map(self, center, zoom=10, title="地图", coord_system='WGS-84', fit_points=None):
        """
        显示地图

        参数:
            center: 地图中心坐标 [纬度, 经度]
            zoom: 缩放级别
            title: 地图标题
            coord_system: 传入坐标的坐标系统 ('WGS-84' 或 'GCJ-02')，默认 'WGS-84'
            fit_points: 可选，WGS-84 坐标点列表；提供时渲染后调用 Leaflet fitBounds
                        精确适配所有点（含 80px padding），保证点完整处于可视空间内，
                        替代手算缩放级别的近似（避免元素出视野或贴边）
        """
        from modules.map import MapRenderer
        from services.config.map_config import map_config

        # 获取地图模式
        map_mode = map_config.get_map_mode()
        # 获取地图源
        map_source = map_config.get_map_source()

        # 创建地图 - create_base_map内部会根据map_source和coord_system自动处理坐标转换
        m = MapRenderer.create_base_map(
            center,
            zoom_start=zoom,
            map_type=map_mode,
            map_source=map_source,
            coord_system=coord_system  # 明确告知传入坐标的坐标系统
        )

        # 添加已选择的点（起点、终点、途径点）
        self._add_selected_points_to_map(m)

        # 添加当前位置标识（数据存在即渲染，与其他全量重建入口保持一致）
        self._add_location_marker_to_map(m)

        # 添加收藏点（受 show_favorites 开关控制，双地图源通用）
        self._add_favorites_to_map(m)
        
        # 如果有预览的地点，添加高亮标记（纯绿色气泡，与起点 play / 终点 stop 区分）
        if hasattr(self.data_manager, 'preview_location') and self.data_manager.preview_location:
            from app.constants import COLOR_SUCCESS, ICON_DOT
            preview = self.data_manager.preview_location
            coords = preview['coords']
            name = preview['name']
            coord_system = preview.get('coord_system', 'WGS-84')

            # 添加高亮标记
            MapRenderer.add_marker(
                m, [coords[0], coords[1]],
                f"<b>已选中: {name}</b>",
                color=COLOR_SUCCESS, icon=ICON_DOT,
                map_source=map_source,
                coord_system=coord_system
            )
            self.logger.debug(f"[地图切换] 恢复预览标记: {name} at {coords}")

        # 如果有路线数据，添加路线到地图（统一入口：多路线渲染/库渲染叠加在此生效）
        if (hasattr(self.data_manager, 'route_points')
                and (self.data_manager.route_points or self._library_rendered_records)):
            self._add_route_to_map(m)

        # 精确适配视野：将指定点转换到地图坐标系后调用 Leaflet fitBounds
        # （含 80px padding），保证所有点完整处于可视空间内
        if fit_points:
            fit_pts = [p for p in fit_points if p is not None]
            if map_source == 'gaode':
                fit_pts = [CoordinateTransform.convert(p[0], p[1], 'WGS-84', 'GCJ-02')
                           for p in fit_pts]
            MapRenderer.fit_bounds(m, fit_pts)

        # 保存地图并获取URL
        url = MapRenderer.save_and_get_url(m)

        # 在地图视图中加载地图
        try:
            if self.map_view:
                self.map_view.setUrl(url)
                # 保存当前中心和缩放级别
                self.current_center = center
                self.current_zoom = zoom
                # 记录当前地图源
                self._current_map_source = map_source
            else:
                self.logger.error("地图视图为None，无法显示地图")
        except RuntimeError as e:
            self.logger.error(f"地图视图已被删除，无法显示地图: {e}")

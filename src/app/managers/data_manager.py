"""
数据状态管理器
负责管理应用的所有数据状态
"""

from typing import Optional, List, Tuple
from domain.models.location import Location


class _WaypointCoordSystemsProxy(list):
    """可写的途径点坐标系代理列表。

    list.__getitem__ / __setitem__ / append 均同步到 Location 对象，
    使旧代码 ``data_manager.waypoint_coord_systems[i] = 'GCJ-02'``
    和 ``data_manager.waypoint_coord_systems.append(...)`` 正常工作。
    """

    def __init__(self, waypoints: List[Location]):
        self._waypoints = waypoints
        super().__init__(wp.coord_system for wp in waypoints)

    def __setitem__(self, index: int, value: str):
        super().__setitem__(index, value)
        if 0 <= index < len(self._waypoints):
            self._waypoints[index].coord_system = value

    def append(self, value: str):
        # append 只能影响已有 Location 对象；若列表比 waypoints 短则扩展
        idx = len(self)
        super().append(value)
        if idx < len(self._waypoints):
            self._waypoints[idx].coord_system = value


class DataManager:
    """数据状态管理器

    负责管理应用的所有数据状态，包括：
    - 起点、终点、途径点信息
    - 路线数据和预估时间
    - 搜索结果和选中状态
    - 当前位置信息
    """

    def __init__(self):
        """初始化数据状态"""
        # ── 起点 / 终点 / 途径点（领域模型） ──────────────────────────────
        self.start_location: Optional[Location] = None   # 起点（Location 对象）
        self.end_location: Optional[Location] = None     # 终点（Location 对象）
        self.waypoints: List[Location] = []              # 途径点列表

        # 路线数据
        self.current_route = None  # 当前路线对象
        self.route_points: List[Tuple[float, float]] = []  # 路线坐标点列表（优化后）
        self.original_route_points: List[Tuple[float, float]] = []  # 原始路线坐标点列表（未优化）
        self.estimated_duration_seconds: int = 0  # 预估路线耗时（秒）
        self.current_zoom_level: int = 12  # 当前地图缩放级别

        # 多路线方案支持
        self.route_alternatives: List[dict] = []  # 所有路线方案列表
        self.selected_route_index: int = 0  # 当前选中的路线方案索引

        # 搜索相关
        self.search_results: List = []  # 搜索结果列表
        self.searching_for: Optional[str] = None  # 当前搜索的类型（起点/终点/途径点）
        self.selected_search_result_coords: Optional[Tuple[float, float]] = None  # 选中的搜索结果坐标
        
        # 预览相关 - 保存当前正在预览的地点信息
        self.preview_location: Optional[dict] = None  # {'coords': (lat, lon), 'name': str, 'level': str, 'type': str, 'radius': float}

        # 当前位置
        self.current_location: Optional[Tuple[float, float]] = None  # 当前定位位置
        
        # 定位标记信息（用于在地图上显示"我的位置"）
        self.location_marker: Optional[dict] = None  # {'lat': float, 'lon': float, 'popup_text': str}

        # 最后选中的位置信息
        self.last_selected_coords: Optional[Tuple[float, float]] = None  # 最后选中的坐标
        self.last_selected_level: Optional[str] = None  # 最后选中的精度级别
        self.last_selected_type: Optional[str] = None  # 最后选中的类型
        self.last_selected_from_search: bool = False  # 是否从搜索结果中选中

        # 地图状态
        self.last_map_zoom_level: Optional[int] = None  # 最后一次地图更新的缩放级别
        self.last_map_center: Optional[Tuple[float, float]] = None  # 最后一次地图更新的中心点

        print("数据状态初始化完成")

    # ── 向后兼容属性：起点 ────────────────────────────────────────────────

    @property
    def start_coords(self) -> Optional[Tuple[float, float]]:
        """起点坐标（向后兼容）"""
        return self.start_location.coords if self.start_location else None

    @start_coords.setter
    def start_coords(self, value: Optional[Tuple[float, float]]):
        if value is None:
            self.start_location = None
        elif self.start_location is None:
            self.start_location = Location(name='', lat=value[0], lon=value[1])
        else:
            self.start_location.lat = value[0]
            self.start_location.lon = value[1]

    @property
    def start_name(self) -> Optional[str]:
        """起点名称（向后兼容）"""
        return self.start_location.name if self.start_location else None

    @start_name.setter
    def start_name(self, value: Optional[str]):
        if self.start_location is not None:
            self.start_location.name = value or ''

    @property
    def start_level(self) -> Optional[str]:
        """起点精度级别（向后兼容）"""
        return self.start_location.level if self.start_location else None

    @start_level.setter
    def start_level(self, value: Optional[str]):
        if self.start_location is not None:
            self.start_location.level = value

    @property
    def start_coord_system(self) -> str:
        """起点坐标系（向后兼容）"""
        return self.start_location.coord_system if self.start_location else 'WGS-84'

    @start_coord_system.setter
    def start_coord_system(self, value: str):
        if self.start_location is not None:
            self.start_location.coord_system = value

    # ── 向后兼容属性：终点 ────────────────────────────────────────────────

    @property
    def end_coords(self) -> Optional[Tuple[float, float]]:
        """终点坐标（向后兼容）"""
        return self.end_location.coords if self.end_location else None

    @end_coords.setter
    def end_coords(self, value: Optional[Tuple[float, float]]):
        if value is None:
            self.end_location = None
        elif self.end_location is None:
            self.end_location = Location(name='', lat=value[0], lon=value[1])
        else:
            self.end_location.lat = value[0]
            self.end_location.lon = value[1]

    @property
    def end_name(self) -> Optional[str]:
        """终点名称（向后兼容）"""
        return self.end_location.name if self.end_location else None

    @end_name.setter
    def end_name(self, value: Optional[str]):
        if self.end_location is not None:
            self.end_location.name = value or ''

    @property
    def end_level(self) -> Optional[str]:
        """终点精度级别（向后兼容）"""
        return self.end_location.level if self.end_location else None

    @end_level.setter
    def end_level(self, value: Optional[str]):
        if self.end_location is not None:
            self.end_location.level = value

    @property
    def end_coord_system(self) -> str:
        """终点坐标系（向后兼容）"""
        return self.end_location.coord_system if self.end_location else 'WGS-84'

    @end_coord_system.setter
    def end_coord_system(self, value: str):
        if self.end_location is not None:
            self.end_location.coord_system = value

    # ── 向后兼容属性：途径点 ──────────────────────────────────────────────

    @property
    def waypoints_coords(self) -> List[Tuple[float, float]]:
        """途径点坐标列表（向后兼容，返回快照）"""
        return [wp.coords for wp in self.waypoints]

    @property
    def waypoints_names(self) -> List[str]:
        """途径点名称列表（向后兼容，返回快照）"""
        return [wp.name for wp in self.waypoints]

    @property
    def waypoint_coord_systems(self) -> List[str]:
        """途径点坐标系列表（向后兼容，返回可写代理）"""
        return _WaypointCoordSystemsProxy(self.waypoints)

    @waypoint_coord_systems.setter
    def waypoint_coord_systems(self, value: List[str]):
        """批量设置途径点坐标系"""
        for i, cs in enumerate(value):
            if i < len(self.waypoints):
                self.waypoints[i].coord_system = cs

    def set_start_location(self, coords: Tuple[float, float], name: str, level: Optional[str] = None):
        """设置起点

        参数:
            coords: 起点坐标 (纬度, 经度)
            name: 起点名称
            level: 起点精度级别（可选）
        """
        self.start_location = Location(
            name=name or '',
            lat=coords[0],
            lon=coords[1],
            level=level,
        )
        self._update_last_selected(coords, level, None, False)

    def set_end_location(self, coords: Tuple[float, float], name: str, level: Optional[str] = None):
        """设置终点

        参数:
            coords: 终点坐标 (纬度, 经度)
            name: 终点名称
            level: 终点精度级别（可选）
        """
        self.end_location = Location(
            name=name or '',
            lat=coords[0],
            lon=coords[1],
            level=level,
        )
        self._update_last_selected(coords, level, None, False)

    def add_waypoint(self, coords: Tuple[float, float], name: str):
        """添加途径点

        参数:
            coords: 途径点坐标 (纬度, 经度)
            name: 途径点名称
        """
        self.waypoints.append(Location(name=name or '', lat=coords[0], lon=coords[1]))
        self._update_last_selected(coords, None, None, False)

    def update_waypoint(self, index: int, coords: Tuple[float, float], name: str):
        """更新途径点

        参数:
            index: 途径点索引
            coords: 新的途径点坐标 (纬度, 经度)
            name: 新的途径点名称
        """
        if 0 <= index < len(self.waypoints):
            self.waypoints[index].lat = coords[0]
            self.waypoints[index].lon = coords[1]
            self.waypoints[index].name = name or ''

    def remove_waypoint(self, index: int):
        """删除途径点

        参数:
            index: 要删除的途径点索引
        """
        if 0 <= index < len(self.waypoints):
            self.waypoints.pop(index)

    def clear_waypoints(self):
        """清空所有途径点"""
        self.waypoints.clear()

    def set_route(self, route_points: List[Tuple[float, float]], duration_seconds: int = 0):
        """设置路线（单条路线，兼容旧代码）

        参数:
            route_points: 路线坐标点列表
            duration_seconds: 预估路线耗时（秒，可选）
        """
        import logging
        logger = logging.getLogger(__name__)

        # 保存原始路线数据（用于动态渲染）
        self.original_route_points = route_points.copy() if route_points else []
        self.route_points = route_points
        self.estimated_duration_seconds = duration_seconds

        original_count = len([p for p in self.original_route_points if p is not None])
        current_count = len([p for p in self.route_points if p is not None])
        logger.info(f"[DataManager] 设置路线: 原始点数={original_count}, 当前点数={current_count}, 预估时间={duration_seconds}秒")

    def set_route_alternatives(self, alternatives: List[dict], selected_index: int = 0):
        """设置多条路线方案

        参数:
            alternatives: 路线方案列表，每个方案包含：
                - route_points: 路线点列表
                - duration: 预估时间（秒）
                - distance: 路线距离（米）
                - tolls: 收费金额（元）
                - traffic_lights: 红绿灯数量
                - description: 路线描述
            selected_index: 默认选中的方案索引
        """
        import logging
        logger = logging.getLogger(__name__)

        self.route_alternatives = alternatives
        self.selected_route_index = selected_index

        logger.info(f"[DataManager] 设置路线方案: 共{len(alternatives)}个方案, 选中索引={selected_index}")

        # 更新当前路线数据（兼容旧代码）
        if alternatives and 0 <= selected_index < len(alternatives):
            selected_route = alternatives[selected_index]
            route_points = selected_route.get('route_points', [])
            # 保存原始路线数据（用于动态渲染）
            self.original_route_points = route_points.copy() if route_points else []
            self.route_points = route_points
            self.estimated_duration_seconds = selected_route.get('duration', 0)

            original_count = len([p for p in self.original_route_points if p is not None])
            logger.info(f"[DataManager] 方案{selected_index}: 路线点数={original_count}, "
                       f"距离={selected_route.get('distance', 0)}米, 时间={selected_route.get('duration', 0)}秒")

    def select_route_alternative(self, index: int):
        """选择路线方案

        参数:
            index: 路线方案索引
        """
        import logging
        logger = logging.getLogger(__name__)

        if 0 <= index < len(self.route_alternatives):
            self.selected_route_index = index
            selected_route = self.route_alternatives[index]
            route_points = selected_route.get('route_points', [])
            # 保存原始路线数据（用于动态渲染）
            self.original_route_points = route_points.copy() if route_points else []
            self.route_points = route_points
            self.estimated_duration_seconds = selected_route.get('duration', 0)

            original_count = len([p for p in self.original_route_points if p is not None])
            logger.info(f"[DataManager] 切换到路线方案{index}: 点数={original_count}, "
                       f"距离={selected_route.get('distance', 0)}米, 时间={selected_route.get('duration', 0)}秒")

    def get_selected_route(self) -> Optional[dict]:
        """获取当前选中的路线方案

        返回:
            当前选中的路线方案，如果没有则返回None
        """
        if 0 <= self.selected_route_index < len(self.route_alternatives):
            return self.route_alternatives[self.selected_route_index]
        return None

    def set_search_results(self, results: List, searching_for: str):
        """设置搜索结果

        参数:
            results: 搜索结果列表
            searching_for: 搜索的类型（起点/终点/途径点）
        """
        self.search_results = results
        self.searching_for = searching_for

    def clear_search_results(self):
        """清空搜索结果"""
        import traceback
        import logging
        logger = logging.getLogger('GpxStudio')
        logger.debug(f"[数据管理器] search_results 被清空")
        logger.debug(f"[数据管理器] 调用堆栈:\n{''.join(traceback.format_stack()[-5:-1])}")
        self.search_results = []
        self.searching_for = None
        self.selected_search_result_coords = None

    def set_selected_search_result(self, coords: Tuple[float, float], level: Optional[str] = None,
                                   type_info: Optional[str] = None):
        """设置选中的搜索结果

        参数:
            coords: 选中的搜索结果坐标 (纬度, 经度)
            level: 选中结果的精度级别（可选）
            type_info: 选中结果的类型信息（可选）
        """
        self.selected_search_result_coords = coords
        self._update_last_selected(coords, level, type_info, True)

    def _update_last_selected(self, coords: Tuple[float, float], level: Optional[str],
                             type_info: Optional[str], from_search: bool):
        """更新最后选中的位置信息（内部方法）

        参数:
            coords: 选中的坐标 (纬度, 经度)
            level: 精度级别（可选）
            type_info: 类型信息（可选）
            from_search: 是否从搜索结果中选中
        """
        self.last_selected_coords = coords
        self.last_selected_level = level
        self.last_selected_type = type_info
        self.last_selected_from_search = from_search

    def clear_all_route_data(self):
        """清空所有路线相关数据"""
        # 重置起终点 / 途径点（领域模型）
        self.start_location = None
        self.end_location = None
        self.waypoints.clear()

        # 重置路线数据
        self.current_route = None
        self.route_points = []
        self.estimated_duration_seconds = 0

        # 重置多路线方案
        self.route_alternatives = []
        self.selected_route_index = 0

        # 重置搜索相关
        self.search_results = []
        self.searching_for = None
        self.selected_search_result_coords = None

        # 重置最后选中信息
        self.last_selected_coords = None
        self.last_selected_level = None
        self.last_selected_type = None
        self.last_selected_from_search = False

    def get_all_points(self) -> List[Tuple[float, float]]:
        """获取所有点（起点+途径点+终点）

        返回:
            包含所有点坐标的列表，顺序为：起点 -> 途径点 -> 终点
        """
        points = []
        if self.start_location:
            points.append(self.start_location.coords)
        for wp in self.waypoints:
            points.append(wp.coords)
        if self.end_location:
            points.append(self.end_location.coords)
        return points

    def has_route(self) -> bool:
        """检查是否有路线数据

        返回:
            如果有路线数据返回True，否则返回False
        """
        return bool(self.route_points)

    def has_start_end(self) -> bool:
        """检查是否同时设置了起点和终点

        返回:
            如果同时设置了起点和终点返回True，否则返回False
        """
        return self.start_location is not None and self.end_location is not None

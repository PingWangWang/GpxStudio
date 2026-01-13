"""
数据状态管理器
负责管理应用的所有数据状态
"""

from typing import Optional, List, Tuple


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
        # 起点信息
        self.start_coords: Optional[Tuple[float, float]] = None  # 起点坐标 (纬度, 经度)
        self.start_name: Optional[str] = None  # 起点名称
        self.start_level: Optional[str] = None  # 起点精度级别

        # 终点信息
        self.end_coords: Optional[Tuple[float, float]] = None  # 终点坐标 (纬度, 经度)
        self.end_name: Optional[str] = None  # 终点名称
        self.end_level: Optional[str] = None  # 终点精度级别

        # 途径点信息
        self.waypoints_coords: List[Tuple[float, float]] = []  # 途径点坐标列表
        self.waypoints_names: List[str] = []  # 途径点名称列表

        # 路线数据
        self.current_route = None  # 当前路线对象
        self.route_points: List[Tuple[float, float]] = []  # 路线坐标点列表
        self.estimated_duration_seconds: int = 0  # 预估路线耗时（秒）

        # 搜索相关
        self.search_results: List = []  # 搜索结果列表
        self.searching_for: Optional[str] = None  # 当前搜索的类型（起点/终点/途径点）
        self.selected_search_result_coords: Optional[Tuple[float, float]] = None  # 选中的搜索结果坐标

        # 当前位置
        self.current_location: Optional[Tuple[float, float]] = None  # 当前定位位置

        # 最后选中的位置信息
        self.last_selected_coords: Optional[Tuple[float, float]] = None  # 最后选中的坐标
        self.last_selected_level: Optional[str] = None  # 最后选中的精度级别
        self.last_selected_type: Optional[str] = None  # 最后选中的类型
        self.last_selected_from_search: bool = False  # 是否从搜索结果中选中

        print("数据状态初始化完成")

    def set_start_location(self, coords: Tuple[float, float], name: str, level: Optional[str] = None):
        """设置起点
        
        参数:
            coords: 起点坐标 (纬度, 经度)
            name: 起点名称
            level: 起点精度级别（可选）
        """
        self.start_coords = coords
        self.start_name = name
        self.start_level = level
        self._update_last_selected(coords, level, None, False)

    def set_end_location(self, coords: Tuple[float, float], name: str, level: Optional[str] = None):
        """设置终点
        
        参数:
            coords: 终点坐标 (纬度, 经度)
            name: 终点名称
            level: 终点精度级别（可选）
        """
        self.end_coords = coords
        self.end_name = name
        self.end_level = level
        self._update_last_selected(coords, level, None, False)

    def add_waypoint(self, coords: Tuple[float, float], name: str):
        """添加途径点
        
        参数:
            coords: 途径点坐标 (纬度, 经度)
            name: 途径点名称
        """
        self.waypoints_coords.append(coords)
        self.waypoints_names.append(name)
        self._update_last_selected(coords, None, None, False)

    def update_waypoint(self, index: int, coords: Tuple[float, float], name: str):
        """更新途径点
        
        参数:
            index: 途径点索引
            coords: 新的途径点坐标 (纬度, 经度)
            name: 新的途径点名称
        """
        if 0 <= index < len(self.waypoints_coords):
            self.waypoints_coords[index] = coords
            self.waypoints_names[index] = name

    def remove_waypoint(self, index: int):
        """删除途径点
        
        参数:
            index: 要删除的途径点索引
        """
        if 0 <= index < len(self.waypoints_coords):
            self.waypoints_coords.pop(index)
            self.waypoints_names.pop(index)

    def clear_waypoints(self):
        """清空所有途径点"""
        self.waypoints_coords.clear()
        self.waypoints_names.clear()

    def set_route(self, route_points: List[Tuple[float, float]], duration_seconds: int = 0):
        """设置路线
        
        参数:
            route_points: 路线坐标点列表
            duration_seconds: 预估路线耗时（秒，可选）
        """
        self.route_points = route_points
        self.estimated_duration_seconds = duration_seconds

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
        # 重置起点信息
        self.start_coords = None
        self.start_name = None
        self.start_level = None
        
        # 重置终点信息
        self.end_coords = None
        self.end_name = None
        self.end_level = None
        
        # 重置途径点信息
        self.waypoints_coords = []
        self.waypoints_names = []
        
        # 重置路线数据
        self.current_route = None
        self.route_points = []
        self.estimated_duration_seconds = 0
        
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
        if self.start_coords:
            points.append(self.start_coords)
        points.extend(self.waypoints_coords)
        if self.end_coords:
            points.append(self.end_coords)
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
        return self.start_coords is not None and self.end_coords is not None

"""
路线渲染优化工具
提供路线点位简化和渲染性能优化功能
"""

import math
from typing import List, Tuple, Optional


class RouteOptimizer:
    """路线渲染优化器"""

    @staticmethod
    def douglas_peucker(points: List[Tuple[float, float]], epsilon: float) -> List[Tuple[float, float]]:
        """
        Douglas-Peucker算法简化路线点位
        
        Args:
            points: 原始路线点列表 [(lat, lon), ...]
            epsilon: 简化阈值，值越大简化程度越高
            
        Returns:
            简化后的路线点列表
        """
        if len(points) < 3:
            return points
            
        # 找到距离起点终点连线最远的点
        def point_line_distance(point: Tuple[float, float], line_start: Tuple[float, float], line_end: Tuple[float, float]) -> float:
            """计算点到直线的距离"""
            x0, y0 = point
            x1, y1 = line_start
            x2, y2 = line_end
            
            # 如果起点终点相同，返回点到起点的距离
            if x1 == x2 and y1 == y2:
                return math.sqrt((x0 - x1) ** 2 + (y0 - y1) ** 2)
            
            # 计算点到直线的垂直距离
            numerator = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1)
            denominator = math.sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2)
            
            return numerator / denominator if denominator > 0 else 0
        
        def simplify_recursive(point_list: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
            """递归简化点列表"""
            if len(point_list) < 3:
                return point_list
                
            start_point = point_list[0]
            end_point = point_list[-1]
            
            # 找到距离起点终点连线最远的点
            max_distance = 0
            max_index = 0
            
            for i in range(1, len(point_list) - 1):
                distance = point_line_distance(point_list[i], start_point, end_point)
                if distance > max_distance:
                    max_distance = distance
                    max_index = i
            
            # 如果最大距离小于阈值，只保留起点和终点
            if max_distance < epsilon:
                return [start_point, end_point]
            
            # 递归简化两段
            left_points = simplify_recursive(point_list[:max_index + 1])
            right_points = simplify_recursive(point_list[max_index:])
            
            # 合并结果，避免重复中间点
            return left_points[:-1] + right_points
        
        return simplify_recursive(points)

    @staticmethod
    def adaptive_simplify(points: List[Tuple[float, float]], zoom_level: int) -> List[Tuple[float, float]]:
        """
        根据缩放级别自适应简化路线点位
        
        Args:
            points: 原始路线点列表
            zoom_level: 地图缩放级别 (1-20)
            
        Returns:
            简化后的路线点列表
        """
        if not points or len(points) < 3:
            return points
        
        # 根据缩放级别确定简化阈值
        # 缩放级别越低（地图越小），简化程度越高
        if zoom_level >= 16:
            # 高缩放级别：保留更多细节
            epsilon = 0.00001  # 约1米
        elif zoom_level >= 14:
            # 中高缩放级别
            epsilon = 0.00005  # 约5米
        elif zoom_level >= 12:
            # 中等缩放级别
            epsilon = 0.0001   # 约10米
        elif zoom_level >= 10:
            # 中低缩放级别
            epsilon = 0.0005   # 约50米
        elif zoom_level >= 8:
            # 低缩放级别
            epsilon = 0.001    # 约100米
        else:
            # 极低缩放级别：大幅简化
            epsilon = 0.005    # 约500米
        
        return RouteOptimizer.douglas_peucker(points, epsilon)

    @staticmethod
    def uniform_sampling(points: List[Tuple[float, float]], max_points: int) -> List[Tuple[float, float]]:
        """
        均匀采样简化路线点位
        
        Args:
            points: 原始路线点列表
            max_points: 最大保留点数
            
        Returns:
            采样后的路线点列表
        """
        if not points or len(points) <= max_points:
            return points
        
        # 计算采样间隔
        step = len(points) / max_points
        sampled_points = []
        
        # 始终保留第一个点
        sampled_points.append(points[0])
        
        # 均匀采样中间点
        for i in range(1, max_points - 1):
            index = int(i * step)
            if index < len(points):
                sampled_points.append(points[index])
        
        # 始终保留最后一个点
        if len(points) > 1:
            sampled_points.append(points[-1])
        
        return sampled_points

    @staticmethod
    def optimize_route_for_rendering(route_points: List, zoom_level: int = 12, max_points: int = 1000) -> List:
        """
        为渲染优化路线点位
        
        Args:
            route_points: 原始路线点列表，可能包含None分隔符和海拔信息
            zoom_level: 地图缩放级别
            max_points: 每段路线的最大点数
            
        Returns:
            优化后的路线点列表
        """
        if not route_points:
            return route_points
        
        optimized_points = []
        current_segment = []
        
        for point in route_points:
            if point is None:
                # 处理当前段
                if current_segment:
                    # 转换为二维坐标进行优化
                    coords_2d = [(p[0], p[1]) for p in current_segment if len(p) >= 2]
                    
                    if len(coords_2d) > 2:
                        # 先进行自适应简化
                        simplified = RouteOptimizer.adaptive_simplify(coords_2d, zoom_level)
                        
                        # 如果简化后仍然太多点，进行均匀采样
                        if len(simplified) > max_points:
                            simplified = RouteOptimizer.uniform_sampling(simplified, max_points)
                        
                        # 恢复原始格式（包含海拔信息）
                        for coord in simplified:
                            # 在原始点中找到最接近的点，保留其海拔信息
                            closest_point = RouteOptimizer._find_closest_original_point(coord, current_segment)
                            optimized_points.append(closest_point)
                    else:
                        # 点数太少，直接保留
                        optimized_points.extend(current_segment)
                    
                    current_segment = []
                
                # 添加分隔符
                optimized_points.append(None)
            else:
                current_segment.append(point)
        
        # 处理最后一段
        if current_segment:
            coords_2d = [(p[0], p[1]) for p in current_segment if len(p) >= 2]
            
            if len(coords_2d) > 2:
                simplified = RouteOptimizer.adaptive_simplify(coords_2d, zoom_level)
                
                if len(simplified) > max_points:
                    simplified = RouteOptimizer.uniform_sampling(simplified, max_points)
                
                for coord in simplified:
                    closest_point = RouteOptimizer._find_closest_original_point(coord, current_segment)
                    optimized_points.append(closest_point)
            else:
                optimized_points.extend(current_segment)
        
        return optimized_points

    @staticmethod
    def _find_closest_original_point(target_coord: Tuple[float, float], original_points: List) -> Tuple:
        """
        在原始点列表中找到最接近目标坐标的点
        
        Args:
            target_coord: 目标坐标 (lat, lon)
            original_points: 原始点列表
            
        Returns:
            最接近的原始点（保留原始格式）
        """
        if not original_points:
            return target_coord
        
        min_distance = float('inf')
        closest_point = original_points[0]
        
        target_lat, target_lon = target_coord
        
        for point in original_points:
            if len(point) >= 2:
                point_lat, point_lon = point[0], point[1]
                distance = (target_lat - point_lat) ** 2 + (target_lon - point_lon) ** 2
                
                if distance < min_distance:
                    min_distance = distance
                    closest_point = point
        
        return closest_point

    @staticmethod
    def calculate_optimal_zoom(points: List[Tuple[float, float]]) -> int:
        """
        根据路线点分布计算最优缩放级别
        
        Args:
            points: 路线点列表
            
        Returns:
            建议的缩放级别
        """
        if not points or len(points) < 2:
            return 12
        
        # 计算边界框
        lats = [p[0] for p in points if p is not None]
        lons = [p[1] for p in points if p is not None]
        
        if not lats or not lons:
            return 12
        
        lat_range = max(lats) - min(lats)
        lon_range = max(lons) - min(lons)
        max_range = max(lat_range, lon_range)
        
        # 根据范围确定缩放级别
        if max_range > 10:
            return 4   # 国家级
        elif max_range > 5:
            return 5   # 大区域
        elif max_range > 2:
            return 6   # 省级
        elif max_range > 1:
            return 7   # 大城市
        elif max_range > 0.5:
            return 8   # 城市
        elif max_range > 0.2:
            return 9   # 城区
        elif max_range > 0.1:
            return 10  # 区域
        elif max_range > 0.05:
            return 11  # 街区
        elif max_range > 0.02:
            return 12  # 街道
        elif max_range > 0.01:
            return 13  # 详细街道
        elif max_range > 0.005:
            return 14  # 小区域
        else:
            return 15  # 精细级别
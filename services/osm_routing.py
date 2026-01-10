"""
OSM路线规划服务
使用OSRM API实现OSM地图的路线规划功能
"""

import requests
from typing import Optional, List, Dict, Callable, Tuple
from modules.routing.interfaces.routing_service import IRoutingService
import math


class OsmRoutingService(IRoutingService):
    """
    OSM路线规划服务
    使用OSRM API实现路线规划功能
    """

    def __init__(self, api_key: str = "", security_key: str = "", logger: Optional[Callable] = None):
        """
        初始化OSM路线规划服务

        Args:
            api_key: API密钥（OSRM不需要，保留参数以兼容接口）
            security_key: 安全密钥（不需要，保留参数以兼容接口）
            logger: 日志记录器函数，接收(level, message)参数
        """
        self.logger = logger
        # OSRM公共API基础URL，不需要API密钥
        self.base_url = "https://router.project-osrm.org/route/v1"
        # 保存最近一次路线规划的实际距离（公里）
        self.last_route_distance = 0.0

    def _log(self, level: str, message: str):
        """
        记录日志

        Args:
            level: 日志级别
            message: 日志消息
        """
        if self.logger:
            self.logger(level, message)

    def plan_route(self, points: List[Tuple[float, float]], transport_mode: str = "驾车") -> Tuple[List[Tuple[float, float]], int]:
        """
        使用OSRM API规划路线

        Args:
            points: 坐标点列表 [(lat, lon), ...]
            transport_mode: 交通方式（步行/骑行/驾车）

        Returns:
            tuple: (路线点列表， estimated_duration_seconds)
                  路线点列表段之间用None分隔
                  estimated_duration_seconds为预估时间（秒）
        """
        try:
            # 验证点数量
            if len(points) < 2:
                self._log("WARNING", f"OSM路线规划点数量不足: {len(points)}，至少需要2个点")
                return [], 0
            
            # 转换交通方式为OSRM支持的类型
            vehicle = self._get_vehicle_type(transport_mode)
            
            route_points = []
            estimated_duration = 0
            total_distance = 0.0

            self._log("INFO", f"开始规划路线，交通方式: {transport_mode} ({vehicle})")

            # 逐段规划路线
            for i in range(len(points) - 1):
                start = points[i]
                end = points[i + 1]

                self._log("DEBUG", f"规划路段 {i+1}/{len(points)-1}: {start} -> {end}")

                # 构建OSRM API请求URL
                # 尝试使用不同的API端点格式
                # 注意：OSRM公共API可能对不同交通方式的支持有限
                url = f"{self.base_url}/{vehicle}/{start[1]},{start[0]};{end[1]},{end[0]}?overview=full&geometries=geojson"

                self._log("DEBUG", f"请求OSRM API: {url}")

                # 发送请求
                response = requests.get(url, timeout=30)
                
                # 检查响应状态
                self._log("DEBUG", f"OSRM API响应状态: {response.status_code}")
                
                # 打印完整的响应URL（用于调试）
                self._log("DEBUG", f"完整响应URL: {response.url}")
                
                # 解析响应
                data = response.json()
                self._log("DEBUG", f"OSRM API响应代码: {data.get('code')}")
                
                # 打印完整的响应内容（仅用于调试）
                if 'routes' in data and data['routes']:
                    route = data['routes'][0]
                    self._log("DEBUG", f"OSRM API响应 - 距离: {route.get('distance')}, 时间: {route.get('duration')}")
                    # 打印路线点数量
                    if 'geometry' in route and 'coordinates' in route['geometry']:
                        self._log("DEBUG", f"OSRM API响应 - 路线点数量: {len(route['geometry']['coordinates'])}")

                if data.get("code") == "Ok":
                    route = data["routes"][0]
                    coordinates = route["geometry"]["coordinates"]
                    
                    # 添加路线点（转换为(lat, lon)格式）
                    for coord in coordinates:
                        route_points.append((coord[1], coord[0]))

                    # 提取预估时间（秒）
                    # OSRM返回的时间单位是秒
                    if "duration" in route:
                        estimated_duration += int(route["duration"])

                    # 提取实际距离（米）
                    if "distance" in route:
                        distance_meters = route["distance"]
                        distance_km = distance_meters / 1000
                        total_distance += distance_km
                        self._log("INFO", f"路段 {i+1} 规划成功，获取 {len(coordinates)} 个坐标点，距离: {distance_km:.2f}公里，预估时间: {int(route.get('duration', 0))}秒")
                    else:
                        self._log("INFO", f"路段 {i+1} 规划成功，获取 {len(coordinates)} 个坐标点，预估时间: {int(route.get('duration', 0))}秒")

                    # 段之间添加分隔符
                    if i < len(points) - 2:
                        route_points.append(None)
                else:
                    error_msg = data.get('message', 'Unknown error')
                    self._log("ERROR", f"路段 {i+1} 规划失败: {error_msg}")

            if route_points:
                # 保存总距离
                self.last_route_distance = total_distance
                self._log("INFO", f"OSM路线规划成功，路线点数量: {len([p for p in route_points if p is not None])}，总距离: {total_distance:.2f}公里，总预估时间: {estimated_duration}秒")
                return route_points, estimated_duration
            else:
                # 重置距离
                self.last_route_distance = 0.0
                self._log("WARNING", "OSM路线规划返回空路线")
                return [], 0
        except Exception as e:
            self._log("ERROR", f"OSM路线规划异常: {str(e)}")
            return [], 0

    def calculate_distance(self, route_points: List[Tuple[float, float]]) -> float:
        """
        计算路线距离

        Args:
            route_points: 路线点列表

        Returns:
            float: 距离（公里）
        """
        try:
            # 直接使用Haversine公式计算路线距离
            # 注意：这是基于路线点的直线距离计算，不是实际道路距离
            total_distance = 0.0
            for i in range(1, len(route_points)):
                if route_points[i-1] and route_points[i]:
                    lat1, lon1 = route_points[i-1]
                    lat2, lon2 = route_points[i]
                    distance = self._haversine_distance(lat1, lon1, lat2, lon2)
                    total_distance += distance
            
            self._log("INFO", f"使用Haversine公式计算路线距离: {total_distance:.2f}公里")
            return total_distance
        except Exception as e:
            self._log("ERROR", f"计算路线距离异常: {str(e)}")
            return 0.0

    def _get_vehicle_type(self, transport_mode: str) -> str:
        """
        将交通方式转换为OSRM支持的profile类型

        Args:
            transport_mode: 交通方式（步行/骑行/驾车）

        Returns:
            str: OSRM支持的profile类型
        """
        mode_map = {
            "驾车": "car",
            "步行": "foot",
            "骑行": "bike"
        }
        return mode_map.get(transport_mode, "car")

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        使用Haversine公式计算两点之间的距离

        Args:
            lat1: 第一个点的纬度
            lon1: 第一个点的经度
            lat2: 第二个点的纬度
            lon2: 第二个点的经度

        Returns:
            float: 两点之间的距离（公里）
        """
        # 地球半径（公里）
        R = 6371.0
        
        # 转换为弧度
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # 差值
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Haversine公式
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        # 距离（公里）
        distance = R * c
        return distance

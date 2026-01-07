"""
路由规划服务
使用OSRM API进行路线规划
"""

import requests
from typing import Optional, Callable


class RoutingService:
    """路由规划服务，负责路线规划"""

    # OSRM API基础URL
    OSRM_BASE_URL = "http://router.project-osrm.org/route/v1"

    # 交通方式映射
    TRANSPORT_MODES = {
        "步行": "foot",
        "骑行": "bike",
        "驾车": "car"
    }

    def __init__(self, logger: Optional[Callable] = None):
        self.logger = logger

    def log(self, level: str, message: str):
        """输出日志"""
        if self.logger:
            self.logger(level, message)

    def plan_route(self, points, transport_mode="驾车"):
        """
        规划路线

        Args:
            points: 坐标点列表 [(lat, lon), ...]
            transport_mode: 交通方式（步行/骑行/驾车）

        Returns:
            list: 路线点列表，段之间用None分隔
        """
        mode = self.TRANSPORT_MODES.get(transport_mode, "car")
        route_points = []

        def log_cb(level, message):
            if self.logger:
                self.logger(level, message)

        log_cb("INFO", f"开始规划路线，交通方式: {transport_mode} ({mode})")

        try:
            # 逐段规划路线
            for i in range(len(points) - 1):
                start = points[i]
                end = points[i + 1]

                log_cb("DEBUG", f"规划路段 {i+1}/{len(points)-1}: {start} -> {end}")

                url = (f"{self.OSRM_BASE_URL}/{mode}/"
                       f"{start[1]},{start[0]};{end[1]},{end[0]}"
                       f"?overview=full&geometries=geojson")

                log_cb("DEBUG", f"请求OSRM API: {url}")

                response = requests.get(url)
                data = response.json()

                if data.get("code") == "Ok":
                    route = data["routes"][0]
                    coordinates = route["geometry"]["coordinates"]

                    # 添加路线点（经纬度转换）
                    for coord in coordinates:
                        route_points.append((coord[1], coord[0]))

                    log_cb("INFO", f"路段 {i+1} 规划成功，获取 {len(coordinates)} 个坐标点")

                    # 段之间添加分隔符
                    if i < len(points) - 2:
                        route_points.append(None)
                else:
                    error_msg = data.get('message', 'Unknown error')
                    log_cb("ERROR", f"路段 {i+1} 规划失败: {error_msg}")

            log_cb("INFO", f"路线规划完成，共 {len([p for p in route_points if p is not None])} 个坐标点")
            return route_points

        except Exception as e:
            log_cb("ERROR", f"路线规划异常: {str(e)}")
            return []

    def calculate_distance(self, route_points):
        """
        计算路线总距离

        Args:
            route_points: 路线点列表

        Returns:
            float: 总距离（公里）
        """
        from geopy.distance import geodesic

        def log_cb(level, message):
            if self.logger:
                self.logger(level, message)

        total_distance = 0
        prev_point = None

        for point in route_points:
            if point is None:
                prev_point = None
                continue

            if prev_point:
                total_distance += geodesic(prev_point, point).kilometers

            prev_point = point

        log_cb("INFO", f"路线总距离: {total_distance:.2f} 公里")
        return total_distance

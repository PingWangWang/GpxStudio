"""
高德地图路线规划服务
使用高德地图Web服务API进行路线规划
"""

import requests
import hashlib
from typing import Optional, Callable, List


class GaodeRoutingService:
    """高德地图路线规划服务"""

    DIRECTION_URL = "https://restapi.amap.com/v3/direction"

    TRANSPORT_MODES = {
        "步行": "walking",
        "骑行": "bicycling",
        "驾车": "driving"
    }

    def __init__(self, api_key: str = "", security_key: str = "", logger: Optional[Callable] = None):
        self.api_key = api_key
        self.security_key = security_key
        self.logger = logger

    def log(self, level: str, message: str):
        """输出日志"""
        if self.logger:
            self.logger(level, message)

    def _sign(self, params: dict) -> str:
        """生成签名"""
        if not self.security_key:
            return ""
        sorted_params = sorted(params.items())
        sign_str = self.security_key + ''.join(f"{k}{v}" for k, v in sorted_params)
        return hashlib.md5(sign_str.encode()).hexdigest()

    def plan_route(self, points: List[tuple], transport_mode: str = "驾车") -> tuple:
        """
        规划路线

        Args:
            points: 坐标点列表 [(lat, lon), ...]
            transport_mode: 交通方式（步行/骑行/驾车）

        Returns:
            tuple: (路线点列表， estimated_duration_seconds)
                  路线点列表段之间用None分隔
                  estimated_duration_seconds为预估时间（秒）
        """
        def log_cb(level, message):
            if self.logger:
                self.logger(level, message)

        if not self.api_key:
            log_cb("WARNING", "高德地图API Key未配置")
            return [], 0

        mode = self.TRANSPORT_MODES.get(transport_mode, "driving")
        route_points = []
        total_duration = 0

        log_cb("INFO", f"开始规划路线，交通方式: {transport_mode} ({mode})")

        try:
            for i in range(len(points) - 1):
                start = points[i]
                end = points[i + 1]

                log_cb("DEBUG", f"规划路段 {i+1}/{len(points)-1}: {start} -> {end}")

                params = {
                    'key': self.api_key,
                    'origin': f"{start[1]},{start[0]}",
                    'destination': f"{end[1]},{end[0]}",
                    'output': 'json'
                }

                if mode == 'walking':
                    params['strategy'] = '0'
                elif mode == 'bicycling':
                    params['strategy'] = '0'
                else:
                    params['strategy'] = '0'
                    params['extensions'] = 'base'

                if self.security_key:
                    params['sig'] = self._sign(params)

                url = f"{self.DIRECTION_URL}/{mode}"
                response = requests.get(url, params=params, timeout=10)
                data = response.json()

                if data.get('status') == '1':
                    route_data = data.get('route', {})
                    if mode == 'driving':
                        paths = route_data.get('paths', [])
                        if paths:
                            path = paths[0]
                            steps = path.get('steps', [])
                            segment_duration = int(path.get('duration', 0))
                            total_duration += segment_duration
                            for step in steps:
                                polyline = step.get('polyline', '')
                                if polyline:
                                    coords = polyline.split(';')
                                    for coord in coords:
                                        parts = coord.split(',')
                                        if len(parts) == 2:
                                            route_points.append((float(parts[1]), float(parts[0])))
                    else:
                        route_data = data.get('route', {})
                        if route_data:
                            segment_duration = int(route_data.get('duration', 0))
                            total_duration += segment_duration
                            steps = route_data.get('steps', [])
                            for step in steps:
                                polyline = step.get('polyline', '')
                                if polyline:
                                    coords = polyline.split(';')
                                    for coord in coords:
                                        parts = coord.split(',')
                                        if len(parts) == 2:
                                            route_points.append((float(parts[1]), float(parts[0])))

                    log_cb("INFO", f"路段 {i+1} 规划成功")
                else:
                    error_msg = data.get('info', '未知错误')
                    log_cb("ERROR", f"路段 {i+1} 规划失败: {error_msg}")

                if i < len(points) - 2:
                    route_points.append(None)

            log_cb("INFO", f"路线规划完成，共 {len([p for p in route_points if p is not None])} 个坐标点，预估时间: {total_duration} 秒")
            return route_points, total_duration

        except Exception as e:
            log_cb("ERROR", f"路线规划异常: {str(e)}")
            return [], 0

    def calculate_distance(self, route_points: List[tuple]) -> float:
        """
        计算路线总距离

        Args:
            route_points: 路线点列表

        Returns:
            float: 总距离（公里）
        """
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
                from geopy.distance import geodesic
                total_distance += geodesic(prev_point, point).kilometers

            prev_point = point

        log_cb("INFO", f"路线总距离: {total_distance:.2f} 公里")
        return total_distance

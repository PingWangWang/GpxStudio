"""
高德地图路线规划服务模块

该模块实现了高德地图路线规划服务的封装，提供以下功能：
1. 多交通方式路线规划：支持步行、骑行、驾车三种交通方式
2. 路线点获取：获取详细的路线坐标点
3. 海拔数据获取：通过Open-Elevation API获取路线点的海拔信息
4. 距离计算：计算规划路线的总距离
5. 签名生成：支持安全密钥签名验证

依赖：
- requests：用于发送HTTP请求
- hashlib：用于生成MD5签名
- typing：用于类型注解
- geopy：用于计算两点之间的距离

接口规范遵循高德地图Web服务API官方文档：
- 路线规划：https://lbs.amap.com/api/webservice/guide/api/direction
- 步行路线：https://lbs.amap.com/api/webservice/guide/api/direction#walking
- 骑行路线：https://lbs.amap.com/api/webservice/guide/api/direction#bicycling
- 驾车路线：https://lbs.amap.com/api/webservice/guide/api/direction#driving
"""

import requests
import hashlib
from typing import Optional, Callable, List, Tuple

from modules.routing.interfaces.routing_service import IRoutingService


class GaodeRoutingService(IRoutingService):
    """高德地图路线规划服务实现类

    该类实现了IRoutingService接口，封装了高德地图路线规划相关的API调用
    """

    # 不同交通方式使用不同的API版本
    DIRECTION_URLS = {
        "walking": "https://restapi.amap.com/v3/direction/walking",    # 步行路线API（v3版本）
        "bicycling": "https://restapi.amap.com/v4/direction/bicycling",  # 骑行路线API（v4版本）
        "driving": "https://restapi.amap.com/v3/direction/driving"      # 驾车路线API（v3版本）
    }

    # 交通方式映射（中文到英文）
    TRANSPORT_MODES = {
        "步行": "walking",    # 步行交通方式
        "骑行": "bicycling",  # 骑行交通方式
        "驾车": "driving"     # 驾车交通方式
    }

    # 海拔API基础URL（使用Open-Elevation API）
    ELEVATION_API_URL = "https://api.open-elevation.com/api/v1/lookup"

    # 保存最近一次路线规划的带海拔的点列表
    last_route_points_with_elevation = []

    def __init__(self, api_key: str = "", security_key: str = "", logger: Optional[Callable] = None):
        """
        初始化高德路线规划服务

        Args:
            api_key (str): 高德地图Web服务API密钥
            security_key (str): 高德地图安全密钥（可选，用于生成签名）
            logger (Callable): 日志记录回调函数，格式为logger(level: str, message: str)
        """
        # 存储API密钥
        self.api_key = api_key
        # 存储安全密钥（用于签名生成）
        self.security_key = security_key
        # 存储日志记录器
        self.logger = logger

    def log(self, level: str, message: str):
        """
        记录日志信息

        Args:
            level (str): 日志级别，如"DEBUG", "INFO", "WARNING", "ERROR"
            message (str): 日志内容
        """
        if self.logger:
            self.logger(level, message)

    def _sign(self, params: dict) -> str:
        """
        根据高德地图API签名规则生成请求签名

        签名生成规则（遵循高德官方文档）：
        1. 将请求参数按键名升序排列
        2. 将安全密钥作为前缀
        3. 拼接所有"key+value"字符串
        4. 使用MD5加密生成32位小写十六进制签名

        Args:
            params (dict): 请求参数字典

        Returns:
            str: 生成的签名字符串，安全密钥为空时返回空字符串
        """
        if not self.security_key:
            return ""

        # 1. 参数按键名升序排序
        sorted_params = sorted(params.items())

        # 2. 拼接安全密钥和参数键值对
        sign_str = self.security_key + ''.join(f"{k}{v}" for k, v in sorted_params)

        # 3. 生成MD5签名并返回
        return hashlib.md5(sign_str.encode()).hexdigest()

    def _get_elevation(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float, float]]:
        """
        获取多个坐标点的海拔数据

        使用Open-Elevation API获取给定坐标点的海拔信息

        Args:
            points (List[Tuple[float, float]]): 坐标点列表，格式为 [(lat, lon), ...]

        Returns:
            List[Tuple[float, float, float]]: 带海拔的点列表，格式为 [(lat, lon, elevation), ...]
            失败时返回默认海拔为0的点列表
        """
        if not points:
            return []

        try:
            # 构建Open-Elevation API请求数据
            locations = [{"latitude": lat, "longitude": lon} for lat, lon in points]
            payload = {"locations": locations}

            def log_cb(level, message):
                if self.logger:
                    self.logger(level, message)

            log_cb("DEBUG", f"请求海拔数据，点数: {len(points)}")

            # 发送POST请求到Open-Elevation API获取海拔数据
            response = requests.post(self.ELEVATION_API_URL, json=payload, timeout=30)
            data = response.json()

            # 检查响应格式是否正确
            if "results" in data:
                results = data["results"]
                points_with_elevation = []

                # 处理每个点的海拔数据
                for i, result in enumerate(results):
                    lat, lon = points[i]
                    elevation = result.get("elevation", 0.0)
                    points_with_elevation.append((lat, lon, elevation))

                log_cb("INFO", f"成功获取 {len(points_with_elevation)} 个点的海拔数据")
                return points_with_elevation
            else:
                log_cb("WARNING", "海拔API响应格式错误")
                return [(lat, lon, 0.0) for lat, lon in points]
        except Exception as e:
            def log_cb(level, message):
                if self.logger:
                    self.logger(level, message)

            log_cb("ERROR", f"获取海拔数据异常: {str(e)}")
            # 异常时返回默认海拔为0的点列表
            return [(lat, lon, 0.0) for lat, lon in points]

    def plan_route(self, points: List[tuple], transport_mode: str = "驾车") -> tuple:
        """
        根据给定的坐标点和交通方式规划路线

        使用高德地图路线规划API，为给定的一系列点规划连续的路线，并获取详细的路线点信息和海拔数据

        Args:
            points (List[tuple]): 坐标点列表，格式为 [(lat, lon), ...]，至少包含两个点
            transport_mode (str): 交通方式，支持 "步行"、"骑行"、"驾车"，默认值为 "驾车"

        Returns:
            tuple: (路线点列表，预估时间)
                  - 路线点列表：带海拔的坐标点列表，格式为 [(lat, lon, elevation), ..., None, ...]
                    段之间用None分隔
                  - 预估时间：路线总预估时间（秒）
                  规划失败时返回 ([], 0)
        """
        def log_cb(level, message):
            if self.logger:
                self.logger(level, message)

        if not self.api_key:
            log_cb("WARNING", "高德地图API Key未配置")
            return [], 0

        # 将中文交通方式转换为英文标识
        mode = self.TRANSPORT_MODES.get(transport_mode, "driving")
        # 存储完整路线点
        route_points = []
        # 总预估时间（秒）
        total_duration = 0

        log_cb("INFO", f"开始规划路线，交通方式: {transport_mode} ({mode})")

        try:
            # 逐段规划路线（相邻点之间）
            for i in range(len(points) - 1):
                start = points[i]
                end = points[i + 1]

                log_cb("DEBUG", f"规划路段 {i+1}/{len(points)-1}: {start} -> {end}")

                # 构建路线规划请求参数
                params = {
                    'key': self.api_key,                         # API密钥
                    'origin': f"{start[1]},{start[0]}",          # 起点坐标，格式："lon,lat"
                    'destination': f"{end[1]},{end[0]}",         # 终点坐标，格式："lon,lat"
                    'output': 'json'                             # 返回格式为JSON
                }

                # 根据交通方式设置不同的策略参数
                if mode == 'walking':
                    # 步行路线策略：0=推荐路线
                    params['strategy'] = '0'
                elif mode == 'bicycling':
                    # 骑行路线策略：0=推荐路线
                    params['strategy'] = '0'
                else:
                    # 驾车路线策略：0=速度优先
                    params['strategy'] = '0'
                    params['extensions'] = 'base'                # 基础信息

                # 如果配置了安全密钥，生成签名
                if self.security_key:
                    params['sig'] = self._sign(params)

                # 获取对应的API URL
                url = self.DIRECTION_URLS.get(mode, self.DIRECTION_URLS["driving"])
                # 发送GET请求到高德路线规划API
                response = requests.get(url, params=params, timeout=10)
                # 解析JSON响应
                data = response.json()

                # 处理不同API版本的响应格式（骑行API使用v4版本，步行和驾车使用v3版本）
                success = False
                route_data = {}
                paths = []
                segment_duration = 0

                if mode == 'bicycling':
                    # v4版本的骑行API响应格式
                    if data.get('errcode') == 0:
                        success = True
                        route_data = data.get('data', {})
                        paths = route_data.get('paths', [])
                else:
                    # v3版本的API响应格式
                    if data.get('status') == '1':
                        success = True
                        route_data = data.get('route', {})
                        paths = route_data.get('paths', [])

                if success and paths:
                    # 取第一条路线
                    path = paths[0]
                    # 获取路线步骤
                    steps = path.get('steps', [])

                    # 处理持续时间（v4版本返回的是数字，v3版本返回的是字符串）
                    duration_val = path.get('duration', 0)
                    segment_duration = int(duration_val) if isinstance(duration_val, (str, int)) else 0
                    total_duration += segment_duration

                    # 解析路线点
                    segment_points = []
                    for step in steps:
                        # 获取步骤的坐标串
                        polyline = step.get('polyline', '')
                        if polyline:
                            # 解析坐标串，格式为 "lon,lat;lon,lat;..."
                            coords = polyline.split(';')
                            for coord in coords:
                                parts = coord.split(',')
                                if len(parts) == 2:
                                    # 转换为 (lat, lon) 格式
                                    segment_points.append((float(parts[1]), float(parts[0])))

                    # 获取路线点的海拔数据
                    if segment_points:
                        segment_points_with_elevation = self._get_elevation(segment_points)
                        route_points.extend(segment_points_with_elevation)

                    log_cb("INFO", f"路段 {i+1} 规划成功")
                else:
                    # 处理路线规划失败
                    if mode == 'bicycling':
                        error_msg = data.get('errmsg', '未知错误')
                    else:
                        error_msg = data.get('info', '未知错误')
                    log_cb("ERROR", f"路段 {i+1} 规划失败: {error_msg}")

                # 在路段之间添加None分隔符（最后一段不需要）
                if i < len(points) - 2:
                    route_points.append(None)

            # 路线规划完成，记录日志
            log_cb("INFO", f"路线规划完成，共 {len([p for p in route_points if p is not None])} 个坐标点，预估时间: {total_duration} 秒")
            # 保存带海拔的路线点
            self.last_route_points_with_elevation = route_points
            return route_points, total_duration

        except Exception as e:
            # 捕获路线规划异常
            log_cb("ERROR", f"路线规划异常: {str(e)}")
            # 重置路线点
            self.last_route_points_with_elevation = []
            return [], 0

    def calculate_distance(self, route_points: List[tuple]) -> float:
        """
        计算规划路线的总距离

        使用geopy库的geodesic函数计算路线点之间的距离总和

        Args:
            route_points (List[tuple]): 路线点列表，格式为 [(lat, lon), ..., None, ...] 或 [(lat, lon, elevation), ...]

        Returns:
            float: 路线总距离（公里），保留两位小数
        """
        def log_cb(level, message):
            if self.logger:
                self.logger(level, message)

        total_distance = 0
        prev_point = None

        # 遍历路线点计算总距离
        for point in route_points:
            # 遇到None分隔符时重置前一个点
            if point is None:
                prev_point = None
                continue

            if prev_point:
                # 动态导入geopy.distance.geodesic函数
                from geopy.distance import geodesic
                # 提取点的前两个元素（纬度和经度），忽略海拔数据
                prev_point_coords = prev_point[:2] if len(prev_point) >= 2 else prev_point
                current_point_coords = point[:2] if len(point) >= 2 else point
                # 计算两点之间的地理距离并累加
                total_distance += geodesic(prev_point_coords, current_point_coords).kilometers

            prev_point = point

        # 记录总距离日志
        log_cb("INFO", f"路线总距离: {total_distance:.2f} 公里")
        return total_distance

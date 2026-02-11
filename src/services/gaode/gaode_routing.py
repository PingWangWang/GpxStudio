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
        "步行": "walking", "骑行": "bicycling", "驾车": "driving",
        "walking": "walking", "cycling": "bicycling", "driving": "driving"  # 添加英文支持
    }

    # 海拔API基础URL（使用OpenTopoData API）
    ELEVATION_API_URL = "https://api.opentopodata.org/v1/srtm30m"

    # 保存最近一次路线规划的带海拔的点列表
    last_route_points_with_elevation = []

    # 海拔数据缓存，格式为 {(lat, lon): elevation}
    _elevation_cache = {}

    # 批量处理的最大点数量
    MAX_POINTS_PER_REQUEST = 100

    # 最大重试次数
    MAX_RETRY_COUNT = 3

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

        使用Open-Elevation API获取给定坐标点的海拔信息，当点数超过1000时，只提取均匀分布的1000个点的海拔，然后对其他点进行插值计算

        Args:
            points (List[Tuple[float, float]]): 坐标点列表，格式为 [(lat, lon), ...] 或 [(lat, lon, elevation), ...]

        Returns:
            List[Tuple[float, float, float]]: 带海拔的点列表，格式为 [(lat, lon, elevation), ...]
            失败时返回默认海拔为0的点列表
        """
        if not points:
            return []

        # 处理可能带有海拔数据的点列表，确保只使用前两个元素(lat, lon)
        def get_lat_lon(point):
            """从点中提取经纬度，处理可能带有海拔数据的情况"""
            if len(point) >= 2:
                return point[0], point[1]
            else:
                return point[0], point[1] if len(point) > 1 else 0.0

        # Open-Elevation API配置
        ELEVATION_API_URL = "https://api.open-elevation.com/api/v1/lookup"
        MAX_POINTS_PER_REQUEST = 500  # 减小每批处理的点数量，避免服务器拒绝连接
        MAX_RETRY_COUNT = 3
        REQUEST_INTERVAL = 2  # 增加请求间隔时间（秒）
        MAX_ELEVATION_POINTS = 1000  # 最大获取海拔的点数量

        try:
            def log_cb(level, message):
                if self.logger:
                    self.logger(level, message)

            log_cb("DEBUG", f"请求海拔数据，总点数: {len(points)}")

            # 检查点数是否超过限制
            if len(points) <= MAX_ELEVATION_POINTS:
                # 点数在1000以内，获取所有点的海拔数据
                log_cb("INFO", "点数在1000以内，获取所有点的海拔数据")
                points_with_elevation = []
                total_batches = (len(points) + MAX_POINTS_PER_REQUEST - 1) // MAX_POINTS_PER_REQUEST

                for batch_index in range(total_batches):
                    start_idx = batch_index * MAX_POINTS_PER_REQUEST
                    end_idx = min((batch_index + 1) * MAX_POINTS_PER_REQUEST, len(points))
                    batch_points = points[start_idx:end_idx]

                    log_cb("DEBUG", f"处理第 {batch_index + 1}/{total_batches} 批，点数: {len(batch_points)}")

                    # 构建Open-Elevation API请求数据
                    locations = [{"latitude": get_lat_lon(p)[0], "longitude": get_lat_lon(p)[1]} for p in batch_points]
                    payload = {"locations": locations}

                    # 请求重试机制
                    retry_count = 0
                    batch_success = False

                    while retry_count < MAX_RETRY_COUNT:
                        try:
                            # 发送POST请求到Open-Elevation API获取海拔数据
                            log_cb("DEBUG", f"发送请求到Open-Elevation API，批次: {batch_index + 1}, 重试: {retry_count}")
                            response = requests.post(ELEVATION_API_URL, json=payload, timeout=30)
                            data = response.json()

                            # 检查响应格式是否正确
                            if "results" in data:
                                results = data["results"]
                                batch_result = []

                                # 处理每个点的海拔数据
                                for i, result in enumerate(results):
                                    if i < len(batch_points):
                                        lat, lon = get_lat_lon(batch_points[i])
                                        elevation = result.get("elevation", 0.0)
                                        batch_result.append((lat, lon, elevation))

                                points_with_elevation.extend(batch_result)
                                log_cb("INFO", f"成功获取第 {batch_index + 1} 批 {len(batch_result)} 个点的海拔数据")
                                batch_success = True
                                break  # 成功获取数据，跳出重试循环
                            else:
                                log_cb("WARNING", f"第 {batch_index + 1} 批Open-Elevation API响应格式错误")
                                retry_count += 1
                                if retry_count < MAX_RETRY_COUNT:
                                    wait_time = (retry_count + 1) * 2  # 指数退避
                                    log_cb("DEBUG", f"重试获取海拔数据，等待 {wait_time} 秒...")
                                    import time
                                    time.sleep(wait_time)

                        except Exception as e:
                            log_cb("ERROR", f"获取海拔数据异常: {str(e)}")
                            retry_count += 1
                            if retry_count < MAX_RETRY_COUNT:
                                wait_time = (retry_count + 1) * 2  # 指数退避
                                log_cb("DEBUG", f"重试获取海拔数据，等待 {wait_time} 秒...")
                                import time
                                time.sleep(wait_time)

                    # 如果重试失败，为这批点设置默认海拔
                    if not batch_success:
                        log_cb("WARNING", f"第 {batch_index + 1} 批点海拔数据获取失败，使用默认值0.0")
                        for p in batch_points:
                            lat, lon = get_lat_lon(p)
                            points_with_elevation.append((lat, lon, 0.0))

                    # 每批请求之间添加间隔时间，避免服务器拒绝连接
                    if batch_index < total_batches - 1:  # 不是最后一批
                        log_cb("DEBUG", f"批次处理完成，等待 {REQUEST_INTERVAL} 秒后处理下一批...")
                        import time
                        time.sleep(REQUEST_INTERVAL)

                log_cb("INFO", f"总共成功获取 {len(points_with_elevation)} 个点的海拔数据")
                return points_with_elevation
            else:
                # 点数超过1000，提取均匀分布的1000个点
                log_cb("INFO", f"点数超过1000，提取均匀分布的 {MAX_ELEVATION_POINTS} 个点获取海拔数据")

                # 提取均匀分布的点
                sampled_points = self._sample_points_uniformly(points, MAX_ELEVATION_POINTS)
                log_cb("DEBUG", f"提取了 {len(sampled_points)} 个均匀分布的点")

                # 获取采样点的海拔数据
                sampled_points_with_elevation = []
                total_batches = (len(sampled_points) + MAX_POINTS_PER_REQUEST - 1) // MAX_POINTS_PER_REQUEST

                for batch_index in range(total_batches):
                    start_idx = batch_index * MAX_POINTS_PER_REQUEST
                    end_idx = min((batch_index + 1) * MAX_POINTS_PER_REQUEST, len(sampled_points))
                    batch_points = sampled_points[start_idx:end_idx]

                    log_cb("DEBUG", f"处理采样点批次 {batch_index + 1}/{total_batches}，点数: {len(batch_points)}")

                    # 构建Open-Elevation API请求数据
                    locations = [{"latitude": get_lat_lon(p)[0], "longitude": get_lat_lon(p)[1]} for p in batch_points]
                    payload = {"locations": locations}

                    # 请求重试机制
                    retry_count = 0
                    batch_success = False

                    while retry_count < MAX_RETRY_COUNT:
                        try:
                            # 发送POST请求到Open-Elevation API获取海拔数据
                            log_cb("DEBUG", f"发送请求到Open-Elevation API，批次: {batch_index + 1}, 重试: {retry_count}")
                            response = requests.post(ELEVATION_API_URL, json=payload, timeout=30)
                            data = response.json()

                            # 检查响应格式是否正确
                            if "results" in data:
                                results = data["results"]
                                batch_result = []

                                # 处理每个点的海拔数据
                                for i, result in enumerate(results):
                                    if i < len(batch_points):
                                        lat, lon = get_lat_lon(batch_points[i])
                                        elevation = result.get("elevation", 0.0)
                                        batch_result.append((lat, lon, elevation))

                                sampled_points_with_elevation.extend(batch_result)
                                log_cb("INFO", f"成功获取第 {batch_index + 1} 批采样点海拔数据，点数: {len(batch_result)}")
                                batch_success = True
                                break  # 成功获取数据，跳出重试循环
                            else:
                                log_cb("WARNING", f"第 {batch_index + 1} 批Open-Elevation API响应格式错误")
                                retry_count += 1
                                if retry_count < MAX_RETRY_COUNT:
                                    wait_time = (retry_count + 1) * 2  # 指数退避
                                    log_cb("DEBUG", f"重试获取海拔数据，等待 {wait_time} 秒...")
                                    import time
                                    time.sleep(wait_time)

                        except Exception as e:
                            log_cb("ERROR", f"获取海拔数据异常: {str(e)}")
                            retry_count += 1
                            if retry_count < MAX_RETRY_COUNT:
                                wait_time = (retry_count + 1) * 2  # 指数退避
                                log_cb("DEBUG", f"重试获取海拔数据，等待 {wait_time} 秒...")
                                import time
                                time.sleep(wait_time)

                    # 如果重试失败，为这批点设置默认海拔
                    if not batch_success:
                        log_cb("WARNING", f"第 {batch_index + 1} 批采样点海拔数据获取失败，使用默认值0.0")
                        for p in batch_points:
                            lat, lon = get_lat_lon(p)
                            sampled_points_with_elevation.append((lat, lon, 0.0))

                    # 每批请求之间添加间隔时间，避免服务器拒绝连接
                    if batch_index < total_batches - 1:  # 不是最后一批
                        log_cb("DEBUG", f"批次处理完成，等待 {REQUEST_INTERVAL} 秒后处理下一批...")
                        import time
                        time.sleep(REQUEST_INTERVAL)

                # 使用采样点的海拔数据对所有点进行插值计算
                log_cb("INFO", "使用采样点的海拔数据对所有点进行插值计算")
                points_with_elevation = self._interpolate_elevation(points, sampled_points_with_elevation)
                log_cb("INFO", f"完成所有点的海拔插值计算，总点数: {len(points_with_elevation)}")

                return points_with_elevation
        except Exception as e:
            def log_cb(level, message):
                if self.logger:
                    self.logger(level, message)

            log_cb("ERROR", f"获取海拔数据异常: {str(e)}")
            # 异常时返回默认海拔为0的点列表
            return [(get_lat_lon(p)[0], get_lat_lon(p)[1], 0.0) for p in points]

    def _sample_points_uniformly(self, points: List[Tuple[float, float]], max_points: int) -> List[Tuple[float, float]]:
        """
        均匀采样点列表

        Args:
            points: 原始点列表
            max_points: 最大采样点数量

        Returns:
            均匀采样后的点列表
        """
        if len(points) <= max_points:
            return points

        # 计算采样间隔
        interval = len(points) / max_points
        sampled_points = []

        # 均匀采样点
        for i in range(max_points):
            index = int(round(i * interval))
            if index < len(points):
                sampled_points.append(points[index])

        # 确保包含最后一个点
        if len(sampled_points) > 0 and sampled_points[-1] != points[-1]:
            sampled_points[-1] = points[-1]

        return sampled_points

    def _interpolate_elevation(self, all_points: List[Tuple[float, float]], sampled_points_with_elevation: List[Tuple[float, float, float]]) -> List[Tuple[float, float, float]]:
        """
        使用采样点的海拔数据对所有点进行插值计算

        Args:
            all_points: 所有原始点列表，格式为 [(lat, lon), ...] 或 [(lat, lon, elevation), ...]
            sampled_points_with_elevation: 带海拔的采样点列表

        Returns:
            所有点的带海拔列表
        """
        # 处理可能带有海拔数据的点列表，确保只使用前两个元素(lat, lon)
        def get_lat_lon(point):
            """从点中提取经纬度，处理可能带有海拔数据的情况"""
            if len(point) >= 2:
                return point[0], point[1]
            else:
                return point[0], point[1] if len(point) > 1 else 0.0

        if not all_points or not sampled_points_with_elevation:
            return [(get_lat_lon(p)[0], get_lat_lon(p)[1], 0.0) for p in all_points]

        # 创建采样点的索引映射
        sampled_indices = []
        sampled_elevations = []

        # 为每个采样点找到其在原始列表中的索引
        for sampled_point in sampled_points_with_elevation:
            lat, lon, elevation = sampled_point
            # 查找该点在原始列表中的索引
            for i, point in enumerate(all_points):
                point_lat, point_lon = get_lat_lon(point)
                if point_lat == lat and point_lon == lon:
                    sampled_indices.append(i)
                    sampled_elevations.append(elevation)
                    break

        # 对所有点进行插值计算
        result = []
        for i, point in enumerate(all_points):
            lat, lon = get_lat_lon(point)

            # 查找该点位于哪两个采样点之间
            left_idx = -1
            right_idx = -1

            for j, sampled_idx in enumerate(sampled_indices):
                if sampled_idx <= i:
                    left_idx = j
                if sampled_idx >= i and right_idx == -1:
                    right_idx = j
                    break

            # 计算海拔
            if left_idx == -1:
                # 在第一个采样点之前
                elevation = sampled_elevations[0]
            elif right_idx == -1:
                # 在最后一个采样点之后
                elevation = sampled_elevations[-1]
            else:
                # 在两个采样点之间，线性插值
                left_sampled_idx = sampled_indices[left_idx]
                right_sampled_idx = sampled_indices[right_idx]
                left_elevation = sampled_elevations[left_idx]
                right_elevation = sampled_elevations[right_idx]

                if left_sampled_idx == right_sampled_idx:
                    elevation = left_elevation
                else:
                    # 线性插值
                    ratio = (i - left_sampled_idx) / (right_sampled_idx - left_sampled_idx)
                    elevation = left_elevation + (right_elevation - left_elevation) * ratio

            result.append((lat, lon, elevation))

        return result

    def plan_route(self, points: List[tuple], transport_mode: str = "驾车") -> tuple:
        """
        根据给定的坐标点和交通方式规划路线（返回多条路线方案）

        使用高德地图路线规划API，为给定的一系列点规划连续的路线，并获取详细的路线点信息和海拔数据

        Args:
            points (List[tuple]): 坐标点列表，格式为 [(lat, lon), ...]，至少包含两个点
            transport_mode (str): 交通方式，支持 "步行"、"骑行"、"驾车"，默认值为 "驾车"

        Returns:
            tuple: (路线方案列表，默认方案索引)
                  - 路线方案列表：每个方案包含 {
                      'route_points': 带海拔的坐标点列表,
                      'duration': 预估时间（秒）,
                      'distance': 路线距离（米）,
                      'tolls': 收费金额（元）,
                      'traffic_lights': 红绿灯数量,
                      'description': 路线描述
                    }
                  - 默认方案索引：默认选中的方案索引（通常为0）
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

        log_cb("INFO", f"开始规划路线，交通方式: {transport_mode} ({mode})")

        # 验证点数量
        if len(points) < 2:
            log_cb("WARNING", f"路线规划点数量不足: {len(points)}，至少需要2个点")
            return [], 0

        try:
            start = points[0]
            end = points[-1]

            # 构建路线规划请求参数
            params = {
                'key': self.api_key,                         # API密钥
                'origin': f"{start[1]},{start[0]}",          # 起点坐标，格式："lon,lat"
                'destination': f"{end[1]},{end[0]}",         # 终点坐标，格式："lon,lat"
                'output': 'json'                             # 返回格式为JSON
            }

            # 添加途经点（如果有）
            if len(points) > 2:
                waypoints = points[1:-1]
                # 高德地图API要求多个途经点使用英文分号分隔
                waypoints_str = ";".join([f"{lon},{lat}" for lat, lon in waypoints])
                params['waypoints'] = waypoints_str
                log_cb("DEBUG", f"规划路线: {start} -> {waypoints} -> {end}")
                log_cb("DEBUG", f"途经点字符串: {waypoints_str}")
            else:
                log_cb("DEBUG", f"规划路线: {start} -> {end}")

            # 根据交通方式设置不同的策略参数
            if mode == 'walking':
                # 步行路线策略：0=推荐路线（步行只返回一条路线）
                params['strategy'] = '0'
            elif mode == 'bicycling':
                # 骑行路线策略：0=推荐路线（骑行只返回一条路线）
                params['strategy'] = '0'
            else:
                # 驾车路线策略：11=返回三个结果（时间最短、距离最短、躲避拥堵）
                params['strategy'] = '11'
                params['extensions'] = 'all'                # 返回全部信息

            # 如果配置了安全密钥，生成签名
            if self.security_key:
                params['sig'] = self._sign(params)

            # 获取对应的API URL
            url = self.DIRECTION_URLS.get(mode, self.DIRECTION_URLS["driving"])
            # 发送GET请求到高德路线规划API
            response = requests.get(url, params=params, timeout=10)
            # 解析JSON响应
            data = response.json()

            # 处理不同API版本的响应格式
            success = False
            route_data = {}
            paths = []

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

            if not success or not paths:
                # 处理路线规划失败
                if mode == 'bicycling':
                    error_msg = data.get('errmsg', '未知错误')
                else:
                    error_msg = data.get('info', '未知错误')
                log_cb("ERROR", f"路线规划失败: {error_msg}")
                return [], 0

            # 解析所有路线方案
            route_alternatives = []
            for path_index, path in enumerate(paths):
                # 获取路线步骤
                steps = path.get('steps', [])

                # 处理持续时间
                duration_val = path.get('duration', 0)
                duration = int(duration_val) if isinstance(duration_val, (str, int)) else 0

                # 处理距离
                distance_val = path.get('distance', 0)
                distance = int(distance_val) if isinstance(distance_val, (str, int)) else 0

                # 处理收费（仅驾车模式）
                tolls = 0
                traffic_lights = 0
                if mode == 'driving':
                    tolls_val = path.get('tolls', 0)
                    tolls = int(tolls_val) if isinstance(tolls_val, (str, int)) else 0
                    traffic_lights_val = path.get('traffic_lights', 0)
                    traffic_lights = int(traffic_lights_val) if isinstance(traffic_lights_val, (str, int)) else 0

                # 记录原始数据用于调试
                log_cb("DEBUG", f"路线 {path_index}: 距离={distance}米, 时间={duration}秒, "
                              f"收费={tolls}元, 红绿灯={traffic_lights}个")

                # 解析路线点
                route_points = []
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
                                route_points.append((float(parts[1]), float(parts[0])))

                # 保存原始GCJ-02坐标，用于高德地图直接渲染
                # 同时将GCJ-02坐标转换为WGS-84坐标，以便统一存储和导出
                # 所有保存在本地的路线都应该使用国际坐标系WGS-84坐标
                from modules.geolocation.coordinate_transform import CoordinateTransform
                original_gcj02_points = route_points.copy()
                wgs84_route_points = []
                for point in route_points:
                    if point is not None:
                        lat, lon = point
                        wgs84_lat, wgs84_lon = CoordinateTransform.gcj02_to_wgs84(lat, lon)
                        wgs84_route_points.append((wgs84_lat, wgs84_lon))
                    else:
                        wgs84_route_points.append(None)
                route_points = wgs84_route_points
                log_cb("INFO", f"已将{len(route_points)}个GCJ-02坐标转换为WGS-84坐标")

                # 暂时保存路线数据（不生成描述）
                route_alternatives.append({
                    'route_points': route_points,  # 保存WGS-84坐标，用于统一存储和导出
                    'gcj02_route_points': original_gcj02_points,  # 保存原始GCJ-02坐标，用于高德地图直接渲染
                    'duration': duration,
                    'distance': distance,
                    'tolls': tolls,
                    'traffic_lights': traffic_lights,
                    'description': ''  # 稍后生成
                })

                log_cb("INFO", f"方案 {path_index + 1}: {len(route_points)} 个坐标点，"
                              f"距离 {distance/1000:.1f}km，时间 {duration//60}分钟")

            # 为所有路线生成描述（需要所有路线数据来比较）
            for path_index, route_alt in enumerate(route_alternatives):
                route_alt['description'] = self._generate_route_description(
                    route_alt,  # 传入route_alt而不是_path_data
                    mode,
                    path_index,
                    route_alternatives  # 传入所有路线方案
                )
                # 删除临时数据（如果存在）
                if '_path_data' in route_alt:
                    del route_alt['_path_data']

            # 路线规划完成
            log_cb("INFO", f"路线规划完成，共 {len(route_alternatives)} 个方案")

            return route_alternatives, 0  # 默认选中第一个方案

        except Exception as e:
            # 捕获路线规划异常
            log_cb("ERROR", f"路线规划异常: {str(e)}")
            # 重置路线点
            self.last_route_points_with_elevation = []
            return [], 0

    def _generate_route_description(self, path: dict, mode: str, index: int, all_paths: list = None) -> str:
        """生成路线描述

        Args:
            path: 当前路线数据
            mode: 交通方式
            index: 路线索引
            all_paths: 所有路线数据列表（用于比较）

        Returns:
            路线描述字符串
        """
        # 根据路线特征生成描述
        if mode == 'driving' and all_paths and len(all_paths) >= 2:
            # 驾车模式，根据实际数据判断路线类型
            current_distance = int(path.get('distance', 0))
            current_duration = int(path.get('duration', 0))

            # 获取所有路线的距离和时间
            distances = [int(p.get('distance', 0)) for p in all_paths]
            durations = [int(p.get('duration', 0)) for p in all_paths]

            # 判断当前路线的特征
            min_distance = min(distances)
            min_duration = min(durations)

            # 如果是距离最短的路线
            if current_distance == min_distance and current_distance < min(d for d in distances if d != current_distance or distances.count(d) > 1):
                return "距离最短"
            # 如果是时间最短的路线
            elif current_duration == min_duration and current_duration < min(d for d in durations if d != current_duration or durations.count(d) > 1):
                return "推荐方案"
            # 其他情况
            else:
                return "躲避拥堵"
        elif mode == 'driving':
            # 如果没有足够的数据，使用索引判断
            strategy_map = {
                0: "推荐方案",
                1: "距离最短",
                2: "躲避拥堵"
            }
            return strategy_map.get(index, f"方案{index + 1}")
        else:
            # 步行和骑行模式
            return "推荐方案" if index == 0 else f"方案{index + 1}"

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

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
        # 添加合适的请求头
        self.headers = {
            "User-Agent": "GPXStudio/1.2.0 (Route Planning Application; https://github.com/gpxstudio)"
        }
        # 保存最近一次路线规划的实际距离（公里）
        self.last_route_distance = 0.0
        # 海拔API基础URL（使用Open-Elevation API）
        self.elevation_api_url = "https://api.open-elevation.com/api/v1/lookup"
        # 保存最近一次路线规划的带海拔的点列表
        self.last_route_points_with_elevation = []
        # 海拔数据缓存，格式为 {(lat, lon): elevation}
        self._elevation_cache = {}
        # 批量处理的最大点数量（Open-Elevation单次最大支持1024个点，减小以避免服务器拒绝连接）
        self.MAX_POINTS_PER_REQUEST = 500
        # 最大重试次数
        self.MAX_RETRY_COUNT = 3
        # 请求间隔时间（秒）
        self.REQUEST_INTERVAL = 2

    def _log(self, level: str, message: str):
        """
        记录日志

        Args:
            level: 日志级别
            message: 日志消息
        """
        if self.logger:
            self.logger(level, message)

    def _get_elevation(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float, float]]:
        """
        获取多个点的海拔数据

        使用Open-Elevation API获取给定坐标点的海拔信息，支持请求重试、批量处理和缓存
        当点数超过1000时，只提取均匀分布的1000个点的海拔，然后对其他点进行插值计算

        Args:
            points: 坐标点列表 [(lat, lon), ...] 或 [(lat, lon, elevation), ...]

        Returns:
            List[Tuple[float, float, float]]: 带海拔的点列表 [(lat, lon, elevation), ...]
        """
        # 处理可能带有海拔数据的点列表，确保只使用前两个元素(lat, lon)
        def get_lat_lon(point):
            """从点中提取经纬度，处理可能带有海拔数据的情况"""
            if len(point) >= 2:
                return point[0], point[1]
            else:
                return point[0], point[1] if len(point) > 1 else 0.0

        if not points:
            return []

        MAX_ELEVATION_POINTS = 1000  # 最大获取海拔的点数量

        # 1. 从缓存中获取已有海拔数据
        cached_points = []
        uncached_points = []
        for point in points:
            # 确保point是元组，避免使用列表作为字典键
            point_tuple = tuple(point) if isinstance(point, list) else point
            # 提取经纬度作为缓存键
            lat, lon = get_lat_lon(point_tuple)
            cache_key = (lat, lon)
            if cache_key in self._elevation_cache:
                cached_points.append((lat, lon, self._elevation_cache[cache_key]))
            else:
                uncached_points.append(cache_key)

        self._log("DEBUG", f"从缓存中获取到 {len(cached_points)} 个点的海拔数据，需要请求 {len(uncached_points)} 个点")

        # 检查是否所有点都已有缓存的海拔数据
        if len(cached_points) == len(points):
            # 所有点都已有海拔数据，直接返回
            self._log("INFO", "所有点的海拔数据都已在缓存中，直接返回")
            return cached_points

        # 2. 处理未缓存的点
        if uncached_points:
            # 检查点数是否超过限制
            if len(uncached_points) <= MAX_ELEVATION_POINTS:
                # 点数在1000以内，获取所有点的海拔数据
                self._log("INFO", "点数在1000以内，获取所有点的海拔数据")

                # 2.1 批量处理坐标点
                batches = []
                for i in range(0, len(uncached_points), self.MAX_POINTS_PER_REQUEST):
                    batch = uncached_points[i:i + self.MAX_POINTS_PER_REQUEST]
                    batches.append(batch)

                self._log("DEBUG", f"将 {len(uncached_points)} 个点分为 {len(batches)} 批处理")

                # 2.2 处理每一批点
                for batch_index, batch in enumerate(batches):
                    self._log("DEBUG", f"处理第 {batch_index + 1}/{len(batches)} 批，点数: {len(batch)}")

                    # 2.3 构建Open-Elevation API请求数据
                    locations = [{"latitude": lat, "longitude": lon} for lat, lon in batch]
                    payload = {"locations": locations}

                    # 2.4 请求重试机制
                    retry_count = 0
                    while retry_count < self.MAX_RETRY_COUNT:
                        try:
                            # 发送POST请求到Open-Elevation API获取海拔数据
                            self._log("DEBUG", f"请求Open-Elevation API，批次: {batch_index + 1}, 重试次数: {retry_count}")
                            response = requests.post(self.elevation_api_url, json=payload, timeout=30)
                            data = response.json()

                            # 检查响应格式是否正确
                            if "results" in data:
                                results = data["results"]
                                for i, result in enumerate(results):
                                    if i < len(batch):
                                        lat, lon = batch[i]
                                        elevation = result.get("elevation", 0.0)
                                        # 保存到缓存
                                        self._elevation_cache[(lat, lon)] = elevation
                                        # 添加到结果列表
                                        cached_points.append((lat, lon, elevation))

                                self._log("INFO", f"成功获取第 {batch_index + 1} 批 {len(results)} 个点的海拔数据")
                                break  # 成功获取数据，跳出重试循环
                            else:
                                self._log("WARNING", f"第 {batch_index + 1} 批Open-Elevation API响应格式错误")
                                retry_count += 1
                                if retry_count < self.MAX_RETRY_COUNT:
                                    wait_time = (retry_count + 1) * 2  # 指数退避
                                    self._log("DEBUG", f"重试获取海拔数据，等待 {wait_time} 秒...")
                                    import time
                                    time.sleep(wait_time)
                        except Exception as e:
                            self._log("ERROR", f"获取海拔数据异常: {str(e)}")
                            retry_count += 1
                            if retry_count < self.MAX_RETRY_COUNT:
                                wait_time = (retry_count + 1) * 2  # 指数退避
                                self._log("DEBUG", f"重试获取海拔数据，等待 {wait_time} 秒...")
                                import time
                                time.sleep(wait_time)

                    # 如果重试失败，为这批点设置默认海拔
                    if retry_count >= self.MAX_RETRY_COUNT:
                        self._log("WARNING", f"第 {batch_index + 1} 批点海拔数据获取失败，使用默认值0.0")
                        for lat, lon in batch:
                            cached_points.append((lat, lon, 0.0))

                    # 每批请求之间添加间隔时间，避免服务器拒绝连接
                    if batch_index < len(batches) - 1:  # 不是最后一批
                        self._log("DEBUG", f"批次处理完成，等待 {self.REQUEST_INTERVAL} 秒后处理下一批...")
                        import time
                        time.sleep(self.REQUEST_INTERVAL)
            else:
                # 点数超过1000，提取均匀分布的1000个点
                self._log("INFO", f"点数超过1000，提取均匀分布的 {MAX_ELEVATION_POINTS} 个点获取海拔数据")

                # 提取均匀分布的点
                sampled_points = self._sample_points_uniformly(uncached_points, MAX_ELEVATION_POINTS)
                self._log("DEBUG", f"提取了 {len(sampled_points)} 个均匀分布的点")

                # 2.1 批量处理采样点
                batches = []
                for i in range(0, len(sampled_points), self.MAX_POINTS_PER_REQUEST):
                    batch = sampled_points[i:i + self.MAX_POINTS_PER_REQUEST]
                    batches.append(batch)

                self._log("DEBUG", f"将 {len(sampled_points)} 个采样点分为 {len(batches)} 批处理")

                # 2.2 处理每一批采样点
                sampled_points_with_elevation = []
                for batch_index, batch in enumerate(batches):
                    self._log("DEBUG", f"处理采样点批次 {batch_index + 1}/{len(batches)}，点数: {len(batch)}")

                    # 2.3 构建Open-Elevation API请求数据
                    locations = [{"latitude": lat, "longitude": lon} for lat, lon in batch]
                    payload = {"locations": locations}

                    # 2.4 请求重试机制
                    retry_count = 0
                    while retry_count < self.MAX_RETRY_COUNT:
                        try:
                            # 发送POST请求到Open-Elevation API获取海拔数据
                            self._log("DEBUG", f"请求Open-Elevation API，批次: {batch_index + 1}, 重试次数: {retry_count}")
                            response = requests.post(self.elevation_api_url, json=payload, timeout=30)
                            data = response.json()

                            # 检查响应格式是否正确
                            if "results" in data:
                                results = data["results"]
                                for i, result in enumerate(results):
                                    if i < len(batch):
                                        lat, lon = batch[i]
                                        elevation = result.get("elevation", 0.0)
                                        # 保存到缓存
                                        self._elevation_cache[(lat, lon)] = elevation
                                        # 添加到采样结果列表
                                        sampled_points_with_elevation.append((lat, lon, elevation))

                                self._log("INFO", f"成功获取第 {batch_index + 1} 批采样点海拔数据，点数: {len(results)}")
                                break  # 成功获取数据，跳出重试循环
                            else:
                                self._log("WARNING", f"第 {batch_index + 1} 批Open-Elevation API响应格式错误")
                                retry_count += 1
                                if retry_count < self.MAX_RETRY_COUNT:
                                    wait_time = (retry_count + 1) * 2  # 指数退避
                                    self._log("DEBUG", f"重试获取海拔数据，等待 {wait_time} 秒...")
                                    import time
                                    time.sleep(wait_time)
                        except Exception as e:
                            self._log("ERROR", f"获取海拔数据异常: {str(e)}")
                            retry_count += 1
                            if retry_count < self.MAX_RETRY_COUNT:
                                wait_time = (retry_count + 1) * 2  # 指数退避
                                self._log("DEBUG", f"重试获取海拔数据，等待 {wait_time} 秒...")
                                import time
                                time.sleep(wait_time)

                    # 如果重试失败，为这批点设置默认海拔
                    if retry_count >= self.MAX_RETRY_COUNT:
                        self._log("WARNING", f"第 {batch_index + 1} 批采样点海拔数据获取失败，使用默认值0.0")
                        for lat, lon in batch:
                            self._elevation_cache[(lat, lon)] = 0.0
                            sampled_points_with_elevation.append((lat, lon, 0.0))

                    # 每批请求之间添加间隔时间，避免服务器拒绝连接
                    if batch_index < len(batches) - 1:  # 不是最后一批
                        self._log("DEBUG", f"批次处理完成，等待 {self.REQUEST_INTERVAL} 秒后处理下一批...")
                        import time
                        time.sleep(self.REQUEST_INTERVAL)

                # 使用采样点的海拔数据对所有未缓存的点进行插值计算
                self._log("INFO", "使用采样点的海拔数据对所有未缓存的点进行插值计算")
                interpolated_points = self._interpolate_elevation(uncached_points, sampled_points_with_elevation)

                # 将插值结果添加到缓存和结果列表
                for point_with_elevation in interpolated_points:
                    lat, lon, elevation = point_with_elevation
                    # 保存到缓存
                    self._elevation_cache[(lat, lon)] = elevation
                    # 添加到结果列表
                    cached_points.append((point_with_elevation))

                self._log("INFO", f"完成所有点的海拔插值计算，总点数: {len(interpolated_points)}")

        # 3. 按原始顺序返回结果
        result = []
        for point in points:
            # 提取经纬度作为匹配键
            point_lat, point_lon = get_lat_lon(point)
            for cached_point in cached_points:
                if (cached_point[0], cached_point[1]) == (point_lat, point_lon):
                    result.append(cached_point)
                    break

        self._log("INFO", f"总共获取 {len(result)} 个点的海拔数据")
        return result

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

    def plan_route(self, points: List[Tuple[float, float]], transport_mode: str = "驾车",
                   start_name: str = None, end_name: str = None) -> Tuple[List[Dict], int]:
        """
        使用OSRM API规划路线

        Args:
            points: 坐标点列表 [(lat, lon), ...]
            transport_mode: 交通方式（步行/骑行/驾车）
            start_name: 起点名称（可选）
            end_name: 终点名称（可选）

        Returns:
            tuple: (路线方案列表，默认方案索引)
                  - 路线方案列表：每个方案包含 {
                      'route_points': 带海拔的坐标点列表,
                      'duration': 预估时间（秒）,
                      'distance': 路线距离（米）,
                      'tolls': 收费金额（元，OSM固定为0）,
                      'traffic_lights': 红绿灯数量（OSM固定为0）,
                      'description': 路线描述
                    }
                  - 默认方案索引：默认选中的方案索引（OSM只有一个方案，固定为0）
                  规划失败时返回 ([], 0)
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
                response = requests.get(url, headers=self.headers, timeout=30)

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

                    # 转换为(lat, lon)格式
                    segment_points = [(coord[1], coord[0]) for coord in coordinates]

                    # 直接添加不带海拔的路线点
                    for point in segment_points:
                        route_points.append(point)

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
                # 保存总距离和带海拔的点
                self.last_route_distance = total_distance
                self.last_route_points_with_elevation = route_points

                # 构建路线方案（OSM只返回一个方案）
                description = self._generate_route_description(transport_mode, start_name, end_name)

                route_alternative = {
                    'route_points': route_points,
                    'duration': estimated_duration,
                    'distance': int(total_distance * 1000),  # 转换为米
                    'tolls': 0,  # OSM不提供收费信息
                    'traffic_lights': 0,  # OSM不提供红绿灯信息
                    'description': description
                }

                route_alternatives = [route_alternative]

                self._log("INFO", f"OSM路线规划成功，路线点数量: {len([p for p in route_points if p is not None])}，总距离: {total_distance:.2f}公里，总预估时间: {estimated_duration}秒")
                return route_alternatives, 0  # 默认选中第一个（也是唯一的）方案
            else:
                # 重置距离和带海拔的点
                self.last_route_distance = 0.0
                self.last_route_points_with_elevation = []
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
                    # 提取点的前两个元素（纬度和经度），忽略海拔数据
                    lat1, lon1 = route_points[i-1][:2] if len(route_points[i-1]) >= 2 else route_points[i-1]
                    lat2, lon2 = route_points[i][:2] if len(route_points[i]) >= 2 else route_points[i]
                    distance = self._haversine_distance(lat1, lon1, lat2, lon2)
                    total_distance += distance

            self._log("INFO", f"使用Haversine公式计算路线距离: {total_distance:.2f}公里")
            return total_distance
        except Exception as e:
            self._log("ERROR", f"计算路线距离异常: {str(e)}")
            return 0.0

    def _generate_route_description(self, transport_mode: str, start_name: str = None, end_name: str = None) -> str:
        """
        生成路线描述

        Args:
            transport_mode: 交通方式
            start_name: 起点名称
            end_name: 终点名称

        Returns:
            str: 路线描述
        """
        # 提取起点和终点的简短名称
        start_short = self._extract_short_name(start_name) if start_name else "起点"
        end_short = self._extract_short_name(end_name) if end_name else "终点"

        # 生成描述：起点 → 终点
        return f"{start_short} → {end_short}"

    def _extract_short_name(self, full_name: str) -> str:
        """
        从完整名称中提取简短名称

        Args:
            full_name: 完整的地点名称

        Returns:
            str: 提取的简短名称
        """
        if not full_name:
            return ""

        # 移除分号及其后的内容
        short_name = full_name.split(';')[0]
        # 移除逗号及其后的内容
        short_name = short_name.split(',')[0]
        # 清理空白字符
        short_name = short_name.strip()

        # 如果名称太长，截取前15个字符
        if len(short_name) > 15:
            short_name = short_name[:15] + "..."

        return short_name

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

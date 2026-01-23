"""
后台任务适配器
将manager的各种操作封装为后台任务函数
"""

from typing import Optional, Dict, Any, Callable
from modules.geolocation.location_helper import LocationHelper
from services.config.map_config import map_config


class LocationTaskAdapter:
    """定位任务适配器"""

    @staticmethod
    def create_location_task(service_manager, map_source,
                            progress_callback: Callable,
                            log_callback: Callable,
                            cancel_check: Callable) -> Optional[Dict[str, Any]]:
        """
        定位任务函数

        参数:
            service_manager: 服务管理器
            map_source: 地图源
            progress_callback: 进度回调 (percent, message)
            log_callback: 日志回调 (level, message)
            cancel_check: 取消检查函数

        返回:
            定位结果字典 或 None
        """
        try:
            log_callback("INFO", "开始定位流程")
            progress_callback(0, "正在初始化定位服务...")

            if cancel_check():
                return None

            # 1. 尝试 Windows 原生定位
            windows_location = service_manager.windows_location_service
            log_callback("DEBUG", f"Windows位置服务可用: {windows_location.is_available()}")

            if windows_location.is_available():
                progress_callback(10, "正在使用Windows原生定位...")
                log_callback("INFO", "尝试Windows原生定位...")

                if cancel_check():
                    return None

                location_info = windows_location.get_location(timeout=10)
                if location_info:
                    progress_callback(100, "Windows原生定位成功")
                    log_callback("INFO", "Windows原生定位成功")
                    return {'type': 'native', 'data': location_info}

            # 2. Windows定位失败，检查浏览器定位
            log_callback("INFO", "Windows定位不可用")
            progress_callback(30, "Windows定位不可用，尝试其他方式...")

            if cancel_check():
                return None

            # 如果是高德地图，返回需要浏览器定位的标记
            if map_source == "gaode" and map_config.is_gaode_configured():
                log_callback("INFO", "需要浏览器定位")
                return {'type': 'browser', 'data': None}

            # 3. 尝试公共IP定位
            progress_callback(60, "正在使用公共IP定位...")
            log_callback("INFO", "尝试公共IP定位...")

            if cancel_check():
                return None

            def ip_log(level: str, message: str):
                log_callback(level, f"[公共IP定位] {message}")

            location_info = LocationHelper.get_ip_location(logger=ip_log)

            if location_info:
                progress_callback(100, "公共IP定位成功")
                log_callback("INFO", "公共IP定位成功")
                return {'type': 'ip', 'data': location_info, 'source': '公共IP定位'}
            else:
                log_callback("ERROR", "所有定位方式均失败")
                return None

        except Exception as e:
            log_callback("ERROR", f"定位任务异常: {str(e)}")
            import traceback
            log_callback("DEBUG", traceback.format_exc())
            return None


class SearchTaskAdapter:
    """搜索任务适配器"""

    @staticmethod
    def create_search_task(geocoding_service, search_text, map_source,
                          progress_callback: Callable,
                          log_callback: Callable,
                          cancel_check: Callable) -> Optional[list]:
        """
        搜索任务函数

        参数:
            geocoding_service: 地理编码服务
            search_text: 搜索文本
            map_source: 地图源
            progress_callback: 进度回调
            log_callback: 日志回调
            cancel_check: 取消检查函数

        返回:
            搜索结果列表 或 None
        """
        try:
            log_callback("INFO", f"开始搜索: {search_text}")
            progress_callback(0, f"正在搜索: {search_text}...")

            if cancel_check():
                return None

            # 检查高德API配置
            if map_source == "gaode" and not map_config.is_gaode_configured():
                log_callback("WARNING", "高德地图API未配置，无法进行地点搜索")
                return []

            progress_callback(30, "正在查询地理编码服务...")

            if cancel_check():
                return None

            # 执行搜索
            locations = geocoding_service.search_location(search_text)

            if cancel_check():
                return None

            if locations:
                progress_callback(100, f"找到 {len(locations)} 个结果")
                log_callback("INFO", f"搜索成功，找到 {len(locations)} 个结果")
                return locations
            else:
                progress_callback(100, "未找到结果")
                log_callback("WARNING", f"未找到: {search_text}")
                return []

        except Exception as e:
            log_callback("ERROR", f"搜索任务异常: {str(e)}")
            import traceback
            log_callback("DEBUG", traceback.format_exc())
            return None


class RouteTaskAdapter:
    """路线规划任务适配器"""

    @staticmethod
    def create_route_task(routing_service, points, transport_mode, map_source,
                         progress_callback: Callable,
                         log_callback: Callable,
                         cancel_check: Callable,
                         start_name: str = None,
                         end_name: str = None) -> Optional[Dict[str, Any]]:
        """
        路线规划任务函数

        参数:
            routing_service: 路线规划服务
            points: 路线点列表（起点、途径点、终点）
            transport_mode: 交通方式
            map_source: 地图源
            progress_callback: 进度回调
            log_callback: 日志回调
            cancel_check: 取消检查函数
            start_name: 起点名称（可选）
            end_name: 终点名称（可选）

        返回:
            路线规划结果字典 {'route_points': [...], 'duration': seconds} 或 None
        """
        try:
            log_callback("INFO", f"开始规划路线 - 方式: {transport_mode}")
            log_callback("INFO", f"总点数: {len(points)}")
            progress_callback(0, f"正在规划路线（{transport_mode}）...")

            if cancel_check():
                return None

            # 检查高德API配置
            if map_source == "gaode" and not map_config.is_gaode_configured():
                log_callback("WARNING", "高德地图API未配置，无法进行路线规划")
                return None

            progress_callback(20, "正在计算路线...")
            log_callback("DEBUG", "调用路线规划服务...")

            if cancel_check():
                return None

            # 执行路线规划（返回多条路线方案）
            # 检查服务是否支持起点终点名称参数
            if hasattr(routing_service, 'plan_route'):
                import inspect
                sig = inspect.signature(routing_service.plan_route)
                if 'start_name' in sig.parameters and 'end_name' in sig.parameters:
                    # OSM服务支持起点终点名称
                    route_alternatives, default_index = routing_service.plan_route(
                        points, transport_mode, start_name=start_name, end_name=end_name)
                else:
                    # 高德服务不支持起点终点名称参数
                    route_alternatives, default_index = routing_service.plan_route(points, transport_mode)
            else:
                route_alternatives, default_index = routing_service.plan_route(points, transport_mode)

            if cancel_check():
                return None

            if route_alternatives:
                progress_callback(100, f"路线规划成功，共 {len(route_alternatives)} 个方案")
                log_callback("INFO", f"路线规划成功，共 {len(route_alternatives)} 个方案")
                return {
                    'alternatives': route_alternatives,
                    'default_index': default_index
                }
            else:
                progress_callback(100, "路线规划失败")
                log_callback("WARNING", "路线规划失败，未返回路线方案")
                return None

        except Exception as e:
            log_callback("ERROR", f"路线规划任务异常: {str(e)}")
            import traceback
            log_callback("DEBUG", traceback.format_exc())
            return None


class MapRenderTaskAdapter:
    """地图渲染任务适配器"""

    @staticmethod
    def create_route_map_render_task(data_manager, map_source,
                                     progress_callback: Callable,
                                     log_callback: Callable,
                                     cancel_check: Callable) -> Optional[str]:
        """
        路线地图渲染任务函数

        参数:
            data_manager: 数据管理器，提供路线数据
            map_source: 地图数据源
            progress_callback: 进度回调
            log_callback: 日志回调
            cancel_check: 取消检查函数

        返回:
            地图HTML URL 或 None
        """
        import time
        total_start_time = time.time()

        try:
            log_callback("INFO", "开始渲染路线地图")
            progress_callback(0, "正在准备地图数据...")

            if cancel_check():
                return None

            # 检查路线数据
            if not data_manager.route_points:
                log_callback("WARNING", "没有路线数据")
                return None

            # 过滤无效路线点
            valid_points = [p for p in data_manager.route_points if p is not None]
            if not valid_points:
                log_callback("WARNING", "没有有效的路线点")
                return None

            log_callback("INFO", f"有效路线点数量: {len(valid_points)}")
            progress_callback(10, f"正在处理 {len(valid_points)} 个路线点...")

            if cancel_check():
                return None

            # 收集所有坐标点
            combined_coords = []
            if data_manager.start_coords:
                combined_coords.append(data_manager.start_coords)
            combined_coords.extend(data_manager.waypoints_coords)
            if data_manager.end_coords:
                combined_coords.append(data_manager.end_coords)

            for rp in valid_points:
                if rp and rp not in combined_coords:
                    combined_coords.append(rp)

            progress_callback(20, "正在创建地图...")

            if cancel_check():
                return None

            # 导入MapRenderer
            from modules.map.map_renderer import MapRenderer

            # 确定地图中心
            center = data_manager.start_coords or combined_coords[0]

            # 创建基础地图
            map_create_start = time.time()
            log_callback("DEBUG", f"创建地图，中心: {center}")
            m = MapRenderer.create_base_map(center, zoom_start=12, map_source=map_source)
            map_create_time = (time.time() - map_create_start) * 1000

            progress_callback(40, "正在添加地图标记...")

            if cancel_check():
                return None

            # 添加起点、终点、途径点
            markers_start = time.time()
            if data_manager.start_coords:
                start_name = data_manager.start_name or "起点"
                MapRenderer.add_marker(m, data_manager.start_coords, start_name, 'green', 'play')

            if data_manager.end_coords:
                end_name = data_manager.end_name or "终点"
                MapRenderer.add_marker(m, data_manager.end_coords, end_name, 'red', 'stop')

            for i, wp in enumerate(data_manager.waypoints_coords):
                wp_name = data_manager.waypoints_names[i] if i < len(data_manager.waypoints_names) else f"途径点{i+1}"
                MapRenderer.add_marker(m, wp, wp_name, 'blue', 'info-sign')
            markers_time = (time.time() - markers_start) * 1000

            progress_callback(60, "正在绘制路线...")

            if cancel_check():
                return None

            # 添加路线
            log_callback("DEBUG", "添加路线到地图")

            route_add_start = time.time()

            # 处理坐标转换：根据地图源和路线来源决定是否需要转换
            route_points_to_render = data_manager.route_points

            # 检查路线来源：如果存在路线替代方案，说明是通过路线规划服务获取的
            is_route_planned = hasattr(data_manager, 'route_alternatives') and data_manager.route_alternatives

            if map_source == 'gaode':
                # 当前地图源是高德地图
                has_original_gcj02 = False
                if is_route_planned:
                    # 路线是通过路线规划服务获取的，检查是否有原始GCJ-02坐标
                    try:
                        selected_route = data_manager.route_alternatives[data_manager.selected_route_index]
                        if selected_route and 'gcj02_route_points' in selected_route:
                            # 使用原始GCJ-02坐标直接渲染，避免双重转换
                            route_points_to_render = selected_route['gcj02_route_points']
                            log_callback("INFO", f"[路线渲染] 使用原始GCJ-02坐标直接渲染，共{len(route_points_to_render)}个坐标点")
                            has_original_gcj02 = True
                    except (IndexError, AttributeError):
                        # 没有选中的路线方案或索引无效，使用默认转换逻辑
                        log_callback("WARNING", "[路线渲染] 无法获取选中的路线方案，使用默认坐标转换")

                # 如果没有原始GCJ-02坐标，将WGS-84坐标转换为GCJ-02坐标
                if not has_original_gcj02:
                    from modules.geolocation.coordinate_transform import CoordinateTransform
                    transformed_route_points = []
                    for point in route_points_to_render:
                        if point is not None:
                            # 提取坐标部分（忽略海拔）
                            lat, lon = point[0], point[1]
                            # 转换坐标
                            gcj_lat, gcj_lon = CoordinateTransform.wgs84_to_gcj02(lat, lon)
                            # 保留原始格式（可能包含海拔）
                            if len(point) > 2:
                                transformed_point = (gcj_lat, gcj_lon, point[2])
                            else:
                                transformed_point = (gcj_lat, gcj_lon)
                            transformed_route_points.append(transformed_point)
                        else:
                            transformed_route_points.append(None)
                    route_points_to_render = transformed_route_points
                    log_callback("INFO", f"[路线渲染] 已将{len(transformed_route_points)}个WGS-84坐标转换为GCJ-02坐标")

            MapRenderer.add_route(m, route_points_to_render)
            route_add_time = (time.time() - route_add_start) * 1000

            progress_callback(80, "正在调整地图边界...")

            if cancel_check():
                return None

            # 调整地图边界
            fit_bounds_start = time.time()

            # 处理坐标转换：当使用高德地图时，需要将WGS-84坐标转换为GCJ-02坐标
            bounds_points = combined_coords
            if map_source == 'gaode':
                # 当前地图源是高德地图，所有存储的路线数据都是WGS-84坐标，需要转换为GCJ-02坐标
                from modules.geolocation.coordinate_transform import CoordinateTransform
                # 转换边界点坐标
                transformed_bounds_points = []
                for point in bounds_points:
                    if point:
                        lat, lon = point
                        gcj_lat, gcj_lon = CoordinateTransform.wgs84_to_gcj02(lat, lon)
                        transformed_bounds_points.append((gcj_lat, gcj_lon))
                    else:
                        transformed_bounds_points.append(point)
                bounds_points = transformed_bounds_points
                log_callback("INFO", f"[地图边界] 已将{len(transformed_bounds_points)}个WGS-84坐标转换为GCJ-02坐标")

            MapRenderer.fit_bounds(m, bounds_points)
            fit_bounds_time = (time.time() - fit_bounds_start) * 1000

            progress_callback(90, "正在保存地图...")

            if cancel_check():
                return None

            # 保存地图并获取URL
            save_map_start = time.time()
            url = MapRenderer.save_and_get_url(m)
            save_map_time = (time.time() - save_map_start) * 1000

            total_time = (time.time() - total_start_time) * 1000
            log_callback("INFO", f"地图渲染完成: {url}")
            log_callback("INFO", f"[地图渲染任务] 总耗时: {total_time:.2f}ms (创建地图: {map_create_time:.2f}ms, 添加标记: {markers_time:.2f}ms, 路线添加: {route_add_time:.2f}ms, 调整边界: {fit_bounds_time:.2f}ms, 保存地图: {save_map_time:.2f}ms)")

            progress_callback(100, "地图渲染完成")
            return url

        except Exception as e:
            total_time = (time.time() - total_start_time) * 1000
            log_callback("ERROR", f"地图渲染任务异常: {str(e)}, 总耗时: {total_time:.2f}ms")
            import traceback
            log_callback("DEBUG", traceback.format_exc())
            return None

"""
路线管理器
负责路线规划和GPX导出
支持后台线程执行和进度展示
"""

from typing import Optional
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QApplication
from PyQt5.QtCore import QDateTime, QObject, pyqtSlot
from services.config.map_config import map_config
from core.background_task import TaskPriority


class RouteManager(QObject):
    """路线管理器

    负责路线规划和GPX文件导出功能：
    - 根据交通方式规划路线
    - 计算并更新路线时间信息
    - 处理路线规划结果
    - 导出路线为GPX格式文件

    支持后台线程异步执行，主线程快速响应用户操作
    """

    def __init__(self, service_manager, data_manager, ui_updater, logger, task_manager=None):
        """
        初始化路线管理器

        参数:
            service_manager: 服务管理器实例，提供路线规划和GPX导出服务
            data_manager: 数据管理器实例，用于存储和获取路线数据
            ui_updater: UI更新回调函数字典，用于更新界面显示
            logger: 日志器，用于记录路线操作日志
            task_manager: 任务管理器实例，用于后台任务管理
        """
        super().__init__()
        self.service_manager = service_manager  # 服务管理器实例
        self.data_manager = data_manager  # 数据管理器实例
        self.ui_updater = ui_updater  # UI更新回调函数字典
        self.logger = logger  # 日志器
        self.task_manager = task_manager  # 任务管理器

    def plan_route(self, transport_mode: str):
        """
        根据交通方式规划路线

        参数:
            transport_mode: 交通方式（如驾车、步行、骑行等）
        """
        self.logger.info("=" * 80)
        self.logger.info("开始执行路线规划")
        self.logger.info("=" * 80)

        # 检查是否设置了起点和终点
        if not self.data_manager.has_start_end():
            self.logger.warning("路线规划失败：未设置起点或终点")
            self.ui_updater['show_warning']("错误", "请先设置起点和终点")
            return

        # 检查是否设置了地图数据源
        map_source = map_config.get_map_source()
        if not map_source:
            self.logger.warning("路线规划失败：未设置地图数据源")
            self.ui_updater['show_warning']("警告", "请先在地图配置中设置地图数据源")
            return

        # 获取所有点（起点+途径点+终点）
        points = self.data_manager.get_all_points()

        self.logger.info(f"开始规划路线，方式: {transport_mode}")
        self.logger.debug(f"起点: {self.data_manager.start_coords}, 终点: {self.data_manager.end_coords}")
        self.logger.debug(f"途径点数量: {len(self.data_manager.waypoints_coords)}")
        self.logger.debug(f"总点数: {len(points)}")

        # 更新UI显示路线规划开始
        self.ui_updater['set_progress_indeterminate']()
        self.ui_updater['clear_results_list']()
        result_text = f"正在规划路线...\n方式: {transport_mode}"
        self.ui_updater['add_result'](result_text)

        # 如果有任务管理器，使用后台线程执行
        if self.task_manager:
            self.logger.info("使用后台线程执行路线规划任务")
            from .task_adapters import RouteTaskAdapter

            # 获取路线规划服务
            routing_service = self.service_manager.get_routing_service(map_source)

            task_id = self.task_manager.submit_task(
                task_type="routing",
                task_func=RouteTaskAdapter.create_route_task,
                priority=TaskPriority.HIGH,  # 用户操作优先级最高
                routing_service=routing_service,
                points=points,
                transport_mode=transport_mode,
                map_source=map_source,
                start_name=self.data_manager.start_name,
                end_name=self.data_manager.end_name
            )

            self.logger.debug(f"路线规划任务已提交: {task_id}")
        else:
            # 兼容模式：直接执行
            self._perform_route_planning_sync(map_source, points, transport_mode)

    def _perform_route_planning_sync(self, map_source: str, points: list, transport_mode: str):
        """同步执行路线规划（兼容模式）"""
        try:
            self.logger.debug("正在调用路线规划服务...")

            # 获取对应的路线规划服务
            routing_service = self.service_manager.get_routing_service(map_source)

            # 检查高德API配置（如果使用高德地图）
            if map_source == "gaode" and not map_config.is_gaode_configured():
                self.logger.warning("高德地图API未配置，无法进行路线规划")
                self.ui_updater['set_progress_complete']()
                self.ui_updater['show_warning']("错误", "请先在地图配置中配置高德地图API密钥")
                return

            # 执行路线规划（返回多条路线方案）
            # 检查服务是否支持起点终点名称参数
            if hasattr(routing_service, 'plan_route'):
                import inspect
                sig = inspect.signature(routing_service.plan_route)
                if 'start_name' in sig.parameters and 'end_name' in sig.parameters:
                    # OSM服务支持起点终点名称
                    route_alternatives, default_index = routing_service.plan_route(
                        points, transport_mode,
                        start_name=self.data_manager.start_name,
                        end_name=self.data_manager.end_name)
                else:
                    # 高德服务不支持起点终点名称参数
                    route_alternatives, default_index = routing_service.plan_route(points, transport_mode)
            else:
                route_alternatives, default_index = routing_service.plan_route(points, transport_mode)

            # 更新UI显示路线规划完成
            self.ui_updater['set_progress_complete']()

            if route_alternatives:
                # 安全检查：确保default_index在有效范围内
                if default_index >= len(route_alternatives):
                    self.logger.warning(f"默认方案索引 {default_index} 超出范围，重置为0")
                    default_index = 0

                # 保存路线方案到数据管理器
                self.data_manager.set_route_alternatives(route_alternatives, default_index)

                # 更新路线时间信息（使用默认选中的方案）
                selected_route = route_alternatives[default_index]
                self._update_route_times(selected_route['duration'])

                # 路线规划成功
                self._handle_route_success(transport_mode, route_alternatives, default_index)
            else:
                # 路线规划失败（未返回路线点）
                self._handle_route_failure()

        except Exception as e:
            # 捕获路线规划过程中的异常
            self.logger.exception(f"路线规划出错: {str(e)}")
            self.ui_updater['set_progress_complete']()
            self.ui_updater['clear_results_list']()

            # 合并为一条结果显示
            result_text = f"路线规划出错\n错误信息: {str(e)}"
            self.ui_updater['add_result'](result_text)
            self.ui_updater['show_warning']("错误", f"路线规划出错: {str(e)}")

        self.logger.info("路线规划流程完成")
        self.logger.info("=" * 80)

    @pyqtSlot(str, object)
    def on_route_task_completed(self, task_id: str, result):
        """处理路线规划任务完成（槽函数）

        参数:
            task_id: 任务ID
            result: 路线规划结果 {'alternatives': [...], 'default_index': 0}
        """
        self.logger.info(f"路线规划任务完成: {task_id}")

        self.ui_updater['set_progress_complete']()

        if result and result.get('alternatives'):
            # 路线规划成功
            route_alternatives = result['alternatives']
            default_index = result.get('default_index', 0)

            # 安全检查：确保default_index在有效范围内
            if not route_alternatives:
                self.logger.warning("路线方案列表为空")
                self._handle_route_failure()
                return

            if default_index >= len(route_alternatives):
                self.logger.warning(f"默认方案索引 {default_index} 超出范围，重置为0")
                default_index = 0

            # 保存路线方案
            self.data_manager.set_route_alternatives(route_alternatives, default_index)

            # 更新路线时间信息（使用默认选中的方案）
            selected_route = route_alternatives[default_index]
            self._update_route_times(selected_route['duration'])

            # 获取交通方式
            transport_mode = self.ui_updater['get_transport_mode']()

            # 处理成功（立即渲染路线）
            self._handle_route_success(transport_mode, route_alternatives, default_index)

            # 在后台异步获取海拔数据
            self._fetch_elevation_data_async(route_alternatives)
        else:
            # 路线规划失败
            self._handle_route_failure()

    @pyqtSlot(str, str)
    def on_route_task_failed(self, task_id: str, error: str):
        """处理路线规划任务失败（槽函数）

        参数:
            task_id: 任务ID
            error: 错误信息
        """
        self.logger.error(f"路线规划任务失败: {task_id} - {error}")
        self.ui_updater['set_progress_complete']()
        self.ui_updater['clear_results_list']()
        result_text = f"路线规划出错\n错误信息: {error}"
        self.ui_updater['add_result'](result_text)
        self.ui_updater['show_warning']("错误", f"路线规划出错: {error}")

    @pyqtSlot(str, object)
    def on_map_render_task_completed(self, task_id: str, result):
        """处理地图渲染任务完成（槽函数）

        参数:
            task_id: 任务ID
            result: 地图URL
        """
        self.logger.info(f"地图渲染任务完成: {task_id}")

        if result:
            # 在主线程中加载地图
            self.ui_updater['load_map_url'](result)
            self.logger.debug(f"已加载地图: {result}")
        else:
            self.logger.warning("地图渲染失败，URL为空")

    @pyqtSlot(str, str)
    def on_map_render_task_failed(self, task_id: str, error: str):
        """处理地图渲染任务失败（槽函数）

        参数:
            task_id: 任务ID
            error: 错误信息
        """
        self.logger.error(f"地图渲染任务失败: {task_id} - {error}")
        self.ui_updater['show_warning']("警告", f"地图显示失败: {error}")

    def _update_route_times(self, estimated_duration: int):
        """更新路线时间信息（内部方法）

        根据预估路线耗时，计算并更新结束时间和途径时间。
        注意：起始时间不会被更新，保持用户设置的值或程序启动时的初始值。

        参数:
            estimated_duration: 预估路线耗时（秒）
        """
        # 获取当前的起始时间（不更新，使用用户设置的值）
        start_datetime = self.ui_updater['get_start_time']()

        # 计算途径时间（小时，支持小数）
        duration_hours = estimated_duration / 3600
        self.ui_updater['set_duration'](f"{duration_hours:.1f}")

        # 根据起始时间和途径时间计算结束时间
        start_timestamp = start_datetime.toSecsSinceEpoch()
        end_timestamp = start_timestamp + estimated_duration

        # 创建结束时间的 QDateTime 对象
        qt_end_datetime = QDateTime.fromSecsSinceEpoch(end_timestamp)
        self.ui_updater['set_end_time'](qt_end_datetime)

    def _handle_route_success(self, transport_mode: str, route_alternatives: list = None, default_index: int = 0):
        """处理路线规划成功（内部方法）

        路线规划成功后，更新UI显示路线信息并在地图上显示路线。

        参数:
            transport_mode: 交通方式
            route_alternatives: 路线方案列表（可选，如果为None则从data_manager获取）
            default_index: 默认选中的方案索引
        """
        # 如果没有传入路线方案，从data_manager获取
        if route_alternatives is None:
            route_alternatives = self.data_manager.route_alternatives
            default_index = self.data_manager.selected_route_index

        self.logger.info(f"路线规划成功，共 {len(route_alternatives)} 个方案")

        # 更新UI显示路线规划成功
        self.ui_updater['set_progress_complete']()

        # 1. 优先在地图上显示默认选中的路线 - 使用后台线程渲染
        if self.task_manager:
            self.logger.info("使用后台线程渲染路线地图")
            from .task_adapters import MapRenderTaskAdapter

            map_source = map_config.get_map_source()

            task_id = self.task_manager.submit_task(
                task_type="map_render",
                task_func=MapRenderTaskAdapter.create_route_map_render_task,
                priority=TaskPriority.HIGH,  # 用户操作优先级最高
                data_manager=self.data_manager,
                map_source=map_source
            )

            self.logger.debug(f"地图渲染任务已提交: {task_id}")
        else:
            # 兼容模式：直接渲染
            self.ui_updater['show_route_on_map']()

        # 2. 弹出路线待选列表（在路线规划面板中）
        if 'show_route_alternatives' in self.ui_updater:
            self.ui_updater['show_route_alternatives'](route_alternatives, default_index)

        # 3. 在后台异步获取海拔数据
        if self.task_manager:
            self.logger.info("在后台执行海拔数据获取操作")
            # 在后台异步获取海拔数据
            self._fetch_elevation_data_async(route_alternatives)
        else:
            # 兼容模式：直接执行
            # 获取海拔数据
            self._fetch_elevation_data_async(route_alternatives)

        # 4. 保存路线历史记录（在后台线程执行，只执行非UI操作）
        # 放在最后执行，确保不会阻塞地图渲染和页面加载
        if self.task_manager and 'save_route_history' in self.ui_updater:
            selected_route = route_alternatives[default_index] if route_alternatives else None
            if selected_route:
                def save_history_task(progress_callback=None, log_callback=None, cancel_check=None):
                    try:
                        # 只执行数据保存操作，不包含UI操作
                        # 创建一个只包含数据操作的回调
                        def save_history_data():
                            # 这里只执行数据保存，不涉及UI更新
                            # 路线历史存储的add_record方法只涉及文件IO操作
                            if hasattr(self, 'route_history_storage'):
                                # 直接调用存储的add_record方法
                                info = {
                                    'start': self.data_manager.start_name,
                                    'end': self.data_manager.end_name,
                                    'mode': transport_mode,
                                    'waypoints': [wp[0] for wp in self.data_manager.waypoints],
                                    'start_coords': self.data_manager.start_coords,
                                    'end_coords': self.data_manager.end_coords,
                                    'waypoint_coords': [wp[1] for wp in self.data_manager.waypoints_coords],
                                    'distance': selected_route.get('distance'),
                                    'duration': selected_route.get('duration'),
                                    'route_points': self.data_manager.route_points
                                }

                                # 保存到历史记录
                                self.route_history_storage.add_record(
                                    info['start'],
                                    info['end'],
                                    info['mode'],
                                    info['waypoints'],
                                    start_coords=info['start_coords'],
                                    end_coords=info['end_coords'],
                                    waypoint_coords=info['waypoint_coords'],
                                    distance=info['distance'],
                                    duration=info['duration'],
                                    route_points=info['route_points']
                                )
                                self.logger.info(f"[路线面板] 已保存历史记录: {info['start']} → {info['end']}, "
                                               f"距离: {info['distance']}米, 时长: {info['duration']}秒")

                        # 执行数据保存
                        save_history_data()

                        # 注意：UI更新操作（如重新加载历史记录列表）需要在主线程执行
                        # 但为了避免阻塞页面加载，我们暂时不执行UI更新
                        # 用户下次打开路线面板时会自动加载最新的历史记录
                    except Exception as e:
                        self.logger.error(f"保存路线历史记录失败: {e}")

                # 提交后台任务
                task_id = self.task_manager.submit_task(
                    task_type="route_history",
                    task_func=save_history_task,
                    priority=TaskPriority.LOW,  # 历史记录保存优先级为低
                )
                self.logger.debug(f"保存路线历史记录任务已提交: {task_id}")
        elif 'save_route_history' in self.ui_updater:
            # 兼容模式：使用QTimer延迟执行
            selected_route = route_alternatives[default_index] if route_alternatives else None
            if selected_route:
                def save_history():
                    try:
                        self.ui_updater['save_route_history'](
                            distance=selected_route.get('distance'),
                            duration=selected_route.get('duration')
                        )
                    except Exception as e:
                        self.logger.error(f"保存路线历史记录失败: {e}")

                # 使用QTimer延迟执行，确保不会阻塞其他操作
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(1000, save_history)  # 延迟1秒执行，给页面加载更多时间

    def _handle_route_failure(self):
        """处理路线规划失败（内部方法）

        路线规划失败后，更新UI显示失败信息。
        """
        self.logger.warning("路线规划失败，未返回路线点")
        self.ui_updater['clear_results_list']()
        self.ui_updater['add_result']("路线规划失败")
        self.ui_updater['show_warning']("错误", "路线规划失败")

    def _fetch_elevation_data_async(self, route_alternatives: list):
        """在后台异步获取海拔数据

        为每个路线方案的路线点获取海拔数据，并更新路线方案。

        参数:
            route_alternatives: 路线方案列表
        """
        if not route_alternatives:
            return

        # 获取用户当前选择的路线方案索引（默认选择第一条路线）
        selected_index = 0  # 默认选择第一条路线
        if self.data_manager:
            selected_index = self.data_manager.selected_route_index

        self.logger.info(f"开始在后台异步获取海拔数据，共 {len(route_alternatives)} 个路线方案，只处理选中的路线方案索引: {selected_index}")

        # 如果有任务管理器，使用后台线程执行
        if self.task_manager:
            self.logger.info("使用后台线程执行海拔数据获取任务")

            # 获取当前地图源
            map_source = map_config.get_map_source()

            # 获取路线规划服务
            routing_service = self.service_manager.get_routing_service(map_source)

            if routing_service:
                task_id = self.task_manager.submit_task(
                        task_type="elevation",
                        task_func=self._fetch_elevation_data_task,
                        priority=TaskPriority.NORMAL,  # 海拔数据获取优先级为普通
                        routing_service=routing_service,
                        route_alternatives=route_alternatives,
                        selected_index=selected_index
                    )

                self.logger.debug(f"海拔数据获取任务已提交: {task_id}")
            else:
                self.logger.warning("未找到路线规划服务，无法获取海拔数据")
        else:
            # 兼容模式：直接执行
            self.logger.warning("任务管理器不可用，直接执行海拔数据获取")
            # 正确的参数顺序：routing_service, route_alternatives, selected_index, progress_callback, log_callback, cancel_check
            self._fetch_elevation_data_task(None, route_alternatives, selected_index, None, None, lambda: False)

    def _fetch_elevation_data_task(self, routing_service, route_alternatives, selected_index,
                                  progress_callback, log_callback, cancel_check):
        """海拔数据获取任务函数

        参数:
            routing_service: 路线规划服务
            route_alternatives: 路线方案列表
            selected_index: 选中的路线方案索引
            progress_callback: 进度回调
            log_callback: 日志回调
            cancel_check: 取消检查函数

        返回:
            更新后的路线方案列表
        """
        if not routing_service or not route_alternatives:
            return None

        try:
            if log_callback:
                log_callback("INFO", f"开始获取海拔数据，共 {len(route_alternatives)} 个路线方案，只处理选中的路线方案索引: {selected_index}")

            updated_alternatives = []

            # 只处理选中的路线方案
            for i, route_alt in enumerate(route_alternatives):
                if i == selected_index:
                    # 处理选中的路线方案
                    if cancel_check():
                        return None

                    route_points = route_alt.get('route_points', [])
                    if route_points:
                        if progress_callback:
                            progress_callback(0, f"正在获取选中路线方案的海拔数据...")

                        if log_callback:
                            log_callback("INFO", f"获取选中路线方案的海拔数据，共 {len(route_points)} 个点")

                        # 获取海拔数据
                        route_points_with_elevation = routing_service._get_elevation(route_points)

                        # 更新路线方案
                        updated_alt = route_alt.copy()
                        updated_alt['route_points'] = route_points_with_elevation
                        updated_alternatives.append(updated_alt)

                        if log_callback:
                            log_callback("INFO", f"选中路线方案的海拔数据获取完成")
                    else:
                        updated_alternatives.append(route_alt)
                else:
                    # 非选中的路线方案，直接添加到结果列表
                    updated_alternatives.append(route_alt)

            if progress_callback:
                progress_callback(100, "海拔数据获取完成")

            if log_callback:
                log_callback("INFO", "海拔数据获取完成")

            return updated_alternatives
        except Exception as e:
            if log_callback:
                log_callback("ERROR", f"获取海拔数据异常: {str(e)}")
            return None

    def on_elevation_task_completed(self, task_id: str, result):
        """处理海拔数据获取任务完成（槽函数）

        参数:
            task_id: 任务ID
            result: 更新后的路线方案列表
        """
        self.logger.info(f"海拔数据获取任务完成: {task_id}")

        if result:
            # 更新数据管理器中的路线方案
            self.data_manager.set_route_alternatives(result, self.data_manager.selected_route_index)

            self.logger.info(f"已更新 {len(result)} 个路线方案的海拔数据")
        else:
            self.logger.warning("海拔数据获取失败，未更新路线方案")

    def select_route_alternative(self, index: int):
        """选择路线方案

        参数:
            index: 路线方案索引
        """
        self.logger.info(f"用户选择路线方案: {index}")

        # 更新数据管理器中的选中方案
        self.data_manager.select_route_alternative(index)

        # 检查选中的路线是否需要获取海拔数据
        selected_route = self.data_manager.get_selected_route()
        if selected_route:
            # 更新路线时间信息
            self._update_route_times(selected_route['duration'])

            # 检查路线点是否已经有海拔数据
            route_points = selected_route.get('route_points', [])
            has_elevation_data = False
            if route_points:
                # 检查第一个点是否有海拔数据
                first_point = route_points[0]
                if first_point and isinstance(first_point, tuple) and len(first_point) == 3:
                    has_elevation_data = True

            # 如果没有海拔数据，异步获取
            if not has_elevation_data:
                self.logger.info(f"选中的路线方案 {index} 没有海拔数据，开始异步获取")
                # 获取所有路线方案
                all_routes = self.data_manager.route_alternatives
                if all_routes:
                    # 重新执行海拔数据获取任务，只处理选中的路线
                    self._fetch_elevation_data_async(all_routes)

        # 在地图上显示选中的路线
        if self.task_manager:
            self.logger.info("使用后台线程渲染选中的路线")
            from .task_adapters import MapRenderTaskAdapter

            map_source = map_config.get_map_source()

            task_id = self.task_manager.submit_task(
                task_type="map_render",
                task_func=MapRenderTaskAdapter.create_route_map_render_task,
                priority=TaskPriority.HIGH,
                data_manager=self.data_manager,
                map_source=map_source
            )

            self.logger.debug(f"地图渲染任务已提交: {task_id}")
        else:
            # 兼容模式：直接渲染
            self.ui_updater['show_route_on_map']()

    def export_gpx(self):
        """导出路线为GPX文件

        GPX（GPS Exchange Format）是一种通用的GPS数据交换格式，
        导出后可在其他GPS设备或软件中使用。
        """
        self.logger.info("=" * 80)
        self.logger.info("开始执行GPX文件导出")
        self.logger.info("=" * 80)

        # 检查是否已规划路线
        if not self.data_manager.has_route():
            self.logger.warning("GPX导出失败：未规划路线")
            self.ui_updater['show_warning']("错误", "请先规划路线")
            return

        # 生成默认文件名
        default_filename = self._generate_gpx_filename()
        self.logger.debug(f"生成默认文件名: {default_filename}")

        # 打开文件保存对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self.ui_updater['main_window'],
            "保存GPX文件",
            default_filename,
            "GPX文件 (*.gpx);;所有文件 (*.*)"
        )

        if not file_path:
            # 用户取消了保存操作
            self.logger.info("GPX导出取消：用户未选择文件路径")
            return

        self.logger.info(f"开始导出GPX文件: {file_path}")

        try:
            # 更新UI显示导出开始
            self.ui_updater['set_progress_indeterminate']()
            self.ui_updater['clear_results_list']()
            self.ui_updater['add_result']("正在导出GPX文件...")

            self.logger.debug("正在调用GPX导出服务...")
            # 获取起始时间
            start_datetime = self.ui_updater['get_start_time']()

            # 更新进度
            self.ui_updater['set_progress'](50)

            # 提取起点和终点的城市名称
            start_city = self._extract_city_name(self.data_manager.start_name or "起点")
            end_city = self._extract_city_name(self.data_manager.end_name or "终点")

            # 执行GPX导出
            success = self.service_manager.gpx_service.export_to_gpx(
                self.data_manager.route_points,  # 路线点
                start_datetime,  # 起始时间
                file_path,  # 保存路径
                start_name=start_city,  # 起点名称
                end_name=end_city  # 终点名称
            )

            # 更新UI显示导出完成
            self.ui_updater['set_progress_complete']()

            if success:
                # 导出成功
                self.logger.info("GPX文件导出成功")
                self.ui_updater['clear_results_list']()

                # 合并为一条结果显示
                result_text = f"导出成功！\n文件: {file_path}"
                self.ui_updater['add_result'](result_text)
                self.ui_updater['show_info']("成功", f"GPX文件已导出到: {file_path}")
            else:
                # 导出失败
                self.logger.warning("GPX文件导出失败")
                self.ui_updater['clear_results_list']()
                self.ui_updater['add_result']("导出失败")
                self.ui_updater['show_warning']("错误", "导出GPX文件失败")

        except Exception as e:
            # 捕获GPX导出过程中的异常
            self.logger.exception(f"导出GPX文件出错: {str(e)}")
            self.ui_updater['set_progress_complete']()
            self.ui_updater['clear_results_list']()

            # 合并为一条结果显示
            result_text = f"导出出错\n错误信息: {str(e)}"
            self.ui_updater['add_result'](result_text)
            self.ui_updater['show_warning']("错误", f"导出GPX文件出错: {str(e)}")

        self.logger.info("GPX导出流程完成")
        self.logger.info("=" * 80)

    def _generate_gpx_filename(self) -> str:
        """生成默认GPX文件名（内部方法）

        根据起点、终点、交通方式、时间和耗时生成默认文件名。

        返回:
            默认的GPX文件名
        """
        # 提取起点和终点的城市名称
        start_city = self._extract_city_name(self.data_manager.start_name or "起点")
        end_city = self._extract_city_name(self.data_manager.end_name or "终点")

        # 获取交通方式
        transport_mode = self.ui_updater['get_transport_mode']()

        # 获取起始时间
        start_datetime = self.ui_updater['get_start_time']()
        start_time_str = start_datetime.toString("yyyyMMdd_hhmm")

        # 格式化途径时间
        duration_hours = self.data_manager.estimated_duration_seconds // 3600
        duration_minutes = (self.data_manager.estimated_duration_seconds % 3600) // 60
        duration_str = f"{duration_hours}小时{duration_minutes}分钟"

        # 生成文件名：起点_终点_交通方式_时间_耗时.gpx
        return f"{start_city}_{end_city}_{transport_mode}_{start_time_str}_{duration_str}.gpx"

    def _extract_city_name(self, full_name: str) -> str:
        """从完整名称中提取城市名称（内部方法）

        参数:
            full_name: 完整的地点名称

        返回:
            提取的城市名称
        """
        # 移除分号及其后的内容
        city_name = full_name.split(';')[0]
        # 移除逗号及其后的内容
        city_name = city_name.split(',')[0]
        # 清理空白字符
        city_name = city_name.strip()
        return city_name

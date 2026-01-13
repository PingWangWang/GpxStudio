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
                map_source=map_source
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

            # 执行路线规划
            route_points, estimated_duration = routing_service.plan_route(points, transport_mode)

            # 保存路线数据到数据管理器
            self.data_manager.set_route(route_points, estimated_duration)

            # 更新路线时间信息
            self._update_route_times(estimated_duration)

            # 更新UI显示路线规划完成
            self.ui_updater['set_progress_complete']()

            if route_points:
                # 路线规划成功
                self._handle_route_success(transport_mode)
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
            result: 路线规划结果 {'route_points': [...], 'duration': seconds}
        """
        self.logger.info(f"路线规划任务完成: {task_id}")

        self.ui_updater['set_progress_complete']()

        if result and result.get('route_points'):
            # 路线规划成功
            route_points = result['route_points']
            estimated_duration = result['duration']

            # 保存路线数据
            self.data_manager.set_route(route_points, estimated_duration)

            # 更新路线时间信息
            self._update_route_times(estimated_duration)

            # 获取交通方式
            transport_mode = self.ui_updater['get_transport_mode']()

            # 处理成功
            self._handle_route_success(transport_mode)
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

        根据预估路线耗时，计算并更新起始时间、结束时间和途径时间。

        参数:
            estimated_duration: 预估路线耗时（秒）
        """
        # 获取当前时间并去除秒数
        current_time = datetime.now()
        current_time_zero_sec = current_time.replace(second=0)

        # 设置起始时间为当前时间
        qt_current_datetime = QDateTime.fromString(
            current_time_zero_sec.strftime("%Y-%m-%d %H:%M:%S"),
            "yyyy-MM-dd hh:mm:ss"
        )
        self.ui_updater['set_start_time'](qt_current_datetime)

        # 计算途径时间（小时，支持小数）
        duration_hours = estimated_duration / 3600
        self.ui_updater['set_duration'](f"{duration_hours:.1f}")

        # 计算结束时间
        end_time = current_time_zero_sec.timestamp() + estimated_duration
        end_datetime = datetime.fromtimestamp(end_time)
        qt_end_datetime = QDateTime.fromString(
            end_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "yyyy-MM-dd hh:mm:ss"
        )
        self.ui_updater['set_end_time'](qt_end_datetime)

    def _handle_route_success(self, transport_mode: str):
        """处理路线规划成功（内部方法）

        路线规划成功后，更新UI显示路线信息并在地图上显示路线。

        参数:
            transport_mode: 交通方式
        """
        self.logger.info(f"路线规划成功，共 {len(self.data_manager.route_points)} 个点")

        # 更新UI显示路线规划成功
        self.ui_updater['set_progress_complete']()
        self.ui_updater['clear_results_list']()
        self.ui_updater['set_results_title']("路线信息")

        # 获取时间信息
        start_datetime = self.ui_updater['get_start_time']()
        start_time_str = start_datetime.toString("yyyy-MM-dd HH:mm")

        end_datetime = self.ui_updater['get_end_time']()
        end_time_str = end_datetime.toString("yyyy-MM-dd HH:mm")

        # 计算途径时间
        duration_hours = self.data_manager.estimated_duration_seconds // 3600
        duration_minutes = (self.data_manager.estimated_duration_seconds % 3600) // 60

        # 显示路线详细信息 - 合并为一条结果
        result_text = "路线规划成功！\n"
        result_text += "=" * 30 + "\n"

        # 显示起点、途径点和终点信息
        start_name = self.data_manager.start_name or "未命名"
        result_text += f"起点: {start_name}\n"

        # 显示途径点
        if self.data_manager.waypoints_coords:
            for i, name in enumerate(self.data_manager.waypoints_names):
                result_text += f"途径点{i+1}: {name}\n"

        end_name = self.data_manager.end_name or "未命名"
        result_text += f"终点: {end_name}\n"
        result_text += "=" * 30 + "\n"

        # 显示交通方式和时间信息
        result_text += f"交通方式: {transport_mode}\n"
        result_text += f"起始时间: {start_time_str}\n"
        result_text += f"途径时间: {int(duration_hours)}小时{duration_minutes}分钟\n"
        result_text += f"结束时间: {end_time_str}\n"
        result_text += "=" * 30 + "\n"

        # 先添加合并的结果
        self.ui_updater['add_result'](result_text)

        # 在地图上显示路线 - 使用后台线程渲染
        if self.task_manager:
            self.logger.info("使用后台线程渲染路线地图")
            from .task_adapters import MapRenderTaskAdapter
            from services.config.map_config import map_config

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

    def _handle_route_failure(self):
        """处理路线规划失败（内部方法）

        路线规划失败后，更新UI显示失败信息。
        """
        self.logger.warning("路线规划失败，未返回路线点")
        self.ui_updater['clear_results_list']()
        self.ui_updater['add_result']("路线规划失败")
        self.ui_updater['show_warning']("错误", "路线规划失败")

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

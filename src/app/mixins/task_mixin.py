"""TaskMixin — 任务事件直连处理（_rewire_task_signals 前的初始阶段使用）"""
from PyQt5.QtCore import QTimer


class TaskMixin:
    """_on_task_* 旧版直连方法；功能管理器就绪后由 TaskEventHandler 接管。"""

    def _on_task_started(self, task_id: str, task_type: str):
        self.logger.info(f"[任务] 开始: {task_id} ({task_type})")
        task_name_map = {'location': '定位', 'search': '搜索', 'routing': '路线规划', 'map_render': '地图渲染'}
        task_name = task_name_map.get(task_type, task_type)
        self.task_progress_panel.start_task(task_id, task_type, task_name)
        if task_type in ['location', 'search', 'routing']:
            self.start_loading_animation()

    def _on_task_progress(self, task_id: str, percent: int, message: str):
        self.task_progress_panel.update_progress(percent, message)

    def _on_task_completed(self, task_id: str, result):
        self.logger.info(f"[任务] 完成: {task_id}")
        if task_id.startswith('location_'):
            self.stop_loading_animation()
            self.location_manager.on_location_task_completed(task_id, result)
            self.task_progress_panel.task_completed("定位完成")
        elif task_id.startswith('search_'):
            self.stop_loading_animation()
            self.search_manager.on_search_task_completed(task_id, result)
            self.task_progress_panel.task_completed("搜索完成")
        elif task_id.startswith('routing_'):
            self.stop_loading_animation()
            self.hide_loading()
            self.route_manager.on_route_task_completed(task_id, result)
            self.task_progress_panel.task_completed("路线规划完成")
            if self._pending_export_history is not None:
                self.logger.info("[GPX导出] 路线规划完成，准备导出历史记录")
                if result and result.get('alternatives'):
                    alts = result['alternatives']
                    if alts:
                        sel = alts[0]
                        route_data = {
                            'description': f"{self._pending_export_history.get('start','起点')} → {self._pending_export_history.get('end','终点')}",
                            'distance': sel.get('distance', 0),
                            'duration': sel.get('duration', 0),
                            'route_points': sel.get('route_points', [])
                        }
                        self._show_gpx_export_popup(route_data)
                self._pending_export_history = None
        elif task_id.startswith('elevation_'):
            self.route_manager.on_elevation_task_completed(task_id, result)
            self.task_progress_panel.task_completed("海拔数据获取完成")
        elif task_id.startswith('map_render_'):
            self.hide_loading()
            self.route_manager.on_map_render_task_completed(task_id, result)
            self.task_progress_panel.task_completed("地图渲染完成")
            if self.route_plan_panel is not None and self.route_plan_panel.isVisible():
                self.route_plan_panel.hide_loading()
        elif task_id.startswith('context_menu_'):
            self._show_context_menu(result)
            self.task_progress_panel.task_completed("位置信息获取完成")
        else:
            self.task_progress_panel.task_completed("任务完成")
        QTimer.singleShot(3000, self.task_progress_panel.reset)

    def _on_task_failed(self, task_id: str, error: str):
        self.logger.error(f"[任务] 失败: {task_id} - {error}")
        if task_id.startswith('location_'):
            self.stop_loading_animation()
            self.location_manager.on_location_task_failed(task_id, error)
        elif task_id.startswith('search_'):
            self.stop_loading_animation()
            self.hide_loading()
            self.search_manager.on_search_task_failed(task_id, error)
        elif task_id.startswith('routing_'):
            self.stop_loading_animation()
            self.hide_loading()
            self.route_manager.on_route_task_failed(task_id, error)
            if self.route_plan_panel is not None and self.route_plan_panel.isVisible():
                self.route_plan_panel.hide_loading()
                self.route_plan_panel.show_route_plan_error("路线规划失败，请重试")
        elif task_id.startswith('map_render_'):
            self.hide_loading()
            self.route_manager.on_map_render_task_failed(task_id, error)
            if self.route_plan_panel is not None and self.route_plan_panel.isVisible():
                self.route_plan_panel.hide_loading()
                self.route_plan_panel.show_route_plan_error("地图渲染失败，请重试")
        self.task_progress_panel.task_failed(error)
        QTimer.singleShot(5000, self.task_progress_panel.reset)

    def _on_task_cancelled(self, task_id: str):
        self.logger.warning(f"[任务] 已取消: {task_id}")
        self.task_progress_panel.task_cancelled()
        QTimer.singleShot(2000, self.task_progress_panel.reset)

    def _on_task_log(self, task_id: str, level: str, message: str):
        self.task_progress_panel.add_log(level, message)
        level_map = {"DEBUG": self.logger.debug, "INFO": self.logger.info,
                     "WARNING": self.logger.warning, "ERROR": self.logger.error,
                     "CRITICAL": self.logger.critical}
        level_map.get(level, self.logger.info)(f"[任务 {task_id}] {message}")

    def _on_cancel_task_requested(self, task_id: str):
        self.logger.info(f"[任务] 用户请求取消: {task_id}")
        self.task_manager.cancel_task(task_id)

"""
任务管理器事件处理器

将 ``app.py`` 中全部 ``_on_task_*`` 方法提取到独立类，
与主窗口解耦，便于单独测试。

使用方法
--------
在 ``_build_domain()`` 中实例化，然后将任务管理器的信号连接到
本类对应的槽方法::

    handler = TaskEventHandler(
        task_progress_panel=self.task_progress_panel,
        location_manager=self.location_manager,
        search_manager=self.search_manager,
        route_manager=self.route_manager,
        start_animation=self.start_loading_animation,
        stop_animation=self.stop_loading_animation,
        hide_loading=self.hide_loading,
        show_gpx_popup_cb=self._show_gpx_export_popup,
        logger=self.logger,
        pending_export_getter=lambda: self._pending_export_history,
        pending_export_setter=lambda v: setattr(self, '_pending_export_history', v),
    )
    task_manager.task_started.connect(handler.on_task_started)
    ...
"""

import logging
from typing import Callable, Optional
from PyQt5.QtCore import QObject, pyqtSlot, QTimer


class TaskEventHandler(QObject):
    """任务管理器事件处理器。

    不直接持有主窗口引用；通过注入的回调与外部通信。
    """

    def __init__(
        self,
        task_progress_panel,
        location_manager,
        search_manager,
        route_manager,
        start_animation: Callable,
        stop_animation: Callable,
        hide_loading: Callable,
        show_gpx_popup_cb: Callable,
        logger: Optional[logging.Logger] = None,
        pending_export_getter: Optional[Callable] = None,
        pending_export_setter: Optional[Callable] = None,
        route_plan_panel_getter: Optional[Callable] = None,
        parent: Optional[QObject] = None,
    ):
        super().__init__(parent)
        self._panel = task_progress_panel
        self._loc_mgr = location_manager
        self._srch_mgr = search_manager
        self._route_mgr = route_manager
        self._start_anim = start_animation
        self._stop_anim = stop_animation
        self._hide_loading = hide_loading
        self._show_gpx_popup = show_gpx_popup_cb
        self._logger = logger or logging.getLogger(__name__)
        self._pending_getter = pending_export_getter or (lambda: None)
        self._pending_setter = pending_export_setter or (lambda v: None)
        self._rpp_getter = route_plan_panel_getter or (lambda: None)

    # ──────────────────────────────────────────────────────────────────
    # 任务事件槽
    # ──────────────────────────────────────────────────────────────────

    @pyqtSlot(str, str)
    def on_task_started(self, task_id: str, task_type: str):
        self._logger.info(f"[任务] 开始: {task_id} ({task_type})")
        task_name = {'location': '定位', 'search': '搜索',
                     'routing': '路线规划', 'map_render': '地图渲染'}.get(task_type, task_type)
        self._panel.start_task(task_id, task_type, task_name)
        if task_type in ('location', 'search', 'routing'):
            self._start_anim()

    @pyqtSlot(str, int, str)
    def on_task_progress(self, task_id: str, percent: int, message: str):
        self._panel.update_progress(percent, message)

    @pyqtSlot(str, object)
    def on_task_completed(self, task_id: str, result):
        self._logger.info(f"[任务] 完成: {task_id}")

        if task_id.startswith('location_'):
            self._stop_anim()
            self._loc_mgr.on_location_task_completed(task_id, result)
            self._panel.task_completed("定位完成")

        elif task_id.startswith('search_'):
            self._stop_anim()
            self._srch_mgr.on_search_task_completed(task_id, result)
            self._panel.task_completed("搜索完成")

        elif task_id.startswith('routing_'):
            self._stop_anim()
            self._hide_loading()
            self._route_mgr.on_route_task_completed(task_id, result)
            self._panel.task_completed("路线规划完成")
            # 检查是否有待导出的历史记录
            pending = self._pending_getter()
            if pending is not None and result and result.get('alternatives'):
                alts = result['alternatives']
                if alts:
                    sel = alts[0]
                    route_data = {
                        'description': f"{pending.get('start', '起点')} → {pending.get('end', '终点')}",
                        'distance': sel.get('distance', 0),
                        'duration': sel.get('duration', 0),
                        'route_points': sel.get('route_points', []),
                    }
                    self._show_gpx_popup(route_data)
                self._pending_setter(None)

        elif task_id.startswith('elevation_'):
            self._route_mgr.on_elevation_task_completed(task_id, result)
            self._panel.task_completed("海拔数据获取完成")

        elif task_id.startswith('map_render_'):
            self._hide_loading()
            self._route_mgr.on_map_render_task_completed(task_id, result)
            self._panel.task_completed("地图渲染完成")
            rpp = self._rpp_getter()
            if rpp is not None and rpp.isVisible():
                rpp.hide_loading()

        elif task_id.startswith('context_menu_'):
            # 处理右键菜单任务完成（result 是 location_info）
            # 这里通过回调让 app 展示右键菜单
            self._panel.task_completed("位置信息获取完成")

        else:
            self._panel.task_completed("任务完成")

        QTimer.singleShot(3000, self._panel.reset)

    @pyqtSlot(str, str)
    def on_task_failed(self, task_id: str, error: str):
        self._logger.error(f"[任务] 失败: {task_id} - {error}")

        if task_id.startswith('location_'):
            self._stop_anim()
            self._loc_mgr.on_location_task_failed(task_id, error)

        elif task_id.startswith('search_'):
            self._stop_anim()
            self._hide_loading()
            self._srch_mgr.on_search_task_failed(task_id, error)

        elif task_id.startswith('routing_'):
            self._stop_anim()
            self._hide_loading()
            self._route_mgr.on_route_task_failed(task_id, error)
            rpp = self._rpp_getter()
            if rpp is not None and rpp.isVisible():
                rpp.hide_loading()
                rpp.show_route_plan_error("路线规划失败，请重试")

        elif task_id.startswith('map_render_'):
            self._hide_loading()
            self._route_mgr.on_map_render_task_failed(task_id, error)
            rpp = self._rpp_getter()
            if rpp is not None and rpp.isVisible():
                rpp.hide_loading()
                rpp.show_route_plan_error("地图渲染失败，请重试")

        elif task_id.startswith('context_menu_'):
            self._logger.error(f"[地图右键] 任务失败: {error}")

        self._panel.task_failed(error)
        QTimer.singleShot(5000, self._panel.reset)

    @pyqtSlot(str)
    def on_task_cancelled(self, task_id: str):
        self._logger.warning(f"[任务] 已取消: {task_id}")
        self._panel.task_cancelled()
        QTimer.singleShot(2000, self._panel.reset)

    @pyqtSlot(str, str, str)
    def on_task_log(self, task_id: str, level: str, message: str):
        self._panel.add_log(level, message)
        level_map = {
            'DEBUG': self._logger.debug, 'INFO': self._logger.info,
            'WARNING': self._logger.warning, 'ERROR': self._logger.error,
            'CRITICAL': self._logger.critical,
        }
        level_map.get(level, self._logger.info)(f"[任务 {task_id}] {message}")

    @pyqtSlot(str)
    def on_cancel_task_requested(self, task_id: str):
        self._logger.info(f"[任务] 用户请求取消: {task_id}")
        # 通过外部注入的 task_manager 取消（见 _wire_signals）

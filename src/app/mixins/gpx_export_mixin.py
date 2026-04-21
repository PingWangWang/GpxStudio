"""GpxExportMixin — GPX 导出功能相关方法"""
import os
from modules.gpx import GpxExportService
from services.config.map_config import map_config


class GpxExportMixin:
    """GPX 文件导出相关的所有交互逻辑。"""

    def _on_export_gpx_clicked(self, route_data: dict, button=None, item=None):
        """导出GPX按钮点击"""
        self.logger.info(f"[GPX导出] 用户点击导出GPX按钮")

        try:
            from ui.popups.gpx_export_popup import GpxExportPopup

            if self.gpx_export_popup is not None and self.gpx_export_popup.isVisible():
                self.gpx_export_popup.hide()

            self.gpx_export_popup = GpxExportPopup(route_data, self)
            self.gpx_export_popup.export_confirmed.connect(lambda start_time, export_elevation: self._export_gpx_file(route_data, start_time, export_elevation))
            self.gpx_export_popup.closed.connect(self._on_gpx_popup_closed)

            self._register_popup(self.gpx_export_popup)

            if item and button:
                item_global_pos = item.mapToGlobal(item.rect().topLeft())

                if self.route_plan_panel is not None and self.route_plan_panel.isVisible():
                    panel_global_pos = self.route_plan_panel.mapToGlobal(self.route_plan_panel.rect().topLeft())
                    panel_rect = self.route_plan_panel.rect()

                    popup_x = panel_global_pos.x() + panel_rect.width() + 10
                    popup_y = item_global_pos.y()

                    from PyQt5.QtWidgets import QApplication
                    screen = QApplication.primaryScreen().geometry()

                    if popup_x + self.gpx_export_popup.width() > screen.right():
                        popup_x = panel_global_pos.x() - self.gpx_export_popup.width() - 10

                    if popup_y + 200 > screen.bottom():
                        popup_y = screen.bottom() - 250

                    from PyQt5.QtCore import QPoint
                    self.gpx_export_popup.show_at_position(QPoint(popup_x, popup_y))
            elif self.route_plan_panel is not None and self.route_plan_panel.isVisible():
                panel_global_pos = self.route_plan_panel.mapToGlobal(self.route_plan_panel.rect().topLeft())
                panel_rect = self.route_plan_panel.rect()

                popup_x = panel_global_pos.x() + panel_rect.width() + 10
                popup_y = panel_global_pos.y() + 50

                from PyQt5.QtWidgets import QApplication
                screen = QApplication.primaryScreen().geometry()

                if popup_x + self.gpx_export_popup.width() > screen.right():
                    popup_x = panel_global_pos.x() - self.gpx_export_popup.width() - 10

                if popup_y + 200 > screen.bottom():
                    popup_y = screen.bottom() - 250

                from PyQt5.QtCore import QPoint
                self.gpx_export_popup.show_at_position(QPoint(popup_x, popup_y))
            else:
                from PyQt5.QtWidgets import QApplication
                from PyQt5.QtCore import QPoint
                screen = QApplication.primaryScreen().geometry()
                center_x = screen.center().x() - self.gpx_export_popup.width() // 2
                center_y = screen.center().y() - 100
                self.gpx_export_popup.show_at_position(QPoint(center_x, center_y))

        except Exception as e:
            self.logger.error(f"[GPX导出] 创建导出弹出面板失败: {e}")
            self._show_warning("导出失败", f"无法创建导出面板: {str(e)}")

    def _on_gpx_popup_closed(self):
        """GPX导出弹出面板关闭"""
        self.logger.debug("[GPX导出] 弹出面板已关闭")

    def _get_last_export_path(self):
        """获取上次导出路径"""
        try:
            from app.data_paths import get_config_dir
            import json
            import os

            config_path = os.path.join(get_config_dir(), 'export_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('last_export_path')
        except Exception as e:
            self.logger.error(f"[GPX导出] 读取上次导出路径失败: {e}")
        return None

    def _save_last_export_path(self, export_path):
        """保存上次导出路径"""
        try:
            from app.data_paths import get_config_dir
            import json
            import os

            config_path = os.path.join(get_config_dir(), 'export_config.json')
            config = {}

            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

            config['last_export_path'] = export_path

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            self.logger.debug(f"[GPX导出] 已保存上次导出路径: {export_path}")
        except Exception as e:
            self.logger.error(f"[GPX导出] 保存上次导出路径失败: {e}")

    def _export_gpx_file(self, route_data: dict, start_time, export_elevation=False):
        """执行GPX文件导出"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            from PyQt5.QtCore import QThread, pyqtSignal

            self.logger.info(f"[GPX导出] 开始导出GPX文件，导出海拔数据: {export_elevation}")

            route_points = route_data.get('route_points', [])
            if not route_points:
                self._show_warning("导出失败", "路线数据为空，无法导出GPX文件")
                return

            description = route_data.get('description', '路线')

            start_name = route_data.get('start_name', '') or route_data.get('origin_name', '') or self.data_manager.start_name or '起点'
            end_name = route_data.get('end_name', '') or route_data.get('destination_name', '') or self.data_manager.end_name or '终点'

            import re
            safe_start = re.sub(r'[\\/:*?"<>|]', '', start_name)
            safe_end = re.sub(r'[\\/:*?"<>|]', '', end_name)

            if start_time and hasattr(start_time, 'toString'):
                time_str = start_time.toString("yyyyMMdd_hhmm")
                default_filename = f"{safe_start}_{safe_end}_{time_str}.gpx"
            else:
                default_filename = f"{safe_start}_{safe_end}.gpx"

            last_export_path = self._get_last_export_path()
            if last_export_path:
                default_path = os.path.join(last_export_path, default_filename)
            else:
                default_path = default_filename

            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存GPX文件", default_path,
                "GPX文件 (*.gpx);;所有文件 (*)"
            )

            if not file_path:
                self.logger.info("[GPX导出] 用户取消了文件保存")
                return

            export_dir = os.path.dirname(file_path)
            if os.path.isdir(export_dir):
                self._save_last_export_path(export_dir)

            if not file_path.lower().endswith('.gpx'):
                file_path += '.gpx'

            from ui.popups.progress_popup import ProgressPopup
            progress_popup = ProgressPopup(self)
            progress_popup.show_at_center()

            total_duration_seconds = route_data.get('duration', None)
            total_distance_meters = route_data.get('distance', None)

            class ExportThread(QThread):
                """导出线程"""
                progress_updated = pyqtSignal(int, str)
                export_completed = pyqtSignal(bool, str)

                def __init__(self, parent, route_points, start_time, file_path,
                             start_name, end_name, export_elevation,
                             total_duration_seconds, total_distance_meters=None,
                             route_history_storage=None, route_data=None):
                    super().__init__(parent)
                    self.route_points = route_points
                    self.start_time = start_time
                    self.file_path = file_path
                    self.start_name = start_name
                    self.end_name = end_name
                    self.export_elevation = export_elevation
                    self.total_duration_seconds = total_duration_seconds
                    self.total_distance_meters = total_distance_meters
                    self.route_history_storage = route_history_storage
                    self.route_data = route_data

                def run(self):
                    try:
                        def log_callback(level: str, message: str):
                            log_func = getattr(self.parent().logger, level.lower(), self.parent().logger.info)
                            log_func(f"[GPX导出] {message}")

                        gpx_service = GpxExportService(logger=log_callback)

                        elevation_data_obtained = False
                        if self.export_elevation:
                            has_cached_elevation = False
                            if self.route_history_storage and self.route_data:
                                if self.route_points and len(self.route_points) > 0:
                                    for point in self.route_points:
                                        if point is not None and len(point) >= 3:
                                            has_cached_elevation = True
                                            self.parent().logger.info(f"[GPX导出] 使用历史记录中缓存的海拔数据")
                                            self.progress_updated.emit(30, "使用缓存的海拔数据...")
                                            break

                            if not has_cached_elevation:
                                self.progress_updated.emit(20, "正在获取海拔数据...")

                                from services.config.map_config import map_config
                                map_source = map_config.get_map_source()
                                if map_source:
                                    routing_service = self.parent().service_manager.get_routing_service(map_source)
                                    if hasattr(routing_service, '_get_elevation'):
                                        def elevation_progress_callback(progress, message):
                                            self.progress_updated.emit(progress, message)

                                        route_points_with_elevation = routing_service._get_elevation(
                                            self.route_points,
                                            progress_callback=elevation_progress_callback
                                        )
                                        self.route_points = route_points_with_elevation
                                        elevation_data_obtained = True
                                        self.progress_updated.emit(50, "海拔数据获取完成，正在导出GPX文件...")
                                        self.parent().logger.info(f"[GPX导出] 海拔数据获取成功")
                                    else:
                                        self.progress_updated.emit(50, "当前地图服务不支持海拔数据获取，正在导出GPX文件...")
                                else:
                                    self.progress_updated.emit(50, "未设置地图服务，正在导出GPX文件...")
                            else:
                                self.progress_updated.emit(50, "正在导出GPX文件...")
                        else:
                            self.progress_updated.emit(50, "正在导出GPX文件...")

                        success = gpx_service.export_to_gpx(
                            route_points=self.route_points,
                            start_datetime=self.start_time,
                            file_path=self.file_path,
                            start_name=self.start_name,
                            end_name=self.end_name,
                            export_elevation=self.export_elevation,
                            total_duration_seconds=self.total_duration_seconds,
                            total_distance_meters=self.total_distance_meters,
                            transport_mode=self.route_data.get('mode') if self.route_data else None,
                            waypoint_names=self.route_data.get('waypoints') if self.route_data else None,
                            description=f"{self.start_name} → {self.end_name}" if self.start_name and self.end_name else None
                        )

                        if success and elevation_data_obtained and self.route_history_storage and self.route_data:
                            try:
                                start_name = self.route_data.get('start_name') or self.start_name
                                end_name = self.route_data.get('end_name') or self.end_name
                                mode = self.route_data.get('mode', 'driving')

                                self.route_history_storage.add_record(
                                    start=start_name,
                                    end=end_name,
                                    mode=mode,
                                    waypoints=self.route_data.get('waypoints', []),
                                    start_coords=self.route_data.get('start_coords'),
                                    end_coords=self.route_data.get('end_coords'),
                                    waypoint_coords=self.route_data.get('waypoint_coords', []),
                                    distance=self.route_data.get('distance'),
                                    duration=self.route_data.get('duration'),
                                    route_points=self.route_points,
                                    start_coord_system=self.route_data.get('start_coord_system'),
                                    end_coord_system=self.route_data.get('end_coord_system'),
                                    waypoint_coord_systems=self.route_data.get('waypoint_coord_systems', [])
                                )
                                self.parent().logger.info(f"[GPX导出] 已将海拔数据缓存到历史记录: {start_name} → {end_name}")
                            except Exception as e:
                                self.parent().logger.warning(f"[GPX导出] 缓存海拔数据到历史记录失败: {e}")

                        self.progress_updated.emit(100, "导出完成")
                        self.export_completed.emit(success, self.file_path)
                    except Exception as e:
                        error_msg = f"导出过程中发生错误: {str(e)}"
                        self.parent().logger.error(error_msg)
                        self.progress_updated.emit(0, error_msg)
                        self.export_completed.emit(False, str(e))

            from services.config.map_config import map_config
            current_map_source = map_config.get_map_source()
            coord_system = 'GCJ-02' if current_map_source == 'gaode' else 'WGS-84'

            enhanced_route_data = {
                'start_name': start_name,
                'end_name': end_name,
                'mode': route_data.get('mode') or (self.route_plan_panel.current_transport_mode if self.route_plan_panel is not None else 'driving'),
                'waypoints': route_data.get('waypoints') or (self.data_manager.waypoints_names if self.data_manager is not None else []),
                'start_coords': route_data.get('start_coords') or (self.data_manager.start_coords if self.data_manager is not None else None),
                'end_coords': route_data.get('end_coords') or (self.data_manager.end_coords if self.data_manager is not None else None),
                'waypoint_coords': route_data.get('waypoint_coords') or (self.data_manager.waypoints_coords if self.data_manager is not None else []),
                'distance': route_data.get('distance'),
                'duration': route_data.get('duration'),
                'start_coord_system': route_data.get('start_coord_system') or coord_system,
                'end_coord_system': route_data.get('end_coord_system') or coord_system,
                'waypoint_coord_systems': route_data.get('waypoint_coord_systems') or [coord_system for _ in (route_data.get('waypoint_coords') or (self.data_manager.waypoints_coords if self.data_manager is not None else []))]
            }

            route_history_storage = None
            if self.route_manager is not None and hasattr(self.route_manager, 'route_history_storage'):
                route_history_storage = self.route_manager.route_history_storage

            export_thread = ExportThread(
                self, route_points, start_time, file_path, start_name, end_name,
                export_elevation, total_duration_seconds, total_distance_meters,
                route_history_storage, enhanced_route_data
            )

            def on_progress_updated(value, message):
                if progress_popup and progress_popup.isVisible():
                    progress_popup.set_progress(value, message)

            def on_export_completed(success, result):
                if progress_popup and progress_popup.isVisible():
                    if success:
                        progress_popup.set_complete("GPX文件导出成功")
                        self.logger.info(f"[GPX导出] GPX文件导出成功: {result}")
                    else:
                        progress_popup.set_progress(0, f"导出失败: {result}")
                        progress_popup.cancel_button.setText("确定")
                        self.logger.error(f"[GPX导出] GPX文件导出失败: {result}")

            export_thread.progress_updated.connect(on_progress_updated)
            export_thread.export_completed.connect(on_export_completed)
            export_thread.start()

        except Exception as e:
            self.logger.error(f"[GPX导出] 导出过程中发生错误: {e}")
            self._show_warning("导出失败", f"导出过程中发生错误: {str(e)}")

    def _on_history_export_gpx_clicked(self, history_data: dict, button=None, item=None):
        """历史记录导出GPX按钮点击"""
        self.logger.info(f"[GPX导出] 用户点击历史记录导出GPX按钮")

        try:
            route_points = history_data.get('route_points', [])

            if route_points:
                self.logger.info(f"[GPX导出] 历史记录有完整路线数据，直接导出")
                route_data = {
                    'description': f"{history_data.get('start', '起点')} → {history_data.get('end', '终点')}",
                    'distance': history_data.get('distance', 0),
                    'duration': history_data.get('duration', 0),
                    'route_points': route_points,
                    'start_name': history_data.get('start', '起点'),
                    'end_name': history_data.get('end', '终点'),
                    'timestamp': history_data.get('timestamp'),
                    'mode': history_data.get('mode', 'driving'),
                    'waypoints': history_data.get('waypoints', []),
                    'start_coords': history_data.get('start_coords'),
                    'end_coords': history_data.get('end_coords'),
                    'waypoint_coords': history_data.get('waypoint_coords', []),
                    'start_coord_system': history_data.get('start_coord_system'),
                    'end_coord_system': history_data.get('end_coord_system'),
                    'waypoint_coord_systems': history_data.get('waypoint_coord_systems', [])
                }
                self._show_gpx_export_popup(route_data, button, item)
            else:
                self.logger.info(f"[GPX导出] 历史记录没有完整路线数据，需要重新规划路线")

                start_coords = history_data.get('start_coords')
                end_coords = history_data.get('end_coords')

                if start_coords and end_coords:
                    self._replan_and_export_route(history_data)
                else:
                    self._show_warning("导出失败", "该历史记录缺少位置坐标信息，无法重新规划路线。请重新搜索起点和终点。")

        except Exception as e:
            self.logger.error(f"[GPX导出] 处理历史记录导出时出错: {str(e)}")
            self._show_warning("导出失败", f"处理导出请求时发生错误: {str(e)}")

    def _show_gpx_export_popup(self, route_data: dict, button=None, item=None):
        """显示GPX导出弹出面板"""
        try:
            from ui.popups.gpx_export_popup import GpxExportPopup

            if self.gpx_export_popup is not None and self.gpx_export_popup.isVisible():
                self.gpx_export_popup.hide()

            self.gpx_export_popup = GpxExportPopup(route_data, self)
            self.gpx_export_popup.export_confirmed.connect(lambda start_time, export_elevation: self._export_gpx_file(route_data, start_time, export_elevation))
            self.gpx_export_popup.closed.connect(self._on_gpx_popup_closed)

            self._register_popup(self.gpx_export_popup)

            if item and button:
                item_global_pos = item.mapToGlobal(item.rect().topLeft())

                if self.route_plan_panel is not None and self.route_plan_panel.isVisible():
                    panel_global_pos = self.route_plan_panel.mapToGlobal(self.route_plan_panel.rect().topLeft())
                    panel_rect = self.route_plan_panel.rect()

                    popup_y = item_global_pos.y()
                    popup_x = panel_global_pos.x() + panel_rect.width() + 2

                    from PyQt5.QtWidgets import QApplication
                    screen = QApplication.primaryScreen().geometry()

                    if popup_x + self.gpx_export_popup.width() > screen.right():
                        popup_x = panel_global_pos.x() - self.gpx_export_popup.width() - 10

                    if popup_y + 200 > screen.bottom():
                        popup_y = screen.bottom() - 250

                    from PyQt5.QtCore import QPoint
                    self.gpx_export_popup.show_at_position(QPoint(popup_x, popup_y))
                else:
                    from PyQt5.QtWidgets import QApplication
                    from PyQt5.QtCore import QPoint
                    screen = QApplication.primaryScreen().geometry()
                    center_x = screen.center().x() - self.gpx_export_popup.width() // 2
                    center_y = screen.center().y() - 100
                    self.gpx_export_popup.show_at_position(QPoint(center_x, center_y))
            elif self.route_plan_panel is not None and self.route_plan_panel.isVisible():
                panel_global_pos = self.route_plan_panel.mapToGlobal(self.route_plan_panel.rect().topLeft())
                panel_rect = self.route_plan_panel.rect()

                popup_x = panel_global_pos.x() + panel_rect.width() + 10
                popup_y = panel_global_pos.y() + 50

                from PyQt5.QtWidgets import QApplication
                screen = QApplication.primaryScreen().geometry()

                if popup_x + self.gpx_export_popup.width() > screen.right():
                    popup_x = panel_global_pos.x() - self.gpx_export_popup.width() - 10

                if popup_y + 200 > screen.bottom():
                    popup_y = screen.bottom() - 250

                from PyQt5.QtCore import QPoint
                self.gpx_export_popup.show_at_position(QPoint(popup_x, popup_y))
            else:
                from PyQt5.QtWidgets import QApplication
                from PyQt5.QtCore import QPoint
                screen = QApplication.primaryScreen().geometry()
                center_x = screen.center().x() - self.gpx_export_popup.width() // 2
                center_y = screen.center().y() - 100
                self.gpx_export_popup.show_at_position(QPoint(center_x, center_y))

        except Exception as e:
            self.logger.error(f"[GPX导出] 创建导出弹出面板失败: {e}")
            self._show_warning("导出失败", f"无法创建导出面板: {str(e)}")

    def _replan_and_export_route(self, history_data: dict):
        """重新规划路线并导出"""
        self.logger.info(f"[GPX导出] 开始重新规划路线用于导出")

        self._show_info("正在处理", "该历史记录没有完整路线数据，正在重新规划路线...")

        start_coords = history_data.get('start_coords')
        end_coords = history_data.get('end_coords')

        if start_coords:
            self.data_manager.set_start_location(tuple(start_coords), history_data.get('start', ''))
        if end_coords:
            self.data_manager.set_end_location(tuple(end_coords), history_data.get('end', ''))

        self._pending_export_history = history_data

        mode = history_data.get('mode', 'driving')
        self.route_manager.plan_route(mode)

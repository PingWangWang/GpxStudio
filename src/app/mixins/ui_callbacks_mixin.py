"""UICallbacksMixin — ui_updater 字典中各回调方法的实现"""
from typing import Optional

from PyQt5.QtWidgets import QApplication, QMessageBox, QListWidgetItem
from PyQt5.QtCore import Qt, QTimer


class UICallbacksMixin:
    """供 ui_updater 字典使用的 UI 更新回调方法集合。"""

    # ── 对话框 ────────────────────────────────────────────────────────────

    def _show_warning(self, title: str, message: str):
        try:
            from ui.dialogs.custom_message_dialog import CustomMessageDialog
            CustomMessageDialog(self, title=title, message=message, show_cancel=False, ok_text="确定").exec_()
        except ImportError:
            QMessageBox.warning(self, title, message)

    def _show_info(self, title: str, message: str):
        try:
            from ui.dialogs.custom_message_dialog import CustomMessageDialog
            CustomMessageDialog(self, title=title, message=message, show_cancel=False, ok_text="确定").exec_()
        except ImportError:
            QMessageBox.information(self, title, message)

    # ── 进度条 ────────────────────────────────────────────────────────────

    def _set_progress_indeterminate(self):
        self.task_progress_panel.progress_widget.progress_bar.setRange(0, 0)
        QApplication.processEvents()

    def _set_progress_complete(self):
        self.task_progress_panel.progress_widget.progress_bar.setRange(0, 100)
        self.task_progress_panel.progress_widget.progress_bar.setValue(100)
        QApplication.processEvents()

    def _set_progress(self, value: int):
        self.task_progress_panel.progress_widget.progress_bar.setRange(0, 100)
        self.task_progress_panel.progress_widget.progress_bar.setValue(value)
        QApplication.processEvents()

    # ── 结果列表 ──────────────────────────────────────────────────────────

    def _clear_results(self):
        self.search_results_list.clear()
        QApplication.processEvents()

    def _clear_results_list(self):
        self.search_results_list.clear()

    def _add_result(self, text: str):
        self.search_results_list.addItem(text)

    def _set_results_title(self, title: str):
        self.search_results_title.setText(title)

    def _show_search_results(self, locations: list):
        for i, location in enumerate(locations):
            if isinstance(location, dict):
                name = location.get('name', '')
                address = location.get('address', '')
                lat = location.get('lat', 0)
                lon = location.get('lon', 0)
                level = location.get('level', None)
                type_info = location.get('type', None)
                radius = location.get('radius', None)
                display_parts = [f"{i+1}. {name}"]
                if address and address != name:
                    display_parts.append(f"   地址: {address}")
                if type_info:
                    display_parts.append(f"   类型: {type_info}")
                display_parts.append(f"   坐标: {lat:.6f}, {lon:.6f}")
                item_text = "\n".join(display_parts)
                full_name = f"{name}" if not (address and address != name) else f"{name} ({address})"
            else:
                name = location.address
                lat = location.latitude
                lon = location.longitude
                level = None
                type_info = location.type if hasattr(location, 'type') else None
                radius = None
                display_parts = [f"{i+1}. {name}"]
                if type_info:
                    display_parts.append(f"   类型: {type_info}")
                display_parts.append(f"   坐标: {lat:.6f}, {lon:.6f}")
                item_text = "\n".join(display_parts)
                full_name = name
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, (full_name, lat, lon, level, type_info, radius))
            self.search_results_list.addItem(item)

    def _show_search_results_on_map(self, locations: list, location_type: str):
        self.map_manager.show_search_results_on_map(locations, location_type)

    def _show_search_results_dropdown(self, results: list):
        self.hide_loading()
        self.logger.debug(f"[搜索结果] 显示 {len(results)} 条搜索结果")
        if self.search_results_popup is not None and results:
            self.search_results_popup.show_results(results, self.search_container)
            self._refresh_toolbar_buttons()
            QTimer.singleShot(50, lambda: self.cancel_button.raise_())

    # ── 位置显示 ──────────────────────────────────────────────────────────

    def _update_location_display(self, location_type: str, name: str, data: tuple):
        if location_type == "start":
            if self.start_label is not None:
                self.start_label.setText(name)
                self.start_label.setCursorPosition(0)
                self.start_label.setProperty('userData', data)
        elif location_type == "end":
            if self.end_label is not None:
                self.end_label.setText(name)
                self.end_label.setCursorPosition(0)
                self.end_label.setProperty('userData', data)

    def _update_start_from_search(self, name: str, data: tuple):
        if self.start_label is not None:
            self.start_label.setText(name)
            self.start_label.setCursorPosition(0)
            self.start_label.setProperty('userData', data)
        if self.start_list is not None:
            self.start_list.clear()
            self.start_list.addItem(name)
            self.start_list.item(0).setData(Qt.UserRole, data)

    def _update_end_from_search(self, name: str, data: tuple):
        if self.end_label is not None:
            self.end_label.setText(name)
            self.end_label.setCursorPosition(0)
            self.end_label.setProperty('userData', data)
        if self.end_list is not None:
            self.end_list.clear()
            self.end_list.addItem(name)
            self.end_list.item(0).setData(Qt.UserRole, data)

    def _add_waypoint_to_list(self, name: str, data: tuple, level: Optional[str]):
        waypoint_item = QListWidgetItem(
            f"{len(self.data_manager.waypoints_coords)}. {name}"
        )
        level_data = level if level else None
        waypoint_item.setData(Qt.UserRole, (name, data[1], data[2], level_data, None))
        self.waypoint_list.addItem(waypoint_item)

    # ── 地图 ──────────────────────────────────────────────────────────────

    def _update_map_preview(self):
        self.map_manager.update_map_preview()

    def _preview_search_result(self, coords, name, level=None, type_info=None, radius=None, result_data=None):
        self.map_manager.preview_search_result(coords, name, level, type_info, radius, result_data)

    def _show_location_on_map(self, lat: float, lon: float, popup_text: str):
        self.logger.debug(f"[UI回调] 收到显示位置请求: {lat}, {lon}")
        # 路线面板"我的位置"待填状态：定位成功后填充当前输入框
        route_plan_panel = getattr(self, 'route_plan_panel', None)
        if route_plan_panel is not None and route_plan_panel.has_pending_location():
            search_type = route_plan_panel.get_pending_search_type()
            route_plan_panel.fill_pending_location(lat, lon)
            # 同步数据管理器坐标（与右键设置起终点一致）
            name = "我的位置"
            if search_type == 'start':
                self.data_manager.set_start_location((lat, lon), name)
            elif search_type == 'end':
                self.data_manager.set_end_location((lat, lon), name)
            # 同步会话标志：定位填充同样视为本会话已设置起点/终点，
            # 避免后续地址选择触发"会话首次设置"清空已设的"我的位置"
            self._route_plan_session_set = True
        self.map_manager.show_location_on_map(lat, lon, popup_text)

    def _show_route_on_map(self):
        self.map_manager.show_route_on_map()

    def _load_map_url(self, url: str):
        from PyQt5.QtCore import QUrl
        self.map_view.setUrl(QUrl(url))

    def _trigger_browser_location(self):
        if self.map_view and self.map_view.page():
            from modules.map import MapJsBridge
            MapJsBridge.trigger_browser_location(self.map_view.page())

    # ── 时间面板回调 ──────────────────────────────────────────────────────

    def _setup_date_panel_callback(self, callback):
        try:
            self.date_panel.date_selected.disconnect()
        except TypeError:
            pass
        self.date_panel.date_selected.connect(callback)

    def _setup_time_panel_callback(self, callback):
        try:
            self.time_panel.time_selected.disconnect()
        except TypeError:
            pass
        self.time_panel.time_selected.connect(callback)

    def _show_date_panel(self, current_date):
        panel_rect = self.middle_panel.rect()
        panel_pos = self.middle_panel.mapToGlobal(panel_rect.topLeft())
        panel_size = self.middle_panel.size()
        self.date_panel.show_panel(current_date, panel_pos, 0, panel_size)

    def _show_time_panel(self, current_time):
        panel_rect = self.middle_panel.rect()
        panel_pos = self.middle_panel.mapToGlobal(panel_rect.topLeft())
        panel_size = self.middle_panel.size()
        self.time_panel.show_panel(current_time, panel_pos, 0, panel_size)

    def _add_route_time_info(self):
        start_time_str = self.start_time_edit.dateTime().toString("yyyy-MM-dd HH:mm")
        self.search_results_list.addItem(f"起始时间: {start_time_str}")
        duration_hours = self.data_manager.estimated_duration_seconds // 3600
        duration_minutes = (self.data_manager.estimated_duration_seconds % 3600) // 60
        self.search_results_list.addItem(f"途径时间: {int(duration_hours)}小时{duration_minutes}分钟")
        end_time_str = self.end_time_edit.dateTime().toString("yyyy-MM-dd HH:mm")
        self.search_results_list.addItem(f"结束时间: {end_time_str}")

    def _show_initial_map(self):
        if not self.isVisible():
            QTimer.singleShot(1000, self._show_initial_map)
            return
        self.map_manager.show_initial_map()
        self.scale_panel.update_zoom(10)

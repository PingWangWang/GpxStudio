"""SearchMixin — 搜索框交互处理方法"""
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtCore import QTimer


class SearchMixin:
    """搜索输入框、历史记录、搜索结果交互处理。"""

    def on_search_button_clicked(self):
        """搜索按钮点击"""
        search_text = self.search_input.text().strip()
        if not search_text:
            self.logger.debug("[搜索] 搜索框为空，不执行搜索")
            return
        self.logger.info(f"[搜索] 搜索地点: {search_text}")
        self.show_loading()
        self.current_search_text = search_text
        if self.search_history_popup is not None:
            self.search_history_popup.hide()
        self.search_manager.search_location(search_text, "search")

    def _on_search_input_focus_in(self, event):
        QLineEdit.focusInEvent(self.search_input, event)
        self._show_search_history()

    def _on_search_input_mouse_press(self, event):
        QLineEdit.mousePressEvent(self.search_input, event)
        self.logger.debug("[搜索历史] 搜索框被点击，显示历史记录")
        self._show_search_history()

    def _on_search_input_focus_out(self, event):
        QLineEdit.focusOutEvent(self.search_input, event)
        QTimer.singleShot(200, self._hide_search_history_if_needed)

    def _on_search_input_text_changed(self, text: str):
        pass

    def _show_search_history(self):
        if self.search_history_popup is None:
            return
        if getattr(self, '_suppress_history_popup', False):
            self.logger.debug("[搜索历史] 抑制标志已设置，不显示历史记录")
            return
        history_list = self.search_manager.get_search_history(10)
        if history_list:
            self.logger.debug(f"[搜索历史] 显示 {len(history_list)} 条历史记录")
            self.search_history_popup.show_history(history_list, self.search_container)
            QTimer.singleShot(10, lambda: self.search_input.setFocus())
        else:
            self.logger.debug("[搜索历史] 没有历史记录")
            self.search_history_popup.hide()

    def _hide_search_history_if_needed(self):
        if self.search_history_popup is None:
            return
        if not self.search_input.hasFocus():
            if not self.search_history_popup.hasFocus():
                self.search_history_popup.hide()

    def _on_history_selected(self, record: dict):
        self.logger.info(f"[搜索历史] 用户选择: {record.get('name')}")
        self._suppress_history_popup = True
        name = record.get('name', '')
        if self.search_input is not None:
            self.search_input.setText(name)
        if self.search_history_popup is not None:
            self.search_history_popup.hide()
        self.search_manager.select_history_result(record)
        QTimer.singleShot(300, lambda: setattr(self, '_suppress_history_popup', False))

    def _on_result_selected(self, result: dict):
        self.logger.info(f"[搜索结果] 用户选择: {result.get('name')}")
        if self.search_history_popup is not None:
            self.search_history_popup.hide()
        self.search_manager.select_result_from_dropdown(result, self.current_search_text)

    def _on_favorite_requested(self, result: dict):
        """搜索结果：收藏此地点"""
        name = result.get('name', '收藏点')
        self.logger.info(f"[搜索结果] 收藏: {name}")

        # 搜索结果自带坐标系标记（高德结果为GCJ-02，OSM为WGS-84），统一转WGS-84存储
        coord_system = result.get('coord_system', 'WGS-84')
        success, message = self.map_manager.add_favorite(
            result.get('lat', 0), result.get('lon', 0),
            name, address=result.get('address', ''),
            coord_system=coord_system)

        if success:
            self._show_info("收藏成功", f"已收藏：{name}")
        else:
            self._show_warning("收藏失败", message)

    def on_route_button_clicked(self):
        self.logger.info("[路线] 路线按钮点击")
        if hasattr(self.route_button, 'start_animation'):
            self.route_button.start_animation()
        self._show_route_plan_panel()

    def on_cancel_button_clicked(self):
        self.logger.info("[搜索] ========== 关闭按钮点击 ==========")
        if self.search_results_popup is not None:
            self.search_results_popup.hide()
        self.search_input.clear()
        self._switch_to_route_button()

    def _switch_to_cancel_button(self):
        self.logger.debug("[按钮切换] 切换到关闭按钮")
        self.route_button.hide()
        self.cancel_button.show()
        self.cancel_button.raise_()

    def _switch_to_route_button(self):
        self.logger.debug("[按钮切换] 切换回路线按钮")
        self.cancel_button.hide()
        self.route_button.show()
        self.route_button.raise_()

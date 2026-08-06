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
        # 无历史记录时也显示弹窗（仅"我的位置"首行）
        self.logger.debug(f"[搜索历史] 显示 {len(history_list)} 条历史记录")
        self.search_history_popup.show_history(history_list, self.search_container)
        QTimer.singleShot(10, lambda: self.search_input.setFocus())

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
        # 搜索结果弹窗已自关，刷新工具栏按钮态（恢复路线按钮、隐藏关闭按钮）
        self._refresh_toolbar_buttons()

    def _on_favorite_requested(self, result: dict):
        """搜索历史/搜索结果：切换收藏状态（未收藏则收藏，已收藏则取消）

        成功操作不弹提示（按钮已乐观变色 + 地图刷新即反馈）；
        仅失败时显式警告。
        """
        name = result.get('name', '收藏点')
        self.logger.info(f"[收藏点] 切换收藏: {name}")

        # 结果自带坐标系标记（高德结果为GCJ-02，OSM为WGS-84），toggle 内部统一转 WGS-84
        coord_system = result.get('coord_system', 'WGS-84')
        action = self.map_manager.toggle_favorite(
            float(result.get('lat', 0)), float(result.get('lon', 0)),
            name, address=result.get('address', ''),
            coord_system=coord_system, type_text=result.get('type', ''))

        if action == 'failed':
            self._show_warning("收藏操作失败", "请查看日志了解详情")

    def on_route_button_clicked(self):
        self.logger.info("[路线] 路线按钮点击")
        if hasattr(self.route_button, 'start_animation'):
            self.route_button.start_animation()
        self._show_route_plan_panel()

    def on_cancel_button_clicked(self):
        self.logger.info("[搜索] ========== 关闭按钮点击 ==========")
        # 关闭顺序：先关收藏夹弹窗（当前操作层），再关搜索结果弹窗；每步后刷新按钮态
        favorites_popup = getattr(self, 'favorites_popup', None)
        if favorites_popup is not None and favorites_popup.isVisible():
            favorites_popup.hide()
            self._refresh_toolbar_buttons()
            return
        if self.search_results_popup is not None:
            self.search_results_popup.hide()
        self.search_input.clear()
        self._refresh_toolbar_buttons()

    def _refresh_toolbar_buttons(self):
        """按当前可见弹窗集合统一刷新工具栏按钮态（route/favorites/cancel）

        按钮显隐由"搜索结果弹窗可见 / 收藏夹弹窗可见"两个状态决定（幂等）：
        - route 按钮：两个弹窗都关闭时显示
        - favorites 按钮：收藏夹弹窗关闭时显示（搜索结果弹窗打开时保持）
        - cancel 按钮：任一弹窗打开时显示（收藏夹关闭后若搜索结果仍开，cancel 保留，
          保证待选列表可继续关闭——修复多状态叠加时按钮互相覆盖的问题）
        """
        search_results_open = (self.search_results_popup is not None
                               and self.search_results_popup.isVisible())
        # 收藏夹弹窗为延迟创建（首次点击收藏夹按钮才创建），须 getattr 防护
        favorites_popup = getattr(self, 'favorites_popup', None)
        favorites_open = (favorites_popup is not None
                          and favorites_popup.isVisible())

        cancel_needed = search_results_open or favorites_open

        route_button = getattr(self, 'route_button', None)
        favorites_button = getattr(self, 'favorites_button', None)
        cancel_button = getattr(self, 'cancel_button', None)

        if route_button is not None:
            route_button.setVisible(not cancel_needed)
        if favorites_button is not None:
            favorites_button.setVisible(not favorites_open)
        if cancel_button is not None:
            cancel_button.setVisible(cancel_needed)
            if cancel_needed:
                cancel_button.raise_()

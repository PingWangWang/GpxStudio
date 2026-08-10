"""MapMixin — 地图控件交互处理方法（缩放/模式/设置/定位等）"""
import math

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import QRect

from modules.map import MapJsBridge
from modules.map import MapRenderer
from services.config.map_config import map_config


class MapMixin:
    """地图控件（缩放、地图模式、路网、设置按钮、右键菜单触发）相关处理。"""

    # ── 定位 & 缩放 ───────────────────────────────────────────────────────

    def on_locate_clicked(self):
        self.logger.info("[定位按钮] 定位按钮被点击")
        self.start_loading_animation()
        self.location_manager.get_current_location()

    def on_zoom_fit_clicked(self):
        self.logger.info("[缩放] ZOOM按钮点击，开始计算边界框")
        all_points = []
        if self.map_manager is not None:
            # 元素全集：起终点/途径点/路线点 + 当前位置标识（收藏点不参与缩放范围计算）
            all_points = self.map_manager.get_all_visible_element_coords()
        if not all_points:
            self.logger.warning("[缩放] 没有找到地图元素，保持现状")
            return
        # 坐标转换：元素坐标为 WGS-84，地图渲染层统一转 GCJ-02，此处保持一致
        from modules.geolocation.coordinate_transform import CoordinateTransform as _CT
        gcj_points = [_CT.convert(lat, lon, 'WGS-84', 'GCJ-02') for lat, lon in all_points]
        lats = [p[0] for p in gcj_points]
        lons = [p[1] for p in gcj_points]
        center = [(min(lats)+max(lats))/2, (min(lons)+max(lons))/2]
        diagonal = math.sqrt((max(lats)-min(lats))**2 + (max(lons)-min(lons))**2)
        zoom = 15 if diagonal == 0 else max(2, min(18, int(10 - math.log(diagonal, 2))))
        self.logger.info(f"[缩放] 计算完成：中心点={center}，缩放级别={zoom}")
        # JS 侧先判断当前视图是否已包含全部元素：已包含 → 零开销跳过（不刷新界面）；
        # 未包含 → fitBounds 精确适配（含 padding），不再重建地图 HTML
        if self.map_view is not None and self.map_view.page() is not None:
            import json
            from modules.map.js_bridge import MapJsBridge
            bounds_json = json.dumps([[min(lats), min(lons)], [max(lats), max(lons)]])
            self.logger.info(f"[缩放] 调用 fit_bounds JS: {bounds_json}, zoom={zoom}")
            MapJsBridge.fit_bounds(self.map_view.page(), bounds_json,
                                   center[0], center[1], zoom)
        else:
            self.logger.warning("[缩放] map_view/page 不可用，跳过自动缩放 JS 调用")

    def _on_search_history_my_location(self):
        """搜索历史首行"我的位置"点击：触发定位"""
        self.logger.info("[搜索历史] 点击我的位置，触发定位")
        try:
            self.on_locate_clicked()
        except Exception as e:
            self.logger.error(f"处理我的位置点击出错: {e}")

    def _on_route_panel_locate(self):
        """路线面板"我的位置"入口：触发定位（结果将填入待填输入框）"""
        self.logger.info("[路线面板] 收到定位请求（我的位置）")
        try:
            self.on_locate_clicked()
        except Exception as e:
            self.logger.error(f"处理路线面板定位请求出错: {e}")

    # ── 地图模式 & 路网 ───────────────────────────────────────────────────

    def on_map_mode_toggled(self, checked):
        self.logger.debug(f"[地图] 地图模式切换: {checked}")
        map_mode = 'satellite' if checked else 'roadmap'
        map_config.set_map_mode(map_mode)
        if not checked:
            self.road_overlay_button.hide()
        if self.map_manager is not None:
            self.map_manager.reload_map(keep_view=True, keep_route=True, keep_points=True,
                                        keep_search_results=True, keep_location=True)
            self._sync_road_button_state()

    def _sync_road_button_state(self):
        if self.road_overlay_button is not None:
            show_roads = map_config.get_satellite_show_roads()
            self.road_overlay_button.blockSignals(True)
            self.road_overlay_button.setChecked(show_roads)
            self.road_overlay_button.blockSignals(False)

    def on_road_overlay_toggled(self, checked):
        self.logger.debug(f"[地图] 路网开关切换: {checked}")
        map_config.set_satellite_show_roads(checked)
        if self.map_view is not None:
            def on_js_result(result):
                if result:
                    if not result.get('success'):
                        self.logger.warning(f"[地图-路网切换] 操作失败: {result.get('message')}")
                else:
                    self.logger.error("[地图-路网切换] JavaScript返回空结果")
            MapJsBridge.set_road_overlay(self.map_view.page(), checked, on_js_result)

    def on_map_mode_button_enter(self):
        if self.map_mode_button.isChecked():
            map_button_global = self.map_mode_button.mapToGlobal(self.map_mode_button.rect().topLeft())
            container_global = self.map_container.mapFromGlobal(map_button_global)
            road_x = container_global.x() - self.road_overlay_button.width()
            road_y = container_global.y()
            self.road_overlay_button.move(road_x, road_y)
            self.road_overlay_button.show()
            self.road_overlay_button.raise_()

    def on_map_mode_button_leave(self):
        QTimer.singleShot(200, self.check_hide_road_button)

    def on_road_button_enter(self):
        self.road_overlay_button.show()

    def on_road_button_leave(self):
        QTimer.singleShot(200, self.check_hide_road_button)

    def check_hide_road_button(self):
        if not self.map_mode_button.isChecked():
            self.road_overlay_button.hide()
            return
        cursor_pos = QCursor.pos()
        map_rect = QRect(self.map_mode_button.mapToGlobal(self.map_mode_button.rect().topLeft()),
                         self.map_mode_button.rect().size())
        road_rect = QRect(self.road_overlay_button.mapToGlobal(self.road_overlay_button.rect().topLeft()),
                          self.road_overlay_button.rect().size())
        combined = map_rect.united(road_rect).adjusted(-10, -10, 10, 10)
        if not combined.contains(cursor_pos):
            self.road_overlay_button.hide()

    # ── 设置按钮 ──────────────────────────────────────────────────────────

    def on_map_settings_clicked(self):
        self.logger.info("[设置] 打开地图设置面板")
        if self.log_settings_popup is not None:
            self.log_settings_popup.hide()
        if self.about_popup is not None:
            self.about_popup.hide()
        if self.map_settings_popup is not None:
            if hasattr(self.map_settings_button, 'start_animation'):
                self.map_settings_button.start_animation()
            self.map_settings_popup.show_popup(self.map_settings_button)

    def on_log_settings_clicked(self):
        self.logger.info("[设置] 打开日志设置面板")
        if self.map_settings_popup is not None:
            self.map_settings_popup.hide()
        if self.about_popup is not None:
            self.about_popup.hide()
        if self.log_settings_popup is not None:
            self.log_settings_popup.show_popup(self.log_settings_button)

    def on_about_clicked(self):
        self.logger.info("[设置] 打开关于面板")
        if self.map_settings_popup is not None:
            self.map_settings_popup.hide()
        if self.log_settings_popup is not None:
            self.log_settings_popup.hide()
        if self.about_popup is not None:
            self.about_popup.show_popup(self.about_button)

    def _on_map_config_saved(self):
        self.logger.info("[设置] 地图配置已保存，重新加载地图")
        if hasattr(self.map_settings_button, 'stop_animation'):
            self.map_settings_button.stop_animation()
        map_config._load_config()
        self.service_manager.initialize_services()
        self.map_manager.reload_map(keep_view=True, keep_route=True, keep_points=True,
                                    keep_search_results=True, keep_location=True)
        # 海拔剖面图开关即时生效（开启→显示空占位/实际数据，关闭→隐藏）
        if getattr(self, 'elevation_profile_panel', None) is not None:
            self._show_elevation_profile()

    def _on_map_settings_popup_closed(self):
        if self.logger is not None:
            self.logger.debug("[设置] 地图设置面板已关闭")
        if hasattr(self.map_settings_button, 'stop_animation'):
            self.map_settings_button.stop_animation()

    # ── 旧版按钮触发 ──────────────────────────────────────────────────────

    def on_plan_route_clicked(self):
        transport_mode = self.transport_combo.currentText()
        self.route_manager.plan_route(transport_mode)

    def on_export_gpx_clicked(self):
        self.route_manager.export_gpx()

    def on_search_result_clicked(self, item):
        from PyQt5.QtCore import Qt
        data = item.data(Qt.UserRole)
        self.search_manager.select_search_result(data)

    def on_clear_search_clicked(self):
        self.search_manager.clear_search_results()

    # ── 地图缩放 & 比例尺 ─────────────────────────────────────────────────

    def on_map_zoom_changed(self, zoom_level: int):
        self.logger.info(f"[主应用] 缩放级别变化: {zoom_level}")
        if self.scale_panel is not None:
            self.scale_panel.update_zoom(zoom_level)
        try:
            if self.scale_info_label is not None:
                _ = self.scale_info_label.isVisible()
                scale_text = self._get_scale_text(zoom_level)
                self.scale_info_label.setText(f"缩放级别: {zoom_level}  {scale_text}")
                self.scale_info_label.adjustSize()
        except RuntimeError as e:
            self.logger.warning(f"比例尺标签已被删除: {e}")
        try:
            if self.map_manager is not None:
                self.map_manager.on_map_zoom_changed(zoom_level)
        except Exception as e:
            self.logger.error(f"动态路线渲染出错: {e}")

    def on_map_center_changed(self, lat: float, lon: float):
        """地图中心点变化时的处理方法（用户拖拽/平移地图时触发）"""
        self.logger.debug(f"[主应用] 地图中心变化: ({lat:.6f}, {lon:.6f})")
        try:
            if self.map_manager is not None:
                self.map_manager.on_map_center_changed(lat, lon)
        except Exception as e:
            self.logger.error(f"处理地图中心变化出错: {e}")

    def _get_scale_text(self, zoom_level: int) -> str:
        scale_map = {3:"1:40000000",4:"1:20000000",5:"1:10000000",6:"1:5000000",
                     7:"1:2500000",8:"1:1250000",9:"1:625000",10:"1:300000",
                     11:"1:150000",12:"1:75000",13:"1:40000",14:"1:20000",
                     15:"1:10000",16:"1:5000",17:"1:2500",18:"1:1250",
                     19:"1:625",20:"1:300"}
        return f"比例尺: {scale_map.get(zoom_level, '1:100000')}"

    # ── 定位信号 & 地图加载 ───────────────────────────────────────────────

    def _on_geolocation_success(self, lat: float, lon: float, accuracy: float):
        self.hide_loading()
        self.logger.info(f"[主应用] 收到浏览器定位成功信号: {lat}, {lon}, 精度: {accuracy}m")
        if self.location_manager is not None:
            self.location_manager.handle_browser_location_success(lat, lon, accuracy)

    def _on_geolocation_error(self, error_msg: str):
        self.hide_loading()
        self.logger.warning(f"浏览器定位失败: {error_msg}")
        self.location_manager.handle_browser_location_error(error_msg)

    def _on_map_loaded(self):
        # 挂起的海拔剖面（历史路线点击）：页面加载完成后显示——路线先可见、折线图随后
        pending = getattr(self, '_pending_history_elevation_show', None)
        if pending is not None:
            self._pending_history_elevation_show = None
            try:
                self._show_history_elevation_profile(pending[0], pending[1])
            except Exception as e:
                self.logger.error(f"[主应用] 挂起的海拔剖面显示失败: {e}")
        # 页面重建后恢复路线管理库渲染路线（HTML 不含库路线，重新 JS 注入）
        if getattr(self, '_library_rendered_ids', None):
            # 新页面无任何 polyline，重置上一状态强制全量注入
            self._prev_library_rendered_ids = None
            self._inject_library_routes()
        self.hide_loading()
        self.logger.debug("[主应用] 地图加载完成，停止加载动画")

    # ── 右键菜单触发 ──────────────────────────────────────────────────────

    def _on_map_right_click(self, lat: float, lon: float):
        self.logger.info(f"[地图右键] 收到右键点击信号: {lat}, {lon}")
        # [DEBUG漂移] 记录原始坐标和地图源信息，用于定位漂移问题
        self.logger.info(f"[DEBUG漂移] 1_Leaflet原始坐标=({lat:.10f}, {lon:.10f})")
        from modules.geolocation.coordinate_transform import CoordinateTransform as _CT
        _ms = map_config.get_map_source()
        _cs = _CT.coord_system_for_map_source(_ms)
        self.logger.info(f"[DEBUG漂移] 1b_当前地图源={_ms}, 推断坐标系={_cs}")
        location_info = {'success': False, 'name': f'位置 ({lat:.6f}, {lon:.6f})',
                         'lat': lat, 'lon': lon, 'type': '', 'level': None}
        self._show_context_menu(location_info)

    def _on_favorite_delete_requested(self, fav_id: int):
        """收藏点弹窗内点击删除按钮时的处理方法"""
        self.logger.info(f"[收藏点] 收到删除收藏请求: id={fav_id}")
        try:
            if self.map_manager is not None:
                self.map_manager.delete_favorite(fav_id)
        except Exception as e:
            self.logger.error(f"处理删除收藏请求出错: {e}")

    def _on_location_marker_hidden(self):
        """定位 popup 内点击隐藏标识按钮时的处理方法"""
        self.logger.info("[定位标识] 收到隐藏标识请求")
        try:
            if self.map_manager is not None:
                self.map_manager.hide_location_marker()
        except Exception as e:
            self.logger.error(f"处理隐藏定位标识请求出错: {e}")

    def _on_map_middle_double_click(self):
        """地图中键双击：触发自动缩放（效果与工具栏按钮完全一致）"""
        self.logger.info("[缩放] 收到中键双击请求，触发自动缩放")
        try:
            self.on_zoom_fit_clicked()
        except Exception as e:
            self.logger.error(f"处理中键双击缩放出错: {e}")

    # ── 收藏夹弹窗 ──────────────────────────────────────────────────────

    def _close_favorites_panel(self):
        """互斥：关闭收藏夹弹窗（若可见），供路线面板等展开入口调用

        收藏夹弹窗 hide 时经 hideEvent → closed 信号自动刷新工具栏按钮态，
        调用方无需额外恢复操作。
        """
        favorites_popup = getattr(self, 'favorites_popup', None)
        if favorites_popup is not None and favorites_popup.isVisible():
            favorites_popup.hide()

    def on_favorites_button_clicked(self):
        """工具栏收藏夹按钮：展开/收起收藏夹列表"""
        self.logger.info("[收藏夹] 收藏夹按钮点击")

        if not hasattr(self, 'favorites_popup') or self.favorites_popup is None:
            from ui.popups.favorites_list_popup import FavoritesListPopup
            self.favorites_popup = FavoritesListPopup(
                self, map_manager=getattr(self, 'map_manager', None))
            self.favorites_popup.favorite_selected.connect(self._on_favorites_selected)
            self.favorites_popup.import_clicked.connect(self._on_favorites_import)
            self.favorites_popup.export_clicked.connect(self._on_favorites_export)
            self.favorites_popup.select_all_clicked.connect(
                self._on_favorites_select_all)
            self.favorites_popup.delete_clicked.connect(self._on_favorites_delete)
            # 弹窗关闭（含失去焦点自动关闭）时统一刷新工具栏按钮态
            self.favorites_popup.closed.connect(self._refresh_toolbar_buttons)

        if self.favorites_popup.isVisible():
            self.favorites_popup.hide()
            self._refresh_toolbar_buttons()
            return

        # 互斥：先关闭路线规划面板（若展开），再展开收藏夹列表，避免两面板重叠显示
        self._close_route_plan_panel()

        self.favorites_popup.refresh()
        # 先 show 再定位：update_search_popups_position 仅处理可见弹窗
        # （isVisible 过滤），show 前调用会跳过导致弹窗落在残留位置
        self.favorites_popup.show()
        self.favorites_popup.raise_()
        # 位置/宽度/高度与搜索历史列表一致（锚定搜索容器，宽度=整个工具条）
        from ui.popups.popup_positioner import PopupPositioner
        PopupPositioner.update_search_popups_position(
            None, None, getattr(self, 'search_container', None),
            self.logger, favorites_popup=self.favorites_popup)
        # 弹窗展开后统一刷新按钮态（第 3 按钮切换为关闭按钮，保持 3 按钮稳定）
        self._refresh_toolbar_buttons()

    def on_route_manager_button_clicked(self):
        """工具栏路线管理按钮：展开/收起路线管理列表"""
        self.logger.info("[路线管理] 路线管理按钮点击")

        if not hasattr(self, 'route_manager_popup') or self.route_manager_popup is None:
            from ui.popups.route_manager_popup import RouteManagerPopup
            self.route_manager_popup = RouteManagerPopup(self)
            self.route_manager_popup.import_clicked.connect(self._on_route_manager_import)
            self.route_manager_popup.export_clicked.connect(self._on_route_manager_export)
            self.route_manager_popup.select_all_clicked.connect(
                self._on_route_manager_select_all)
            self.route_manager_popup.delete_clicked.connect(
                self._on_route_manager_delete)
            self.route_manager_popup.render_clicked.connect(
                self._on_route_manager_render_clicked)
            self.route_manager_popup.item_render_clicked.connect(
                self._on_route_manager_item_render)
            self.route_manager_popup.elevation_fetch_clicked.connect(
                self._fetch_route_library_elevation)
            self.route_manager_popup.closed.connect(self._refresh_toolbar_buttons)

        if self.route_manager_popup.isVisible():
            self.route_manager_popup.hide()
            self._refresh_toolbar_buttons()
            return

        # 互斥：先关闭路线规划面板/收藏夹列表（若展开），避免面板重叠显示
        self._close_route_plan_panel()
        if hasattr(self, 'favorites_popup') and self.favorites_popup is not None:
            self.favorites_popup.hide()

        self._refresh_route_manager_popup()
        self.route_manager_popup.show()
        self.route_manager_popup.raise_()
        # 刷新各条目渲染按钮高亮（按当前渲染集合）
        self.route_manager_popup.set_rendered_ids(
            getattr(self, '_library_rendered_ids', set()))
        # 位置/宽度/高度与搜索历史列表一致（锚定搜索容器，宽度=整个工具条）
        from ui.popups.popup_positioner import PopupPositioner
        PopupPositioner.update_search_popups_position(
            None, None, getattr(self, 'search_container', None),
            self.logger, favorites_popup=self.route_manager_popup)
        self._refresh_toolbar_buttons()

    def _refresh_route_manager_popup(self):
        """从路线库存储重新加载路线管理列表（并按条目数重算面板高度）"""
        try:
            from modules.routing.storage.route_library_storage import RouteLibraryStorage
            storage = getattr(self, 'route_library_storage', None)
            if storage is None:
                storage = self.route_library_storage = RouteLibraryStorage()
            self.route_manager_popup.refresh(storage.get_all())
            # 删除/导入/清空后条目数变化：若面板可见则复用定位公式重算高度
            # （min(条目高度和, 主窗口底部边界)，避免高度残留旧值）
            if self.route_manager_popup.isVisible():
                from ui.popups.popup_positioner import PopupPositioner
                PopupPositioner.update_search_popups_position(
                    None, None, getattr(self, 'search_container', None),
                    self.logger, route_manager_popup=self.route_manager_popup)
        except Exception as e:
            self.logger.error(f"[路线管理] 刷新列表失败: {e}")

    def _on_route_manager_render_clicked(self, record: dict):
        """条目渲染按钮：单条 toggle 渲染（再点隐藏），全量重建地图"""
        rid = record.get('id')
        if not rid:
            return
        rendered_ids = set(getattr(self, '_library_rendered_ids', set()))
        self._apply_route_render(record, rid not in rendered_ids)

    def _on_route_manager_item_render(self, record: dict):
        """条目点击：仅渲染该路线（已渲染时无操作，取消渲染需点击渲染按钮）"""
        rid = record.get('id')
        if not rid:
            return
        if rid in getattr(self, '_library_rendered_ids', set()):
            return  # 已渲染：点击不取消
        self._apply_route_render(record, True)

    def _apply_route_render(self, record: dict, render: bool):
        """设置单条路线的渲染状态并全量重建（render=True 渲染 / False 取消）

        同步渲染集合 → map_manager 渲染记录 → 重建地图 → 海拔剖面联动 → 按钮高亮刷新。
        """
        try:
            rid = record.get('id')
            if not rid:
                return
            rendered_ids = set(getattr(self, '_library_rendered_ids', set()))
            if render:
                rendered_ids.add(rid)
            else:
                rendered_ids.discard(rid)
            self._library_rendered_ids = rendered_ids
            # 同步渲染记录到 map_manager（全量重建时叠加）
            storage = getattr(self, 'route_library_storage', None)
            if storage is None:
                from modules.routing.storage.route_library_storage import RouteLibraryStorage
                storage = self.route_library_storage = RouteLibraryStorage()
            self.map_manager.set_library_rendered_records(
                [r for r in storage.get_all() if r.get('id') in rendered_ids])
            # 增量注入库渲染路线（JS LayerGroup，不重建页面避免卡顿）
            self._inject_library_routes()
            # 渲染/取消后按当前渲染的所有路线缩放：
            # 开启多路线渲染 → 按渲染集合全部路线缩放；关闭 → 渲染时按该条缩放、
            # 取消时不缩放
            if render or map_config.get_multi_route_render():
                self._fit_library_routes()
            # 海拔剖面图联动：渲染 → 显示其海拔剖面（有海拔直接显示，无则空占位）；
            # 取消渲染 → 恢复当前选中路线的剖面状态
            if render:
                self._show_history_elevation_profile(
                    record.get('route_points', []), record.get('duration') or 0)
            else:
                self._show_elevation_profile()
            self.logger.info(f"[路线管理] 渲染切换: {len(rendered_ids)} 条")
            # 刷新各条目渲染按钮高亮
            popup = getattr(self, 'route_manager_popup', None)
            if popup is not None:
                popup.set_rendered_ids(rendered_ids)
        except Exception as e:
            self.logger.error(f"[路线管理] 渲染切换失败: {e}")

    def _inject_library_routes(self):
        """按 id 增量更新渲染集合的库路线地图图层（GCJ-02，不重建页面）

        与上一状态 diff 出新增/删除路线，只向 JS 传变化量：
        首次调用（页面刚重建，prev=None）→ 全量新增；后续切换仅增删变化的路线。
        """
        try:
            if self.map_view is None or self.map_view.page() is None:
                return
            storage = getattr(self, 'route_library_storage', None)
            if storage is None:
                return
            from modules.geolocation.coordinate_transform import CoordinateTransform as _CT
            from modules.map.js_bridge import MapJsBridge
            import json
            rendered_ids = getattr(self, '_library_rendered_ids', set())
            prev_ids = getattr(self, '_prev_library_rendered_ids', None)

            def _gcj(c):
                """WGS-84 → GCJ-02（无坐标返回 None）"""
                if not c or len(c) < 2:
                    return None
                lat, lon = _CT.convert(c[0], c[1], 'WGS-84', 'GCJ-02')
                return [lat, lon]

            to_add = []
            for rec in storage.get_all():
                if rec.get('id') not in rendered_ids:
                    continue
                if prev_ids is not None and rec.get('id') in prev_ids:
                    continue  # 已在页面，无需重复绘制
                coords = []
                for p in (rec.get('route_points') or []):
                    if p is None:
                        continue
                    gcj_lat, gcj_lon = _CT.convert(p[0], p[1], 'WGS-84', 'GCJ-02')
                    coords.append([gcj_lat, gcj_lon])
                if len(coords) >= 2:
                    # 起终点/途径点小圆点：优先取显式坐标，缺失时回退路线首尾点
                    start = _gcj(rec.get('start_coords')) or coords[0]
                    end = _gcj(rec.get('end_coords')) or coords[-1]
                    waypoints = []
                    for w in (rec.get('waypoint_coords') or []):
                        wc = _gcj(w)
                        if wc:
                            waypoints.append(wc)
                    to_add.append({
                        'id': rec.get('id'),
                        'coords': coords,
                        'color': self.map_manager.ROUTE_COLORS[
                            (rec.get('color_index') or 0)
                            % len(self.map_manager.ROUTE_COLORS)],
                        'start': start,
                        'end': end,
                        'waypoints': waypoints,
                    })
            to_remove = sorted(prev_ids - rendered_ids) if prev_ids is not None else []
            payload = {'add': to_add, 'remove': to_remove}
            MapJsBridge.update_library_routes(self.map_view.page(), json.dumps(payload))
            self._prev_library_rendered_ids = set(rendered_ids)
        except Exception as e:
            self.logger.error(f"[路线管理] 库路线注入失败: {e}")

    def _fit_library_routes(self):
        """按当前渲染集合的全部路线缩放地图（fitBounds，GCJ-02）

        渲染/取消渲染后调用：始终以渲染集合整体为边界，而非单条路线。
        无渲染路线时直接返回，不打断当前视图。
        """
        try:
            if self.map_view is None or self.map_view.page() is None:
                return
            storage = getattr(self, 'route_library_storage', None)
            if storage is None:
                return
            from modules.geolocation.coordinate_transform import CoordinateTransform as _CT
            rendered_ids = getattr(self, '_library_rendered_ids', set())
            pts = []
            for rec in storage.get_all():
                if rec.get('id') not in rendered_ids:
                    continue
                for p in (rec.get('route_points') or []):
                    if p is not None:
                        pts.append(p)
            if not pts:
                return
            # WGS-84 → GCJ-02（与地图渲染层一致）；route_points 可能带海拔
            # （3 元素 [lat, lon, ele]），显式取前两个坐标，避免解包异常
            gcj = [_CT.convert(p[0], p[1], 'WGS-84', 'GCJ-02') for p in pts]
            self._fit_gcj_points(gcj, f"[路线管理] 按渲染集合缩放: {len(rendered_ids)} 条")
        except Exception as e:
            self.logger.error(f"[路线管理] 渲染集合缩放失败: {e}")

    def _fit_gcj_points(self, gcj_points: list, log_tag: str = ""):
        """对 GCJ-02 坐标点集执行强制缩放（fitBounds，单点退化 setView）

        复用自动缩放 JS，force=True 跳过"已包含即跳过"判断，始终精确适配。
        """
        try:
            if not gcj_points or self.map_view is None or self.map_view.page() is None:
                return
            from modules.map.js_bridge import MapJsBridge
            import json
            lats = [p[0] for p in gcj_points]
            lons = [p[1] for p in gcj_points]
            bounds_json = json.dumps([[min(lats), min(lons)], [max(lats), max(lons)]])
            center = [(min(lats) + max(lats)) / 2, (min(lons) + max(lons)) / 2]
            diagonal = math.sqrt((max(lats) - min(lats)) ** 2 + (max(lons) - min(lons)) ** 2)
            zoom = 15 if diagonal == 0 else max(2, min(18, int(10 - math.log(diagonal, 2))))
            MapJsBridge.fit_bounds(self.map_view.page(), bounds_json,
                                   center[0], center[1], zoom, force=True)
            if log_tag:
                self.logger.info(f"{log_tag}, zoom={zoom}")
        except Exception as e:
            self.logger.error(f"[缩放] 强制缩放失败: {e}")

    def _inject_planned_route(self):
        """将当前规划路线增量渲染到地图（路线线 + 起终点/途径点标记 + 缩放）

        历史条目/路线规划切换复用：页面其他图层（收藏点/当前位置/库渲染路线）
        保持不动，仅更新专用规划路线图层，避免全量重建 HTML 卡顿。
        """
        try:
            if self.map_view is None or self.map_view.page() is None:
                return
            from modules.geolocation.coordinate_transform import CoordinateTransform as _CT
            from modules.map.js_bridge import MapJsBridge
            import json
            from services.config.map_config import map_config
            is_gcj = (map_config.get_map_source() == 'gaode')

            # 路线线：data_manager.route_points 为 WGS-84，高德源转 GCJ-02（保留分段结构）
            route_segments = []
            current = []
            for p in (getattr(self.data_manager, 'route_points', None) or []):
                if p is None:
                    if len(current) >= 2:
                        route_segments.append(current)
                    current = []
                    continue
                if is_gcj:
                    lat, lon = _CT.convert(p[0], p[1], 'WGS-84', 'GCJ-02')
                else:
                    lat, lon = p[0], p[1]
                current.append([lat, lon])
            if len(current) >= 2:
                route_segments.append(current)

            # 起终点/途径点标记：坐标已按当前地图坐标系存储（gaode=GCJ-02，其他=WGS-84）
            dm = getattr(self, 'data_manager', None)
            markers = []
            if dm is not None:
                start = getattr(dm, 'start_coords', None)
                if start and len(start) >= 2:
                    markers.append({'lat': start[0], 'lng': start[1], 'type': 'start',
                                    'label': getattr(dm, 'start_name', None) or '起'})
                for i, wpt in enumerate(getattr(dm, 'waypoints_coords', None) or []):
                    if wpt and len(wpt) >= 2:
                        markers.append({'lat': wpt[0], 'lng': wpt[1], 'type': 'waypoint',
                                        'number': i + 1})
                end = getattr(dm, 'end_coords', None)
                if end and len(end) >= 2:
                    markers.append({'lat': end[0], 'lng': end[1], 'type': 'end',
                                    'label': getattr(dm, 'end_name', None) or '终'})

            MapJsBridge.update_planned_route(
                self.map_view.page(),
                json.dumps(route_segments),
                json.dumps(markers))

            # 缩放：以路线线 + 标记整体为边界（强制适配）
            all_pts = [p for seg in route_segments for p in seg]
            all_pts += [[m['lat'], m['lng']] for m in markers]
            self._fit_gcj_points(all_pts, "[路线面板] 规划路线缩放")
        except Exception as e:
            self.logger.error(f"[路线面板] 规划路线增量渲染失败: {e}")

    def _fetch_route_library_elevation(self, record: dict):
        """获取单条库路线的海拔（复用历史海拔链路：task_id 关联回写）
        已有海拔时弹窗确认是否重新获取（覆盖原数据，与历史列表一致）。"""
        try:
            route_points = record.get('route_points', [])
            duration = record.get('duration') or 0
            has_elevation = any(
                p is not None and len(p) >= 3 and p[2] is not None
                for p in (route_points or []))
            if has_elevation:
                from ui.dialogs.custom_message_dialog import CustomMessageDialog
                dialog = CustomMessageDialog(
                    self, title="重新获取海拔",
                    message="该路线已获取过海拔数据。\n是否重新获取？\n重新获取将覆盖原有的海拔数据。",
                    show_cancel=True, ok_text="重新获取")
                if not dialog.exec_():
                    return
            task_id = self.route_manager._fetch_elevation_data_async(
                [{'route_points': list(route_points), 'duration': duration}])
            if task_id:
                pending = getattr(self, '_pending_library_elevation', None)
                if pending is None:
                    pending = self._pending_library_elevation = {}
                pending[task_id] = record
                self.show_loading()
        except Exception as e:
            self.logger.error(f"[路线管理] 海拔获取失败: {e}")

    def _on_route_manager_import(self):
        """路线管理导入：多选 GPX 文件 → 逐文件解析 → 确认面板 → 入库"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            file_paths, _ = QFileDialog.getOpenFileNames(
                self, "选择 GPX 文件（可多选）", "", "GPX文件 (*.gpx);;所有文件 (*)")
            if not file_paths:
                return

            from modules.gpx.gpx_import import GpxImportParser
            from ui.popups.gpx_import_confirm_popup import GpxImportConfirmPopup
            storage = getattr(self, 'route_library_storage', None)
            if storage is None:
                from modules.routing.storage.route_library_storage import RouteLibraryStorage
                storage = self.route_library_storage = RouteLibraryStorage()

            imported = 0
            for path in file_paths:
                try:
                    parsed = GpxImportParser.parse(path)
                except Exception as e:
                    self._show_warning("导入失败", f"{path}\n解析失败: {e}")
                    continue
                # 解析成功 → 信息确认面板（用户手动确认后入库）
                import os
                confirm = GpxImportConfirmPopup(self, parsed, os.path.basename(path))
                if not confirm.exec_():
                    continue
                storage.add_record(
                    start=parsed['start'], end=parsed['end'],
                    route_points=parsed['route_points'],
                    distance=parsed['distance'], duration=parsed['duration'],
                    color_index=len(storage.get_all()))
                imported += 1

            if imported > 0:
                self._refresh_route_manager_popup()
                self._show_info("导入完成", f"成功导入 {imported} 条路线")
        except Exception as e:
            self.logger.error(f"[路线管理] 导入失败: {e}")
            self._show_warning("导入失败", f"导入出错: {e}")

    def _on_route_manager_export(self):
        """路线管理导出：单条 → 保存对话框；多条（多选）→ 选目录逐条导出独立 GPX"""
        try:
            if getattr(self, 'route_manager_popup', None) is None:
                return
            records = self.route_manager_popup.get_export_records()
            if not records:
                self._show_warning("导出", "请先选择要导出的路线（点击条目，或多选模式勾选多条）")
                return

            from PyQt5.QtWidgets import QFileDialog
            if len(records) == 1:
                self._export_single_record(records[0])
                return

            # 多条：选择保存目录，逐条导出独立 GPX 文件（自动命名 起点_终点.gpx）
            export_dir = QFileDialog.getExistingDirectory(self, "选择保存目录")
            if not export_dir:
                return
            self.show_loading()
            ok_count = 0
            for rec in records:
                if self._export_record_to_dir(rec, export_dir):
                    ok_count += 1
            self.hide_loading()
            self._show_info("导出完成", f"已导出 {ok_count}/{len(records)} 条路线到:\n{export_dir}")
        except Exception as e:
            self.logger.error(f"[路线管理] 导出失败: {e}")
            self.hide_loading()
            self._show_warning("导出失败", f"导出出错: {e}")

    def _export_single_record(self, record: dict):
        """单条路线导出（复用 GPX 导出弹窗/线程链路）"""
        from PyQt5.QtCore import QDateTime
        route_data = {
            'route_points': record.get('route_points', []),
            'start_name': record.get('start', '起点'),
            'end_name': record.get('end', '终点'),
            'mode': record.get('mode', 'driving'),
            'waypoints': record.get('waypoints', []),
            'distance': record.get('distance'),
            'duration': record.get('duration'),
            'start_coords': record.get('start_coords'),
            'end_coords': record.get('end_coords'),
            'waypoint_coords': record.get('waypoint_coords', []),
            'start_coord_system': 'WGS-84',
            'end_coord_system': 'WGS-84',
        }
        self._export_gpx_file(route_data, QDateTime.currentDateTime(), export_elevation=False)

    def _export_record_to_dir(self, record: dict, export_dir: str) -> bool:
        """将单条路线导出到指定目录（自动命名，同步执行）"""
        try:
            import os
            from modules.gpx import GpxExportService
            from PyQt5.QtCore import QDateTime
            start = record.get('start', '起点')
            end = record.get('end', '终点')
            import re
            safe_start = re.sub(r'[\\/:*?"<>|]', '', start)
            safe_end = re.sub(r'[\\/:*?"<>|]', '', end)
            file_path = os.path.join(
                export_dir, f"{safe_start}_{safe_end}.gpx")
            # 重名时追加序号
            counter = 1
            while os.path.exists(file_path):
                file_path = os.path.join(
                    export_dir, f"{safe_start}_{safe_end}_{counter}.gpx")
                counter += 1
            service = GpxExportService(logger=lambda *a, **k: None)
            return service.export_to_gpx(
                route_points=record.get('route_points', []),
                start_datetime=QDateTime.currentDateTime(),
                file_path=file_path,
                start_name=start, end_name=end,
                export_elevation=False,
                total_duration_seconds=record.get('duration'),
                total_distance_meters=record.get('distance'))
        except Exception as e:
            self.logger.error(f"[路线管理] 导出 {record.get('start')} 失败: {e}")
            return False

    def _on_route_manager_select_all(self):
        """路线管理全选按钮：toggle 全选/取消全选（按钮高亮随选中状态）"""
        popup = getattr(self, 'route_manager_popup', None)
        if popup is not None:
            popup.toggle_select_all()

    def _on_route_manager_delete(self):
        """路线管理删除：删除勾选的条目（以勾选结果为准）"""
        try:
            popup = getattr(self, 'route_manager_popup', None)
            if popup is None:
                return
            records = popup.get_checked_records()
            if not records:
                self._show_warning("提示", "请先勾选要删除的路线（点击条目右侧 ☐ 勾选）")
                return
            storage = getattr(self, 'route_library_storage', None)
            if storage is None:
                from modules.routing.storage.route_library_storage import RouteLibraryStorage
                storage = self.route_library_storage = RouteLibraryStorage()
            deleted_ids = set()
            for rec in records:
                rid = rec.get('id')
                if rid and storage.remove(rid):
                    deleted_ids.add(rid)
            # 渲染集合中移除被删条目（地图上的库渲染层同步）
            if deleted_ids:
                rendered_ids = set(getattr(self, '_library_rendered_ids', set()))
                rendered_ids -= deleted_ids
                self._library_rendered_ids = rendered_ids
                self.map_manager.set_library_rendered_records(
                    [r for r in storage.get_all() if r.get('id') in rendered_ids])
            self._refresh_route_manager_popup()
            # 同步历史列表收藏按钮状态（被删路线取消收藏）
            self._sync_history_favorite_status()
            self._show_info("删除完成", f"已删除 {len(deleted_ids)} 条路线")
        except Exception as e:
            self.logger.error(f"[路线管理] 删除失败: {e}")

    def _on_favorites_selected(self, fav: dict):
        """收藏夹条目点击：仅将地图缩放定位到该收藏点（不添加额外标记）

        收藏点金星标识由收藏图层渲染（show_map 全量重建自带），
        此处只移动地图中心，避免预览高亮标记与金星标识叠加。
        """
        name = fav.get('name', '收藏点')
        self.logger.info(f"[收藏夹] 选择收藏点: {name}")
        try:
            if self.map_manager is not None:
                # POI 级缩放（16），坐标按 WGS-84 处理（收藏统一存储坐标系）
                self.map_manager.show_map(
                    [fav.get('lat', 0), fav.get('lon', 0)], zoom=16,
                    title=name, coord_system='WGS-84')
        except Exception as e:
            self.logger.error(f"处理收藏点选择出错: {e}")

    def _on_favorites_select_all(self):
        """收藏夹全选按钮：toggle 全选/取消全选（按钮高亮随选中状态）"""
        popup = getattr(self, 'favorites_popup', None)
        if popup is not None:
            popup.toggle_select_all()

    def _on_favorites_delete(self):
        """收藏夹删除：删除勾选的收藏（列表与地图同步）"""
        popup = getattr(self, 'favorites_popup', None)
        if popup is None:
            return
        records = popup.get_checked_records()
        if not records:
            self._show_warning("提示", "请先勾选要删除的收藏（点击条目右侧 ☐ 勾选）")
            return
        deleted = 0
        for fav in records:
            fav_id = fav.get('id')
            if fav_id is not None and self.map_manager is not None:
                if self.map_manager.delete_favorite(fav_id):
                    deleted += 1
        self.logger.info(f"[收藏夹] 删除 {deleted} 个收藏")
        popup.refresh()
        if deleted:
            self._show_info("删除完成", f"已删除 {deleted} 个收藏")

    def _on_favorites_import(self):
        """收藏夹导入：选择 JSON 文件合并导入"""
        self.logger.info("[收藏夹] 导入收藏")
        try:
            from PyQt5.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getOpenFileName(
                self, "导入收藏", "", "收藏文件 (*.json)")
            if not file_path:
                return

            storage = self.map_manager.favorites_storage
            imported, skipped, error = storage.import_from_file(file_path)
            if error:
                self._show_warning("导入失败", error)
                return

            self.map_manager.reload_map()
            if hasattr(self, 'favorites_popup') and self.favorites_popup is not None:
                self.favorites_popup.refresh()
            self._show_info("导入完成", f"新增 {imported} 个收藏，跳过 {skipped} 个")
        except Exception as e:
            self.logger.error(f"处理收藏导入出错: {e}")

    def _on_favorites_export(self):
        """收藏夹导出：收藏列表写入 JSON 文件"""
        self.logger.info("[收藏夹] 导出收藏")
        try:
            from PyQt5.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出收藏", "FavoritesList.json", "收藏文件 (*.json)")
            if not file_path:
                return

            storage = self.map_manager.favorites_storage
            if storage.export_to_file(file_path):
                self._show_info("导出完成", f"已导出 {len(storage.get_all())} 个收藏")
            else:
                self._show_warning("导出失败", "写入文件失败，请查看日志")
        except Exception as e:
            self.logger.error(f"处理收藏导出出错: {e}")


    def _on_location_favorite_requested(self, lat: float, lon: float, name: str):
        """定位 popup 内点击收藏按钮时的处理方法（切换收藏，成功不弹窗）

        收藏信息与右键"收藏此位置"保持一致：逆地理编码获取名称/地址
        （高德源下定位坐标 WGS-84 先转 GCJ-02 再查询），失败降级为面板标题文本。
        """
        self.logger.info(f"[定位标识] 收到收藏当前位置请求: ({lat}, {lon}) {name}")
        try:
            if self.map_manager is None:
                return

            # 逆地理编码：复用右键收藏链路（_resolve_map_click_address 期望地图源坐标系）
            from services.config.map_config import map_config
            from modules.geolocation import CoordinateTransform

            query_lat, query_lon = lat, lon
            if map_config.get_map_source() == 'gaode':
                # 定位坐标 WGS-84 → 高德 GCJ-02（逆地理编码 API 期望 GCJ-02 输入）
                query_lat, query_lon = CoordinateTransform.convert(lat, lon, 'WGS-84', 'GCJ-02')

            try:
                geo = self._resolve_map_click_address(query_lat, query_lon)
                fav_name = geo['name']
                fav_address = geo.get('address', '')
                fav_type = geo.get('type_info', '') or ''
            except Exception:
                # 降级：面板标题文本（如"我的位置"），地址为空
                self.logger.warning("[定位标识] 逆地理编码失败，使用面板标题作为收藏名称")
                fav_name, fav_address, fav_type = name, '', ''

            action = self.map_manager.toggle_favorite(
                lat, lon, fav_name, address=fav_address, coord_system='WGS-84',
                type_text=fav_type)
            if action == 'failed':
                self.logger.error(f"[定位标识] 收藏当前位置失败")
        except Exception as e:
            self.logger.error(f"处理收藏当前位置请求出错: {e}")

    def _show_context_menu(self, location_info: dict):
        self.logger.info(f"[DEBUG漂移] 2_show_menu传入坐标=({location_info['lat']:.10f}, {location_info['lon']:.10f})")
        self.logger.debug(f"[地图右键] 显示右键菜单: {location_info}")
        self._context_menu_location_info = location_info
        cursor_pos = QCursor.pos()
        self._context_menu_click_pos = cursor_pos
        self.map_context_menu.show_menu(cursor_pos, location_info['lat'], location_info['lon'])

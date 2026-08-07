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
        lats = [p[0] for p in all_points]
        lons = [p[1] for p in all_points]
        center = [(min(lats)+max(lats))/2, (min(lons)+max(lons))/2]
        diagonal = math.sqrt((max(lats)-min(lats))**2 + (max(lons)-min(lons))**2)
        zoom = 15 if diagonal == 0 else max(2, min(18, int(10 - math.log(diagonal, 2))))
        self.logger.info(f"[缩放] 计算完成：中心点={center}，缩放级别={zoom}")
        if self.map_manager is not None:
            # 多点场景传入 fit_points：由 Leaflet fitBounds 精确适配视野（含 padding），
            # 避免手算缩放级别导致元素出视野或贴边；单点保持手算 zoom
            self.map_manager.show_map(
                center=center, zoom=zoom, title="地图",
                fit_points=all_points if len(all_points) > 1 else None)

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
            self.favorites_popup.favorite_delete_requested.connect(self._on_favorites_delete)
            self.favorites_popup.import_clicked.connect(self._on_favorites_import)
            self.favorites_popup.export_clicked.connect(self._on_favorites_export)
            self.favorites_popup.clear_clicked.connect(self._on_favorites_clear)
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

    def _on_favorites_delete(self, fav_id: int):
        """收藏夹金星按钮：删除收藏（列表与地图同步）"""
        self.logger.info(f"[收藏夹] 删除收藏: id={fav_id}")
        try:
            if self.map_manager is not None:
                self.map_manager.delete_favorite(fav_id)
            if hasattr(self, 'favorites_popup') and self.favorites_popup is not None:
                self.favorites_popup.refresh()
        except Exception as e:
            self.logger.error(f"处理收藏删除出错: {e}")

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

    def _on_favorites_clear(self):
        """收藏夹清空（二次确认后执行，确认面板与项目其他弹窗风格一致）"""
        self.logger.info("[收藏夹] 清空收藏")
        try:
            from PyQt5.QtWidgets import QDialog
            from ui.dialogs.custom_message_dialog import CustomMessageDialog
            reply = CustomMessageDialog(
                self, title="确认清空", message="确定要清空全部收藏吗？此操作不可恢复。",
                show_cancel=True, ok_text="清空", cancel_text="取消").exec_()
            if reply != QDialog.Accepted:
                return

            self.map_manager.favorites_storage.clear_all()
            self.map_manager.reload_map()
            if hasattr(self, 'favorites_popup') and self.favorites_popup is not None:
                self.favorites_popup.refresh()
        except Exception as e:
            self.logger.error(f"处理收藏清空出错: {e}")

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

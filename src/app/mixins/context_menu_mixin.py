"""ContextMenuMixin — 右键菜单及地图点击相关处理方法"""
from PyQt5.QtCore import Qt
from modules.map.map_renderer import MapRenderer
from services.config.map_config import map_config


class ContextMenuMixin:
    """旧版与新版右键菜单处理，以及公共辅助方法。"""

    # ------------------------------------------------------------------ #
    #  旧版右键菜单处理（兼容旧信号）                                      #
    # ------------------------------------------------------------------ #

    def _on_context_menu_set_start(self, name: str, lat: float, lon: float):
        """右键菜单：设为起点"""
        self.logger.info(f"[右键菜单] 设为起点: {name} ({lat}, {lon})")

        location_info = getattr(self, '_context_menu_location_info', {})
        level = location_info.get('level', None)
        type_info = location_info.get('type', None)

        self.data_manager.set_start_location((lat, lon), name)

        data = (name, lat, lon, None, None, None)
        self._update_start_from_search(name, data)

        self.search_manager.clear_search_results()

        all_coords = self.map_manager._get_all_selected_coords()
        if len(all_coords) >= 2:
            self.map_manager.update_map_preview(auto_fit=True)
        else:
            zoom_level = MapRenderer.get_zoom_by_level(level, type_info)
            self.logger.info(f"[右键菜单] 单点缩放: level={level}, type={type_info}, zoom={zoom_level}")
            self.map_manager.update_map_preview_simple((lat, lon), zoom_level=zoom_level)

    def _on_context_menu_add_waypoint(self, name: str, lat: float, lon: float):
        """右键菜单：添加途径点"""
        self.logger.info(f"[右键菜单] 添加途径点: {name} ({lat}, {lon})")

        location_info = getattr(self, '_context_menu_location_info', {})
        level = location_info.get('level', None)
        type_info = location_info.get('type', None)

        self.data_manager.add_waypoint((lat, lon), name)

        data = (name, lat, lon, None, None, None)
        self._add_waypoint_to_list(name, data, None)

        self.search_manager.clear_search_results()

        all_coords = self.map_manager._get_all_selected_coords()
        if len(all_coords) >= 2:
            self.map_manager.update_map_preview(auto_fit=True)
        else:
            zoom_level = MapRenderer.get_zoom_by_level(level, type_info)
            self.logger.info(f"[右键菜单] 单点缩放: level={level}, type={type_info}, zoom={zoom_level}")
            self.map_manager.update_map_preview_simple((lat, lon), zoom_level=zoom_level)

    def _on_context_menu_set_end(self, name: str, lat: float, lon: float):
        """右键菜单：设为终点"""
        self.logger.info(f"[右键菜单] 设为终点: {name} ({lat}, {lon})")

        location_info = getattr(self, '_context_menu_location_info', {})
        level = location_info.get('level', None)
        type_info = location_info.get('type', None)

        self.data_manager.set_end_location((lat, lon), name)

        data = (name, lat, lon, None, None, None)
        self._update_end_from_search(name, data)

        self.search_manager.clear_search_results()

        all_coords = self.map_manager._get_all_selected_coords()
        if len(all_coords) >= 2:
            self.map_manager.update_map_preview(auto_fit=True)
        else:
            zoom_level = MapRenderer.get_zoom_by_level(level, type_info)
            self.logger.info(f"[右键菜单] 单点缩放: level={level}, type={type_info}, zoom={zoom_level}")
            self.map_manager.update_map_preview_simple((lat, lon), zoom_level=zoom_level)

    # ------------------------------------------------------------------ #
    #  公共方法（由 PanelFactory 调用）                                    #
    # ------------------------------------------------------------------ #

    def search_location(self, location_type: str):
        """搜索地点（起点/终点）"""
        search_text = getattr(self, f"{location_type}_input").text()
        if search_text:
            self.search_manager.search_location(search_text, location_type)

    def search_waypoint(self):
        """搜索途径点"""
        search_text = self.waypoint_input.text()
        if search_text:
            self.search_manager.search_location(search_text, "waypoint")

    def select_location(self, item, location_type: str):
        """选择地点（从下拉框）"""
        data = item.data(Qt.UserRole)
        self.search_manager.select_location_from_list(data, location_type)

    def remove_waypoint(self):
        """删除途径点"""
        current_row = self.waypoint_list.currentRow()
        if current_row >= 0:
            self.waypoint_list.takeItem(current_row)
            self.data_manager.remove_waypoint(current_row)

            for i in range(self.waypoint_list.count()):
                item = self.waypoint_list.item(i)
                data = item.data(Qt.UserRole)
                item.setText(f"{i+1}. {data[0]}")

            self.map_manager.update_map_preview()

    def clear_all_waypoints(self):
        """清空所有途径点"""
        self.waypoint_list.clear()
        self.data_manager.clear_waypoints()
        self.map_manager.update_map_preview()

    def show_date_panel(self, time_type: str):
        """显示日期选择面板"""
        self.time_manager.show_date_panel(time_type)

    def show_time_panel(self, time_type: str):
        """显示时间选择面板"""
        self.time_manager.show_time_panel(time_type)

    # ------------------------------------------------------------------ #
    #  新版右键菜单处理                                                    #
    # ------------------------------------------------------------------ #

    def _resolve_map_click_address(self, lat: float, lon: float) -> dict:
        """将地图点击坐标解析为地址信息（含逆地理编码）。"""
        map_source = map_config.get_map_source()
        from modules.geolocation.coordinate_transform import CoordinateTransform
        coord_system = CoordinateTransform.coord_system_for_map_source(map_source)

        address_name = f'位置 ({lat:.6f}, {lon:.6f})'
        level = None
        type_info = None

        geocoding_service = self.service_manager.get_geocoding_service(map_source)
        if geocoding_service:
            try:
                self.logger.info(f"[右键菜单] 开始逆地理编码查询: ({lat}, {lon})")
                result = geocoding_service.reverse_geocode(lat, lon)
                if result:
                    address_name = result.get('full_address', address_name)
                    level = result.get('level')
                    type_info = result.get('type')
                    self.logger.info(f"[右键菜单] 逆地理编码成功: {address_name}")
                else:
                    self.logger.warning("[右键菜单] 逆地理编码失败，使用坐标作为名称")
            except Exception as e:
                self.logger.error(f"[右键菜单] 逆地理编码异常: {str(e)}")
        else:
            self.logger.warning("[右键菜单] 地理编码服务不可用")

        return {
            'name': address_name,
            'level': level,
            'type_info': type_info,
            'coord_system': coord_system,
            'map_source': map_source,
        }

    def _refresh_map_after_point_set(self, lat: float, lon: float, level, type_info) -> None:
        """设置地图标记点后刷新地图显示。"""
        all_coords = self.map_manager._get_all_selected_coords()
        if len(all_coords) >= 2:
            self.map_manager.update_map_preview(auto_fit=True)
        else:
            zoom_level = MapRenderer.get_zoom_by_level(level, type_info)
            self.logger.info(f"[右键菜单] 单点缩放: level={level}, type={type_info}, zoom={zoom_level}")
            self.map_manager.update_map_preview_simple((lat, lon), zoom_level=zoom_level)

    def _on_context_menu_set_start_new(self, lat: float, lon: float):
        """右键菜单：设为起点（新版）"""
        self.logger.info(f"[右键菜单] 设为起点: ({lat}, {lon})")

        if not self.route_plan_panel.isVisible():
            self.route_plan_panel.show()
            self._update_route_panel_position()

        geo = self._resolve_map_click_address(lat, lon)

        self.route_plan_panel.start_input.setText(geo['name'])
        self.route_plan_panel.start_coords = (lat, lon)

        self.data_manager.set_start_location((lat, lon), geo['name'])
        self.data_manager.start_level = geo['level']
        self.data_manager.start_coord_system = geo['coord_system']
        self.logger.debug(f"[右键菜单] 保存起点坐标系: {geo['coord_system']}")

        self.search_manager.clear_search_results()
        self._refresh_map_after_point_set(lat, lon, geo['level'], geo['type_info'])

    def _on_context_menu_add_waypoint_new(self, lat: float, lon: float):
        """右键菜单：设为途经点（新版）"""
        self.logger.info(f"[右键菜单] 设为途经点: ({lat}, {lon})")

        if not self.route_plan_panel.isVisible():
            self.route_plan_panel.show()
            self._update_route_panel_position()

        if len(self.route_plan_panel.waypoint_widgets) >= 5:
            self.logger.warning("[右键菜单] 途径点已达到5个上限，无法添加")
            return

        geo = self._resolve_map_click_address(lat, lon)

        self.route_plan_panel._add_waypoint()
        if self.route_plan_panel.waypoint_widgets:
            self.route_plan_panel.waypoint_widgets[-1]['input'].setText(geo['name'])

        if not hasattr(self.route_plan_panel, 'waypoint_coords_list'):
            self.route_plan_panel.waypoint_coords_list = []
        self.route_plan_panel.waypoint_coords_list.append((lat, lon))

        self.data_manager.add_waypoint((lat, lon), geo['name'])
        if not hasattr(self.data_manager, 'waypoints_level'):
            self.data_manager.waypoints_level = []
        self.data_manager.waypoints_level.append(geo['level'])
        if not hasattr(self.data_manager, 'waypoint_coord_systems'):
            self.data_manager.waypoint_coord_systems = []
        self.data_manager.waypoint_coord_systems.append(geo['coord_system'])
        self.logger.debug(f"[右键菜单] 保存途径点坐标系: {geo['coord_system']}")

        self.search_manager.clear_search_results()
        self._refresh_map_after_point_set(lat, lon, geo['level'], geo['type_info'])

    def _on_context_menu_set_end_new(self, lat: float, lon: float):
        """右键菜单：设为终点（新版）"""
        self.logger.info(f"[右键菜单] 设为终点: ({lat}, {lon})")

        if not self.route_plan_panel.isVisible():
            self.route_plan_panel.show()
            self._update_route_panel_position()

        geo = self._resolve_map_click_address(lat, lon)

        self.route_plan_panel.end_input.setText(geo['name'])
        self.route_plan_panel.end_coords = (lat, lon)

        self.data_manager.set_end_location((lat, lon), geo['name'])
        self.data_manager.end_level = geo['level']
        self.data_manager.end_coord_system = geo['coord_system']
        self.logger.debug(f"[右键菜单] 保存终点坐标系: {geo['coord_system']}")

        self.search_manager.clear_search_results()
        self._refresh_map_after_point_set(lat, lon, geo['level'], geo['type_info'])

    def _on_context_menu_query_here(self, lat: float, lon: float):
        """右键菜单：这是哪儿"""
        self.logger.info(f"[右键菜单] 这是哪儿: ({lat}, {lon})")

        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            self.logger.warning(f"[右键菜单] 无效的坐标: lat={lat}, lon={lon}")
            location_data = {
                'name': '无效坐标',
                'address': f'坐标值超出有效范围',
                'lat': lat,
                'lon': lon,
                'type': ''
            }
            from PyQt5.QtGui import QCursor
            cursor_pos = QCursor.pos()
            if self.location_info_popup is not None:
                self.location_info_popup.show_location_info(location_data, cursor_pos)
            return

        map_source = map_config.get_map_source()
        geocoding_service = self.service_manager.get_geocoding_service(map_source)

        location_data = {
            'name': f'位置 ({lat:.6f}, {lon:.6f})',
            'address': '',
            'lat': lat,
            'lon': lon,
            'type': ''
        }

        if geocoding_service:
            try:
                self.logger.info(f"[右键菜单] 开始逆地理编码查询: ({lat}, {lon})")
                result = geocoding_service.reverse_geocode(lat, lon)

                if result:
                    full_address = result.get('full_address', '')
                    name = result.get('name', full_address)
                    type_info = result.get('type', '')

                    if name:
                        location_data['name'] = name
                    if full_address:
                        location_data['address'] = full_address
                    if type_info:
                        location_data['type'] = type_info

                    self.logger.info(f"[右键菜单] 逆地理编码成功: {name}")
                else:
                    self.logger.warning(f"[右键菜单] 逆地理编码未返回结果")

            except Exception as e:
                self.logger.error(f"[右键菜单] 逆地理编码异常: {str(e)}")
        else:
            self.logger.warning("[右键菜单] 地理编码服务不可用")

        click_pos = getattr(self, '_context_menu_click_pos', None)
        if click_pos is None:
            from PyQt5.QtGui import QCursor
            click_pos = QCursor.pos()

        if self.location_info_popup is not None:
            self.location_info_popup.show_location_info(location_data, click_pos)
        else:
            self.logger.error("[右键菜单] 位置信息面板不存在")

    def _on_context_menu_set_center(self, lat: float, lon: float):
        """右键菜单：设为地图中心点（仅平移，显示箭头标记）"""
        self.logger.info(f"[右键菜单] 设为地图中心点: ({lat}, {lon})")

        self.center_point_marker = (lat, lon)

        from modules.map.webengine import MapJsBridge
        if self.map_view and self.map_view.page():
            MapJsBridge.pan_to_center(self.map_view.page(), lat, lon)
            self.logger.info(f"[右键菜单] 已执行地图中心点平移和箭头标记 JavaScript 代码")
        else:
            self.logger.warning("[右键菜单] 地图视图或页面不存在")

    def _on_context_menu_clear_route(self):
        """右键菜单：清空地图"""
        self.logger.info("[右键菜单] 清空地图")

        self.data_manager.clear_all_route_data()
        self.route_plan_panel.clear_all_inputs()
        self.map_manager.clear_map_and_keep_view()

        self.logger.info("[右键菜单] 地图已清空")

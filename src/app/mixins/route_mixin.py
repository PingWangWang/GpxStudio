"""RouteMixin — 路线规划面板事件处理方法"""
from modules.geolocation import CoordinateTransform
from modules.map import MapRenderer
from services.config.map_config import map_config
from modules.routing.ui.route_plan_panel import MAX_WAYPOINTS


class RouteMixin:
    """路线规划面板的所有交互逻辑。"""

    def _show_route_plan_panel(self):
        """显示路线规划面板"""
        self.logger.info("[路线面板] 显示路线规划面板")

        # 新会话开始：重置会话设置标志（本会话首次设置起终点时清空上次残留规划数据）
        self._route_plan_session_set = False

        # 互斥：先关闭收藏夹弹窗（若展开），避免两面板重叠显示
        self._close_favorites_panel()

        if self.search_history_popup is not None:
            self.search_history_popup.hide()
        if self.search_results_popup is not None:
            self.search_results_popup.hide()

        if self.search_container is not None and self.route_plan_panel is not None:
            self.route_plan_panel.clear_all_inputs()

            # 顶部对齐工具栏下方（与地点搜索列表一致），高度先取临时值便于布局测量
            container_rect = self.search_container.rect()
            container_global_pos = self.search_container.mapToGlobal(container_rect.bottomLeft())
            panel_x = container_global_pos.x()
            panel_y = container_global_pos.y() + 4

            self.route_plan_panel.setGeometry(panel_x, panel_y, self.search_container.width(), 500)

            from modules.routing import RouteHistoryStorage
            fresh_storage = RouteHistoryStorage()
            history_list = fresh_storage.get_history(10)
            self.route_plan_panel.load_history(history_list)

            self.route_plan_panel._switch_transport_mode("driving")

            self.route_plan_panel.show()
            self.route_plan_panel.raise_()
            self.route_plan_panel.setFocus()

            # 布局完成后按内容自然高与主窗口边界约束调整面板总高
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, self.route_plan_panel._update_panel_height)

            self.logger.debug(f"[路线面板] 面板位置: ({panel_x}, {panel_y})")
            self.logger.debug(f"[路线面板] 面板大小: {self.search_container.width()} x 动态")
            self.logger.debug("[路线面板] 路线规划面板已显示并设置焦点")

    def _on_route_panel_cancel(self):
        """路线规划面板取消按钮点击"""
        self.logger.info("[路线面板] 取消路线规划")

        if self.route_button is not None and hasattr(self.route_button, 'stop_animation'):
            self.route_button.stop_animation()

        if self.route_plan_panel is not None:
            self.route_plan_panel.restore_history_mode()

        if self.route_plan_panel is not None:
            self.route_plan_panel.hide()

    def _close_route_plan_panel(self):
        """互斥：关闭路线规划面板（若可见），供收藏夹等展开入口调用

        复用取消按钮的完整关闭流程（停止按钮动画 + 恢复历史模式 + 隐藏）。
        """
        if (self.route_plan_panel is not None
                and self.route_plan_panel.isVisible()):
            self._on_route_panel_cancel()

    def _on_route_plan_clicked(self, start: str, end: str, mode: str, waypoints: list):
        """路线规划按钮点击"""
        self.logger.info(f"[路线规划] 开始规划路线: {start} → {end}, 方式: {mode}")
        self.logger.info(f"[路线规划] 途径点: {waypoints}")
        # 新规划开始：清除历史选择的挂起剖面（避免残留显示在新规划之后）
        self._pending_history_elevation_show = None

        if not start or not end:
            self.route_plan_panel.show_route_plan_error("请先设置起点和终点")
            return

        if not self.data_manager.has_start_end():
            self.route_plan_panel.show_route_plan_error("请先搜索并选择起点和终点位置")
            return

        if waypoints:
            if len(self.data_manager.waypoints_coords) < len(waypoints):
                self.route_plan_panel.show_route_plan_error("请先搜索并选择所有途径点位置")
                return

        self._current_route_info = {
            'start': start,
            'end': end,
            'mode': mode,
            'waypoints': waypoints,
            'start_coords': self.data_manager.start_coords,
            'end_coords': self.data_manager.end_coords,
            'waypoint_coords': self.data_manager.waypoints_coords
        }

        self.show_loading()
        self.route_plan_panel.show_loading()

        self.route_manager.plan_route(mode)

    def _on_route_clear_clicked(self):
        """清除路线按钮点击"""
        self.logger.info("[路线面板] 清除路线")

        self.data_manager.clear_all_route_data()
        self.route_plan_panel.clear_all_inputs()
        self.map_manager.update_map_preview(auto_fit=False, keep_zoom=True)

        self.logger.info("[路线面板] 路线已清除")

    def _on_route_switch_start_end(self):
        """切换起止点按钮点击，并反转途径点顺序"""
        self.logger.info("[路线面板] 切换起止点")

        temp_coords = self.data_manager.start_coords
        temp_name = self.data_manager.start_name
        temp_level = self.data_manager.start_level

        self.data_manager.start_coords = self.data_manager.end_coords
        self.data_manager.start_name = self.data_manager.end_name
        self.data_manager.start_level = self.data_manager.end_level

        self.data_manager.end_coords = temp_coords
        self.data_manager.end_name = temp_name
        self.data_manager.end_level = temp_level

        if self.data_manager.waypoints_coords:
            self.data_manager.waypoints_coords.reverse()
            self.data_manager.waypoints_names.reverse()
            self.logger.info(f"[路线面板] 途径点已反转，数量: {len(self.data_manager.waypoints_coords)}")

        if self._current_route_info is not None:
            self._current_route_info['start'] = self.data_manager.start_name
            self._current_route_info['end'] = self.data_manager.end_name
            self._current_route_info['start_coords'] = self.data_manager.start_coords
            self._current_route_info['end_coords'] = self.data_manager.end_coords
            self._current_route_info['waypoints'] = self.data_manager.waypoints_names[:]
            self._current_route_info['waypoint_coords'] = self.data_manager.waypoints_coords[:]
            self.logger.info(f"[路线面板] 已更新_current_route_info: 途径点数量={len(self._current_route_info['waypoints'])}")

        self.map_manager.update_map_preview(auto_fit=False, keep_zoom=True)

        self.logger.info(f"[路线面板] 起止点已交换: 起点={self.data_manager.start_name}, 终点={self.data_manager.end_name}")

    def _on_route_location_search(self, search_text: str, location_type: str):
        """路线面板中的地点搜索"""
        self.logger.info(f"[路线面板] 搜索地点: {search_text}, 类型: {location_type}")

        self.route_plan_panel.show_loading()

        map_source = map_config.get_map_source()

        if map_source == 'gaode' and not map_config.is_gaode_configured():
            self.logger.warning("高德地图API未配置，无法进行路线面板地点搜索")
            self.route_plan_panel.hide_loading()
            self._show_warning(
                "高德地图API未配置",
                "使用高德地图搜索需要先配置API密钥。\n\n"
                "请在【地图设置】中配置高德地图Web服务API密钥。\n\n"
                "获取方式：\n"
                "1. 访问高德开放平台：https://lbs.amap.com/\n"
                "2. 注册并创建应用\n"
                "3. 获取Web服务API密钥"
            )
            self.route_plan_panel.show_search_error(location_type)
            return

        geocoding_service = self.service_manager.get_geocoding_service(map_source)

        if not geocoding_service:
            self.logger.warning(f"未找到地图源 {map_source} 的地理编码服务")
            self.route_plan_panel.hide_loading()
            self.route_plan_panel.show_search_error(location_type)
            return

        try:
            results = geocoding_service.search_location(search_text)

            self.route_plan_panel.hide_loading()

            if results:
                suggestions = []
                for result in results:
                    name = result.get('name', '')
                    address = result.get('address', result.get('formatted_address', ''))

                    coord_system = result.get('coord_system', 'WGS-84')
                    data_source = result.get('data_source', map_source or 'unknown')

                    if 'location' in result:
                        location = result['location']
                    elif 'lat' in result and 'lon' in result:
                        location = f"{result['lon']},{result['lat']}"
                    elif 'lng' in result and 'lat' in result:
                        location = f"{result['lng']},{result['lat']}"
                    else:
                        location = ''

                    suggestions.append({
                        'name': name,
                        'address': address,
                        'location': location,
                        'level': result.get('level'),
                        'type': result.get('type'),
                        'radius': result.get('radius'),
                        'coord_system': coord_system,
                        'data_source': data_source
                    })

                self.route_plan_panel.show_address_suggestions(suggestions)

                if suggestions and suggestions[0].get('location'):
                    first_addr = suggestions[0]
                    location = first_addr['location']
                    if ',' in location:
                        try:
                            lng, lat = location.split(',')
                            self.map_manager.preview_search_result(
                                coords=(float(lat), float(lng)),
                                name=f"{first_addr['name']}\n{first_addr['address']}",
                                level=first_addr.get('level'),
                                type_info=first_addr.get('type'),
                                radius=first_addr.get('radius'),
                                result_data=first_addr
                            )
                        except (ValueError, IndexError) as e:
                            self.logger.error(f"无效的坐标格式: {location}, 错误: {e}")
            else:
                self.route_plan_panel.hide_address_suggestions_and_show_history()
                self.route_plan_panel.show_search_error(location_type)
                self.logger.warning(f"未找到地址: {search_text}")

        except Exception as e:
            self.logger.error(f"搜索地址失败: {e}")
            self.route_plan_panel.hide_loading()
            self.route_plan_panel.hide_address_suggestions_and_show_history()
            self.route_plan_panel.show_search_error(location_type)

    def _on_route_address_selected(self, address_data: dict, location_type: str, should_zoom: bool = True):
        """处理地址选中事件"""
        self.logger.info(f"[路线面板] 地址选中: {address_data.get('name', '')}, 类型: {location_type}, 缩放: {should_zoom}")

        lat_float = None
        lng_float = None

        if 'lat' in address_data and 'lon' in address_data:
            try:
                lat_float = float(address_data['lat'])
                lng_float = float(address_data['lon'])
            except (ValueError, TypeError) as e:
                self.logger.warning(f"无法解析 lat/lon 字段: {e}")

        if lat_float is None or lng_float is None:
            location = address_data.get('location', '')
            if location and ',' in location:
                try:
                    lng, lat = location.split(',')
                    lat_float = float(lat)
                    lng_float = float(lng)
                except (ValueError, IndexError) as e:
                    self.logger.warning(f"无法解析 location 字段: {location}, 错误: {e}")

        if lat_float is None or lng_float is None:
            self.logger.warning(f"地址缺少有效坐标信息: {address_data}")
            return

        try:
            saved_coord_system = address_data.get('coord_system', 'WGS-84')
            current_map_source = map_config.get_map_source()
            current_coord_system = 'GCJ-02' if current_map_source == 'gaode' else 'WGS-84'

            self.logger.debug(f"[坐标系] 历史记录坐标系: {saved_coord_system}, 当前地图坐标系: {current_coord_system}")

            if saved_coord_system != current_coord_system:
                lat_float, lng_float = CoordinateTransform.convert(lat_float, lng_float, saved_coord_system, current_coord_system)
                self.logger.info(f"[坐标转换] {saved_coord_system} -> {current_coord_system}: ({address_data.get('lat')}, {address_data.get('lon')}) -> ({lat_float}, {lng_float})")

            name = address_data.get('name', '')
            level = address_data.get('level')

            # 本会话首次设置起/终/途径点时，清空上一次会话残留的规划数据（重新规划语义）；
            # 同一会话内继续设置不清空，避免设置终点时误清已设的起点标识
            if not getattr(self, '_route_plan_session_set', False):
                self.data_manager.clear_all_route_data()
                self._route_plan_session_set = True

            if location_type == "start":
                self.data_manager.set_start_location((lat_float, lng_float), name, level)
                self.data_manager.start_coord_system = current_coord_system
                self.logger.info(f"[路线面板] 设置起点: {name} ({lat_float}, {lng_float})")
            elif location_type == "end":
                self.data_manager.set_end_location((lat_float, lng_float), name, level)
                self.data_manager.end_coord_system = current_coord_system
                self.logger.info(f"[路线面板] 设置终点: {name} ({lat_float}, {lng_float})")
            elif location_type == "waypoint":
                waypoint_count = len(self.data_manager.waypoints_coords)
                input_count = len(self.route_plan_panel.waypoint_widgets)

                if waypoint_count < input_count:
                    self.data_manager.add_waypoint((lat_float, lng_float), name)
                    if not hasattr(self.data_manager, 'waypoint_coord_systems'):
                        self.data_manager.waypoint_coord_systems = []
                    self.data_manager.waypoint_coord_systems.append(current_coord_system)
                    self.logger.info(f"[路线面板] 添加途径点: {name} ({lat_float}, {lng_float})")
                else:
                    self.data_manager.update_waypoint(waypoint_count - 1, (lat_float, lng_float), name)
                    if not hasattr(self.data_manager, 'waypoint_coord_systems'):
                        self.data_manager.waypoint_coord_systems = []
                    while len(self.data_manager.waypoint_coord_systems) <= waypoint_count - 1:
                        self.data_manager.waypoint_coord_systems.append(current_coord_system)
                    self.data_manager.waypoint_coord_systems[waypoint_count - 1] = current_coord_system
                    self.logger.info(f"[路线面板] 更新途径点: {name} ({lat_float}, {lng_float})")

            is_from_history = 'timestamp' in address_data
            if not is_from_history:
                search_text = address_data.get('_search_text', name)
                if search_text:
                    result_dict = {
                        'name': name,
                        'address': address_data.get('address', ''),
                        'lat': lat_float,
                        'lon': lng_float,
                        'type': address_data.get('type', ''),
                        'level': address_data.get('level', ''),
                        'radius': address_data.get('radius', None),
                        'coord_system': address_data.get('coord_system', 'WGS-84'),
                        'data_source': address_data.get('data_source', map_config.get_map_source() or 'unknown')
                    }
                    self.search_manager._save_to_history(search_text, result_dict)
                    self.logger.info(f"[路线面板] 已保存到搜索历史: {search_text} -> {name}")
            else:
                self.logger.debug(f"[路线面板] 跳过保存历史（数据来自历史记录）: {name}")

            if should_zoom:
                self.data_manager.last_selected_coords = (lat_float, lng_float)
                self.data_manager.last_selected_level = address_data.get('level')
                self.data_manager.last_selected_type = address_data.get('type')
                self.data_manager.last_map_center = (lat_float, lng_float)

                zoom_level = MapRenderer.get_zoom_by_level(
                    address_data.get('level'),
                    address_data.get('type'),
                    address_data.get('radius')
                )

                max_zoom = 18 if current_map_source == 'gaode' else 19
                if zoom_level > max_zoom:
                    zoom_level = max_zoom
                    self.logger.debug(f"[路线面板] 缩放级别限制为 {max_zoom}（{current_map_source}地图上限）")

                self.data_manager.last_map_zoom_level = zoom_level

                self.map_manager.update_map_preview(auto_fit=False, keep_zoom=True)

                self.logger.info(f"[路线面板] 地图已缩放到: {name} ({lat_float}, {lng_float}), 缩放级别: {zoom_level}, 类型: {location_type}")
            else:
                self.logger.info(f"[路线面板] 跳过地图缩放（双击确认）")

        except Exception as e:
            self.logger.error(f"处理地址选中事件时出错: {e}, 地址数据: {address_data}")

    def _on_route_history_selected(self, history_data: dict):
        """选择路线搜索历史"""
        try:
            start = history_data.get('start', '')
            end = history_data.get('end', '')
            mode = history_data.get('mode', 'driving')

            mode_map = {"驾车": "driving", "骑行": "cycling", "步行": "walking"}
            mode = mode_map.get(mode, mode)

            start_coords = history_data.get('start_coords')
            end_coords = history_data.get('end_coords')
            waypoint_coords = history_data.get('waypoint_coords', [])
            start_coord_system = history_data.get('start_coord_system')
            end_coord_system = history_data.get('end_coord_system')
            waypoint_coord_systems = history_data.get('waypoint_coord_systems')

            route_points = history_data.get('route_points', [])
            distance = history_data.get('distance', 0)
            duration = history_data.get('duration', 0)

            self.logger.info(f"[路线面板] 选择历史记录: {start} → {end}")
            self.logger.info(f"[路线面板] 起点坐标: {start_coords}, 终点坐标: {end_coords}")
            self.logger.info(f"[路线面板] 路线点数量: {len(route_points)}, 距离: {distance}m, 时长: {duration}s")

            # 主窗口工具栏加载指示器（⏳ 旋转动画）：覆盖路线渲染与海拔折线图渲染期间
            self.show_loading()

            self.data_manager.clear_all_route_data()
            self.data_manager.clear_waypoints()

            if self.route_plan_panel is not None:
                self.route_plan_panel.restore_history_mode()
                self.route_plan_panel.clear_all_inputs()
                self.route_plan_panel.set_selected_history(history_data)

            if self.route_plan_panel is not None:
                self.route_plan_panel.set_start_location(start)
                self.route_plan_panel.set_end_location(end)
                self.route_plan_panel._switch_transport_mode(mode)

            has_coords = False

            from services.config.map_config import map_config
            current_map_source = map_config.get_map_source()
            current_coord_system = 'GCJ-02' if current_map_source == 'gaode' else 'WGS-84'

            if start_coords and isinstance(start_coords, (list, tuple)) and len(start_coords) == 2:
                saved_coord_system = start_coord_system or 'WGS-84'

                if saved_coord_system != current_coord_system:
                    lat, lon = CoordinateTransform.convert(start_coords[0], start_coords[1], saved_coord_system, current_coord_system)
                    start_coords = (lat, lon)
                    self.logger.info(f"[路线面板] 起点坐标已转换: {saved_coord_system} → {current_coord_system}")

                self.data_manager.set_start_location(tuple(start_coords), start)
                self.data_manager.start_coord_system = current_coord_system
                self.logger.info(f"[路线面板] 已恢复起点坐标: {start_coords} (坐标系: {current_coord_system})")
                has_coords = True

            if end_coords and isinstance(end_coords, (list, tuple)) and len(end_coords) == 2:
                saved_coord_system = end_coord_system or 'WGS-84'

                if saved_coord_system != current_coord_system:
                    lat, lon = CoordinateTransform.convert(end_coords[0], end_coords[1], saved_coord_system, current_coord_system)
                    end_coords = (lat, lon)
                    self.logger.info(f"[路线面板] 终点坐标已转换: {saved_coord_system} → {current_coord_system}")

                self.data_manager.set_end_location(tuple(end_coords), end)
                self.data_manager.end_coord_system = current_coord_system
                self.logger.info(f"[路线面板] 已恢复终点坐标: {end_coords} (坐标系: {current_coord_system})")
                has_coords = has_coords and True
            else:
                has_coords = False

            if waypoint_coords:
                waypoints = history_data.get('waypoints', [])
                self.data_manager.__dict__.setdefault('waypoint_coord_systems', [])

                for i, coords in enumerate(waypoint_coords):
                    if coords and isinstance(coords, (list, tuple)) and len(coords) == 2:
                        waypoint_name = waypoints[i] if i < len(waypoints) else f"途径点{i+1}"

                        saved_coord_system = 'WGS-84'
                        if waypoint_coord_systems and i < len(waypoint_coord_systems):
                            saved_coord_system = waypoint_coord_systems[i] or 'WGS-84'

                        if saved_coord_system != current_coord_system:
                            lat, lon = CoordinateTransform.convert(coords[0], coords[1], saved_coord_system, current_coord_system)
                            coords = (lat, lon)
                            self.logger.info(f"[路线面板] 途径点{i+1}坐标已转换: {saved_coord_system} → {current_coord_system}")

                        self.data_manager.waypoint_coord_systems.append(current_coord_system)
                        self.data_manager.add_waypoint(tuple(coords), waypoint_name)

                        if self.route_plan_panel is not None:
                            self.route_plan_panel._add_waypoint()
                            if i < len(self.route_plan_panel.waypoint_widgets):
                                self.route_plan_panel.waypoint_widgets[i]['input'].setText(waypoint_name)
                        self.logger.info(f"[路线面板] 已恢复途径点{i+1}坐标: {coords} (坐标系: {current_coord_system})")

            if self.route_plan_panel is not None:
                self.route_plan_panel._update_transport_mode_ui()

            if self.route_plan_panel is not None:
                if mode == "driving":
                    waypoint_count = len(waypoint_coords)
                    if waypoint_count >= MAX_WAYPOINTS:
                        self.route_plan_panel.add_waypoint_button.setEnabled(False)
                        self.route_plan_panel.add_waypoint_button.setToolTip(f"最多添加{MAX_WAYPOINTS}个途径点")
                    else:
                        self.route_plan_panel.add_waypoint_button.setEnabled(True)
                        self.route_plan_panel.add_waypoint_button.setToolTip("添加途径点")
                    self.route_plan_panel._update_add_button_position()
                else:
                    self.route_plan_panel.add_waypoint_button.setVisible(False)

            if not has_coords:
                self.logger.info(f"[路线面板] 历史记录缺少坐标，开始自动搜索...")
                self._auto_search_history_locations(start, end, mode, history_data)
            else:
                if route_points and len(route_points) > 0:
                    converted_route_points = []
                    for point in route_points:
                        if isinstance(point, (list, tuple)) and len(point) >= 2:
                            converted_route_points.append(tuple(point))

                    if converted_route_points:
                        self.data_manager.set_route(converted_route_points, duration)
                        self.logger.info(f"[路线面板] 已恢复路线点数据: {len(converted_route_points)} 个点")

                        self.map_manager.show_route_on_map()
                        self.logger.info(f"[路线面板] 路线已渲染到地图")

                        # 历史路线海拔剖面：挂起到地图页面加载完成后再显示
                        # （先渲染路线后显示折线图；页面加载完成后经 _on_map_loaded 显示并关闭加载指示器）
                        self._pending_history_elevation_show = (converted_route_points, duration)

                        if self.route_plan_panel is not None:
                            self.route_plan_panel.update_history_route_data_status(history_data, True)
                else:
                    self.logger.info(f"[路线面板] 历史记录中没有路线点数据，只显示起点和终点")

                    if self.route_plan_panel is not None:
                        self.route_plan_panel.update_history_route_data_status(history_data, False)

                    if self.data_manager.start_coords and self.data_manager.end_coords:
                        self.map_manager.update_map_preview(auto_fit=True)

                    self.hide_loading()

        except Exception as e:
            self.logger.error(f"[路线面板] 处理历史记录选择时出错: {str(e)}")
            self.hide_loading()

    def _auto_search_history_locations(self, start: str, end: str, mode: str, history_data: dict):
        """自动搜索历史记录中的起点和终点坐标"""
        map_source = map_config.get_map_source()
        geocoding_service = self.service_manager.get_geocoding_service(map_source)

        if not geocoding_service:
            self.logger.warning(f"未找到地图源 {map_source} 的地理编码服务")
            return

        try:
            self.logger.info(f"[路线面板] 搜索起点: {start}")
            start_results = geocoding_service.search_location(start)
            if start_results and len(start_results) > 0:
                first_result = start_results[0]
                location = first_result.get('location', '')
                if location and ',' in location:
                    lng, lat = location.split(',')
                    start_coords = (float(lat), float(lng))
                    self.data_manager.set_start_location(start_coords, start, first_result.get('level'))
                    self.logger.info(f"[路线面板] 起点坐标已找到: {start_coords}")

            self.logger.info(f"[路线面板] 搜索终点: {end}")
            end_results = geocoding_service.search_location(end)
            if end_results and len(end_results) > 0:
                first_result = end_results[0]
                location = first_result.get('location', '')
                if location and ',' in location:
                    lng, lat = location.split(',')
                    end_coords = (float(lat), float(lng))
                    self.data_manager.set_end_location(end_coords, end, first_result.get('level'))
                    self.logger.info(f"[路线面板] 终点坐标已找到: {end_coords}")

            if self.data_manager.start_coords and self.data_manager.end_coords:
                self.map_manager.update_map_preview(auto_fit=True)
                self.logger.info(f"[路线面板] 已在地图上显示起点和终点")

                self.route_history_storage.add_record(
                    start, end, mode, [],
                    start_coords=self.data_manager.start_coords,
                    end_coords=self.data_manager.end_coords,
                    waypoint_coords=[]
                )
                self.logger.info(f"[路线面板] 已更新历史记录中的坐标")
            else:
                self.logger.warning(f"[路线面板] 未能找到起点或终点的坐标")

        except Exception as e:
            self.logger.error(f"[路线面板] 自动搜索历史记录位置失败: {str(e)}")
        finally:
            if self.route_plan_panel is not None:
                self.route_plan_panel.hide_loading()
                self.route_plan_panel.update_history_route_data_status(history_data, False)

    def _on_route_alternative_selected(self, index: int):
        """用户选择路线方案"""
        self.logger.info(f"[路线面板] 用户选择路线方案: {index}")

        self.route_plan_panel.hide_loading()
        self.route_manager.select_route_alternative(index)

    def _show_history_elevation_profile(self, route_points, duration):
        """历史路线海拔剖面显示（仅渲染，不自动获取）

        历史切换时直接从历史 route_points 计算剖面显示（绕开 data_manager，
        其 route_alternatives 在历史切换时已被清空）：
        有海拔 → 直接显示剖面；无海拔 → 显示空占位。
        海拔数据仅在用户手动点击"获取海拔"按钮时获取。

        Args:
            route_points: 历史路线点列表 [(lat, lon) 或 (lat, lon, elevation), ...]
            duration: 路线耗时（秒）
        """
        try:
            from services.config.map_config import map_config
            from ui.widgets.elevation_profile_panel import ElevationProfilePanel
            panel = getattr(self, 'elevation_profile_panel', None)
            if panel is None:
                return
            # 开关关闭时隐藏面板（与 _show_elevation_profile 三分支一致）
            if not map_config.get_show_elevation_profile():
                panel.clear_route()
                return
            distances, elevations = ElevationProfilePanel.compute_profile(route_points)
            if distances is None:
                # 无有效海拔点：清空悬停映射（无剖面数据时圆点不显示）
                self._profile_route_points = None
                panel.show_empty()
                return
            # 缓存有效路线点序列（与剖面序列一一对应，过滤规则与 compute_profile 一致）：
            # 折线图悬停索引 → 直取路线坐标，在地图上显示定位圆点
            self._profile_route_points = [
                p for p in route_points
                if p is not None and len(p) >= 3 and p[2] is not None
            ]
            # 路线名称不在面板显示，传空串
            panel.show_route("", distances, elevations, duration or 0)
        except Exception as e:
            self.logger.error(f"[路线面板] 历史路线海拔剖面显示失败: {e}")

    @staticmethod
    def _history_has_elevation(route_points) -> bool:
        """历史路线点是否已含海拔数据（任一点为三元组且第三维非 None）"""
        return any(
            p is not None and len(p) >= 3 and p[2] is not None
            for p in (route_points or []))

    def _on_elevation_chart_hovered(self, index: int, distance: float, elevation: float):
        """海拔折线图悬停：地图路线上显示对应位置的定位圆点

        剖面序列与显示剖面时的有效路线点序列（_profile_route_points）一一对应，
        索引直取坐标 → 转 GCJ-02（与地图渲染层一致）→ JS 动态更新圆点。
        """
        try:
            points = getattr(self, '_profile_route_points', None)
            if not points or not (0 <= index < len(points)):
                return
            point = points[index]
            # 路线点为 WGS-84，地图渲染层统一转 GCJ-02，此处保持一致
            lat, lon = CoordinateTransform.convert(point[0], point[1], 'WGS-84', 'GCJ-02')
            if self.map_view is not None and self.map_view.page() is not None:
                from modules.map.js_bridge import MapJsBridge
                MapJsBridge.update_elevation_dot(self.map_view.page(), lat, lon)
        except Exception as e:
            self.logger.debug(f"[海拔悬停] 地图圆点更新失败: {e}")

    def _on_elevation_chart_hover_ended(self):
        """海拔折线图悬停结束：隐藏地图路线上的定位圆点"""
        try:
            if self.map_view is not None and self.map_view.page() is not None:
                from modules.map.js_bridge import MapJsBridge
                MapJsBridge.hide_elevation_dot(self.map_view.page())
        except Exception as e:
            self.logger.debug(f"[海拔悬停] 地图圆点隐藏失败: {e}")

    def _on_history_elevation_fetch_clicked(self, history_data: dict):
        """历史条目"获取海拔"按钮点击：手动获取该历史路线的海拔

        无海拔 → 直接获取；已有海拔 → 弹窗确认后重新获取（覆盖原海拔数据）。
        获取完成后经 on_elevation_task_completed → elevation_fetch_completed
        回写历史记录并刷新剖面图。

        Args:
            history_data: 历史记录数据
        """
        try:
            route_points = history_data.get('route_points', [])
            duration = history_data.get('duration', 0)

            # 已有海拔：弹窗确认是否重新获取（覆盖原数据）
            if self._history_has_elevation(route_points):
                from ui.dialogs.custom_message_dialog import CustomMessageDialog
                dialog = CustomMessageDialog(
                    self, title="重新获取海拔",
                    message="该路线已获取过海拔数据。\n是否重新获取？\n重新获取将覆盖原有的海拔数据。",
                    show_cancel=True, ok_text="重新获取")
                if not dialog.exec_():
                    self.logger.info("[路线面板] 用户取消重新获取海拔")
                    return

            self.logger.info(f"[路线面板] 手动获取历史路线海拔: "
                             f"{history_data.get('start', '')} → {history_data.get('end', '')}")

            # 构造单方案触发异步获取（选中索引默认 0，即该历史路线）
            task_id = self.route_manager._fetch_elevation_data_async(
                [{'route_points': list(route_points), 'duration': duration}])
            if task_id:
                # 记录待回写历史（task_id → history_data），完成后回写海拔并持久化
                pending = getattr(self, '_pending_history_elevation', None)
                if pending is None:
                    pending = self._pending_history_elevation = {}
                pending[task_id] = history_data
                # 开启主窗口工具栏加载指示器（⏳ 旋转动画），任务完成后自动关闭
                self.show_loading()
        except Exception as e:
            self.logger.error(f"[路线面板] 历史路线海拔获取失败: {e}")

    def _on_elevation_fetch_completed(self, task_id, result):
        """海拔获取任务完成回调：回写海拔到历史记录并更新按钮高亮

        Args:
            task_id: 任务ID（与 _pending_history_elevation 关联）
            result: 更新后的路线方案列表（含海拔），失败时为 None
        """
        pending = getattr(self, '_pending_history_elevation', None)
        if not pending:
            return
        history_data = pending.pop(task_id, None)
        # 所有海拔获取任务完成后关闭加载指示器（并发任务未完成时保持旋转）
        if not pending:
            self.hide_loading()
        if history_data is None or not result:
            return
        try:
            # 取单方案更新后的路线点（带海拔）
            updated = result[0].get('route_points')
            if not updated:
                return

            # 持久化回写历史记录（storage 文件）
            if self.route_history_storage is not None:
                self.route_history_storage.update_route_points(history_data, updated)

            # 同步面板内存数据源（_last_history_list 与条目 widget 同引用）
            if self.route_plan_panel is not None:
                last_list = getattr(self.route_plan_panel, '_last_history_list', None)
                if last_list:
                    for rec in last_list:
                        if (rec.get('start') == history_data.get('start')
                                and rec.get('end') == history_data.get('end')
                                and rec.get('mode') == history_data.get('mode')
                                and (rec.get('waypoints') or []) == (history_data.get('waypoints') or [])):
                            rec['route_points'] = list(updated)
                            break
                # 更新条目按钮高亮（已获取海拔）
                self.route_plan_panel.update_history_elevation_status(history_data, True)
        except Exception as e:
            self.logger.error(f"[路线面板] 历史路线海拔回写失败: {e}")

    def _show_route_alternatives(self, alternatives: list, selected_index: int = 0):
        """显示路线待选列表"""
        self.logger.info(f"[路线面板] 显示路线待选列表，共 {len(alternatives)} 个方案")

        self.route_plan_panel.hide_loading()
        self.route_plan_panel.show_route_alternatives(alternatives, selected_index)

    def _save_route_history(self, distance: float = None, duration: int = None):
        """保存路线历史记录（在路线规划成功后调用）"""
        if self._current_route_info is None:
            self.logger.warning("[路线面板] 没有当前路线信息，无法保存历史记录")
            return

        info = self._current_route_info

        route_points = self.data_manager.route_points if hasattr(self.data_manager, 'route_points') else None

        if route_points:
            valid_points = [p for p in route_points if p is not None]
            self.logger.debug(f"[路线面板] 准备保存路线点数据，共 {len(valid_points)} 个有效点")
        else:
            self.logger.warning("[路线面板] 没有路线点数据")

        self.route_history_storage.add_record(
            info['start'],
            info['end'],
            info['mode'],
            info['waypoints'],
            start_coords=info['start_coords'],
            end_coords=info['end_coords'],
            waypoint_coords=info['waypoint_coords'],
            distance=distance,
            duration=duration,
            route_points=route_points
        )

        self.logger.info(f"[路线面板] 已保存历史记录: {info['start']} → {info['end']}, "
                         f"距离: {distance}米, 时长: {duration}秒")

        history_list = self.route_history_storage.get_history(10)
        self.route_plan_panel.load_history(history_list)

        delattr(self, '_current_route_info')

    def _get_mode_text(self, mode: str) -> str:
        """获取交通方式文本"""
        mode_map = {
            'driving': '驾车',
            'cycling': '骑行',
            'walking': '步行'
        }
        return mode_map.get(mode, '驾车')

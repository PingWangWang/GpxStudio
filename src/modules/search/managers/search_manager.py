"""
搜索管理器
负责地点搜索功能
支持后台线程执行和进度展示
"""

from typing import List, Optional
from PyQt5.QtWidgets import QMessageBox, QListWidgetItem, QApplication
from PyQt5.QtCore import Qt, QObject, pyqtSlot
from services.config.map_config import map_config
from modules.geolocation import CoordinateTransform
from core.background_task import TaskPriority
from ..storage import GeoInfoStorage


class SearchManager(QObject):
    """搜索管理器

    负责地点搜索和地理编码功能：
    - 支持多种地图源的地点搜索
    - 处理搜索结果的展示和选择
    - 管理搜索结果与地图的交互
    - 根据搜索类型（起点/终点/途径点）处理搜索结果
    - 管理搜索历史记录的持久化存储

    支持后台线程异步执行，主线程快速响应用户操作
    """

    def __init__(self, service_manager, data_manager, ui_updater, logger,
                 task_manager=None, search_viewmodel=None, geo_storage=None):
        """
        初始化搜索管理器

        参数:
            service_manager: 服务管理器实例，提供地理编码服务
            data_manager: 数据管理器实例，用于存储和获取搜索相关数据
            ui_updater: UI更新回调函数字典，用于更新界面显示
            logger: 日志器，用于记录搜索操作日志
            task_manager: 任务管理器实例，用于后台任务管理
            search_viewmodel: SearchViewModel 实例（可选）；若提供，搜索结果将
                通过 ``search_viewmodel.set_results()`` 信号驱动，而非直接调用
                ``ui_updater['show_search_results_dropdown']``
            geo_storage: 共享地点搜索历史存储（与路线面板最近搜索同一实例，
                         数据源统一；未注入时自建）
        """
        super().__init__()
        self.service_manager = service_manager
        self.data_manager = data_manager
        self.ui_updater = ui_updater
        self.logger = logger
        self.task_manager = task_manager
        # ViewModel（Step 8 引入）：若提供则优先通过信号通知 UI
        self.search_viewmodel = search_viewmodel

        # 初始化地理信息存储（共享主窗口实例，数据源统一）
        self.geo_storage = geo_storage or GeoInfoStorage()
        self.logger.info("[搜索管理器] 地理信息存储已初始化")

    def search_location(self, search_text: str, location_type: str):
        """
        搜索地点

        参数:
            search_text: 搜索文本，用户输入的地点名称或地址
            location_type: 位置类型（start/end/waypoint），指定搜索结果的用途
        """
        if not search_text:
            return

        # 检查地图源是否已设置
        map_source = map_config.get_map_source()
        if not map_source:
            self.ui_updater.show_warning("警告", "请先在地图配置中设置地图数据源")
            return

        # 恢复信息展示框标题
        self.ui_updater.set_results_title("搜索结果")
        self.ui_updater.clear_results_list()
        self.ui_updater.set_progress_indeterminate()
        QApplication.processEvents()

        # 如果有任务管理器，使用后台线程执行
        if self.task_manager:
            self.logger.info(f"使用后台线程执行搜索任务: {search_text}")
            from app.managers.task_adapters import SearchTaskAdapter

            # 获取地理编码服务
            geocoding_service = self.service_manager.get_geocoding_service(map_source)

            task_id = self.task_manager.submit_task(
                task_type="search",
                task_func=SearchTaskAdapter.create_search_task,
                priority=TaskPriority.HIGH,  # 用户操作优先级最高
                geocoding_service=geocoding_service,
                search_text=search_text,
                map_source=map_source
            )

            # 保存location_type用于后续处理
            self.data_manager.searching_for = location_type

            self.logger.debug(f"搜索任务已提交: {task_id}")
        else:
            # 兼容模式：直接执行
            self._perform_search(search_text, location_type, map_source)

    @pyqtSlot(str, object)
    def on_search_task_completed(self, task_id: str, result):
        """处理搜索任务完成（槽函数）

        参数:
            task_id: 任务ID
            result: 搜索结果列表
        """
        self.logger.info(f"搜索任务完成: {task_id}")

        self.ui_updater.set_progress_complete()
        QApplication.processEvents()

        if result is not None and len(result) > 0:
            # 搜索成功 - 通过 ViewModel 信号（优先）或 ui_updater 回调显示结果
            location_type = self.data_manager.searching_for

            # 转换搜索结果为标准格式
            formatted_results = self._format_search_results(result)

            if self.search_viewmodel is not None:
                # ViewModel 路径（Step 8）：set_results 发射 results_changed 信号
                self.search_viewmodel.set_results(formatted_results)
            elif hasattr(self.ui_updater, 'show_search_results_dropdown'):
                # 兼容旧路径（未传入 ViewModel 时）
                self.ui_updater.show_search_results_dropdown(formatted_results)
        else:
            # 搜索失败或无结果
            search_text = "未知"  # 由于是异步，无法直接获取search_text
            self._handle_search_failure(search_text)

    def _format_search_results(self, results: list) -> list:
        """
        格式化搜索结果为标准字典格式

        参数:
            results: 原始搜索结果列表

        返回:
            list: 格式化后的结果列表
        """
        formatted = []
        for result in results:
            if isinstance(result, dict):
                # 高德地图格式
                formatted.append({
                    'name': result.get('name', ''),
                    'address': result.get('address', ''),
                    'lat': result.get('lat', 0),
                    'lon': result.get('lon', 0),
                    'type': result.get('type', ''),
                    'level': result.get('level', ''),
                    'radius': result.get('radius', None),
                    'coord_system': result.get('coord_system', 'WGS-84'),
                    'data_source': result.get('data_source', 'unknown')
                })
            else:
                # OSM格式
                formatted.append({
                    'name': result.address if hasattr(result, 'address') else str(result),
                    'address': result.address if hasattr(result, 'address') else '',
                    'lat': result.latitude if hasattr(result, 'latitude') else 0,
                    'lon': result.longitude if hasattr(result, 'longitude') else 0,
                    'type': result.type if hasattr(result, 'type') else '',
                    'level': '',
                    'radius': None,
                    'coord_system': 'WGS-84',
                    'data_source': 'osm'
                })
        return formatted

    @pyqtSlot(str, str)
    def on_search_task_failed(self, task_id: str, error: str):
        """处理搜索任务失败（槽函数）

        参数:
            task_id: 任务ID
            error: 错误信息
        """
        self.logger.error(f"搜索任务失败: {task_id} - {error}")
        self.ui_updater.set_progress_complete()
        self.ui_updater.show_warning("搜索失败", f"搜索出错: {error}")

    def _perform_search(self, search_text: str, location_type: str, map_source: str):
        """执行搜索（内部方法）

        根据地图源选择对应的地理编码服务，并执行实际的地点搜索。

        参数:
            search_text: 搜索文本
            location_type: 位置类型
            map_source: 地图源（如：gaode、osm等）
        """
        # 根据地图源选择服务
        geocoding_service = self.service_manager.get_geocoding_service(map_source)

        # 检查高德API配置
        if map_source == "gaode" and not map_config.is_gaode_configured():
            self.logger.warning("高德地图API未配置，无法进行地点搜索。请先配置高德地图API密钥。")
            locations = []
        else:
            locations = geocoding_service.search_location(search_text)

        self.ui_updater.set_progress_complete()
        QApplication.processEvents()

        if locations:
            self._handle_search_success(locations, location_type)
        else:
            self._handle_search_failure(search_text)

    def _handle_search_success(self, locations: List, location_type: str):
        """处理搜索成功（内部方法）

        搜索成功后，更新数据管理器中的搜索结果，并在界面和地图上显示结果。

        参数:
            locations: 搜索结果列表，包含地点名称、坐标等信息
            location_type: 位置类型
        """
        self.data_manager.set_search_results(locations, location_type)

        # 更新标题
        from app.constants import SEARCH_LIST_TITLES, SEARCH_RESULTS_TITLE
        title = SEARCH_LIST_TITLES.get(location_type, SEARCH_RESULTS_TITLE)
        self.ui_updater.set_results_title(title)

        # 显示搜索结果
        self.ui_updater.show_search_results(locations)

        # 在地图上显示搜索结果
        self.ui_updater.show_search_results_on_map(locations, location_type)

    def _handle_search_failure(self, search_text: str):
        """处理搜索失败（内部方法）

        搜索失败后，向用户显示失败提示和建议。

        参数:
            search_text: 搜索文本
        """
        self.ui_updater.show_warning(
            "搜索失败",
            f"未找到: {search_text}\n\n建议：\n"
            "1. 尝试使用更具体的地址（如：陕西省西安市）\n"
            "2. 尝试使用英文搜索（如：Xi'an）\n"
            "3. 检查网络连接\n"
            "4. 稍后再试（可能是服务暂时不可用）\n\n"
            "提示：某些城市名可能需要加上省份名称才能找到更多结果"
        )

    def select_location_from_list(self, data: tuple, location_type: str):
        """
        从下拉框选择地点

        参数:
            data: 地点数据 (name, lat, lon, level, type_info)，包含地点名称、坐标和其他信息
            location_type: 位置类型（start/end/waypoint）
        """
        if not data:
            return

        name = data[0]
        coords = (data[1], data[2])
        level = data[3] if len(data) > 3 else None
        type_info = data[4] if len(data) > 4 else None

        # 更新数据
        if location_type == "start":
            self.data_manager.set_start_location(coords, name, level)
        elif location_type == "end":
            self.data_manager.set_end_location(coords, name, level)
        elif location_type == "waypoint":
            # 由UI层处理途径点的更新
            pass

        # 更新UI和地图
        self.ui_updater.update_location_display(location_type, name, data)
        self.ui_updater.update_map_preview()

    def select_search_result(self, data: tuple):
        """
        从搜索结果中选择（旧版本，保留用于兼容）

        参数:
            data: 地点数据 (name, lat, lon, level, type_info)，包含地点名称、坐标和其他信息
        """
        if not data:
            return

        # 添加调试日志
        self.logger.info(f"[调试] select_search_result 收到的 data: {data}")
        # 提取数据（数据结构：name, lat, lon, level, type_info, radius）
        full_name = data[0]
        coords = (data[1], data[2])
        level = data[3] if len(data) > 3 else None
        type_info = data[4] if len(data) > 4 else None
        radius = data[5] if len(data) > 5 else None  # 提取POI半径

        # 提取纯地址名称（去除地址后缀）
        # 格式如 "name (address)" 只保留 name 部分
        clean_name = full_name.split(' (')[0] if ' (' in full_name else full_name

        searching_for = self.data_manager.searching_for

        # 注意：不在这里保存历史记录，而是在用户从下拉列表选择时保存

        # 设置选中的搜索结果坐标
        self.data_manager.set_selected_search_result(coords, level, type_info)

        # 根据搜索类型更新数据
        if searching_for == "start":
            self.data_manager.set_start_location(coords, clean_name, level)
            self.ui_updater.update_start_from_search(clean_name, data)
        elif searching_for == "end":
            self.data_manager.set_end_location(coords, clean_name, level)
            self.ui_updater.update_end_from_search(clean_name, data)
        elif searching_for == "waypoint":
            self.data_manager.add_waypoint(coords, clean_name)
            self.ui_updater.add_waypoint_to_list(clean_name, data, level)

        # 预览选中的搜索结果，传递type_info和radius以便根据地址类型和实际范围进行缩放
        # preview_search_result 方法已经完整渲染并显示了地图，包含选中点和搜索结果
        # 因此不需要再调用 update_map_preview
        self.ui_updater.preview_search_result(coords, clean_name, level, type_info, radius)

    def _save_to_history(self, search_text: str, result: dict):
        """
        保存搜索结果到历史记录

        参数:
            search_text: 搜索关键词
            result: 搜索结果字典
        """
        try:
            self.logger.debug(f"[搜索历史] 准备保存: {search_text}, result: {result}")
            # 直接使用result字典（已经是标准格式）
            self.geo_storage.add_search_result(search_text, result)
            self.logger.info(f"[搜索历史] 已保存: {search_text}")
        except Exception as e:
            self.logger.error(f"[搜索历史] 保存失败: {e}")
            import traceback
            self.logger.error(f"[搜索历史] 详细错误: {traceback.format_exc()}")

    def get_search_history(self, limit: int = 10) -> List[dict]:
        """
        获取搜索历史记录

        参数:
            limit: 返回的最大记录数

        Returns:
            List[dict]: 历史记录列表
        """
        return self.geo_storage.get_recent_history(limit)

    def select_history_result(self, record: dict):
        """
        从历史记录中选择地点（不需要重新进行地理编码）

        参数:
            record: 历史记录字典
        """
        self.logger.info(f"[搜索历史] 选择历史记录: {record.get('name')}")

        # 提取数据
        name = record.get('name', '')
        lat = record.get('lat', 0)
        lon = record.get('lon', 0)
        level = record.get('level', None)
        type_info = record.get('type', None)
        radius = record.get('radius', None)
        
        # 获取保存时的坐标系统（默认为WGS-84以兼容旧数据）
        saved_coord_system = record.get('coord_system', 'WGS-84')

        coords = (lat, lon)
        
        # 检查当前地图源需要的坐标系统
        from services.config.map_config import map_config
        current_map_source = map_config.get_map_source()
        current_coord_system = CoordinateTransform.coord_system_for_map_source(current_map_source)

        # 如果坐标系统不匹配，需要转换
        if saved_coord_system != current_coord_system:
            lat, lon = CoordinateTransform.convert(lat, lon, saved_coord_system, current_coord_system)
            coords = (lat, lon)
            self.logger.info(f"[搜索历史] 坐标已转换: {saved_coord_system} → {current_coord_system}")
        
        # 更新record中的坐标系统为当前系统
        updated_record = record.copy()
        updated_record['coord_system'] = current_coord_system
        updated_record['lat'] = coords[0]
        updated_record['lon'] = coords[1]

        # 直接在地图上预览（不需要搜索），传递更新后的记录
        self.ui_updater.preview_search_result(coords, name, level, type_info, radius, updated_record)

    def select_result_from_dropdown(self, result: dict, search_text: str):
        """
        从搜索结果下拉列表中选择地点

        参数:
            result: 搜索结果字典
            search_text: 原始搜索文本
        """
        self.logger.info(f"[搜索结果] 选择搜索结果: {result.get('name')}")

        # 提取数据
        name = result.get('name', '')
        lat = result.get('lat', 0)
        lon = result.get('lon', 0)
        level = result.get('level', None)
        type_info = result.get('type', None)
        radius = result.get('radius', None)

        coords = (lat, lon)

        # 保存到历史记录
        self._save_to_history(search_text, result)

        # 在地图上预览并缩放到对应范围，传递完整结果以保留坐标系统
        self.ui_updater.preview_search_result(coords, name, level, type_info, radius, result)

    def clear_search_results(self):
        """清空搜索结果

        清除所有搜索结果，并重置界面显示。
        """
        self.data_manager.clear_search_results()
        self.ui_updater.clear_results_list()
        self.ui_updater.set_results_title("搜索结果")

"""InitMixin — GpxStudio 初始化、信号连接、日志、UI 搭建及窗口事件方法"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QApplication, QDialog)
from PyQt5.QtCore import QTimer, QPoint
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile

from modules.map import MapJsBridge
from services.config.map_config import map_config
from app.ui_callbacks import UICallbacks


class InitMixin:
    """封装除 __init__ 之外的所有初始化逻辑及生命周期方法。"""

    # ------------------------------------------------------------------ #
    #  启动辅助                                                           #
    # ------------------------------------------------------------------ #

    def _update_splash(self, progress: int, message: str = ""):
        if self.splash_screen:
            self.splash_screen.update_progress(progress, message)
            QApplication.processEvents()

    # ------------------------------------------------------------------ #
    #  属性空值初始化                                                      #
    # ------------------------------------------------------------------ #

    def _init_null_attributes(self):
        """声明所有实例属性为 None，消除 hasattr 防御性代码。"""
        # 管理器
        self.logger = None
        self.task_manager = None
        self.data_manager = None
        self.service_manager = None
        self.window_manager = None
        self.map_manager = None
        self.search_manager = None
        self.route_manager = None
        self.location_manager = None
        self.time_manager = None
        self.update_manager = None
        self.signal_manager = None
        self.geolocation_handler = None
        self.route_history_storage = None
        self.logger_callbacks = None
        self.ui_updater = None
        # UI 组件
        self.map_view = None
        self.web_page = None
        self.map_context_menu = None
        self.search_container = None
        self.route_plan_panel = None
        self.gpx_export_popup = None
        self.search_history_popup = None
        self.search_input = None
        self.search_results_popup = None
        self.start_label = None
        self.end_label = None
        self.start_list = None
        self.end_list = None
        self.waypoint_list = None
        self.search_results_list = None
        self.search_results_title = None
        self.road_overlay_button = None
        self.route_button = None
        self.log_settings_popup = None
        self.about_popup = None
        self.map_settings_popup = None
        self.scale_panel = None
        self.scale_info_label = None
        self.time_panel = None
        self.date_panel = None
        self.location_info_popup = None
        self.center_point_marker = None
        # 内部状态
        self._widget_refs = None
        self._pending_export_history = None
        self._current_route_info = None
        self.last_window_geometry = None
        self.active_popups = None
        # ViewModel 层
        self.app_viewmodel = None

    # ------------------------------------------------------------------ #
    #  各阶段初始化                                                        #
    # ------------------------------------------------------------------ #

    def _init_managers(self):
        from ..managers import (DataManager, ServiceManager, WindowManager, UpdateManager)
        from ..constants import WINDOW_TITLE, WINDOW_SIZE
        print("开始初始化管理器")

        self.data_manager = DataManager()

        # 共享地点搜索历史存储（主窗口搜索历史列表与路线面板最近搜索列表共用同一实例）
        from modules.search.storage import GeoInfoStorage
        self.geo_info_storage = GeoInfoStorage()

        self.logger_callbacks = {
            'geocoding': self._log_to_geocoding,
            'routing': self._log_to_routing,
            'gpx': self._log_to_gpx,
            'service': self._log_to_service
        }

        self.service_manager = ServiceManager(self.logger_callbacks)

        if self.logger is not None:
            self.service_manager.initialize_windows_location_service()

        self.window_manager = WindowManager(self, WINDOW_TITLE, WINDOW_SIZE)
        self.ui_updater = {}

        from version import __version__ as current_version
        self.update_manager = UpdateManager(current_version, self.logger, main_window=self)

        print("管理器初始化完成")

    def _init_window(self):
        print("开始初始化窗口设置")
        self.window_manager.setup_window()
        self._create_menu_bar()
        print("窗口设置初始化完成")

    def _init_services(self):
        print("开始初始化服务")
        map_config._load_config()
        self.service_manager.initialize_services()
        print("服务初始化完成")

    def _init_signals(self):
        from core.signals import SignalManager
        from modules.geolocation import GeolocationHandler
        print("开始初始化信号系统")
        self.signal_manager = SignalManager()
        self.geolocation_handler = GeolocationHandler(signal_manager=self.signal_manager)

        if self.update_manager is not None:
            self.update_manager.update_available.connect(self._on_update_available)
            self.update_manager.update_downloaded.connect(self._on_update_downloaded)
            self.update_manager.update_error.connect(self._on_update_error)

        print("信号系统初始化完成")

    def _init_ui(self):
        from ui.popups.map_context_menu_popup import MapContextMenuPopup
        self._create_map_view()
        self.init_ui()

        self.map_context_menu = MapContextMenuPopup(self)
        self.map_context_menu.set_as_start.connect(self._on_context_menu_set_start_new)
        self.map_context_menu.set_as_via.connect(self._on_context_menu_add_waypoint_new)
        self.map_context_menu.set_as_end.connect(self._on_context_menu_set_end_new)
        self.map_context_menu.query_here.connect(self._on_context_menu_query_here)
        self.map_context_menu.add_favorite.connect(self._on_context_menu_add_favorite)
        self.map_context_menu.set_center.connect(self._on_context_menu_set_center)
        self.map_context_menu.clear_route.connect(self._on_context_menu_clear_route)

        self._init_search_popups()
        self._init_settings_popups()
        self._init_location_info_popup()
        self._init_route_plan_panel()

    def _init_search_popups(self):
        try:
            from modules.search import SearchHistoryPopup
            from modules.search import SearchResultsPopup
            # 注入 map_manager 供弹窗查询收藏状态（按钮初始金色/灰色）
            map_manager = getattr(self, 'map_manager', None)
            self.search_history_popup = SearchHistoryPopup(self, map_manager=map_manager)
            self.search_history_popup.history_selected.connect(self._on_history_selected)
            self.search_history_popup.favorite_requested.connect(self._on_favorite_requested)
            self.search_history_popup.my_location_clicked.connect(self._on_search_history_my_location)
            self.search_results_popup = SearchResultsPopup(self, map_manager=map_manager)
            self.search_results_popup.result_selected.connect(self._on_result_selected)
            self.search_results_popup.favorite_requested.connect(self._on_favorite_requested)
        except ImportError as e:
            (self.logger or print)(f"无法导入搜索弹出面板: {e}") if self.logger else print(f"无法导入搜索弹出面板: {e}")

    def _init_settings_popups(self):
        try:
            from ui.popups.settings_popup import MapSettingsPopup, LogSettingsPopup, AboutPopup
            self.map_settings_popup = MapSettingsPopup(self)
            self.map_settings_popup.config_saved.connect(self._on_map_config_saved)
            self.map_settings_popup.closed.connect(self._on_map_settings_popup_closed)
            self.log_settings_popup = LogSettingsPopup(self)
            self.about_popup = AboutPopup(self)
        except ImportError as e:
            print(f"无法导入设置弹出面板: {e}")

    def _init_location_info_popup(self):
        try:
            from ui.popups.location_info_popup import LocationInfoPopup
            self.location_info_popup = LocationInfoPopup(self)
        except ImportError as e:
            print(f"无法导入位置信息弹出面板: {e}")

    def _init_route_plan_panel(self):
        try:
            from modules.routing import RoutePlanPanel
            from modules.routing import RouteHistoryStorage

            self.route_history_storage = RouteHistoryStorage()
            self.route_plan_panel = RoutePlanPanel(
                self, geo_info_storage=getattr(self, 'geo_info_storage', None))
            self.route_plan_panel.cancel_clicked.connect(self._on_route_panel_cancel)
            self.route_plan_panel.locate_requested.connect(self._on_route_panel_locate)
            self.route_plan_panel.plan_route_clicked.connect(self._on_route_plan_clicked)
            self.route_plan_panel.clear_route_clicked.connect(self._on_route_clear_clicked)
            self.route_plan_panel.switch_start_end_clicked.connect(self._on_route_switch_start_end)
            self.route_plan_panel.search_location_clicked.connect(self._on_route_location_search)
            self.route_plan_panel.address_selected.connect(self._on_route_address_selected)
            self.route_plan_panel.history_selected.connect(self._on_route_history_selected)
            self.route_plan_panel.route_alternative_selected.connect(self._on_route_alternative_selected)
            self.route_plan_panel.export_gpx_clicked.connect(self._on_export_gpx_clicked)
            self.route_plan_panel.history_export_gpx_clicked.connect(self._on_history_export_gpx_clicked)
            self.route_plan_panel.history_delete_clicked.connect(self._on_history_delete_clicked)
            self.route_plan_panel.history_clear_all_clicked.connect(self._on_history_clear_all_clicked)
        except ImportError as e:
            print(f"无法导入路线规划面板: {e}")

    # ------------------------------------------------------------------ #
    #  地图视图创建                                                        #
    # ------------------------------------------------------------------ #

    def _recreate_map_view(self):
        from modules.map import ConsoleWebEnginePage
        try:
            self.logger.info("开始重新创建地图视图")
            self.map_view = QWebEngineView(self)
            self.web_page = ConsoleWebEnginePage(signal_manager=self.signal_manager)
            self.web_page.set_geolocation_handler(self.geolocation_handler)
            self.map_view.setPage(self.web_page)
            if self._widget_refs is not None:
                self._widget_refs.append(self.map_view)
            self.map_manager.map_view = self.map_view
            self.map_view.show()
            self._sync_road_button_state()
            self.logger.info(f"成功重新创建地图视图: {id(self.map_view)}")
            return True
        except Exception as e:
            self.logger.error(f"重新创建地图视图失败: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

    def _create_map_view(self):
        from modules.map import ConsoleWebEnginePage
        QApplication.processEvents()
        self.map_view = QWebEngineView(self)
        if self._widget_refs is None:
            self._widget_refs = []
        self._widget_refs.append(self.map_view)
        self.web_page = ConsoleWebEnginePage(signal_manager=self.signal_manager)
        self.web_page.set_geolocation_handler(self.geolocation_handler)
        self.map_view.setPage(self.web_page)
        QApplication.processEvents()

    # ------------------------------------------------------------------ #
    #  日志 & 任务管理器初始化                                             #
    # ------------------------------------------------------------------ #

    def _init_logging(self):
        from ui.panels.log_panel import setup_logger
        from core.background_task import TaskManager
        print("开始初始化日志系统")
        self.logger = setup_logger(None, "GpxStudio")
        self.task_manager = TaskManager(self.logger)
        self._connect_task_manager_signals()
        self.logger.debug("日志系统初始化完成")

    def _init_popup_management(self):
        print("开始初始化弹出面板管理")
        self.active_popups = []
        self.installEventFilter(self)
        self.last_window_geometry = self.geometry()
        print("弹出面板管理初始化完成")

    def _init_functional_managers(self):
        from ..managers import (LocationManager, MapManager, SearchManager,
                               RouteManager, TimeManager)
        from ui.viewmodels import AppViewModel
        print("开始初始化功能管理器")

        self.app_viewmodel = AppViewModel(self)
        self.app_viewmodel.search_vm.results_changed.connect(self._show_search_results_dropdown)
        self.app_viewmodel.map_vm.loading_changed.connect(self._on_map_loading_changed)

        self._build_ui_updater()

        self.location_manager = LocationManager(
            self.service_manager, self.data_manager,
            self.ui_updater, self.logger, self.task_manager
        )
        self.map_manager = MapManager(
            self.data_manager, self.map_view, self.logger, self._recreate_map_view
        )
        self.search_manager = SearchManager(
            self.service_manager, self.data_manager,
            self.ui_updater, self.logger, self.task_manager,
            search_viewmodel=self.app_viewmodel.search_vm,
            geo_storage=getattr(self, 'geo_info_storage', None)
        )
        self.route_manager = RouteManager(
            self.service_manager, self.data_manager,
            self.ui_updater, self.logger, self.task_manager,
            route_history_storage=self.route_history_storage
        )
        self.time_manager = TimeManager(
            self.data_manager, self.ui_updater, self.logger
        )

        from app.managers.task_event_handler import TaskEventHandler
        self.task_event_handler = TaskEventHandler(
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
            route_plan_panel_getter=lambda: self.route_plan_panel,
            parent=self,
        )
        self._rewire_task_signals()
        print("功能管理器初始化完成")

    def _build_ui_updater(self):
        """构建类型化 UI 回调对象（UICallbacks），替代原 ui_updater 字典。"""
        self.ui_updater = UICallbacks(
            main_window=self,
            show_warning=self._show_warning,
            show_info=self._show_info,
            set_progress_indeterminate=self._set_progress_indeterminate,
            set_progress_complete=self._set_progress_complete,
            set_progress=self._set_progress,
            clear_results=self._clear_results,
            clear_results_list=self._clear_results_list,
            add_result=self._add_result,
            set_results_title=self._set_results_title,
            show_search_results=self._show_search_results,
            show_search_results_on_map=self._show_search_results_on_map,
            show_search_results_dropdown=self._show_search_results_dropdown,
            update_location_display=self._update_location_display,
            update_start_from_search=self._update_start_from_search,
            update_end_from_search=self._update_end_from_search,
            add_waypoint_to_list=self._add_waypoint_to_list,
            update_map_preview=self._update_map_preview,
            preview_search_result=self._preview_search_result,
            show_location_on_map=self._show_location_on_map,
            show_route_on_map=self._show_route_on_map,
            load_map_url=self._load_map_url,
            trigger_browser_location=self._trigger_browser_location,
            get_start_time=lambda: self.start_time_edit.dateTime(),
            set_start_time=lambda dt: self.start_time_edit.setDateTime(dt),
            get_end_time=lambda: self.end_time_edit.dateTime(),
            set_end_time=lambda dt: self.end_time_edit.setDateTime(dt),
            get_duration=lambda: self.duration_time_edit.text(),
            set_duration=lambda text: self.duration_time_edit.setText(text),
            get_transport_mode=lambda: self.transport_combo.currentText(),
            hide_time_panel=lambda: self.time_panel.hide() if self.time_panel is not None and self.time_panel.isVisible() else None,
            hide_date_panel=lambda: self.date_panel.hide() if self.date_panel is not None and self.date_panel.isVisible() else None,
            setup_date_panel_callback=self._setup_date_panel_callback,
            setup_time_panel_callback=self._setup_time_panel_callback,
            show_date_panel=self._show_date_panel,
            show_time_panel=self._show_time_panel,
            add_route_time_info=self._add_route_time_info,
            show_route_alternatives=self._show_route_alternatives,
            save_route_history=self._save_route_history,
        )

    # ------------------------------------------------------------------ #
    #  信号连接                                                            #
    # ------------------------------------------------------------------ #

    def _connect_signals(self):
        self.signal_manager.geolocation_success.connect(self._on_geolocation_success)
        self.signal_manager.geolocation_error.connect(self._on_geolocation_error)
        self.signal_manager.map_zoom_changed.connect(self.on_map_zoom_changed)
        self.signal_manager.map_center_changed.connect(self.on_map_center_changed)
        self.signal_manager.map_right_click.connect(self._on_map_right_click)
        self.signal_manager.map_middle_double_click.connect(self._on_map_middle_double_click)
        self.signal_manager.map_loaded.connect(self._on_map_loaded)
        self.signal_manager.favorite_delete_requested.connect(self._on_favorite_delete_requested)
        self.signal_manager.location_marker_hidden.connect(self._on_location_marker_hidden)
        self.signal_manager.location_favorite_requested.connect(self._on_location_favorite_requested)

    def _connect_task_manager_signals(self):
        self.task_manager.task_started.connect(self._on_task_started)
        self.task_manager.task_progress.connect(self._on_task_progress)
        self.task_manager.task_completed.connect(self._on_task_completed)
        self.task_manager.task_failed.connect(self._on_task_failed)
        self.task_manager.task_cancelled.connect(self._on_task_cancelled)
        self.task_manager.task_log.connect(self._on_task_log)

    def _rewire_task_signals(self):
        if not hasattr(self, 'task_event_handler') or self.task_event_handler is None:
            return
        try:
            self.task_manager.task_started.disconnect(self._on_task_started)
            self.task_manager.task_progress.disconnect(self._on_task_progress)
            self.task_manager.task_completed.disconnect(self._on_task_completed)
            self.task_manager.task_failed.disconnect(self._on_task_failed)
            self.task_manager.task_cancelled.disconnect(self._on_task_cancelled)
            self.task_manager.task_log.disconnect(self._on_task_log)
        except (RuntimeError, TypeError):
            pass
        h = self.task_event_handler
        self.task_manager.task_started.connect(h.on_task_started)
        self.task_manager.task_progress.connect(h.on_task_progress)
        self.task_manager.task_completed.connect(h.on_task_completed)
        self.task_manager.task_failed.connect(h.on_task_failed)
        self.task_manager.task_cancelled.connect(h.on_task_cancelled)
        self.task_manager.task_log.connect(h.on_task_log)

    # ------------------------------------------------------------------ #
    #  日志回调                                                            #
    # ------------------------------------------------------------------ #

    def _log_to_service(self, level: str, message: str):
        self._log_with_prefix("Windows定位", level, message)

    def _log_to_geocoding(self, level: str, message: str):
        self._log_with_prefix("地理编码", level, message)

    def _log_to_routing(self, level: str, message: str):
        self._log_with_prefix("路线规划", level, message)

    def _log_to_gpx(self, level: str, message: str):
        self._log_with_prefix("GPX导出", level, message)

    def _log_with_prefix(self, prefix: str, level: str, message: str):
        if self.logger is None:
            return
        level_map = {
            "DEBUG": self.logger.debug, "INFO": self.logger.info,
            "WARNING": self.logger.warning, "ERROR": self.logger.error,
            "CRITICAL": self.logger.critical
        }
        level_map.get(level, self.logger.info)(f"[{prefix}] {message}")

    # ------------------------------------------------------------------ #
    #  UI 搭建                                                             #
    # ------------------------------------------------------------------ #

    def _create_menu_bar(self):
        """创建菜单栏（暂为空）"""
        pass

    def init_ui(self):
        """初始化用户界面 — 仅显示地图"""
        from ..constants import MAP_LOAD_DELAY_MS
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self._init_hidden_ui_components()
        map_panel = self.create_map_panel()
        main_layout.addWidget(map_panel)
        QTimer.singleShot(MAP_LOAD_DELAY_MS + 2000, self._show_initial_map)

    def create_map_panel(self):
        """创建地图面板（铺满整个界面）。按钮逻辑由 MapToolbar 负责。"""
        from ui.widgets.map_toolbar import MapToolbar
        from ui.popups.popup_positioner import PopupPositioner

        map_widget = QWidget()
        layout = QVBoxLayout(map_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        profile = QWebEngineProfile.defaultProfile()
        profile.setHttpUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        map_container = QWidget()
        map_container_layout = QVBoxLayout(map_container)
        map_container_layout.setContentsMargins(0, 0, 0, 0)
        map_container_layout.setSpacing(0)

        try:
            if self.map_view is None:
                print("[调试] map_view不存在，重新创建")
                self._create_map_view()
            _ = self.map_view.size()
            print(f"[调试] map_view有效: {id(self.map_view)}")
        except (RuntimeError, AttributeError) as e:
            print(f"[调试] map_view无效: {e}，重新创建")
            self._create_map_view()

        self.map_view.setParent(map_container)
        map_container_layout.addWidget(self.map_view)

        self.map_container = map_container
        toolbar = MapToolbar(app=self, map_container=map_container, control_height=36)
        toolbar.copy_refs_to_app()
        self.map_toolbar = toolbar

        map_container.resizeEvent = lambda a0: PopupPositioner.update_button_positions(
            map_container, toolbar
        )

        layout.addWidget(map_container)
        return map_widget

    # ------------------------------------------------------------------ #
    #  窗口事件                                                            #
    # ------------------------------------------------------------------ #

    def moveEvent(self, event):
        super().moveEvent(event)
        if (self.logger is not None and
                self.search_container is not None and
                self.route_plan_panel is not None):
            self._update_route_panel_position()
        self._update_search_popups_position()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if (self.logger is not None and
                self.search_container is not None and
                self.route_plan_panel is not None):
            self._update_route_panel_position()
        self._update_search_popups_position()

    def _update_route_panel_position(self):
        from ui.popups.popup_positioner import PopupPositioner
        PopupPositioner.update_route_panel_position(
            getattr(self, 'route_plan_panel', None),
            getattr(self, 'search_container', None),
            getattr(self, 'gpx_export_popup', None),
            self.logger,
        )

    def _update_search_popups_position(self):
        """主窗口移动/缩放后，按搜索容器锚点重算下拉弹窗位置
        （搜索历史/搜索结果/收藏夹三弹窗共用公式，与路线面板同构）"""
        from ui.popups.popup_positioner import PopupPositioner
        PopupPositioner.update_search_popups_position(
            getattr(self, 'search_history_popup', None),
            getattr(self, 'search_results_popup', None),
            getattr(self, 'search_container', None),
            self.logger,
            favorites_popup=getattr(self, 'favorites_popup', None),
        )

    def _update_button_positions(self, container):
        from ui.popups.popup_positioner import PopupPositioner
        toolbar = getattr(self, 'map_toolbar', None)
        PopupPositioner.update_button_positions(container, toolbar)

    def on_zoom_in_clicked(self):
        self.logger.info("[缩放] 放大按钮点击")
        if self.map_view and self.map_view.page():
            MapJsBridge.zoom_in(self.map_view.page())
        else:
            self.logger.warning("[缩放] 地图视图或页面不存在")

    def on_zoom_out_clicked(self):
        self.logger.info("[缩放] 缩小按钮点击")
        if self.map_view and self.map_view.page():
            MapJsBridge.zoom_out(self.map_view.page())
        else:
            self.logger.warning("[缩放] 地图视图或页面不存在")

    def closeEvent(self, event):
        self.window_manager.handle_close_event(event)

    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
        if obj == self:
            if event.type() == QEvent.WindowDeactivate:
                if self.gpx_export_popup is not None and self.gpx_export_popup.isVisible():
                    if hasattr(self.gpx_export_popup, 'picker_popup') and self.gpx_export_popup.picker_popup and self.gpx_export_popup.picker_popup.isVisible():
                        return super().eventFilter(obj, event)
                self._close_all_popups()
            elif event.type() == QEvent.WindowActivate:
                # 收藏夹弹窗展开时，用户点击回主窗口（地图/其他区域）→ 弹窗自动关闭
                favorites_popup = getattr(self, 'favorites_popup', None)
                if favorites_popup is not None and favorites_popup.isVisible():
                    favorites_popup.hide()
            elif event.type() == QEvent.Move:
                self._update_popup_positions()
            elif event.type() == QEvent.Resize:
                self._update_popup_positions()
        return super().eventFilter(obj, event)

    # ------------------------------------------------------------------ #
    #  弹出面板管理                                                        #
    # ------------------------------------------------------------------ #

    def _register_popup(self, popup):
        if popup not in self.active_popups:
            self.active_popups.append(popup)
            if hasattr(popup, 'closed'):
                popup.closed.connect(lambda: self._unregister_popup(popup))

    def _unregister_popup(self, popup):
        if popup in self.active_popups:
            self.active_popups.remove(popup)

    def _close_all_popups(self):
        for popup in self.active_popups[:]:
            if popup and popup.isVisible():
                popup.hide()

    def _update_popup_positions(self):
        current_geometry = self.geometry()
        if self.last_window_geometry is not None:
            dx = current_geometry.x() - self.last_window_geometry.x()
            dy = current_geometry.y() - self.last_window_geometry.y()
            for popup in self.active_popups:
                if popup and popup.isVisible():
                    popup.move(popup.pos() + QPoint(dx, dy))
        self.last_window_geometry = current_geometry

    # ------------------------------------------------------------------ #
    #  加载动画                                                            #
    # ------------------------------------------------------------------ #

    def show_loading(self):
        if self.app_viewmodel is not None:
            self.app_viewmodel.map_vm.set_loading(True)
        else:
            self._do_show_loading()

    def hide_loading(self):
        if self.app_viewmodel is not None:
            self.app_viewmodel.map_vm.set_loading(False)
        else:
            self._do_hide_loading()

    def _on_map_loading_changed(self, loading: bool):
        if loading:
            self._do_show_loading()
        else:
            self._do_hide_loading()

    def _do_show_loading(self):
        if not self.is_loading:
            self.is_loading = True
            self.loading_rotation = 0
            self.loading_timer.start(50)
            self.loading_button.setToolTip("正在加载...")
            self.logger.debug("[加载] 开始加载动画")

    def _do_hide_loading(self):
        self.logger.debug(f"[加载] hide_loading被调用 - is_loading={self.is_loading}")
        if self.is_loading:
            self.is_loading = False
            self.loading_timer.stop()
            self.loading_rotation = 0
            self.loading_button.update()
            self.loading_button.setToolTip("加载状态指示器")
            self.logger.debug("[加载] 停止加载动画")
        else:
            self.loading_timer.stop()
            self.loading_rotation = 0
            self.loading_button.update()

    def _reset_loading_icon(self):
        pass

    def _animate_loading(self):
        if not self.is_loading:
            return
        self.loading_rotation = (self.loading_rotation + 15) % 360
        self.loading_button.update()

    def start_loading_animation(self):
        self.show_loading()

    def stop_loading_animation(self):
        self.hide_loading()

    # ------------------------------------------------------------------ #
    #  公共路线/时间辅助                                                   #
    # ------------------------------------------------------------------ #

    def calculate_times(self):
        self.time_manager.calculate_times()

    def clear_route_data(self):
        self.data_manager.clear_all_route_data()
        if self.start_label is not None:
            self.start_label.setText('')
        if self.end_label is not None:
            self.end_label.setText('')
        if self.start_list is not None:
            self.start_list.clear()
        if self.end_list is not None:
            self.end_list.clear()
        if self.waypoint_list is not None:
            self.waypoint_list.clear()
        if self.search_results_list is not None:
            self.search_results_list.clear()
        if self.search_results_title is not None:
            self.search_results_title.setText("搜索结果")
        self.logger.info("已清空所有路线相关数据")

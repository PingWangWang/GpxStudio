"""
GPX Studio 主应用窗口 (重构版)
使用管理器模式，提高代码的可复用性、可维护性、可扩展性
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QListWidget, QFileDialog,
                             QMessageBox, QSplitter, QListWidgetItem, QScrollArea,
                             QApplication, QDialog, QTimeEdit, QMenuBar, QMenu, QAction,
                             QComboBox, QLineEdit)
from PyQt5.QtCore import Qt, QTimer, QSize, QPoint
from PyQt5.QtGui import QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile

import sys
import os
from typing import Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.ui_callbacks import UICallbacks

# 确保日志重定向生效 - 必须在其他导入之前执行
import core.logging_setup

# 导入信号管理器
from core.signals import SignalManager

# 导入模块
from modules.geolocation import GeolocationHandler
from modules.map import ConsoleWebEnginePage
from modules.map import MapRenderer
from modules.map import MapJsBridge
from services.config.map_config import map_config
from ui.icons.icon_manager import create_icon_button

# 导入UI组件
from ui.styles import UIStyles
from ui.panels.panel_factory import PanelFactory
from ui.panels.log_panel import LogPanel, setup_logger
from ui.panels.scale_panel import ScalePanel
from ui.popups.map_context_menu_popup import MapContextMenuPopup
from ui.layout.layout_manager import LayoutManager

# 导入常量
from .constants import (
    WINDOW_TITLE, WINDOW_SIZE, MAP_LOAD_DELAY_MS
)

# 导入管理器
from .managers import (
    WindowManager, ServiceManager, DataManager,
    LocationManager, SearchManager, MapManager,
    RouteManager, TimeManager, UpdateManager
)

# 导入 ViewModel 层
from ui.viewmodels import AppViewModel

# 导入 Mixin
from .mixins import (
    InitMixin, HiddenUIMixin, SearchMixin, UICallbacksMixin,
    MapMixin, TaskMixin, RouteMixin, GpxExportMixin,
    ContextMenuMixin, UpdateMixin,
)


class GpxStudio(InitMixin, HiddenUIMixin, SearchMixin, UICallbacksMixin,
                MapMixin, TaskMixin, RouteMixin, GpxExportMixin,
                ContextMenuMixin, UpdateMixin,
                QMainWindow):
    """GPX Studio 主应用窗口（重构版）"""

    # ==================== 类型注解（替代 hasattr 防御）====================
    # 管理器
    logger: Any
    task_manager: Any
    data_manager: Any
    service_manager: Any
    window_manager: Any
    map_manager: Any
    search_manager: Any
    route_manager: Any
    location_manager: Any
    time_manager: Any
    update_manager: Any
    signal_manager: Any
    geolocation_handler: Any
    route_history_storage: Any
    # UI 组件
    map_view: Any
    web_page: Any
    map_context_menu: Any
    search_container: Any
    route_plan_panel: Any
    gpx_export_popup: Any
    search_history_popup: Any
    search_input: Any
    search_results_popup: Any
    start_label: Any
    end_label: Any
    start_list: Any
    end_list: Any
    waypoint_list: Any
    search_results_list: Any
    search_results_title: Any
    road_overlay_button: Any
    route_button: Any
    log_settings_popup: Any
    about_popup: Any
    map_settings_popup: Any
    scale_panel: Any
    scale_info_label: Any
    time_panel: Any
    date_panel: Any
    location_info_popup: Any
    center_point_marker: Optional[tuple]
    # 内部状态
    splash_screen: Any
    _widget_refs: Optional[list]
    _pending_export_history: Any
    _current_route_info: Optional[dict]
    last_window_geometry: Any
    logger_callbacks: Optional[dict]
    active_popups: Optional[list]
    ui_updater: Optional["UICallbacks"]

    def __init__(self, splash_screen=None):
        """
        初始化主窗口

        Args:
            splash_screen: 启动画面实例，用于更新加载进度
        """
        super().__init__()
        # 声明所有属性为 None，消除 hasattr 防御性代码
        self._init_null_attributes()
        self.splash_screen = splash_screen

        print("=" * 80)
        print("GPX Studio 程序启动开始（重构版）")
        print("=" * 80)

        # 初始化数据目录（最先执行）
        from .data_paths import init_data_directories
        init_data_directories()

        # 初始化各个部分（进度范围：10-95，为启动和完成阶段留出空间）
        self._update_splash(15, "正在初始化日志系统...")
        self._init_logging()

        self._update_splash(30, "正在初始化管理器...")
        self._init_managers()

        self._update_splash(45, "正在设置窗口...")
        self._init_window()

        self._update_splash(60, "正在初始化服务...")
        self._init_services()

        self._update_splash(70, "正在初始化信号系统...")
        self._init_signals()

        self._update_splash(80, "正在初始化弹出面板管理...")
        self._init_popup_management()

        self._update_splash(90, "正在加载用户界面...")
        self._init_ui()

        self._update_splash(92, "正在初始化功能管理器...")
        self._init_functional_managers()

        self._update_splash(94, "正在连接信号...")
        self._connect_signals()

        self._update_splash(95, "准备就绪...")

        # 启动完成
        self.logger.info("=" * 80)
        self.logger.info("GPX Studio 程序启动完成")
        self.logger.info("=" * 80)

        # 标记首次启动完成
        from core.logging_setup import mark_first_run_completed
        mark_first_run_completed()

        # 启动定时检查更新的任务
        self.start_update_check()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GpxStudio()
    window.show()
    sys.exit(app.exec_())

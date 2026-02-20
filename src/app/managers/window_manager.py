"""
窗口和系统托盘管理器
负责窗口设置、图标、托盘图标等
"""

import os
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIcon
from core.resource_path import get_icon_path


class WindowManager:
    """窗口和系统托盘管理器
    
    负责窗口设置和系统托盘功能：
    - 窗口标题和大小设置
    - 窗口图标管理
    - 窗口居中显示
    - 系统托盘图标初始化和管理
    - 窗口关闭事件处理（最小化到托盘）
    """

    def __init__(self, main_window, window_title: str, window_size: tuple):
        """
        初始化窗口管理器

        参数:
            main_window: 主窗口实例
            window_title: 窗口标题
            window_size: 窗口大小 (width, height)
        """
        self.main_window = main_window
        self.window_title = window_title
        self.window_size = window_size
        self.app_icon = None
        self.tray_icon = None

    def setup_window(self):
        """设置窗口
        
        配置窗口的基本属性：
        - 设置窗口标题
        - 设置窗口大小
        - 配置窗口图标
        - 将窗口居中显示
        """
        print(f"设置窗口标题: {self.window_title}")
        self.main_window.setWindowTitle(self.window_title)

        print(f"设置窗口大小: {self.window_size}")
        self.main_window.resize(*self.window_size)

        # 设置窗口图标
        self._setup_icon()

        # 窗口居中
        self._center_window()

    def _setup_icon(self):
        """设置窗口图标（内部方法）
        
        加载窗口图标并设置到主窗口上，同时初始化系统托盘图标。
        """
        print("设置窗口图标")
        icon_path = get_icon_path()
        print(f"图标路径: {icon_path}")

        if os.path.exists(icon_path):
            self.app_icon = QIcon(icon_path)
            self.main_window.setWindowIcon(self.app_icon)
            print("窗口图标设置成功")

            # 初始化系统托盘图标
            self._init_tray_icon()
        else:
            print(f"警告: 图标文件不存在 - {icon_path}")
            self.app_icon = None

    def _center_window(self):
        """窗口居中（内部方法）
        
        计算屏幕中心点，将窗口移动到屏幕中央。
        """
        print("开始窗口居中操作")
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        print(f"屏幕几何信息: {screen_geometry}")

        window_geometry = self.main_window.frameGeometry()
        center_point = screen_geometry.center()
        print(f"屏幕中心点: {center_point}")

        window_geometry.moveCenter(center_point)
        print(f"窗口居中后的位置: {window_geometry.topLeft()}")
        self.main_window.move(window_geometry.topLeft())
        print("窗口居中操作完成")

    def _init_tray_icon(self):
        """初始化系统托盘图标（内部方法）
        
        创建系统托盘图标并设置上下文菜单，支持显示/隐藏窗口和退出程序功能。
        """
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("系统不支持系统托盘")
            return

        print("初始化系统托盘图标")

        # 创建系统托盘图标
        self.tray_icon = QSystemTrayIcon(self.main_window)
        if self.app_icon:
            self.tray_icon.setIcon(self.app_icon)

        # 创建托盘菜单
        tray_menu = QMenu()

        # 显示/隐藏窗口动作
        show_action = QAction("显示窗口", self.main_window)
        show_action.triggered.connect(self.show_window)
        tray_menu.addAction(show_action)

        hide_action = QAction("隐藏窗口", self.main_window)
        hide_action.triggered.connect(self.main_window.hide)
        tray_menu.addAction(hide_action)

        tray_menu.addSeparator()

        # 退出动作
        quit_action = QAction("退出程序", self.main_window)
        quit_action.triggered.connect(self.close_application)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)

        # 设置托盘图标工具提示
        self.tray_icon.setToolTip("GPX Studio - GPS路线规划工具")

        # 连接双击事件
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

        # 显示托盘图标
        self.tray_icon.show()
        print("系统托盘图标初始化完成")

    def show_window(self):
        """显示窗口
        
        显示并激活窗口，使其处于最上层。
        """
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()

    def on_tray_icon_activated(self, reason):
        """托盘图标激活事件处理
        
        处理托盘图标的各种事件，如双击显示窗口。
        
        参数:
            reason: 事件类型，如双击、右键点击等
        """
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()

    def close_application(self):
        """关闭应用程序
        
        隐藏托盘图标并退出应用程序。
        """
        print("[WindowManager] Closing application...")
        
        # 1. 先关闭所有弹出窗口和面板
        try:
            self._close_all_windows_and_panels()
        except Exception as e:
            print(f"[WindowManager] Error closing windows: {e}")
        
        # 2. 不再需要停止地图服务，因为已移除HTTP服务器
            
        # 3. 隐藏托盘图标
        if self.tray_icon:
            self.tray_icon.hide()
        
        # 4. 关闭主窗口
        try:
            print("[WindowManager] Closing main window...")
            self.main_window.close()
        except Exception as e:
            print(f"[WindowManager] Error closing main window: {e}")
            
        print("[WindowManager] Quitting QApplication...")
        QApplication.quit()
        
        # 5. 确保进程退出（如果QApplication.quit()没有生效）
        import sys
        QTimer.singleShot(500, lambda: sys.exit(0))

    def _close_all_windows_and_panels(self):
        """关闭所有弹出窗口和面板
        
        包括：路线规划面板、GPX导出面板、搜索弹出窗口、设置弹出窗口等
        """
        print("[WindowManager] Closing all windows and panels...")
        
        # 关闭路线规划面板
        if hasattr(self.main_window, 'route_plan_panel'):
            try:
                if self.main_window.route_plan_panel and self.main_window.route_plan_panel.isVisible():
                    print("[WindowManager] Closing route plan panel...")
                    self.main_window.route_plan_panel.hide()
                    self.main_window.route_plan_panel.deleteLater()
            except Exception as e:
                print(f"[WindowManager] Error closing route plan panel: {e}")
        
        # 关闭GPX导出面板及其子窗口
        if hasattr(self.main_window, 'gpx_export_popup'):
            try:
                if self.main_window.gpx_export_popup and self.main_window.gpx_export_popup.isVisible():
                    print("[WindowManager] Closing GPX export popup...")
                    # 先关闭时间日期选择器子窗口
                    if hasattr(self.main_window.gpx_export_popup, 'picker_popup'):
                        if self.main_window.gpx_export_popup.picker_popup and self.main_window.gpx_export_popup.picker_popup.isVisible():
                            print("[WindowManager] Closing datetime picker...")
                            self.main_window.gpx_export_popup.picker_popup.hide()
                            self.main_window.gpx_export_popup.picker_popup.deleteLater()
                    # 再关闭GPX导出面板
                    self.main_window.gpx_export_popup.hide()
                    self.main_window.gpx_export_popup.deleteLater()
            except Exception as e:
                print(f"[WindowManager] Error closing GPX export popup: {e}")
        
        # 关闭所有注册的弹出窗口
        if hasattr(self.main_window, 'active_popups'):
            try:
                for popup in self.main_window.active_popups[:]:
                    if popup and popup.isVisible():
                        print(f"[WindowManager] Closing popup: {popup.__class__.__name__}")
                        popup.hide()
                        popup.deleteLater()
            except Exception as e:
                print(f"[WindowManager] Error closing popups: {e}")
        
        # 关闭搜索相关弹出窗口和其他弹出窗口
        popup_attrs = ['search_history_popup', 'search_results_popup', 
                       'map_settings_popup', 'log_settings_popup', 'about_popup',
                       'map_context_menu']
        for attr in popup_attrs:
            if hasattr(self.main_window, attr):
                try:
                    popup = getattr(self.main_window, attr)
                    if popup and popup.isVisible():
                        print(f"[WindowManager] Closing {attr}...")
                        popup.hide()
                        popup.deleteLater()
                except Exception as e:
                    print(f"[WindowManager] Error closing {attr}: {e}")
        
        print("[WindowManager] All windows and panels closed")
    
    def handle_close_event(self, event):
        """处理关闭事件
        
        当用户点击窗口关闭按钮时，根据配置决定是退出还是隐藏到托盘。
        
        参数:
            event: 关闭事件对象
        """
        from services.config.map_config import map_config
        
        close_action = map_config.get_close_action()
        print(f"[WindowManager] 处理关闭事件 - 配置动作: {close_action}")
        
        if close_action == 'hide' and QSystemTrayIcon.isSystemTrayAvailable():
            # 隐藏窗口而不是退出
            event.ignore()
            self.main_window.hide()
            # 可以选择性显示气泡提示
            # self.tray_icon.showMessage("GPX Studio", "应用程序已最小化到系统托盘", QSystemTrayIcon.Information, 2000)
        else:
            # 直接接受关闭事件，退出应用程序
            event.accept()
            # 显式调用退出函数，确保完全退出（包括销毁托盘、停止后台线程等）
            self.close_application()

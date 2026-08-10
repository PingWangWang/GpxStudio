"""
地图工具栏组件

封装地图面板上所有浮动控件的创建逻辑：
- 右侧按钮组容器（地图模式、路网、设置、日志、关于、放大、缩小、定位、适配、加载指示器）
- 左上角搜索容器（搜索框、搜索按钮、路线按钮、关闭按钮）
- 左下角比例尺标签
- 路网悬浮按钮（绝对定位）

使用方法
--------
在 ``create_map_panel()`` 中实例化，控件作为子控件添加到 map_container 中：

    toolbar = MapToolbar(app=self, map_container=map_container, control_height=36)
    # app 中直接引用：
    self.search_input   = toolbar.search_input
    self.zoom_in_button = toolbar.zoom_in_button
    ...
"""

from PyQt5.QtWidgets import (
    QPushButton, QWidget, QLabel, QLineEdit,
    QHBoxLayout, QVBoxLayout,
)
from PyQt5.QtCore import QTimer
from ui.theme import theme


class MapToolbar:
    """地图面板工具栏 — 负责在 map_container 内创建所有浮动控件。

    创建后，各控件引用附属在此对象上；主窗口按需拷贝引用。
    控件的位置由外部的 ``PopupPositioner.update_button_positions()`` 管理。
    """

    _BUTTON_STYLE = """
        QPushButton {
            background-color: transparent;
            border: none;
            border-radius: 4px;
            padding: 0px;
            font-size: 18px;
        }
        QPushButton:hover { background-color: __HOVER__; }
        QPushButton:pressed { background-color: __HOVER_STRONG__; }
    """

    def __init__(self, app, map_container: QWidget, control_height: int = 36):
        self._app = app
        self._h = control_height
        self._container = map_container

        self._build_right_buttons()
        self._build_search_container()
        self._build_scale_label()
        self._build_road_overlay_button()
        self._setup_loading_button()

    # ──────────────────────────────────────────────────────────────────
    # 右侧按钮组
    # ──────────────────────────────────────────────────────────────────

    def _build_right_buttons(self):
        h = self._h
        ctr = self._container

        self.right_buttons_container = QWidget()
        self.right_buttons_container.setParent(ctr)
        theme.set_theme_stylesheet(self.right_buttons_container, """
            QWidget {
                background-color: __PANEL_BG__;
                border-radius: 6px;
                border: 1px solid __BORDER__;
            }
        """)
        layout = QVBoxLayout(self.right_buttons_container)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(5)

        from services.config.map_config import map_config

        # 地图模式（卫星/街道）
        self.map_mode_button = self._make_btn("🗺️", "切换地图模式（卫星/街道）", h, checkable=True)
        theme.apply_to_sub(self.map_mode_button, """
            QPushButton {
                background-color: transparent; border: none;
                border-radius: 4px; padding: 0px; font-size: 18px;
            }
            QPushButton:hover { background-color: __HOVER__; }
            QPushButton:pressed { background-color: __HOVER_STRONG__; }
            QPushButton:checked { background-color: __ACCENT__; border: 1px solid __ACCENT__; }
        """)
        self.map_mode_button.setChecked(map_config.get_map_mode() == 'satellite')
        self.map_mode_button.enterEvent = lambda e: self._app.on_map_mode_button_enter()
        self.map_mode_button.leaveEvent = lambda e: self._app.on_map_mode_button_leave()
        self.map_mode_button.clicked.connect(self._app.on_map_mode_toggled)
        layout.addWidget(self.map_mode_button)

        # 地图设置
        self.map_settings_button = self._make_btn("⚙️", "地图设置", h)
        self.map_settings_button.clicked.connect(self._app.on_map_settings_clicked)
        layout.addWidget(self.map_settings_button)

        # 日志
        self.log_settings_button = self._make_btn("📋", "日志设置", h)
        self.log_settings_button.clicked.connect(self._app.on_log_settings_clicked)
        layout.addWidget(self.log_settings_button)

        # 关于
        self.about_button = self._make_btn("ℹ️", "关于", h)
        self.about_button.clicked.connect(self._app.on_about_clicked)
        layout.addWidget(self.about_button)

        # 放大
        self.zoom_in_button = self._make_btn("➕", "放大", h)
        self.zoom_in_button.clicked.connect(self._app.on_zoom_in_clicked)
        layout.addWidget(self.zoom_in_button)

        # 缩小
        self.zoom_out_button = self._make_btn("➖", "缩小", h)
        self.zoom_out_button.clicked.connect(self._app.on_zoom_out_clicked)
        layout.addWidget(self.zoom_out_button)

        # 定位
        self.locate_button = self._make_btn("📍", "定位到当前位置", h)
        self.locate_button.clicked.connect(self._app.on_locate_clicked)
        layout.addWidget(self.locate_button)

        # 适配
        self.zoom_fit_button = self._make_btn("⏺️", "自动缩放以显示所有元素", h)
        self.zoom_fit_button.clicked.connect(self._app.on_zoom_fit_clicked)
        layout.addWidget(self.zoom_fit_button)

        # 加载指示器（正常状态显示静态图标，动画文本在 _setup_loading_button 中轮换）
        self.loading_button = self._make_btn("⏳", "加载状态指示器", h)
        layout.addWidget(self.loading_button)

    # ──────────────────────────────────────────────────────────────────
    # 路网悬浮按钮
    # ──────────────────────────────────────────────────────────────────

    def _build_road_overlay_button(self):
        from services.config.map_config import map_config
        h = self._h
        self.road_overlay_button = QPushButton(self._container)
        self.road_overlay_button.setText("🛣️")
        self.road_overlay_button.setToolTip("路网")
        self.road_overlay_button.setFixedSize(h, h)
        theme.apply_to_sub(self.road_overlay_button, """
            QPushButton {
                background-color: __PANEL_BG__; border: 1px solid __BORDER__;
                border-radius: 6px; padding: 0px; font-size: 18px;
            }
            QPushButton:hover { background-color: __HOVER__; }
            QPushButton:pressed { background-color: __HOVER_STRONG__; }
            QPushButton:checked { background-color: __ACCENT__; border: 1px solid __ACCENT__; }
        """)
        self.road_overlay_button.setCheckable(True)
        self.road_overlay_button.setChecked(map_config.get_satellite_show_roads())
        self.road_overlay_button.clicked.connect(self._app.on_road_overlay_toggled)
        self.road_overlay_button.enterEvent = lambda e: self._app.on_road_button_enter()
        self.road_overlay_button.leaveEvent = lambda e: self._app.on_road_button_leave()
        self.road_overlay_button.hide()

    # ──────────────────────────────────────────────────────────────────
    # 比例尺标签
    # ──────────────────────────────────────────────────────────────────

    def _build_scale_label(self):
        self.scale_info_label = QLabel(self._container)
        theme.apply_to_sub(self.scale_info_label, """
            QLabel {
                background-color: __PANEL_BG__;
                border: 1px solid __BORDER__;
                border-radius: 4px; padding: 8px 12px;
                font-size: 12px; color: __TEXT__;
            }
        """)
        self.scale_info_label.setText("缩放级别: 10")

    # ──────────────────────────────────────────────────────────────────
    # 搜索容器
    # ──────────────────────────────────────────────────────────────────

    def _build_search_container(self):
        h = self._h
        ctr = self._container

        self.search_container = QWidget()
        self.search_container.setParent(ctr)
        theme.set_theme_stylesheet(self.search_container, """
            QWidget {
                background-color: __PANEL_BG__; border-radius: 6px;
                border: 1px solid __BORDER__;
            }
        """)
        layout = QHBoxLayout(self.search_container)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        # 搜索输入框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索地点...")
        theme.apply_to_sub(self.search_input, """
            QLineEdit {
                background-color: __INPUT_BG__; border: none; border-radius: 4px;
                padding: 0px 12px; font-size: 13px;
                color: __TEXT__;
                min-width: 250px; max-width: 250px;
            }
            QLineEdit:focus { background-color: __WINDOW_BG__; }
            QLineEdit::placeholder { color: __TEXT_TERTIARY__; }
        """)
        self.search_input.setFixedHeight(h)
        self.search_input.returnPressed.connect(self._app.on_search_button_clicked)
        self.search_input.textChanged.connect(self._app._on_search_input_text_changed)
        self.search_input.focusInEvent = self._app._on_search_input_focus_in
        self.search_input.focusOutEvent = self._app._on_search_input_focus_out
        self.search_input.mousePressEvent = self._app._on_search_input_mouse_press
        layout.addWidget(self.search_input)

        # 搜索按钮
        self.search_button = self._make_btn("🔍", "搜索", h)
        self.search_button.clicked.connect(self._app.on_search_button_clicked)
        layout.addWidget(self.search_button)

        # 路线按钮
        self.route_button = self._make_btn("🛣", "路线", h)
        self.route_button.clicked.connect(self._app.on_route_button_clicked)
        layout.addWidget(self.route_button)

        # 收藏夹按钮（点击展开收藏夹管理列表）
        self.favorites_button = self._make_btn("⭐", "收藏夹", h)
        self.favorites_button.clicked.connect(self._app.on_favorites_button_clicked)
        layout.addWidget(self.favorites_button)

        # 路线管理按钮（收藏夹右侧，点击展开路线管理列表）
        self.route_manager_button = self._make_btn("🗂", "路线管理", h)
        self.route_manager_button.clicked.connect(self._app.on_route_manager_button_clicked)
        layout.addWidget(self.route_manager_button)

        # 关闭按钮（初始隐藏）
        self.cancel_button = self._make_btn("❌", "关闭", h)
        self.cancel_button.clicked.connect(self._app.on_cancel_button_clicked)
        self.cancel_button.hide()
        layout.addWidget(self.cancel_button)

    # ──────────────────────────────────────────────────────────────────
    # 加载动画 paintEvent 覆盖
    # ──────────────────────────────────────────────────────────────────

    def _setup_loading_button(self):
        app = self._app

        # 加载动画定时器（存放在 app 上供其他方法访问）
        app.loading_timer = QTimer()
        app.loading_timer.timeout.connect(app._animate_loading)
        # 动画 emoji 轮换状态（与 init_mixin._animate_loading 对齐）
        app.loading_emoji_index = 0
        app.is_loading = False

    # ──────────────────────────────────────────────────────────────────
    # 工具方法
    # ──────────────────────────────────────────────────────────────────

    def _make_btn(self, text: str, tooltip: str, size: int,
                  checkable: bool = False) -> QPushButton:
        btn = QPushButton()
        btn.setText(text)
        btn.setToolTip(tooltip)
        btn.setFixedSize(size, size)
        btn.setCheckable(checkable)
        theme.apply_to_sub(btn, self._BUTTON_STYLE)
        return btn

    def copy_refs_to_app(self):
        """将工具栏内所有控件引用复制到 app，保持向后兼容。"""
        app = self._app
        for attr in (
            'right_buttons_container', 'map_mode_button', 'road_overlay_button',
            'map_settings_button', 'log_settings_button', 'about_button',
            'zoom_in_button', 'zoom_out_button', 'locate_button', 'zoom_fit_button',
            'loading_button', 'scale_info_label',
            'search_container', 'search_input', 'search_button',
            'route_button', 'favorites_button', 'route_manager_button', 'cancel_button',
        ):
            setattr(app, attr, getattr(self, attr))

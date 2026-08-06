"""
主题管理（深色/浅色切换框架）

颜色集中在主题表中（light/dark 两套），面板 QSS 中的颜色使用占位符
（如 __PANEL_BG__、__TEXT__），经 Theme.apply() 渲染为实际颜色；
切换主题时遍历已注册控件重新应用样式。

面板接入模式：
    1. 主样式：用 theme.set_theme_stylesheet(widget, QSS含占位符) 替代 setStyleSheet
       （保存模板并按主题渲染，同时注册，切主题时自动刷新）
    2. 子控件样式：用 theme.apply_to_sub(widget, QSS含占位符) 替代 setStyleSheet
       （同样注册，切主题时自动刷新）
    3. 控件销毁时通过 destroyed 信号自动注销，无需手动 unregister

主题模式（theme.set_theme 的入参）：
    'light'  / 'dark'          —— 固定浅色 / 深色
    'system'                   —— 跟随系统（Windows 浅/深色偏好，见 ui.system_theme）
    theme.requested 保存用户选择，theme.current 为实际生效主题
    （'system' 模式下系统主题变化时，主窗口通过 nativeEvent 调用 theme.apply_system_theme()）

切换入口由设置面板的"主题"下拉框触发，选择经 map_config 持久化，
应用启动时（QApplication 创建后）读取并应用，避免界面闪烁。
"""

from ui.system_theme import detect_system_theme

# 可选主题模式（固定模式 + 跟随系统）
THEME_NAMES = ('light', 'dark', 'system')

# 主题颜色表：light（浅色，本次默认）与 dark（原深色值回填，供后续切换）
THEMES = {
    'light': {
        # 背景
        'PANEL_BG': '#ffffff',          # 面板主背景
        'WINDOW_BG': '#f5f5f5',         # 外层/次级背景
        'INPUT_BG': '#f5f5f5',          # 输入框背景（浅灰，与白面板区分，边框更明显）
        # 文字
        'TEXT': '#333333',              # 主文字
        'TEXT_SECONDARY': '#666666',    # 次要文字
        'TEXT_TERTIARY': '#999999',     # 辅助/弱化文字
        'TEXT_ON_ACCENT': '#ffffff',    # 强调色底上的文字（按钮）
        # 边框与分隔
        'BORDER': '#cfcfcf',            # 边框（略深，浅色模式下边界清晰）
        'DIVIDER': '#f0f0f0',           # 分隔线
        # 状态
        'HOVER': 'rgba(0, 0, 0, 0.05)',     # 悬停背景
        'HOVER_STRONG': 'rgba(0, 0, 0, 0.1)',
        # 语义色
        'ACCENT': '#1890ff',            # 强调蓝
        'DANGER': '#f5222d',            # 危险红
        'SUCCESS': '#52c41a',           # 成功绿
        'GOLD': '#FFD700',              # 收藏金
        # 主按钮（品牌蓝，两主题一致）
        'BTN_PRIMARY_BG': '#4A90E2',
        'BTN_PRIMARY_HOVER': '#357ABD',
        'BTN_PRIMARY_PRESSED': '#2A629A',
        'BTN_PRIMARY_TEXT': '#ffffff',
        # 次按钮
        'BTN_SECONDARY_BG': '#ffffff',
        'BTN_SECONDARY_HOVER': '#f5f5f5',
        'BTN_SECONDARY_PRESSED': '#f0f0f0',
        'BTN_SECONDARY_TEXT': '#333333',
        'BTN_SECONDARY_BORDER': '#cfcfcf',
    },
    'dark': {
        # 背景
        'PANEL_BG': '#3b4453',
        'WINDOW_BG': '#2b3240',
        'INPUT_BG': '#232a36',          # 输入框背景（深色，配 __TEXT__ 白字可读）
        # 文字
        'TEXT': '#ffffff',
        'TEXT_SECONDARY': '#aaaaaa',
        'TEXT_TERTIARY': '#999999',
        'TEXT_ON_ACCENT': '#ffffff',
        # 边框与分隔
        'BORDER': 'rgba(255, 255, 255, 0.2)',
        'DIVIDER': 'rgba(255, 255, 255, 0.15)',
        # 状态
        'HOVER': 'rgba(255, 255, 255, 0.1)',
        'HOVER_STRONG': 'rgba(255, 255, 255, 0.2)',
        # 语义色
        'ACCENT': '#1890ff',
        'DANGER': '#f5222d',
        'SUCCESS': '#52c41a',
        'GOLD': '#FFD700',
        # 主按钮（品牌蓝，两主题一致）
        'BTN_PRIMARY_BG': '#4A90E2',
        'BTN_PRIMARY_HOVER': '#357ABD',
        'BTN_PRIMARY_PRESSED': '#2A629A',
        'BTN_PRIMARY_TEXT': '#ffffff',
        # 次按钮（深色下保持半透明白底深字）
        'BTN_SECONDARY_BG': 'rgba(255, 255, 255, 0.9)',
        'BTN_SECONDARY_HOVER': 'rgba(255, 255, 255, 0.2)',
        'BTN_SECONDARY_PRESSED': 'rgba(255, 255, 255, 0.15)',
        'BTN_SECONDARY_TEXT': '#3b4453',
        'BTN_SECONDARY_BORDER': 'rgba(255, 255, 255, 0.2)',
    },
}

_PLACEHOLDERS = (
    'PANEL_BG', 'WINDOW_BG', 'INPUT_BG',
    'TEXT', 'TEXT_SECONDARY', 'TEXT_TERTIARY', 'TEXT_ON_ACCENT',
    'BORDER', 'DIVIDER',
    'HOVER', 'HOVER_STRONG',
    'ACCENT', 'DANGER', 'SUCCESS', 'GOLD',
    'BTN_PRIMARY_BG', 'BTN_PRIMARY_HOVER', 'BTN_PRIMARY_PRESSED', 'BTN_PRIMARY_TEXT',
    'BTN_SECONDARY_BG', 'BTN_SECONDARY_HOVER', 'BTN_SECONDARY_PRESSED',
    'BTN_SECONDARY_TEXT', 'BTN_SECONDARY_BORDER',
)


class _Theme:
    """主题单例：占位符替换 + 控件注册刷新

    requested: 用户选择的主题模式（light / dark / system）
    current:   当前实际生效的主题（light / dark，system 已解析为实际值）
    """

    def __init__(self):
        self.requested = 'light'
        self.current = 'light'
        self._registered = []  # 已注册控件（destroyed 时自动注销）

    def apply(self, qss: str, theme_name: str = None) -> str:
        """将 QSS 中的占位符替换为指定主题的实际颜色

        Args:
            qss: 含 __占位符__ 的样式表
            theme_name: 主题名（默认当前主题）

        Returns:
            str: 替换后的样式表
        """
        colors = THEMES.get(theme_name or self.current, THEMES['light'])
        for key in _PLACEHOLDERS:
            qss = qss.replace(f'__{key}__', colors[key])
        return qss

    def register(self, widget):
        """注册控件：切换主题时自动重新应用样式（销毁时自动注销）"""
        if widget is not None and widget not in self._registered:
            self._registered.append(widget)
            try:
                widget.destroyed.connect(lambda *_: self.unregister(widget))
            except (RuntimeError, TypeError):
                pass  # 非 QObject 或已销毁

    def unregister(self, widget):
        """注销控件（destroyed 信号触发，防止悬垂引用）"""
        if widget in self._registered:
            self._registered.remove(widget)

    def set_theme_stylesheet(self, widget, qss_template: str):
        """面板主样式接入：保存模板 → 按当前主题渲染 → 注册自动刷新

        替代 setStyleSheet 使用；切主题时无需面板侧额外代码。
        """
        if widget is None:
            return
        widget._theme_qss_template = qss_template
        widget.setStyleSheet(self.apply(qss_template))
        self.register(widget)

    def apply_to_sub(self, widget, qss_template: str):
        """子控件样式接入：渲染并按当前主题注册自动刷新

        替代子控件上的 setStyleSheet 使用；同样保存模板，
        切主题时随控件一起自动重渲染。
        """
        if widget is None:
            return
        widget._theme_qss_template = qss_template
        widget.setStyleSheet(self.apply(qss_template))
        self.register(widget)

    def set_theme(self, name: str):
        """切换主题并刷新所有已注册控件

        Args:
            name: 'light' / 'dark' / 'system'（跟随系统，自动解析为实际主题）

        Raises:
            ValueError: 未知主题模式
        """
        if name not in THEME_NAMES:
            raise ValueError(f"未知主题: {name}")
        self.requested = name
        self.current = name if name != 'system' else detect_system_theme()
        for widget in list(self._registered):
            try:
                template = getattr(widget, '_theme_qss_template', None)
                if template is not None:
                    widget.setStyleSheet(self.apply(template))
                elif hasattr(widget, 'apply_theme'):
                    widget.apply_theme()
            except RuntimeError:
                # 控件已销毁（C++ 对象释放），跳过并从注册表移除
                self.unregister(widget)

    def apply_system_theme(self):
        """按当前系统主题重新应用（仅"跟随系统"模式）

        系统主题变化（WM_SETTINGCHANGE）时由主窗口调用；
        非"跟随系统"模式下不产生任何效果。
        """
        if self.requested == 'system':
            self.set_theme('system')


theme = _Theme()

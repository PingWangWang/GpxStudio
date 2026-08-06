"""
系统主题检测（Windows）

读取 Windows 系统浅/深色偏好（注册表 AppsUseLightTheme），
供"跟随系统"主题模式使用。非 Windows 或读取失败时回退为浅色。
"""

try:
    import winreg
except ImportError:
    winreg = None  # 非 Windows 平台

# Windows 主题偏好注册表位置
_THEME_KEY = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
_APPS_USE_LIGHT_THEME = "AppsUseLightTheme"


def detect_system_theme() -> str:
    """检测当前 Windows 系统主题

    Returns:
        str: 'light'（浅色）或 'dark'（深色）；
             非 Windows 或读取失败时回退 'light'
    """
    if winreg is None:
        return 'light'
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _THEME_KEY) as key:
            value, _ = winreg.QueryValueEx(key, _APPS_USE_LIGHT_THEME)
        # AppsUseLightTheme: 1=浅色，0=深色
        return 'light' if value else 'dark'
    except OSError:
        # 注册表项不存在或无法读取（如精简版系统），按浅色处理
        return 'light'

"""
处理器模块
包含定位处理和自定义WebEngine页面
"""

from .geolocation import GeolocationHandler
from .webengine import ConsoleWebEnginePage

__all__ = ['GeolocationHandler', 'ConsoleWebEnginePage']

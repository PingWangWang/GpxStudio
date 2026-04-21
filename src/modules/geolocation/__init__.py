"""
地理定位模块

提供坐标转换、Windows 原生位置获取、位置辅助工具及定位处理器。

使用示例：
    from modules.geolocation import CoordinateTransform, GeolocationHandler
    from modules.geolocation import LocationHelper, WindowsLocationService
"""

from .coordinate_transform import CoordinateTransform
from .geolocation import GeolocationHandler
from .location_helper import LocationHelper
from .windows_location import WindowsLocationService

__all__ = [
    'CoordinateTransform',
    'GeolocationHandler',
    'LocationHelper',
    'WindowsLocationService',
]

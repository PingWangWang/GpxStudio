"""
定位处理器
处理浏览器定位和IP定位的信号与回调
"""

from PyQt5.QtCore import QObject

# 导入信号管理器
from core.signals import signal_manager


class GeolocationHandler(QObject):
    """定位处理器，用于发送定位成功/失败信号"""

    def __init__(self):
        super().__init__()
        print("[GeolocationHandler] 初始化定位处理器")

    def test_geolocation(self):
        """测试定位功能"""
        print("[GeolocationHandler] 测试定位功能")
        signal_manager.geolocation_error.emit("测试定位功能")
    
    def emit_geolocation_success(self, lat, lon, accuracy):
        """发送定位成功信号"""
        signal_manager.geolocation_success.emit(lat, lon, accuracy)
    
    def emit_geolocation_error(self, error_msg):
        """发送定位失败信号"""
        signal_manager.geolocation_error.emit(error_msg)

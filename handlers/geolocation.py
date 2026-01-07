"""
定位处理器
处理浏览器定位和IP定位的信号与回调
"""

from PyQt5.QtCore import QObject, pyqtSignal


class GeolocationHandler(QObject):
    """定位处理器，用于发送定位成功/失败信号"""
    geolocation_success = pyqtSignal(float, float, float)
    geolocation_error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        print("[GeolocationHandler] 初始化定位处理器")

    def test_geolocation(self):
        """测试定位功能"""
        print("[GeolocationHandler] 测试定位功能")
        self.geolocation_error.emit("测试定位功能")

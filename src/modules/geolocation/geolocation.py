"""
定位处理器
处理浏览器定位和IP定位的信号与回调
"""

from PyQt5.QtCore import QObject


class GeolocationHandler(QObject):
    """定位处理器，用于发送定位成功/失败信号"""

    def __init__(self, signal_manager=None):
        super().__init__()
        self.signal_manager = signal_manager
        print("[GeolocationHandler] 初始化定位处理器")
        if signal_manager:
            print(f"[GeolocationHandler] 使用传入的信号管理器: {signal_manager}")
        else:
            print("[GeolocationHandler] 警告：未传入信号管理器")

    def test_geolocation(self):
        """测试定位功能"""
        print("[GeolocationHandler] 测试定位功能")
        if self.signal_manager:
            self.signal_manager.geolocation_error.emit("测试定位功能")

    def emit_geolocation_success(self, lat, lon, accuracy):
        """发送定位成功信号"""
        print(f"[GeolocationHandler] 准备发送定位成功信号: {lat}, {lon}, {accuracy}")
        if self.signal_manager:
            print("[GeolocationHandler] 使用信号管理器发送信号")
            self.signal_manager.geolocation_success.emit(lat, lon, accuracy)
            print("[GeolocationHandler] 信号发送完成")
        else:
            print("[GeolocationHandler] 错误：信号管理器未设置，无法发送信号")

    def emit_geolocation_error(self, error_msg):
        """发送定位失败信号"""
        print(f"[GeolocationHandler] 准备发送定位失败信号: {error_msg}")
        if self.signal_manager:
            self.signal_manager.geolocation_error.emit(error_msg)
        else:
            print("[GeolocationHandler] 错误：信号管理器未设置，无法发送信号")

"""
Windows原生位置服务
提供高精度地理位置获取功能
"""

import asyncio
import platform
from typing import Optional, Dict, Any, Callable

from modules.geolocation.interfaces.location_service import ILocationService


class WindowsLocationService(ILocationService):
    """Windows原生位置服务"""

    def __init__(self, logger: Optional[Callable] = None):
        self._system = platform.system()
        self.logger = logger

    def log(self, level: str, message: str):
        """输出日志"""
        if self.logger:
            self.logger(level, message)

    def is_available(self) -> bool:
        """检查Windows位置服务是否可用"""
        if self._system != "Windows":
            return False

        try:
            from winrt.windows.devices.geolocation import Geolocator
            return True
        except ImportError:
            return False

    async def _get_location_async(self) -> Optional[Dict[str, Any]]:
        """异步获取位置"""
        if self._system != "Windows":
            return None

        try:
            from winrt.windows.devices.geolocation import Geolocator

            geolocator = Geolocator()

            try:
                from winrt.windows.devices.geolocation import GeolocationAccessStatus
                access_status = await geolocator.request_access_async()

                if access_status != GeolocationAccessStatus.ALLOWED:
                    self.log("ERROR", f"Windows定位访问被拒绝，访问状态: {access_status}")
                    self.log("INFO", "请在Windows设置中开启位置服务：设置 → 隐私 → 位置 → 开启'允许应用访问你的位置'")
                    return None
            except AttributeError:
                self.log("DEBUG", "request_access_async 不可用，直接尝试获取位置")

            position = await geolocator.get_geoposition_async()

            location_data = {
                "latitude": position.coordinate.latitude,
                "longitude": position.coordinate.longitude,
                "accuracy": position.coordinate.accuracy,
                "altitude": getattr(position.coordinate, 'altitude', None),
                "timestamp": getattr(position.coordinate, 'timestamp', None),
                "source": "windows_native"
            }

            # 添加详细的成功日志
            self.log("INFO", f"Windows原生定位成功 - 坐标: {location_data['latitude']:.6f}, {location_data['longitude']:.6f}, 精度: {location_data['accuracy']:.0f}米")

            return location_data

        except ImportError as e:
            if "winrt" in str(e):
                self.log("WARNING", "Windows位置服务不可用：winrt库不完整")
            else:
                self.log("WARNING", f"Windows位置服务不可用：{str(e)}")
            return None
        except Exception as e:
            error_msg = str(e)
            if "winrt" in error_msg.lower():
                self.log("WARNING", "Windows位置服务不可用：winrt库配置问题")
            else:
                self.log("ERROR", f"获取位置失败: {error_msg}")
            return None

    def get_location(self, timeout: float = 10.0) -> Optional[Dict[str, Any]]:
        """
        获取当前位置（同步接口）

        Args:
            timeout: 超时时间（秒）

        Returns:
            位置信息字典，失败返回None
        """
        if not self.is_available():
            self.log("WARNING", "当前系统不支持Windows原生位置服务")
            return None

        try:
            if platform.system() == "Windows":
                self.log("INFO", f"开始执行Windows原生定位，超时时间: {timeout}秒")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        asyncio.wait_for(self._get_location_async(), timeout=timeout)
                    )
                    if result:
                        self.log("INFO", "Windows原生定位完成")
                    else:
                        self.log("WARNING", "Windows原生定位未获取到位置信息")
                    return result
                finally:
                    loop.close()
            else:
                self.log("WARNING", "当前系统不是Windows，无法使用Windows原生定位")
                return None

        except asyncio.TimeoutError:
            self.log("ERROR", f"Windows定位超时 ({timeout}秒)")
            self.log("INFO", "请检查网络连接和位置服务状态")
            return None
        except Exception as e:
            self.log("ERROR", f"Windows定位异常: {str(e)}")
            self.log("INFO", "请检查Windows位置服务是否已开启")
            return None

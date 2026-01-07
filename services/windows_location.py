"""
Windows原生位置服务
提供高精度地理位置获取功能
"""

import asyncio
import platform
from typing import Optional, Dict, Any, Callable


class WindowsLocationService:
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
                    self.log("WARNING", f"访问状态: {access_status}")
                    return None
            except AttributeError:
                self.log("DEBUG", "request_access_async 不可用，直接尝试获取位置")

            position = await geolocator.get_geoposition_async()

            return {
                "latitude": position.coordinate.latitude,
                "longitude": position.coordinate.longitude,
                "accuracy": position.coordinate.accuracy,
                "altitude": getattr(position.coordinate, 'altitude', None),
                "timestamp": getattr(position.coordinate, 'timestamp', None),
                "source": "windows_native"
            }

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
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(
                        asyncio.wait_for(self._get_location_async(), timeout=timeout)
                    )
                finally:
                    loop.close()
            else:
                return None

        except asyncio.TimeoutError:
            self.log("WARNING", "获取位置超时")
            return None
        except Exception as e:
            self.log("ERROR", f"获取位置异常: {str(e)}")
            return None

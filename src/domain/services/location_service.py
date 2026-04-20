"""
位置服务接口（ABC）

替代 src/modules/geolocation/interfaces/location_service.py 的非抽象版本。
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class ILocationService(ABC):
    """位置服务抽象基类

    所有设备定位服务必须实现此接口。
    """

    @abstractmethod
    def is_available(self) -> bool:
        """检查位置服务是否可用

        Returns:
            服务可用返回 True，否则 False。
        """

    @abstractmethod
    def get_location(self, timeout: float = 10.0) -> Optional[Dict[str, Any]]:
        """获取当前位置（同步）

        Args:
            timeout: 超时时间（秒）

        Returns:
            位置信息字典，包含 latitude、longitude、accuracy 等字段；
            失败或超时返回 None。
        """

"""
地理编码服务接口（ABC）

使用 ABC 抽象基类，强制实现方强制实现所有核心方法。
替代 src/services/interfaces/geocoding_service.py 的非抽象版本。
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Callable


class IGeocodingService(ABC):
    """地理编码服务抽象基类

    所有地理编码服务（高德、OSM 等）必须实现此接口。
    """

    @abstractmethod
    def search_location(self, search_text: str) -> Optional[List[Dict]]:
        """正地理编码：关键词 → 地点列表

        Args:
            search_text: 搜索文本

        Returns:
            搜索结果列表，每个元素包含 name、address、lat、lon 等字段；
            失败返回 None。
        """

    @abstractmethod
    def reverse_geocode(self, lat: float, lon: float) -> Optional[Dict]:
        """逆地理编码：坐标 → 地址信息

        Args:
            lat: 纬度
            lon: 经度

        Returns:
            地址信息字典，包含 name、address、level 等字段；
            失败返回 None。
        """

    @abstractmethod
    def get_ip_location(self) -> Optional[Dict]:
        """IP 定位：获取当前设备的大致位置

        Returns:
            定位信息字典，包含 lat、lon、city、source 等字段；
            失败或不支持返回 None。
        """

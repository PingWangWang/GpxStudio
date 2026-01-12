"""
地理编码服务接口
定义地理编码相关服务的契约
"""

from typing import Optional, List, Dict, Callable


class IGeocodingService:
    """
    地理编码服务接口
    定义了地点搜索和反向地理编码的方法
    """

    def __init__(self, api_key: str = "", security_key: str = "", logger: Optional[Callable] = None):
        """初始化服务

        Args:
            api_key: API密钥
            security_key: 安全密钥
            logger: 日志记录器函数，接收(level, message)参数
        """
        ...

    def search_location(self, search_text: str) -> Optional[List[Dict]]:
        """
        搜索地点

        Args:
            search_text: 搜索文本

        Returns:
            list: 搜索结果列表，每个结果包含name, address, lat, lon
        """
        ...

    def reverse_geocode(self, lat: float, lon: float) -> Optional[Dict]:
        """
        反向地理编码（根据坐标获取地址信息）

        Args:
            lat: 纬度
            lon: 经度

        Returns:
            dict: 地址信息，包含name, address, lat, lon
        """
        ...

    def get_ip_location(self) -> Optional[Dict]:
        """
        使用IP定位API获取当前位置

        Returns:
            dict: 定位信息 {'lat': float, 'lon': float, 'city': str, 'source': str}
                 失败返回None
        """
        ...

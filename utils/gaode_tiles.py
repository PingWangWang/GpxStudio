"""
高德地图瓦片服务
提供高德地图瓦片获取和显示功能
"""

import os
from typing import Optional


class GaodeTileService:
    """高德地图瓦片服务"""

    TILE_URLS = {
        'roadmap': 'https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
        'satellite': 'https://webst01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=6&x={x}&y={y}&z={z}',
        'hybrid': 'https://webst01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}'
    }

    def __init__(self, map_type: str = 'roadmap'):
        self.map_type = map_type

    def get_tile_url(self, x: int, y: int, z: int) -> str:
        """获取瓦片URL"""
        url_template = self.TILE_URLS.get(self.map_type, self.TILE_URLS['roadmap'])
        return url_template.format(x=x, y=y, z=z)

    def get_attribution(self) -> str:
        """获取地图版权信息"""
        return '© 高德地图'

    @staticmethod
    def get_map_types() -> list:
        """获取支持的地图类型"""
        return [
            ('roadmap', '街道图'),
            ('satellite', '卫星图'),
            ('hybrid', '混合图')
        ]

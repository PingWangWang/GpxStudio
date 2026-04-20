"""
搜索结果领域模型
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SearchResult:
    """POI 搜索结果"""
    name: str
    lat: float
    lon: float
    address: str = ''
    city: str = ''
    district: str = ''
    type: Optional[str] = None
    level: Optional[str] = None
    coord_system: str = 'WGS-84'
    data_source: str = 'unknown'
    # 原始数据（用于需要完整数据的场景）
    raw: dict = field(default_factory=dict)

    @property
    def coords(self) -> tuple:
        """返回 (lat, lon) 元组"""
        return (self.lat, self.lon)

    @property
    def display_name(self) -> str:
        """显示名称（含地址）"""
        if self.address:
            return f"{self.name} ({self.address})"
        return self.name

"""
地点领域模型
"""
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Location:
    """地点模型

    替代原先散落在 DataManager 中的 (coords, name, level, coord_system) 四元组。
    """
    name: str
    lat: float
    lon: float
    address: str = ''
    level: Optional[str] = None
    type: Optional[str] = None
    radius: Optional[float] = None
    coord_system: str = 'WGS-84'
    data_source: str = 'unknown'

    @property
    def coords(self) -> tuple:
        """返回 (lat, lon) 元组，方便与旧代码兼容"""
        return (self.lat, self.lon)

    def __bool__(self) -> bool:
        """非空判断：lat/lon 均不为 None 时视为有效"""
        return self.lat is not None and self.lon is not None


@dataclass
class RouteWaypoints:
    """路线途经点集合"""
    start: Optional[Location] = None
    end: Optional[Location] = None
    waypoints: List[Location] = field(default_factory=list)

    def is_complete(self) -> bool:
        """起点和终点都已设置时返回 True"""
        return self.start is not None and self.end is not None

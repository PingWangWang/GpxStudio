"""
路线规划领域模型
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class RoutePoint:
    """路线上的单个坐标点"""
    lat: float
    lon: float
    elevation: Optional[float] = None

    @property
    def coords(self) -> tuple:
        """返回 (lat, lon) 元组"""
        return (self.lat, self.lon)


@dataclass
class RouteAlternative:
    """单条路线方案"""
    index: int
    distance: float          # 米
    duration: int            # 秒
    points: List[RoutePoint] = field(default_factory=list)
    description: str = ''
    tolls: float = 0.0       # 收费金额（元）
    traffic_lights: int = 0  # 红绿灯数量


@dataclass
class RouteResult:
    """路线规划结果（含多方案）"""
    alternatives: List[RouteAlternative] = field(default_factory=list)
    selected_index: int = 0

    @property
    def selected(self) -> Optional[RouteAlternative]:
        """当前选中的路线方案"""
        if self.alternatives and 0 <= self.selected_index < len(self.alternatives):
            return self.alternatives[self.selected_index]
        return None

    def select(self, index: int) -> bool:
        """切换选中方案，返回是否成功"""
        if 0 <= index < len(self.alternatives):
            self.selected_index = index
            return True
        return False

"""
路线规划服务接口（ABC）

替代 src/modules/routing/interfaces/routing_service.py 的非抽象版本。
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Tuple


class IRoutingService(ABC):
    """路线规划服务抽象基类

    所有路线规划服务（高德、OSRM 等）必须实现此接口。
    """

    @abstractmethod
    def plan_route(
        self,
        points: List[Tuple[float, float]],
        transport_mode: str = "驾车",
    ) -> Tuple[List[Tuple[float, float]], int]:
        """规划路线

        Args:
            points: 坐标点列表 [(lat, lon), ...]，包含起点、途经点、终点
            transport_mode: 交通方式（步行 / 骑行 / 驾车）

        Returns:
            (路线点列表, 预估耗时秒数)
            路线点列表中段之间用 None 分隔。
        """

    @abstractmethod
    def calculate_distance(self, route_points: List[Tuple[float, float]]) -> float:
        """计算路线总距离

        Args:
            route_points: 路线点列表 [(lat, lon), ...]

        Returns:
            总距离（公里）
        """

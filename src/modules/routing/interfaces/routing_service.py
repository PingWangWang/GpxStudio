"""
路线规划服务接口
定义路线规划相关服务的契约
"""

from typing import Optional, List, Dict, Callable, Tuple


class IRoutingService:
    """
    路线规划服务接口
    定义了路线规划和路线查询的方法
    """

    def __init__(self, api_key: str = "", security_key: str = "", logger: Optional[Callable] = None):
        """
        初始化路线规划服务

        Args:
            api_key: API密钥
            security_key: 安全密钥
            logger: 日志记录器函数，接收(level, message)参数
        """
        ...

    def plan_route(self, points: List[Tuple[float, float]], transport_mode: str = "驾车") -> Tuple[List[Tuple[float, float]], int]:
        """
        规划路线

        Args:
            points: 坐标点列表 [(lat, lon), ...]
            transport_mode: 交通方式（步行/骑行/驾车）

        Returns:
            tuple: (路线点列表， estimated_duration_seconds)
                  路线点列表段之间用None分隔
                  estimated_duration_seconds为预估时间（秒）
        """
        ...

    def calculate_distance(self, route_points: List[Tuple[float, float]]) -> float:
        """
        计算路线总距离

        Args:
            route_points: 路线点列表

        Returns:
            float: 总距离（公里）
        """
        ...

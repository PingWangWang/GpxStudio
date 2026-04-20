"""
路线规划业务协调器

封装路线规划的核心业务逻辑：
- 校验起终点
- 调用 IRoutingService 规划路线
- 处理多方案结果
- 通过回调通知 UI 层

不依赖任何 PyQt5 组件，可在无 Qt 环境下进行单元测试。
"""

from typing import Callable, List, Optional, Tuple
import logging

from domain.services.routing_service import IRoutingService


logger = logging.getLogger(__name__)


class RouteCoordinator:
    """路线规划业务协调器

    职责
    ----
    * 校验起终点是否已设置
    * 调用 ``IRoutingService.plan_route()``
    * 处理多方案结果（安全检查索引越界）
    * 通过回调通知 UI 层（route_ready / error）

    不依赖 Qt，可直接 mock ``IRoutingService`` 进行单元测试。

    示例
    ----
    >>> coordinator = RouteCoordinator(
    ...     routing_service=mock_svc,
    ...     on_route_ready=lambda alts, idx: ...,
    ...     on_error=lambda msg: ...,
    ... )
    >>> coordinator.plan_route(points, 'driving', 'gaode')
    """

    def __init__(
        self,
        routing_service: IRoutingService,
        on_route_ready: Callable[[List[dict], int], None],
        on_error: Callable[[str], None],
        gaode_configured_check: Optional[Callable[[], bool]] = None,
    ):
        """
        参数:
            routing_service: 路线规划服务实例
            on_route_ready: 规划成功回调，接收 (alternatives, default_index)
            on_error: 规划失败回调，接收错误描述字符串
            gaode_configured_check: 可选；高德 API 已配置检查函数
        """
        self._routing = routing_service
        self._on_route_ready = on_route_ready
        self._on_error = on_error
        self._gaode_check = gaode_configured_check

    def plan_route(
        self,
        points: list,
        transport_mode: str,
        map_source: str = '',
        start_name: str = '',
        end_name: str = '',
    ) -> None:
        """执行路线规划。

        参数:
            points: 坐标点列表 [(lat, lon), ...]，顺序为起点→途径点→终点
            transport_mode: 交通方式（如 'driving' / 'walking' / 'cycling'）
            map_source: 当前地图源标识（'gaode' / 'osm'）
            start_name: 起点名称（部分服务支持）
            end_name: 终点名称（部分服务支持）
        """
        if len(points) < 2:
            self._on_error("未设置起点或终点")
            return

        # 高德 API 未配置
        if map_source == 'gaode' and self._gaode_check and not self._gaode_check():
            self._on_error(
                "使用高德地图规划路线需要先配置API密钥。\n"
                "请在【地图设置】中配置高德地图Web服务API密钥。"
            )
            return

        try:
            import inspect
            sig = inspect.signature(self._routing.plan_route)
            if 'start_name' in sig.parameters and 'end_name' in sig.parameters:
                result = self._routing.plan_route(
                    points, transport_mode,
                    start_name=start_name,
                    end_name=end_name,
                )
            else:
                result = self._routing.plan_route(points, transport_mode)

            if isinstance(result, (list, tuple)) and len(result) == 2:
                alternatives, default_index = result
            else:
                alternatives, default_index = result, 0

            if not alternatives:
                self._on_error("路线规划未返回任何方案，请检查起终点设置")
                return

            # 安全边界检查
            if default_index >= len(alternatives):
                logger.warning(
                    f"[RouteCoordinator] default_index={default_index} 超出范围，重置为0"
                )
                default_index = 0

            logger.info(
                f"[RouteCoordinator] 规划成功：{len(alternatives)} 个方案，"
                f"默认方案索引={default_index}"
            )
            self._on_route_ready(alternatives, default_index)

        except Exception as e:
            logger.error(f"[RouteCoordinator] 路线规划异常: {e}")
            self._on_error(str(e))

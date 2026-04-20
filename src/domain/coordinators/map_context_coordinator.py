"""
地图右键菜单业务协调器

封装右键菜单点击的纯业务逻辑：
- 调用地理编码服务进行逆地理编码
- 构造标准化地点信息字典
- 通过回调通知 UI 层更新面板和数据

不依赖任何 PyQt5 组件，可在无 Qt 环境下进行单元测试。
"""

from typing import Callable, Optional
import logging


logger = logging.getLogger(__name__)


class MapContextCoordinator:
    """地图右键菜单业务协调器

    职责
    ----
    * 对地图点击坐标执行逆地理编码
    * 构造标准化地点信息字典（name / level / type_info / coord_system / map_source）
    * 通过回调通知 UI 层（``on_resolved`` / ``on_error``）

    不依赖 Qt，``geocoding_service_provider`` 返回实际服务实例即可。

    结果字典结构
    ------------
    .. code-block:: python

        {
            'name': str,           # 地点名称
            'level': str,          # 详细等级（如 'POI' / 'street' / 'city'）
            'type_info': str,      # 地点类型描述
            'coord_system': str,   # 坐标系（'gcj02' / 'wgs84'）
            'map_source': str,     # 地图源标识
        }

    示例
    ----
    >>> coordinator = MapContextCoordinator(
    ...     geocoding_service_provider=lambda: mock_svc,
    ...     coord_system_provider=lambda ms: 'gcj02',
    ...     on_resolved=lambda info: ...,
    ...     on_error=lambda msg: ...,
    ... )
    >>> coordinator.resolve_address(39.9, 116.4, map_source='gaode')
    """

    def __init__(
        self,
        geocoding_service_provider: Callable[[], object],
        coord_system_provider: Callable[[str], str],
        on_resolved: Callable[[dict], None],
        on_error: Callable[[str], None],
    ):
        """
        参数:
            geocoding_service_provider: 无参可调用，返回具有 ``reverse_geocode(lat, lon)``
                方法的地理编码服务实例
            coord_system_provider: 接收 map_source 字符串，返回坐标系标识
            on_resolved: 成功回调，接收地点信息字典
            on_error: 失败回调，接收错误描述字符串
        """
        self._get_service = geocoding_service_provider
        self._get_coord_system = coord_system_provider
        self._on_resolved = on_resolved
        self._on_error = on_error

    def resolve_address(
        self,
        lat: float,
        lon: float,
        map_source: str = '',
    ) -> None:
        """对坐标执行逆地理编码，解析为地点信息字典。

        参数:
            lat: 纬度
            lon: 经度
            map_source: 当前地图源标识（'gaode' / 'osm'）
        """
        logger.debug(f"[MapContextCoordinator] 解析坐标: ({lat:.6f}, {lon:.6f}), map_source={map_source}")

        try:
            service = self._get_service()
            if service is None:
                logger.warning("[MapContextCoordinator] 地理编码服务不可用，使用坐标作为名称")
                self._on_resolved(self._fallback_info(lat, lon, map_source))
                return

            result = service.reverse_geocode(lat, lon)

            if result and isinstance(result, dict) and result.get('name'):
                coord_system = self._get_coord_system(map_source)
                info = {
                    'name': result.get('name', f"{lat:.6f},{lon:.6f}"),
                    'level': result.get('level', ''),
                    'type_info': result.get('type_info', ''),
                    'coord_system': coord_system,
                    'map_source': map_source,
                }
                logger.info(f"[MapContextCoordinator] 逆地理编码成功: {info['name']}")
                self._on_resolved(info)
            else:
                logger.info("[MapContextCoordinator] 逆地理编码无结果，使用坐标作为名称")
                self._on_resolved(self._fallback_info(lat, lon, map_source))

        except Exception as e:
            logger.error(f"[MapContextCoordinator] 逆地理编码异常: {e}")
            # 失败时降级为坐标名称，而非完全报错（保持右键菜单可用）
            self._on_resolved(self._fallback_info(lat, lon, map_source))

    # ──────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _fallback_info(self, lat: float, lon: float, map_source: str) -> dict:
        """生成降级地点信息（直接使用坐标字符串作为名称）。"""
        coord_system = self._get_coord_system(map_source)
        return {
            'name': f"{lat:.6f},{lon:.6f}",
            'level': '',
            'type_info': '',
            'coord_system': coord_system,
            'map_source': map_source,
        }

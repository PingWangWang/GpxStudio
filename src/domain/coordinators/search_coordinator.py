"""
搜索业务协调器

封装地点搜索的核心业务逻辑：
- 关键词搜索（正地理编码）
- 历史记录管理
- 搜索结果格式化

不依赖任何 PyQt5 组件，可在无 Qt 环境下进行单元测试。
"""

from typing import Callable, List, Optional
import logging

from domain.services.geocoding_service import IGeocodingService


logger = logging.getLogger(__name__)


def _format_raw_results(results: list) -> list:
    """将原始地理编码结果统一格式化为标准字典列表。

    支持高德格式（dict）和 OSM 格式（对象属性）。

    参数:
        results: 原始搜索结果

    返回:
        格式化后的字典列表，每个元素包含
        name / address / lat / lon / type / level / radius /
        coord_system / data_source
    """
    formatted = []
    for item in results:
        if isinstance(item, dict):
            formatted.append({
                'name':         item.get('name', ''),
                'address':      item.get('address', ''),
                'lat':          item.get('lat', 0),
                'lon':          item.get('lon', 0),
                'type':         item.get('type', ''),
                'level':        item.get('level', ''),
                'radius':       item.get('radius'),
                'coord_system': item.get('coord_system', 'WGS-84'),
                'data_source':  item.get('data_source', 'unknown'),
            })
        else:
            # OSM geocoder 对象（geopy.Location 等）
            formatted.append({
                'name':         getattr(item, 'address', str(item)),
                'address':      getattr(item, 'address', ''),
                'lat':          getattr(item, 'latitude', 0),
                'lon':          getattr(item, 'longitude', 0),
                'type':         getattr(item, 'type', ''),
                'level':        '',
                'radius':       None,
                'coord_system': 'WGS-84',
                'data_source':  'osm',
            })
    return formatted


class SearchCoordinator:
    """搜索业务协调器

    职责
    ----
    * 调用 ``IGeocodingService`` 执行正地理编码（关键词搜索）
    * 将原始结果格式化为统一字典格式
    * 通过回调通知 UI 层（results / error）

    不依赖 Qt，可直接 mock ``IGeocodingService`` 进行单元测试。

    示例
    ----
    >>> coordinator = SearchCoordinator(
    ...     geocoding_service=mock_svc,
    ...     on_results=lambda r: ...,
    ...     on_error=lambda e: ...,
    ... )
    >>> coordinator.search('北京', map_source='gaode')
    """

    def __init__(
        self,
        geocoding_service: IGeocodingService,
        on_results: Callable[[List[dict]], None],
        on_error: Callable[[str], None],
        gaode_configured_check: Optional[Callable[[], bool]] = None,
    ):
        """
        参数:
            geocoding_service: 地理编码服务实例
            on_results: 搜索成功回调，接收格式化结果列表
            on_error: 搜索失败回调，接收错误描述字符串
            gaode_configured_check: 可选；高德 API 已配置检查函数，
                ``lambda: map_config.is_gaode_configured()``
        """
        self._geocoding = geocoding_service
        self._on_results = on_results
        self._on_error = on_error
        self._gaode_check = gaode_configured_check

    def search(self, query: str, map_source: str = '') -> None:
        """执行地点搜索。

        参数:
            query: 搜索关键词
            map_source: 当前地图源标识（'gaode' / 'osm'），
                用于判断高德 API 配置检查
        """
        if not query:
            return

        # 高德 API 未配置时直接返回空结果
        if map_source == 'gaode' and self._gaode_check and not self._gaode_check():
            logger.warning("[SearchCoordinator] 高德地图API未配置，跳过搜索")
            self._on_results([])
            return

        try:
            raw = self._geocoding.search_location(query)
            results = _format_raw_results(raw)
            logger.debug(f"[SearchCoordinator] 搜索 '{query}' 返回 {len(results)} 条结果")
            self._on_results(results)
        except Exception as e:
            logger.error(f"[SearchCoordinator] 搜索异常: {e}")
            self._on_error(str(e))

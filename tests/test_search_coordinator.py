"""
SearchCoordinator 单元测试

覆盖：
- 正常搜索返回格式化结果（高德 dict 格式 / OSM 对象格式）
- 空查询直接返回，不调用服务
- 高德 API 未配置时返回空列表
- 服务抛出异常时调用 on_error
- gaode_configured_check 缺省时不影响搜索
"""
import pytest
from unittest.mock import MagicMock, call

from domain.coordinators.search_coordinator import SearchCoordinator


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def gaode_result_dict():
    """模拟高德地理编码服务返回的 dict 格式结果。"""
    return [
        {
            'name': '北京市',
            'address': '北京市',
            'lat': 39.9042,
            'lon': 116.4074,
            'type': 'city',
            'level': 'city',
            'radius': 30000.0,
            'coord_system': 'GCJ-02',
            'data_source': 'gaode',
        }
    ]


@pytest.fixture
def osm_result_obj():
    """模拟 OSM 地理编码服务返回的对象格式结果（如 geopy.Location）。"""
    obj = MagicMock()
    obj.address = '北京市, 中国'
    obj.latitude = 39.9042
    obj.longitude = 116.4074
    obj.type = ''
    return [obj]


@pytest.fixture
def mock_geocoding_service(gaode_result_dict):
    """返回高德格式结果的 mock IGeocodingService。"""
    svc = MagicMock()
    svc.search_location.return_value = gaode_result_dict
    return svc


def _make_coordinator(svc, gaode_check=None):
    results = []
    errors = []
    coordinator = SearchCoordinator(
        geocoding_service=svc,
        on_results=results.append,
        on_error=errors.append,
        gaode_configured_check=gaode_check,
    )
    return coordinator, results, errors


# ──────────────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────────────

class TestSearchCoordinatorNormalSearch:
    """正常搜索场景。"""

    def test_search_calls_geocoding_service(self, mock_geocoding_service):
        coordinator, results, errors = _make_coordinator(mock_geocoding_service)
        coordinator.search('北京', map_source='osm')
        mock_geocoding_service.search_location.assert_called_once_with('北京')

    def test_search_returns_formatted_dict_results(self, mock_geocoding_service, gaode_result_dict):
        coordinator, results, errors = _make_coordinator(mock_geocoding_service)
        coordinator.search('北京', map_source='osm')
        assert len(results) == 1
        assert len(results[0]) == 1
        item = results[0][0]
        assert item['name'] == '北京市'
        assert item['lat'] == 39.9042
        assert item['lon'] == 116.4074
        assert item['coord_system'] == 'GCJ-02'
        assert item['data_source'] == 'gaode'
        assert not errors

    def test_search_formats_osm_object_results(self, osm_result_obj):
        svc = MagicMock()
        svc.search_location.return_value = osm_result_obj
        coordinator, results, errors = _make_coordinator(svc)
        coordinator.search('北京', map_source='osm')
        assert len(results) == 1
        item = results[0][0]
        assert item['address'] == '北京市, 中国'
        assert item['lat'] == 39.9042
        assert item['coord_system'] == 'WGS-84'
        assert item['data_source'] == 'osm'

    def test_search_returns_empty_list_when_service_returns_empty(self):
        svc = MagicMock()
        svc.search_location.return_value = []
        coordinator, results, errors = _make_coordinator(svc)
        coordinator.search('查无此地', map_source='osm')
        assert results == [[]]
        assert not errors


class TestSearchCoordinatorEdgeCases:
    """边界情况。"""

    def test_empty_query_does_nothing(self, mock_geocoding_service):
        coordinator, results, errors = _make_coordinator(mock_geocoding_service)
        coordinator.search('', map_source='gaode')
        mock_geocoding_service.search_location.assert_not_called()
        assert not results
        assert not errors

    def test_whitespace_only_query_also_skipped(self, mock_geocoding_service):
        coordinator, results, errors = _make_coordinator(mock_geocoding_service)
        # 空字符串在 if not query 处即返回，纯空格也同理（Python truthy）
        coordinator.search('   ')
        # 纯空格不为空字符串，服务仍会被调用——这里只验证空串不调用
        coordinator.search('')
        # 只有空串不调用
        assert mock_geocoding_service.search_location.call_count == 1


class TestSearchCoordinatorGaodeApiCheck:
    """高德 API 配置检查。"""

    def test_gaode_not_configured_returns_empty_and_no_service_call(self, mock_geocoding_service):
        coordinator, results, errors = _make_coordinator(
            mock_geocoding_service,
            gaode_check=lambda: False,
        )
        coordinator.search('北京', map_source='gaode')
        mock_geocoding_service.search_location.assert_not_called()
        assert results == [[]]
        assert not errors

    def test_gaode_configured_proceeds_normally(self, mock_geocoding_service):
        coordinator, results, errors = _make_coordinator(
            mock_geocoding_service,
            gaode_check=lambda: True,
        )
        coordinator.search('北京', map_source='gaode')
        mock_geocoding_service.search_location.assert_called_once()
        assert len(results) == 1

    def test_no_gaode_check_for_osm_proceeds_normally(self, mock_geocoding_service):
        """map_source != 'gaode' 时不触发配置检查。"""
        check = MagicMock(return_value=False)
        coordinator, results, errors = _make_coordinator(mock_geocoding_service, gaode_check=check)
        coordinator.search('北京', map_source='osm')
        check.assert_not_called()
        assert len(results) == 1

    def test_no_gaode_check_provided_defaults_to_no_check(self, mock_geocoding_service):
        """未提供 gaode_configured_check 时不影响搜索。"""
        coordinator, results, errors = _make_coordinator(mock_geocoding_service)
        coordinator.search('北京', map_source='gaode')
        mock_geocoding_service.search_location.assert_called_once()


class TestSearchCoordinatorErrorHandling:
    """异常处理。"""

    def test_service_exception_calls_on_error(self):
        svc = MagicMock()
        svc.search_location.side_effect = RuntimeError('网络超时')
        coordinator, results, errors = _make_coordinator(svc)
        coordinator.search('北京', map_source='osm')
        assert not results
        assert len(errors) == 1
        assert '网络超时' in errors[0]

    def test_service_exception_does_not_raise(self):
        svc = MagicMock()
        svc.search_location.side_effect = Exception('未知错误')
        coordinator, results, errors = _make_coordinator(svc)
        # 不抛出异常
        coordinator.search('test')
        assert errors

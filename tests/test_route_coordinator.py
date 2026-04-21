"""
RouteCoordinator 单元测试

覆盖：
- 正常路线规划：返回多方案，调用 on_route_ready
- 起终点不足时调用 on_error
- 高德 API 未配置时调用 on_error
- 服务返回空列表时调用 on_error
- default_index 越界时自动重置为 0
- 服务抛出异常时调用 on_error
- 仅有两个点（起点+终点）时正常规划
"""
import pytest
from unittest.mock import MagicMock, patch

from domain.coordinators.route_coordinator import RouteCoordinator


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _make_coordinator(svc, gaode_check=None):
    route_ready_calls = []
    errors = []
    coordinator = RouteCoordinator(
        routing_service=svc,
        on_route_ready=lambda alts, idx: route_ready_calls.append((alts, idx)),
        on_error=errors.append,
        gaode_configured_check=gaode_check,
    )
    return coordinator, route_ready_calls, errors


def _mock_service_with_result(alternatives, default_index=0):
    """返回 (alternatives, default_index) 的 mock routing service。"""
    svc = MagicMock()
    svc.plan_route.return_value = (alternatives, default_index)
    return svc


MOCK_ALTERNATIVES = [
    {'distance': 10000, 'duration': 1200, 'points': [(39.9, 116.4), (39.95, 116.45)]},
    {'distance': 12000, 'duration': 1400, 'points': [(39.9, 116.4), (39.93, 116.42)]},
]

POINTS_OK = [(39.9, 116.4), (39.95, 116.45)]        # 起点 + 终点
POINTS_WITH_WAYPOINT = [(39.9, 116.4), (39.92, 116.42), (39.95, 116.45)]  # 含途经点


# ──────────────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────────────

class TestRouteCoordinatorNormal:
    """正常规划场景。"""

    def test_plan_route_calls_service(self):
        svc = _mock_service_with_result(MOCK_ALTERNATIVES)
        coordinator, calls, errors = _make_coordinator(svc)
        coordinator.plan_route(POINTS_OK, 'driving', map_source='osm')
        svc.plan_route.assert_called_once()
        assert not errors

    def test_plan_route_passes_points_and_mode(self):
        svc = _mock_service_with_result(MOCK_ALTERNATIVES)
        coordinator, calls, errors = _make_coordinator(svc)
        coordinator.plan_route(POINTS_OK, 'walking', map_source='osm')
        args = svc.plan_route.call_args
        assert POINTS_OK in args[0] or POINTS_OK == args[0][0]
        assert 'walking' in args[0]

    def test_on_route_ready_receives_alternatives_and_index(self):
        svc = _mock_service_with_result(MOCK_ALTERNATIVES, default_index=1)
        coordinator, calls, errors = _make_coordinator(svc)
        coordinator.plan_route(POINTS_OK, 'driving')
        assert len(calls) == 1
        alts, idx = calls[0]
        assert alts == MOCK_ALTERNATIVES
        assert idx == 1

    def test_two_points_minimum_works(self):
        svc = _mock_service_with_result(MOCK_ALTERNATIVES[:1])
        coordinator, calls, errors = _make_coordinator(svc)
        coordinator.plan_route(POINTS_OK, 'driving')
        assert len(calls) == 1
        assert not errors

    def test_three_points_with_waypoint(self):
        svc = _mock_service_with_result(MOCK_ALTERNATIVES)
        coordinator, calls, errors = _make_coordinator(svc)
        coordinator.plan_route(POINTS_WITH_WAYPOINT, 'driving')
        assert len(calls) == 1
        assert not errors


class TestRouteCoordinatorValidation:
    """输入验证。"""

    def test_single_point_calls_on_error(self):
        svc = MagicMock()
        coordinator, calls, errors = _make_coordinator(svc)
        coordinator.plan_route([(39.9, 116.4)], 'driving')
        svc.plan_route.assert_not_called()
        assert len(errors) == 1
        assert '起点' in errors[0] or '终点' in errors[0]

    def test_empty_points_calls_on_error(self):
        svc = MagicMock()
        coordinator, calls, errors = _make_coordinator(svc)
        coordinator.plan_route([], 'driving')
        svc.plan_route.assert_not_called()
        assert errors


class TestRouteCoordinatorGaodeApiCheck:
    """高德 API 配置检查。"""

    def test_gaode_not_configured_calls_on_error(self):
        svc = MagicMock()
        coordinator, calls, errors = _make_coordinator(svc, gaode_check=lambda: False)
        coordinator.plan_route(POINTS_OK, 'driving', map_source='gaode')
        svc.plan_route.assert_not_called()
        assert len(errors) == 1
        assert 'API' in errors[0] or '密钥' in errors[0]

    def test_gaode_configured_proceeds_normally(self):
        svc = _mock_service_with_result(MOCK_ALTERNATIVES)
        coordinator, calls, errors = _make_coordinator(svc, gaode_check=lambda: True)
        coordinator.plan_route(POINTS_OK, 'driving', map_source='gaode')
        assert len(calls) == 1
        assert not errors

    def test_osm_skips_gaode_check(self):
        check = MagicMock(return_value=False)
        svc = _mock_service_with_result(MOCK_ALTERNATIVES)
        coordinator, calls, errors = _make_coordinator(svc, gaode_check=check)
        coordinator.plan_route(POINTS_OK, 'driving', map_source='osm')
        check.assert_not_called()
        assert len(calls) == 1


class TestRouteCoordinatorEdgeCases:
    """边界情况。"""

    def test_empty_alternatives_calls_on_error(self):
        svc = _mock_service_with_result([])
        coordinator, calls, errors = _make_coordinator(svc)
        coordinator.plan_route(POINTS_OK, 'driving')
        assert not calls
        assert len(errors) == 1

    def test_default_index_out_of_range_resets_to_zero(self):
        svc = _mock_service_with_result(MOCK_ALTERNATIVES, default_index=99)
        coordinator, calls, errors = _make_coordinator(svc)
        coordinator.plan_route(POINTS_OK, 'driving')
        assert len(calls) == 1
        alts, idx = calls[0]
        assert idx == 0

    def test_service_exception_calls_on_error(self):
        svc = MagicMock()
        svc.plan_route.side_effect = RuntimeError('API 限流')
        coordinator, calls, errors = _make_coordinator(svc)
        coordinator.plan_route(POINTS_OK, 'driving')
        assert not calls
        assert len(errors) == 1
        assert 'API 限流' in errors[0]

    def test_service_exception_does_not_propagate(self):
        svc = MagicMock()
        svc.plan_route.side_effect = Exception('未知')
        coordinator, calls, errors = _make_coordinator(svc)
        coordinator.plan_route(POINTS_OK, 'driving')  # 不应抛出
        assert errors

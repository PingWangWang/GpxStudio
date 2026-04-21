"""
Location / RouteWaypoints dataclass 序列化与基本行为测试

覆盖：
- Location 字段默认值
- Location.coords 属性
- Location.__bool__ 判断
- RouteWaypoints.is_complete()
- RoutePoint / RouteAlternative / RouteResult 行为
- RouteResult.selected 属性
- RouteResult.select() 越界保护
"""
import pytest

from domain.models.location import Location, RouteWaypoints
from domain.models.route import RoutePoint, RouteAlternative, RouteResult


# ──────────────────────────────────────────────────────────────────────────────
# Location
# ──────────────────────────────────────────────────────────────────────────────

class TestLocation:
    def test_required_fields(self):
        loc = Location(name='北京', lat=39.9, lon=116.4)
        assert loc.name == '北京'
        assert loc.lat == 39.9
        assert loc.lon == 116.4

    def test_default_field_values(self):
        loc = Location(name='北京', lat=39.9, lon=116.4)
        assert loc.address == ''
        assert loc.level is None
        assert loc.type is None
        assert loc.radius is None
        assert loc.coord_system == 'WGS-84'
        assert loc.data_source == 'unknown'

    def test_coords_property_returns_tuple(self):
        loc = Location(name='测试', lat=31.23, lon=121.47)
        assert loc.coords == (31.23, 121.47)

    def test_bool_true_when_lat_lon_present(self):
        loc = Location(name='测试', lat=0.0, lon=0.0)
        # lat/lon 不为 None 即为 truthy（即使为 0.0）
        assert bool(loc) is True

    def test_bool_false_when_lat_is_none(self):
        loc = Location.__new__(Location)
        object.__setattr__(loc, 'name', '测试')
        object.__setattr__(loc, 'lat', None)
        object.__setattr__(loc, 'lon', 116.4)
        object.__setattr__(loc, 'address', '')
        object.__setattr__(loc, 'level', None)
        object.__setattr__(loc, 'type', None)
        object.__setattr__(loc, 'radius', None)
        object.__setattr__(loc, 'coord_system', 'WGS-84')
        object.__setattr__(loc, 'data_source', 'unknown')
        assert bool(loc) is False

    def test_custom_coord_system(self):
        loc = Location(name='高德点', lat=39.91, lon=116.41, coord_system='GCJ-02')
        assert loc.coord_system == 'GCJ-02'

    def test_equality(self):
        loc1 = Location(name='北京', lat=39.9, lon=116.4)
        loc2 = Location(name='北京', lat=39.9, lon=116.4)
        assert loc1 == loc2

    def test_inequality_different_coords(self):
        loc1 = Location(name='北京', lat=39.9, lon=116.4)
        loc2 = Location(name='上海', lat=31.2, lon=121.5)
        assert loc1 != loc2


# ──────────────────────────────────────────────────────────────────────────────
# RouteWaypoints
# ──────────────────────────────────────────────────────────────────────────────

class TestRouteWaypoints:
    def test_default_is_not_complete(self):
        wp = RouteWaypoints()
        assert wp.is_complete() is False

    def test_only_start_not_complete(self):
        wp = RouteWaypoints(start=Location(name='起点', lat=39.9, lon=116.4))
        assert wp.is_complete() is False

    def test_only_end_not_complete(self):
        wp = RouteWaypoints(end=Location(name='终点', lat=31.2, lon=121.5))
        assert wp.is_complete() is False

    def test_both_start_and_end_is_complete(self):
        wp = RouteWaypoints(
            start=Location(name='起点', lat=39.9, lon=116.4),
            end=Location(name='终点', lat=31.2, lon=121.5),
        )
        assert wp.is_complete() is True

    def test_with_waypoints_still_complete(self):
        mid = Location(name='途经', lat=35.0, lon=118.0)
        wp = RouteWaypoints(
            start=Location(name='起点', lat=39.9, lon=116.4),
            end=Location(name='终点', lat=31.2, lon=121.5),
            waypoints=[mid],
        )
        assert wp.is_complete() is True
        assert len(wp.waypoints) == 1


# ──────────────────────────────────────────────────────────────────────────────
# RoutePoint
# ──────────────────────────────────────────────────────────────────────────────

class TestRoutePoint:
    def test_coords_property(self):
        pt = RoutePoint(lat=39.9, lon=116.4)
        assert pt.coords == (39.9, 116.4)

    def test_elevation_optional(self):
        pt = RoutePoint(lat=39.9, lon=116.4)
        assert pt.elevation is None

    def test_elevation_set(self):
        pt = RoutePoint(lat=39.9, lon=116.4, elevation=50.0)
        assert pt.elevation == 50.0


# ──────────────────────────────────────────────────────────────────────────────
# RouteAlternative
# ──────────────────────────────────────────────────────────────────────────────

class TestRouteAlternative:
    def test_default_fields(self):
        alt = RouteAlternative(index=0, distance=5000, duration=600)
        assert alt.points == []
        assert alt.description == ''
        assert alt.tolls == 0.0
        assert alt.traffic_lights == 0

    def test_with_points(self):
        pts = [RoutePoint(39.9, 116.4), RoutePoint(39.95, 116.45)]
        alt = RouteAlternative(index=0, distance=5000, duration=600, points=pts)
        assert len(alt.points) == 2


# ──────────────────────────────────────────────────────────────────────────────
# RouteResult
# ──────────────────────────────────────────────────────────────────────────────

class TestRouteResult:
    @pytest.fixture
    def two_alternatives(self):
        return [
            RouteAlternative(index=0, distance=5000, duration=600),
            RouteAlternative(index=1, distance=6000, duration=700),
        ]

    def test_selected_returns_first_by_default(self, two_alternatives):
        result = RouteResult(alternatives=two_alternatives)
        assert result.selected is two_alternatives[0]

    def test_selected_returns_correct_index(self, two_alternatives):
        result = RouteResult(alternatives=two_alternatives, selected_index=1)
        assert result.selected is two_alternatives[1]

    def test_selected_none_when_empty(self):
        result = RouteResult()
        assert result.selected is None

    def test_selected_none_when_index_out_of_range(self, two_alternatives):
        result = RouteResult(alternatives=two_alternatives, selected_index=99)
        assert result.selected is None

    def test_select_valid_index(self, two_alternatives):
        result = RouteResult(alternatives=two_alternatives)
        success = result.select(1)
        assert success is True
        assert result.selected_index == 1

    def test_select_invalid_index_returns_false(self, two_alternatives):
        result = RouteResult(alternatives=two_alternatives)
        success = result.select(99)
        assert success is False
        assert result.selected_index == 0  # 未改变

    def test_select_negative_index_returns_false(self, two_alternatives):
        result = RouteResult(alternatives=two_alternatives)
        success = result.select(-1)
        assert success is False

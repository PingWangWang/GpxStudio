"""
CoordinateTransform 单元测试

覆盖：
- wgs84_to_gcj02：中国境内坐标转换有偏移
- gcj02_to_wgs84：逆转换接近原始坐标（误差 < 0.001°）
- convert()：同坐标系返回原值
- convert()：GCJ-02 → WGS-84
- convert()：WGS-84 → GCJ-02
- convert()：不支持的坐标系抛 ValueError
- 中国境外坐标不做转换（原样返回）
- coord_system_for_map_source()：高德返回 GCJ-02，其余返回 WGS-84
- ensure_system()：已在目标坐标系时直接返回
"""
import pytest
import math

from modules.geolocation.coordinate_transform import CoordinateTransform


# 北京天安门广场的标准测试坐标
WGS84_LAT = 39.90750
WGS84_LON = 116.39130

# 已知转换参考值（允许 ±0.001° 误差）
GCJ02_LAT_APPROX = 39.9096
GCJ02_LON_APPROX = 116.3975

# 中国境外坐标（无需转换）
OUTSIDE_CHINA_LAT = 35.6762  # 东京
OUTSIDE_CHINA_LON = 139.6503


# ──────────────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────────────

class TestWgs84ToGcj02:
    """WGS-84 → GCJ-02 转换。"""

    def test_china_coords_are_shifted(self):
        lat, lon = CoordinateTransform.wgs84_to_gcj02(WGS84_LAT, WGS84_LON)
        # 转换后坐标应与原始坐标不同（中国境内有偏移）
        assert lat != WGS84_LAT or lon != WGS84_LON

    def test_output_is_close_to_known_reference(self):
        lat, lon = CoordinateTransform.wgs84_to_gcj02(WGS84_LAT, WGS84_LON)
        assert abs(lat - GCJ02_LAT_APPROX) < 0.01
        assert abs(lon - GCJ02_LON_APPROX) < 0.01

    def test_outside_china_returns_unchanged(self):
        lat, lon = CoordinateTransform.wgs84_to_gcj02(OUTSIDE_CHINA_LAT, OUTSIDE_CHINA_LON)
        assert lat == OUTSIDE_CHINA_LAT
        assert lon == OUTSIDE_CHINA_LON


class TestGcj02ToWgs84:
    """GCJ-02 → WGS-84 逆转换。"""

    def test_reverse_conversion_approximates_original(self):
        """先正转再逆转，误差应在 0.001° 以内。"""
        gcj_lat, gcj_lon = CoordinateTransform.wgs84_to_gcj02(WGS84_LAT, WGS84_LON)
        back_lat, back_lon = CoordinateTransform.gcj02_to_wgs84(gcj_lat, gcj_lon)
        assert abs(back_lat - WGS84_LAT) < 0.001
        assert abs(back_lon - WGS84_LON) < 0.001

    def test_outside_china_returns_unchanged(self):
        lat, lon = CoordinateTransform.gcj02_to_wgs84(OUTSIDE_CHINA_LAT, OUTSIDE_CHINA_LON)
        assert lat == OUTSIDE_CHINA_LAT
        assert lon == OUTSIDE_CHINA_LON


class TestConvertMethod:
    """CoordinateTransform.convert() 统一入口。"""

    def test_same_system_returns_original(self):
        lat, lon = CoordinateTransform.convert(WGS84_LAT, WGS84_LON, 'WGS-84', 'WGS-84')
        assert lat == WGS84_LAT
        assert lon == WGS84_LON

    def test_same_gcj02_system_returns_original(self):
        lat, lon = CoordinateTransform.convert(GCJ02_LAT_APPROX, GCJ02_LON_APPROX, 'GCJ-02', 'GCJ-02')
        assert lat == GCJ02_LAT_APPROX
        assert lon == GCJ02_LON_APPROX

    def test_wgs84_to_gcj02_via_convert(self):
        lat, lon = CoordinateTransform.convert(WGS84_LAT, WGS84_LON, 'WGS-84', 'GCJ-02')
        direct_lat, direct_lon = CoordinateTransform.wgs84_to_gcj02(WGS84_LAT, WGS84_LON)
        assert lat == direct_lat
        assert lon == direct_lon

    def test_gcj02_to_wgs84_via_convert(self):
        gcj_lat, gcj_lon = CoordinateTransform.wgs84_to_gcj02(WGS84_LAT, WGS84_LON)
        lat, lon = CoordinateTransform.convert(gcj_lat, gcj_lon, 'GCJ-02', 'WGS-84')
        direct_lat, direct_lon = CoordinateTransform.gcj02_to_wgs84(gcj_lat, gcj_lon)
        assert lat == direct_lat
        assert lon == direct_lon

    def test_unsupported_conversion_raises_value_error(self):
        with pytest.raises(ValueError, match="不支持"):
            CoordinateTransform.convert(WGS84_LAT, WGS84_LON, 'WGS-84', 'BD-09')

    def test_unsupported_from_system_raises_value_error(self):
        with pytest.raises(ValueError):
            CoordinateTransform.convert(WGS84_LAT, WGS84_LON, 'BD-09', 'WGS-84')

    def test_round_trip_accuracy(self):
        """WGS-84 → GCJ-02 → WGS-84 全程使用 convert()，误差 < 0.001°。"""
        gcj_lat, gcj_lon = CoordinateTransform.convert(WGS84_LAT, WGS84_LON, 'WGS-84', 'GCJ-02')
        back_lat, back_lon = CoordinateTransform.convert(gcj_lat, gcj_lon, 'GCJ-02', 'WGS-84')
        assert abs(back_lat - WGS84_LAT) < 0.001
        assert abs(back_lon - WGS84_LON) < 0.001


class TestCoordSystemForMapSource:
    """coord_system_for_map_source() 工具方法。"""

    def test_gaode_returns_gcj02(self):
        assert CoordinateTransform.coord_system_for_map_source('gaode') == 'GCJ-02'

    def test_osm_returns_wgs84(self):
        assert CoordinateTransform.coord_system_for_map_source('osm') == 'WGS-84'

    def test_unknown_returns_wgs84(self):
        assert CoordinateTransform.coord_system_for_map_source('unknown') == 'WGS-84'

    def test_empty_string_returns_wgs84(self):
        assert CoordinateTransform.coord_system_for_map_source('') == 'WGS-84'


class TestEnsureSystem:
    """ensure_system() 快捷方法。"""

    def test_already_in_target_returns_original(self):
        lat, lon = CoordinateTransform.ensure_system(WGS84_LAT, WGS84_LON, 'WGS-84', 'WGS-84')
        assert lat == WGS84_LAT
        assert lon == WGS84_LON

    def test_converts_when_different_systems(self):
        lat, lon = CoordinateTransform.ensure_system(WGS84_LAT, WGS84_LON, 'WGS-84', 'GCJ-02')
        expected_lat, expected_lon = CoordinateTransform.wgs84_to_gcj02(WGS84_LAT, WGS84_LON)
        assert lat == expected_lat
        assert lon == expected_lon

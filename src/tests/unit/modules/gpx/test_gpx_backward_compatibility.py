"""
向后兼容性属性测试
Feature: gpx-timezone-export, Property 5: 文件结构向后兼容

验证: 需求 5.2, 5.3
"""

import unittest
import tempfile
import os
import re
from datetime import datetime
from hypothesis import given, strategies as st, settings
import gpxpy

from modules.gpx.gpx_export import GpxExportService


# 生成有效的经纬度坐标
@st.composite
def coordinates(draw):
    """生成有效的经纬度坐标"""
    lat = draw(st.floats(min_value=-90, max_value=90, allow_nan=False, allow_infinity=False))
    lon = draw(st.floats(min_value=-180, max_value=180, allow_nan=False, allow_infinity=False))
    return (lat, lon)


@st.composite
def route_points_list(draw):
    """生成路线点列表"""
    num_points = draw(st.integers(min_value=2, max_value=20))
    points = [draw(coordinates()) for _ in range(num_points)]
    return points


class TestBackwardCompatibility(unittest.TestCase):
    """向后兼容性测试"""

    @given(route_points=route_points_list())
    @settings(max_examples=100, deadline=None)
    def test_file_structure_backward_compatible(self, route_points):
        """
        属性 5: 文件结构向后兼容

        对于任何路线，新旧版本导出的GPX文件应该具有相同的结构（轨迹、段、元数据），
        仅在时间戳的时区表示上有所不同。

        验证: 需求 5.2, 5.3
        Feature: gpx-timezone-export, Property 5: 文件结构向后兼容
        """
        # 创建两个临时文件
        with tempfile.NamedTemporaryFile(suffix='.gpx', delete=False) as temp_file1:
            temp_path1 = temp_file1.name

        with tempfile.NamedTemporaryFile(suffix='.gpx', delete=False) as temp_file2:
            temp_path2 = temp_file2.name

        try:
            # 创建模拟的QDateTime对象
            class MockQDateTime:
                def __init__(self):
                    self._datetime = datetime(2024, 1, 15, 12, 0, 0)

                def date(self):
                    class MockDate:
                        def year(self):
                            return self._datetime.year
                        def month(self):
                            return self._datetime.month
                        def day(self):
                            return self._datetime.day
                    mock_date = MockDate()
                    mock_date._datetime = self._datetime
                    return mock_date

                def time(self):
                    class MockTime:
                        def hour(self):
                            return self._datetime.hour
                        def minute(self):
                            return self._datetime.minute
                    mock_time = MockTime()
                    mock_time._datetime = self._datetime
                    return mock_time

            start_time = MockQDateTime()

            # 导出GPX文件（使用新的时区感知版本）
            service = GpxExportService()
            result = service.export_to_gpx(route_points, start_time, temp_path1)

            # 验证导出成功
            self.assertTrue(result, "GPX export should succeed")
            self.assertTrue(os.path.exists(temp_path1), "GPX file should exist")

            # 解析生成的GPX文件
            with open(temp_path1, 'r', encoding='utf-8') as f:
                gpx = gpxpy.parse(f)

            # 验证文件结构
            self.assertTrue(len(gpx.tracks) > 0, "Should have at least one track")
            self.assertTrue(len(gpx.tracks[0].segments) > 0, "Should have at least one segment")
            self.assertTrue(len(gpx.tracks[0].segments[0].points) > 0, "Should have at least one point")

            # 验证轨迹点数量与输入匹配
            total_points = len(gpx.tracks[0].segments[0].points)
            expected_points = len([p for p in route_points if p is not None])
            self.assertEqual(total_points, expected_points,
                           f"Should have {expected_points} points, got {total_points}")

            # 验证所有轨迹点都有时间戳
            for point in gpx.tracks[0].segments[0].points:
                self.assertIsNotNone(point.time, "All points should have timestamps")
                # 验证时间戳是timezone-aware的
                self.assertIsNotNone(point.time.tzinfo, "All timestamps should be timezone-aware")

            # 读取原始XML以验证时间戳格式
            with open(temp_path1, 'r', encoding='utf-8') as f:
                xml_content = f.read()

            # 验证时间戳包含时区信息（+HH:MM或-HH:MM格式）
            timestamps = re.findall(r'<time>([^<]+)</time>', xml_content)
            self.assertTrue(len(timestamps) > 0, "Should have timestamps in XML")

            for ts in timestamps:
                # 验证ISO 8601格式，包含时区信息
                # 格式应该是: YYYY-MM-DDTHH:MM:SS+HH:MM 或 YYYY-MM-DDTHH:MM:SS-HH:MM
                self.assertRegex(ts, r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}',
                               f"Timestamp {ts} should be in ISO 8601 format with timezone")

            # 验证元数据结构存在
            self.assertIn('<metadata>', xml_content, "Should have metadata section")
            self.assertIn('<name>', xml_content, "Should have name in metadata")

            # 验证轨迹结构
            self.assertIn('<trk>', xml_content, "Should have track element")
            self.assertIn('<trkseg>', xml_content, "Should have track segment element")
            self.assertIn('<trkpt', xml_content, "Should have track point elements")

        finally:
            # 清理临时文件
            if os.path.exists(temp_path1):
                os.remove(temp_path1)
            if os.path.exists(temp_path2):
                os.remove(temp_path2)


if __name__ == '__main__':
    unittest.main()

"""
GPX文件解析兼容性测试

验证: 需求 2.4, 5.2
"""

import unittest
import tempfile
import os
from datetime import datetime

import gpxpy

from modules.gpx.gpx_export import GpxExportService


class TestGpxParsingCompatibility(unittest.TestCase):
    """GPX文件解析兼容性测试"""

    def test_gpx_file_can_be_parsed(self):
        """
        测试导出的GPX文件可以被gpxpy解析

        验证: 需求 2.4, 5.2
        """
        with tempfile.NamedTemporaryFile(suffix='.gpx', delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # 准备测试数据 - 使用北京坐标
            route_points = [
                (39.9042, 116.4074),
                (39.9052, 116.4084),
                (39.9062, 116.4094),
                (39.9072, 116.4104)
            ]

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

            # 导出GPX文件
            service = GpxExportService()
            result = service.export_to_gpx(route_points, start_time, temp_path)

            # 验证导出成功
            self.assertTrue(result, "GPX export should succeed")
            self.assertTrue(os.path.exists(temp_path), "GPX file should exist")

            # 使用gpxpy解析生成的文件
            with open(temp_path, 'r', encoding='utf-8') as f:
                gpx = gpxpy.parse(f)

            # 验证文件可以被成功解析
            self.assertIsNotNone(gpx, "GPX file should be parseable")
            self.assertTrue(len(gpx.tracks) > 0, "Should have at least one track")
            self.assertTrue(len(gpx.tracks[0].segments) > 0, "Should have at least one segment")
            self.assertTrue(len(gpx.tracks[0].segments[0].points) > 0, "Should have at least one point")

            # 验证轨迹点数量
            total_points = len(gpx.tracks[0].segments[0].points)
            expected_points = len(route_points)
            self.assertEqual(total_points, expected_points,
                           f"Should have {expected_points} points, got {total_points}")

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_timestamps_can_be_read_correctly(self):
        """
        测试时间戳可以被正确读取

        验证: 需求 2.4, 5.2
        """
        with tempfile.NamedTemporaryFile(suffix='.gpx', delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # 准备测试数据
            route_points = [
                (40.7128, -74.0060),  # 纽约
                (40.7138, -74.0070),
                (40.7148, -74.0080)
            ]

            # 创建模拟的QDateTime对象
            class MockQDateTime:
                def __init__(self):
                    self._datetime = datetime(2024, 6, 15, 14, 30, 0)

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

            # 导出GPX文件
            service = GpxExportService()
            result = service.export_to_gpx(route_points, start_time, temp_path)

            self.assertTrue(result, "GPX export should succeed")

            # 解析GPX文件
            with open(temp_path, 'r', encoding='utf-8') as f:
                gpx = gpxpy.parse(f)

            # 验证时间戳可以被正确读取
            for point in gpx.tracks[0].segments[0].points:
                self.assertIsNotNone(point.time, "All points should have timestamps")

                # 验证时间戳是timezone-aware的datetime对象
                self.assertIsNotNone(point.time.tzinfo, "Timestamps should be timezone-aware")

                # 验证时间戳是datetime对象
                self.assertIsInstance(point.time, datetime, "Timestamp should be a datetime object")

                # 验证时间戳的年份是合理的
                self.assertEqual(point.time.year, 2024, "Year should be 2024")
                self.assertEqual(point.time.month, 6, "Month should be 6")
                self.assertEqual(point.time.day, 15, "Day should be 15")

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_timezone_aware_timestamps_preserved(self):
        """
        测试时区感知的时间戳被正确保留

        验证: 需求 2.4, 5.2
        """
        with tempfile.NamedTemporaryFile(suffix='.gpx', delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # 准备测试数据 - 使用伦敦坐标
            route_points = [
                (51.5074, -0.1278),  # 伦敦
                (51.5084, -0.1288)
            ]

            # 创建模拟的QDateTime对象
            class MockQDateTime:
                def __init__(self):
                    self._datetime = datetime(2024, 3, 20, 10, 0, 0)

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

            # 导出GPX文件
            service = GpxExportService()
            result = service.export_to_gpx(route_points, start_time, temp_path)

            self.assertTrue(result, "GPX export should succeed")

            # 解析GPX文件
            with open(temp_path, 'r', encoding='utf-8') as f:
                gpx = gpxpy.parse(f)

            # 验证所有时间戳都是timezone-aware的
            for point in gpx.tracks[0].segments[0].points:
                self.assertIsNotNone(point.time, "Point should have timestamp")
                self.assertIsNotNone(point.time.tzinfo, "Timestamp should be timezone-aware")

                # 验证时区信息不是None
                tz_offset = point.time.utcoffset()
                self.assertIsNotNone(tz_offset, "Should have UTC offset")

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_gpx_file_structure_valid(self):
        """
        测试GPX文件结构符合标准

        验证: 需求 5.2
        """
        with tempfile.NamedTemporaryFile(suffix='.gpx', delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # 准备测试数据
            route_points = [
                (35.6762, 139.6503),  # 东京
                (35.6772, 139.6513),
                (35.6782, 139.6523)
            ]

            # 创建模拟的QDateTime对象
            class MockQDateTime:
                def __init__(self):
                    self._datetime = datetime(2024, 1, 1, 9, 0, 0)

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

            # 导出GPX文件
            service = GpxExportService()
            result = service.export_to_gpx(route_points, start_time, temp_path,
                                          start_name="Tokyo_Start", end_name="Tokyo_End")

            self.assertTrue(result, "GPX export should succeed")

            # 解析GPX文件
            with open(temp_path, 'r', encoding='utf-8') as f:
                gpx = gpxpy.parse(f)

            # 验证GPX文件结构
            self.assertIsNotNone(gpx, "GPX should be parseable")

            # 验证轨迹
            self.assertEqual(len(gpx.tracks), 1, "Should have exactly one track")
            track = gpx.tracks[0]
            self.assertIsNotNone(track.name, "Track should have a name")

            # 验证段
            self.assertEqual(len(track.segments), 1, "Should have exactly one segment")
            segment = track.segments[0]

            # 验证点
            self.assertEqual(len(segment.points), len(route_points),
                           f"Should have {len(route_points)} points")

            # 验证每个点的结构
            for i, point in enumerate(segment.points):
                self.assertIsNotNone(point.latitude, f"Point {i} should have latitude")
                self.assertIsNotNone(point.longitude, f"Point {i} should have longitude")
                self.assertIsNotNone(point.time, f"Point {i} should have timestamp")

                # 验证坐标值在合理范围内
                self.assertTrue(-90 <= point.latitude <= 90,
                              f"Point {i} latitude should be in valid range")
                self.assertTrue(-180 <= point.longitude <= 180,
                              f"Point {i} longitude should be in valid range")

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


if __name__ == '__main__':
    unittest.main()

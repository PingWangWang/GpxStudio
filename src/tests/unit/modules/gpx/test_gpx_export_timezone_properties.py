"""
Property-based tests for GPX timezone detection
Feature: gpx-timezone-export
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

import unittest
import tempfile
import re
from datetime import datetime
from hypothesis import given, strategies as st, settings
from unittest.mock import MagicMock, patch

from modules.gpx.gpx_export import GpxExportService


# 生成有效的经纬度坐标
@st.composite
def coordinates(draw):
    """生成有效的经纬度坐标"""
    lat = draw(st.floats(min_value=-90, max_value=90, allow_nan=False, allow_infinity=False))
    lon = draw(st.floats(min_value=-180, max_value=180, allow_nan=False, allow_infinity=False))
    return (lat, lon)


# 生成路线点列表
@st.composite
def route_points(draw):
    """生成路线点列表"""
    num_points = draw(st.integers(min_value=2, max_value=5))
    points = [draw(coordinates()) for _ in range(num_points)]
    return points


class TestTimezoneDetectionProperties(unittest.TestCase):
    """时区检测的属性测试"""

    @given(coord=coordinates())
    @settings(max_examples=10)
    def test_property_timezone_detection_uses_coordinates(self, coord):
        """
        Feature: gpx-timezone-export, Property 1: 时区检测使用起点坐标

        属性: 对于任何有效的坐标，时区检测应该被调用且使用正确的坐标
        验证: 需求 1.1, 1.2
        """
        lat, lon = coord

        # 创建服务实例
        logs = []
        def log_callback(level, message):
            logs.append((level, message))

        service = GpxExportService(logger=log_callback)

        # 调用时区检测
        tz = service._detect_timezone(lat, lon)

        # 验证时区检测被调用（通过检查日志或返回值）
        self.assertIsNotNone(tz, f"时区检测应该返回一个时区对象，坐标: ({lat}, {lon})")

        # 验证日志中包含坐标信息（INFO或WARNING级别）
        coord_in_logs = any(
            (str(lat) in msg or str(lon) in msg)
            for level, msg in logs
        )
        self.assertTrue(
            coord_in_logs,
            f"日志应该包含坐标信息 ({lat}, {lon})"
        )

        # 验证返回的是有效的时区对象
        # 时区对象应该有zone属性或者是pytz.UTC
        try:
            import pytz
            self.assertTrue(
                hasattr(tz, 'zone') or tz == pytz.UTC or str(tz) == 'UTC',
                f"返回值应该是有效的时区对象，得到: {tz}"
            )
        except ImportError:
            # 如果pytz不可用，应该返回标准库的timezone.utc
            from datetime import timezone
            self.assertTrue(
                tz == timezone.utc,
                f"当pytz不可用时，应该返回timezone.utc，得到: {tz}"
            )


class TestTimestampFormatProperties(unittest.TestCase):
    """时间戳格式的属性测试"""

    @given(points=route_points())
    @settings(max_examples=10, deadline=None)
    def test_property_timestamps_contain_timezone_info(self, points):
        """
        Feature: gpx-timezone-export, Property 2: 时间戳包含正确的时区信息

        属性: 对于任何导出的GPX文件，所有轨迹点的时间戳应该包含时区信息且符合ISO 8601格式
        验证: 需求 2.1, 2.2, 2.4
        """
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.gpx', delete=False) as temp_file:
            temp_path = temp_file.name

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
            service = GpxExportService()

            # 导出GPX文件
            result = service.export_to_gpx(points, start_time, temp_path)

            # 验证导出成功
            self.assertTrue(result, f"导出应该成功，路线点数: {len(points)}")

            # 读取并验证文件内容
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取所有时间戳
            timestamps = re.findall(r'<time>([^<]+)</time>', content)

            # 验证至少有一个时间戳
            self.assertTrue(len(timestamps) > 0, "GPX文件应该包含至少一个时间戳")

            # ISO 8601格式正则表达式：YYYY-MM-DDTHH:MM:SS±HH:MM
            iso8601_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$'

            # 验证所有时间戳符合ISO 8601格式且包含时区信息
            for ts in timestamps:
                self.assertRegex(
                    ts,
                    iso8601_pattern,
                    f"时间戳应该符合ISO 8601格式并包含时区信息: {ts}"
                )

                # 验证时区偏移部分存在（+HH:MM或-HH:MM）
                self.assertTrue(
                    '+' in ts or '-' in ts[-6:],  # 检查最后6个字符中是否有时区偏移
                    f"时间戳应该包含时区偏移信息: {ts}"
                )

        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestTimezoneConsistencyProperties(unittest.TestCase):
    """时区一致性的属性测试"""

    @given(points=route_points())
    @settings(max_examples=10, deadline=None)
    def test_property_timezone_consistency(self, points):
        """
        Feature: gpx-timezone-export, Property 3: 时区信息一致性

        属性: 对于任何导出的GPX文件，所有轨迹点应该使用相同的时区偏移
        验证: 需求 2.3
        """
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.gpx', delete=False) as temp_file:
            temp_path = temp_file.name

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
            service = GpxExportService()

            # 导出GPX文件
            result = service.export_to_gpx(points, start_time, temp_path)

            # 验证导出成功
            self.assertTrue(result, f"导出应该成功，路线点数: {len(points)}")

            # 读取并验证文件内容
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取所有时间戳
            timestamps = re.findall(r'<time>([^<]+)</time>', content)

            # 如果有时间戳，验证它们的时区一致性
            if len(timestamps) > 0:
                # 提取所有时区偏移（最后6个字符，格式为±HH:MM）
                timezones = []
                for ts in timestamps:
                    # 提取时区偏移部分
                    tz_offset = ts[-6:]  # 例如: +08:00 或 +00:00
                    timezones.append(tz_offset)

                # 验证所有时区偏移相同
                first_tz = timezones[0]
                for tz in timezones:
                    self.assertEqual(
                        tz,
                        first_tz,
                        f"所有时间戳应该使用相同的时区偏移。期望: {first_tz}, 实际: {tz}"
                    )

                # 验证时区偏移格式正确（±HH:MM）
                tz_pattern = r'^[+-]\d{2}:\d{2}$'
                for tz in timezones:
                    self.assertRegex(
                        tz,
                        tz_pattern,
                        f"时区偏移应该符合±HH:MM格式: {tz}"
                    )

        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestErrorFallbackProperties(unittest.TestCase):
    """错误回退的属性测试"""

    @given(points=route_points(), failure_scenario=st.sampled_from(['timezonefinder_unavailable', 'pytz_unavailable', 'query_failure', 'invalid_coordinates']))
    @settings(max_examples=100, deadline=None)
    def test_property_timezone_detection_fallback_to_utc(self, points, failure_scenario):
        """
        Feature: gpx-timezone-export, Property 4: 时区检测失败时回退到UTC

        属性: 对于任何时区检测失败的情况，系统应该回退到UTC时区，记录警告日志，并成功完成导出操作
        验证: 需求 4.1, 4.2, 4.4
        """
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.gpx', delete=False) as temp_file:
            temp_path = temp_file.name

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

            # 捕获日志
            logs = []
            def log_callback(level, message):
                logs.append((level, message))

            service = GpxExportService(logger=log_callback)

            # 根据失败场景模拟不同的错误
            if failure_scenario == 'timezonefinder_unavailable':
                # 模拟TimezoneFinder库不可用
                with patch('builtins.__import__', side_effect=lambda name, *args, **kwargs:
                          (_ for _ in ()).throw(ImportError(f"No module named '{name}'")) if name == 'timezonefinder' else __import__(name, *args, **kwargs)):
                    result = service.export_to_gpx(points, start_time, temp_path)

            elif failure_scenario == 'pytz_unavailable':
                # 模拟pytz库不可用（这种情况下应该回退到标准库的timezone.utc）
                # 注意：实际实现中，如果pytz不可用，会使用标准库的timezone.utc
                with patch('builtins.__import__', side_effect=lambda name, *args, **kwargs:
                          (_ for _ in ()).throw(ImportError(f"No module named '{name}'")) if name == 'pytz' else __import__(name, *args, **kwargs)):
                    result = service.export_to_gpx(points, start_time, temp_path)

            elif failure_scenario == 'query_failure':
                # 模拟TimezoneFinder查询返回None（海洋坐标）
                # 使用海洋坐标来触发这个场景
                ocean_points = [(0.0, -160.0), (0.0, -161.0)]
                result = service.export_to_gpx(ocean_points, start_time, temp_path)

            elif failure_scenario == 'invalid_coordinates':
                # 模拟无效坐标（空列表或全为None）
                invalid_points = []
                result = service.export_to_gpx(invalid_points, start_time, temp_path)

            # 验证导出操作成功完成
            self.assertTrue(result, f"导出应该成功，即使时区检测失败。失败场景: {failure_scenario}")

            # 验证文件存在
            self.assertTrue(os.path.exists(temp_path), f"GPX文件应该被创建。失败场景: {failure_scenario}")

            # 读取文件内容
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取时间戳
            timestamps = re.findall(r'<time>([^<]+)</time>', content)

            # 如果有时间戳，验证使用了UTC时区（+00:00）
            if len(timestamps) > 0:
                for ts in timestamps:
                    self.assertIn('+00:00', ts,
                                f"时区检测失败时应该使用UTC（+00:00）。失败场景: {failure_scenario}, 时间戳: {ts}")

            # 验证警告日志被记录
            warning_logs = [msg for level, msg in logs if level == 'WARNING']
            self.assertTrue(len(warning_logs) > 0,
                          f"应该记录警告日志。失败场景: {failure_scenario}")

            # 验证警告日志包含相关信息
            warning_text = ' '.join(warning_logs)
            if failure_scenario in ['timezonefinder_unavailable', 'pytz_unavailable']:
                self.assertTrue('不可用' in warning_text or 'UTC' in warning_text,
                              f"警告日志应该提到库不可用或使用UTC。失败场景: {failure_scenario}")
            elif failure_scenario == 'query_failure':
                self.assertTrue('未找到时区' in warning_text or 'UTC' in warning_text,
                              f"警告日志应该提到未找到时区或使用UTC。失败场景: {failure_scenario}")
            elif failure_scenario == 'invalid_coordinates':
                self.assertTrue('未找到有效的路线点' in warning_text or 'UTC' in warning_text,
                              f"警告日志应该提到未找到有效路线点或使用UTC。失败场景: {failure_scenario}")

        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)


if __name__ == '__main__':
    unittest.main()

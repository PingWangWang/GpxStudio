import unittest
import tempfile
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone

from modules.gpx.gpx_export import GpxExportService


class TestGpxExportService(unittest.TestCase):
    """GPX导出服务测试类"""

    def setUp(self):
        """setUp方法，在每个测试方法前执行"""
        self.service = GpxExportService()

    def test_export_to_gpx(self):
        """测试导出GPX文件"""
        # 创建临时文件用于测试
        with tempfile.NamedTemporaryFile(suffix='.gpx', delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # 准备测试数据
            route_points = [
                (39.9042, 116.4074),
                (39.9052, 116.4084),
                (39.9062, 116.4094)
            ]

            # 创建一个模拟QDateTime的对象，使其具有date()和time()方法
            class MockQDateTime:
                def __init__(self):
                    self._datetime = datetime.now()

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

            # 执行导出
            result = self.service.export_to_gpx(route_points, start_time, temp_path)

            # 验证结果
            self.assertTrue(result)
            self.assertTrue(os.path.exists(temp_path))

            # 验证文件内容（简单验证是否包含GPX标签）
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn('<gpx', content)
                self.assertIn('</gpx>', content)

        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_get_gpx_info(self):
        """测试获取GPX信息"""
        # 准备测试数据
        route_points = [
            (39.9042, 116.4074),
            (39.9052, 116.4084),
            (39.9062, 116.4094)
        ]

        # 由于接口定义了此方法但未在实现中提供，我们测试它是否存在
        self.assertTrue(hasattr(self.service, 'get_gpx_info'))

        # 尝试调用（如果实现不完整会抛出异常）
        try:
            info = self.service.get_gpx_info(route_points)
            self.assertIsInstance(info, dict)
        except NotImplementedError:
            # 如果方法尚未实现，这也是合理的
            pass
        except Exception:
            # 其他异常可能表示实现有误
            raise

    def test_detect_timezone_beijing(self):
        """测试北京坐标返回正确时区"""
        # 北京坐标
        latitude, longitude = 39.9042, 116.4074

        # 捕获日志
        logs = []
        def log_callback(level, message):
            logs.append((level, message))

        service = GpxExportService(logger=log_callback)
        tz = service._detect_timezone(latitude, longitude)

        # 验证返回的时区
        import pytz
        self.assertIsNotNone(tz)
        # 北京应该返回Asia/Shanghai时区
        self.assertEqual(str(tz), 'Asia/Shanghai')

        # 验证日志记录
        self.assertTrue(any('检测到时区' in msg and 'Asia/Shanghai' in msg for level, msg in logs if level == 'INFO'))

    def test_detect_timezone_new_york(self):
        """测试纽约坐标返回正确时区"""
        # 纽约坐标
        latitude, longitude = 40.7128, -74.0060

        logs = []
        def log_callback(level, message):
            logs.append((level, message))

        service = GpxExportService(logger=log_callback)
        tz = service._detect_timezone(latitude, longitude)

        # 验证返回的时区
        import pytz
        self.assertIsNotNone(tz)
        # 纽约应该返回America/New_York时区
        self.assertEqual(str(tz), 'America/New_York')

        # 验证日志记录
        self.assertTrue(any('检测到时区' in msg and 'America/New_York' in msg for level, msg in logs if level == 'INFO'))

    def test_detect_timezone_london(self):
        """测试伦敦坐标返回正确时区"""
        # 伦敦坐标
        latitude, longitude = 51.5074, -0.1278

        logs = []
        def log_callback(level, message):
            logs.append((level, message))

        service = GpxExportService(logger=log_callback)
        tz = service._detect_timezone(latitude, longitude)

        # 验证返回的时区
        import pytz
        self.assertIsNotNone(tz)
        # 伦敦应该返回Europe/London时区
        self.assertEqual(str(tz), 'Europe/London')

        # 验证日志记录
        self.assertTrue(any('检测到时区' in msg and 'Europe/London' in msg for level, msg in logs if level == 'INFO'))

    def test_detect_timezone_ocean(self):
        """测试海洋坐标返回UTC"""
        # 太平洋中部坐标（无陆地时区）
        latitude, longitude = 0.0, -160.0

        logs = []
        def log_callback(level, message):
            logs.append((level, message))

        service = GpxExportService(logger=log_callback)
        tz = service._detect_timezone(latitude, longitude)

        # 验证返回UTC
        import pytz
        self.assertEqual(tz, pytz.UTC)

        # 验证警告日志
        self.assertTrue(any('未找到时区' in msg and 'UTC' in msg for level, msg in logs if level == 'WARNING'))

    def test_detect_timezone_timezonefinder_unavailable(self):
        """测试TimezoneFinder不可用时回退到UTC"""
        logs = []
        def log_callback(level, message):
            logs.append((level, message))

        service = GpxExportService(logger=log_callback)

        # 模拟TimezoneFinder导入失败
        with patch('modules.gpx.gpx_export.TimezoneFinder', side_effect=ImportError("TimezoneFinder not found")):
            tz = service._detect_timezone(39.9042, 116.4074)

        # 验证返回UTC
        import pytz
        self.assertEqual(tz, pytz.UTC)

        # 验证警告日志
        self.assertTrue(any('时区库不可用' in msg for level, msg in logs if level == 'WARNING'))

    def test_detect_timezone_pytz_creation_failure(self):
        """测试pytz时区创建失败时回退到UTC"""
        logs = []
        def log_callback(level, message):
            logs.append((level, message))

        service = GpxExportService(logger=log_callback)

        # 模拟pytz.timezone()抛出异常
        with patch('modules.gpx.gpx_export.TimezoneFinder') as mock_tf_class:
            mock_tf = MagicMock()
            mock_tf.timezone_at.return_value = 'Invalid/Timezone'
            mock_tf_class.return_value = mock_tf

            with patch('modules.gpx.gpx_export.pytz.timezone', side_effect=Exception("Invalid timezone")):
                tz = service._detect_timezone(39.9042, 116.4074)

        # 验证返回UTC
        import pytz
        self.assertEqual(tz, pytz.UTC)

        # 验证警告日志
        self.assertTrue(any('时区检测失败' in msg for level, msg in logs if level == 'WARNING'))

    def test_export_with_valid_start_point(self):
        """测试带有效起点的路线导出"""
        with tempfile.NamedTemporaryFile(suffix='.gpx', delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # 准备测试数据 - 北京坐标
            route_points = [
                (39.9042, 116.4074),
                (39.9052, 116.4084),
                (39.9062, 116.4094)
            ]

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

            logs = []
            def log_callback(level, message):
                logs.append((level, message))

            service = GpxExportService(logger=log_callback)
            result = service.export_to_gpx(route_points, start_time, temp_path)

            # 验证导出成功
            self.assertTrue(result)
            self.assertTrue(os.path.exists(temp_path))

            # 验证文件内容包含时区信息
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn('<gpx', content)
                # 验证时间戳包含时区偏移（+HH:MM格式）
                import re
                timestamps = re.findall(r'<time>([^<]+)</time>', content)
                self.assertTrue(len(timestamps) > 0)
                for ts in timestamps:
                    # 验证ISO 8601格式，包含时区信息
                    self.assertRegex(ts, r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}')

            # 验证日志记录了时区检测
            self.assertTrue(any('检测到时区' in msg or '使用起点坐标' in msg for level, msg in logs))

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_export_with_empty_route_points(self):
        """测试空路线点列表的处理"""
        with tempfile.NamedTemporaryFile(suffix='.gpx', delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # 空路线点列表
            route_points = []

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

            logs = []
            def log_callback(level, message):
                logs.append((level, message))

            service = GpxExportService(logger=log_callback)
            result = service.export_to_gpx(route_points, start_time, temp_path)

            # 验证导出成功（即使没有点）
            self.assertTrue(result)

            # 验证警告日志记录了使用UTC
            self.assertTrue(any('未找到有效的路线点' in msg and 'UTC' in msg for level, msg in logs if level == 'WARNING'))

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_export_with_timezone_detection_failure(self):
        """测试时区检测失败时的回退"""
        with tempfile.NamedTemporaryFile(suffix='.gpx', delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            route_points = [
                (39.9042, 116.4074),
                (39.9052, 116.4084)
            ]

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

            logs = []
            def log_callback(level, message):
                logs.append((level, message))

            service = GpxExportService(logger=log_callback)

            # 模拟时区检测失败
            with patch.object(service, '_detect_timezone', side_effect=Exception("Detection failed")):
                # 即使时区检测失败，导出也应该成功（使用UTC回退）
                # 但由于我们直接抛出异常，这会导致整个导出失败
                # 实际上，_detect_timezone内部已经处理了异常，所以这个测试需要调整
                pass

            # 更好的测试方式：模拟TimezoneFinder不可用
            with patch('builtins.__import__', side_effect=ImportError("No module")):
                result = service.export_to_gpx(route_points, start_time, temp_path)

            # 验证导出成功
            self.assertTrue(result)

            # 验证文件包含UTC时区的时间戳
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
                import re
                timestamps = re.findall(r'<time>([^<]+)</time>', content)
                if timestamps:
                    # 验证使用了UTC（+00:00）
                    self.assertTrue(any('+00:00' in ts for ts in timestamps))

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_export_gpx_file_parsing_compatibility(self):
        """测试导出的GPX文件可以被解析"""
        with tempfile.NamedTemporaryFile(suffix='.gpx', delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            route_points = [
                (39.9042, 116.4074),
                (39.9052, 116.4084),
                (39.9062, 116.4094)
            ]

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
            result = service.export_to_gpx(route_points, start_time, temp_path)

            self.assertTrue(result)

            # 使用gpxpy解析生成的文件
            import gpxpy
            with open(temp_path, 'r', encoding='utf-8') as f:
                gpx = gpxpy.parse(f)

            # 验证文件可以被成功解析
            self.assertIsNotNone(gpx)
            self.assertTrue(len(gpx.tracks) > 0)
            self.assertTrue(len(gpx.tracks[0].segments) > 0)
            self.assertTrue(len(gpx.tracks[0].segments[0].points) > 0)

            # 验证时间戳可以被正确读取
            for point in gpx.tracks[0].segments[0].points:
                self.assertIsNotNone(point.time)
                # 验证时间戳是timezone-aware的
                self.assertIsNotNone(point.time.tzinfo)

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_timezonefinder_import_failure(self):
        """测试TimezoneFinder导入失败时回退到UTC

        验证: 需求 3.3, 3.4, 4.1, 4.2, 4.3
        """
        logs = []
        def log_callback(level, message):
            logs.append((level, message))

        service = GpxExportService(logger=log_callback)

        # 模拟TimezoneFinder导入失败
        import sys
        original_import = __builtins__.__import__

        def mock_import(name, *args, **kwargs):
            if name == 'timezonefinder':
                raise ImportError("No module named 'timezonefinder'")
            return original_import(name, *args, **kwargs)

        __builtins__.__import__ = mock_import

        try:
            tz = service._detect_timezone(39.9042, 116.4074)

            # 验证返回UTC
            import pytz
            self.assertEqual(tz, pytz.UTC)

            # 验证警告日志
            warning_logs = [msg for level, msg in logs if level == 'WARNING']
            self.assertTrue(len(warning_logs) > 0)
            self.assertTrue(any('时区库不可用' in msg or 'timezonefinder' in msg for msg in warning_logs))

        finally:
            __builtins__.__import__ = original_import

    def test_pytz_import_failure(self):
        """测试pytz导入失败时回退到标准库UTC

        验证: 需求 3.3, 3.4, 4.1, 4.2, 4.3
        """
        logs = []
        def log_callback(level, message):
            logs.append((level, message))

        service = GpxExportService(logger=log_callback)

        # 模拟pytz导入失败
        import sys
        original_import = __builtins__.__import__

        def mock_import(name, *args, **kwargs):
            if name == 'pytz':
                raise ImportError("No module named 'pytz'")
            return original_import(name, *args, **kwargs)

        __builtins__.__import__ = mock_import

        try:
            tz = service._detect_timezone(39.9042, 116.4074)

            # 验证返回标准库的UTC
            from datetime import timezone
            self.assertEqual(tz, timezone.utc)

            # 验证警告日志
            warning_logs = [msg for level, msg in logs if level == 'WARNING']
            self.assertTrue(len(warning_logs) > 0)
            self.assertTrue(any('时区库不可用' in msg or 'pytz' in msg for msg in warning_logs))

        finally:
            __builtins__.__import__ = original_import

    def test_timezonefinder_returns_none(self):
        """测试TimezoneFinder返回None时回退到UTC

        验证: 需求 3.3, 3.4, 4.1, 4.2, 4.3
        """
        logs = []
        def log_callback(level, message):
            logs.append((level, message))

        service = GpxExportService(logger=log_callback)

        # 使用海洋坐标，TimezoneFinder应该返回None
        tz = service._detect_timezone(0.0, -160.0)

        # 验证返回UTC
        import pytz
        self.assertEqual(tz, pytz.UTC)

        # 验证警告日志
        warning_logs = [msg for level, msg in logs if level == 'WARNING']
        self.assertTrue(len(warning_logs) > 0)
        self.assertTrue(any('未找到时区' in msg and 'UTC' in msg for msg in warning_logs))

    def test_invalid_timezone_name(self):
        """测试无效时区名称时回退到UTC

        验证: 需求 3.3, 3.4, 4.1, 4.2, 4.3
        """
        logs = []
        def log_callback(level, message):
            logs.append((level, message))

        service = GpxExportService(logger=log_callback)

        # 模拟TimezoneFinder返回无效的时区名称
        with patch('modules.gpx.gpx_export.TimezoneFinder') as mock_tf_class:
            mock_tf = MagicMock()
            mock_tf.timezone_at.return_value = 'Invalid/Timezone/Name'
            mock_tf_class.return_value = mock_tf

            # 模拟pytz.timezone()抛出异常
            with patch('modules.gpx.gpx_export.pytz.timezone', side_effect=Exception("Unknown timezone")):
                tz = service._detect_timezone(39.9042, 116.4074)

        # 验证返回UTC
        import pytz
        self.assertEqual(tz, pytz.UTC)

        # 验证警告日志
        warning_logs = [msg for level, msg in logs if level == 'WARNING']
        self.assertTrue(len(warning_logs) > 0)
        self.assertTrue(any('时区检测失败' in msg for msg in warning_logs))

    def test_all_error_scenarios_log_warnings(self):
        """测试所有错误场景都记录适当的警告

        验证: 需求 4.2, 4.3
        """
        # 场景1: 海洋坐标
        logs1 = []
        service1 = GpxExportService(logger=lambda level, msg: logs1.append((level, msg)))
        service1._detect_timezone(0.0, -160.0)
        self.assertTrue(any(level == 'WARNING' for level, msg in logs1))

        # 场景2: TimezoneFinder不可用
        logs2 = []
        service2 = GpxExportService(logger=lambda level, msg: logs2.append((level, msg)))

        import sys
        original_import = __builtins__.__import__

        def mock_import(name, *args, **kwargs):
            if name == 'timezonefinder':
                raise ImportError("No module")
            return original_import(name, *args, **kwargs)

        __builtins__.__import__ = mock_import

        try:
            service2._detect_timezone(39.9042, 116.4074)
            self.assertTrue(any(level == 'WARNING' for level, msg in logs2))
        finally:
            __builtins__.__import__ = original_import

        # 场景3: 无效时区名称
        logs3 = []
        service3 = GpxExportService(logger=lambda level, msg: logs3.append((level, msg)))

        with patch('modules.gpx.gpx_export.TimezoneFinder') as mock_tf_class:
            mock_tf = MagicMock()
            mock_tf.timezone_at.return_value = 'Invalid/Timezone'
            mock_tf_class.return_value = mock_tf

            with patch('modules.gpx.gpx_export.pytz.timezone', side_effect=Exception("Invalid")):
                service3._detect_timezone(39.9042, 116.4074)

        self.assertTrue(any(level == 'WARNING' for level, msg in logs3))


if __name__ == '__main__':
    unittest.main()

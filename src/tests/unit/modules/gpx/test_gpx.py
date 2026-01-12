import unittest
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock

from modules.gpx.gpx_export import GpxExportService


class TestGpxExportService(unittest.TestCase):
    """GPX导出服务测试类"""

    def setUp(self):
        """setUp方法，在每个测试方法前执行"""
        self.exporter = GpxExportService()

    def test_export_to_gpx_success(self):
        """测试成功导出GPX文件"""
        # 创建模拟的QDateTime对象
        class MockQDateTime:
            class MockDate:
                def year(self): return 2023
                def month(self): return 1
                def day(self): return 1
            class MockTime:
                def hour(self): return 10
                def minute(self): return 0
            def date(self): return MockQDateTime.MockDate()
            def time(self): return MockQDateTime.MockTime()
        
        mock_datetime = MockQDateTime()
        
        # 使用临时文件进行测试
        with tempfile.NamedTemporaryFile(suffix='.gpx', delete=False) as tmp_file:
            temp_filename = tmp_file.name
        
        try:
            route_points = [(39.9042, 116.4074), (39.9052, 116.4084)]
            success = self.exporter.export_to_gpx(route_points, mock_datetime, temp_filename)
            
            # 验证保存成功
            self.assertTrue(success)
            
            # 验证文件确实存在且包含GPX内容
            with open(temp_filename, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn('<gpx', content)
                self.assertIn('</gpx>', content)
                
        finally:
            # 清理临时文件
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

    def test_export_to_gpx_with_segments(self):
        """测试导出带分段的GPX文件"""
        # 创建模拟的QDateTime对象
        class MockQDateTime:
            class MockDate:
                def year(self): return 2023
                def month(self): return 1
                def day(self): return 1
            class MockTime:
                def hour(self): return 10
                def minute(self): return 0
            def date(self): return MockQDateTime.MockDate()
            def time(self): return MockQDateTime.MockTime()
        
        mock_datetime = MockQDateTime()
        
        # 使用临时文件进行测试
        with tempfile.NamedTemporaryFile(suffix='.gpx', delete=False) as tmp_file:
            temp_filename = tmp_file.name
        
        try:
            # 包含分段的路线点
            route_points = [(39.9042, 116.4074), (39.9052, 116.4084), None, (39.9062, 116.4094)]
            success = self.exporter.export_to_gpx(route_points, mock_datetime, temp_filename)
            
            # 验证保存成功
            self.assertTrue(success)
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

    def test_logger_callback(self):
        """测试日志记录回调功能"""
        # 创建mock logger
        mock_logger = Mock()
        exporter = GpxExportService(logger=mock_logger)
        
        # 测试日志记录方法
        exporter.log("INFO", "Test message")
        
        # 验证logger被调用
        mock_logger.assert_called_once_with("INFO", "Test message")


if __name__ == '__main__':
    unittest.main()
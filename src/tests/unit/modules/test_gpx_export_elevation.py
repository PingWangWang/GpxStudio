import unittest
import sys
import os
import tempfile
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from modules.gpx.gpx_export import GpxExportService


class TestGpxExportServiceElevation(unittest.TestCase):
    """GPX导出服务海拔功能测试类"""

    def setUp(self):
        """setUp方法，在每个测试方法前执行"""
        self.service = GpxExportService()

    def test_export_with_elevation(self):
        """测试导出带海拔数据的GPX文件"""
        # 创建带海拔的路线点
        route_points = [
            (39.9042, 116.4074, 100.0),  # 带海拔的点
            (39.9052, 116.4084, 150.0),  # 带海拔的点
            (39.9062, 116.4094, 200.0),  # 带海拔的点
        ]

        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.gpx', delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            # 模拟QDateTime对象
            class MockQDateTime:
                def date(self):
                    class MockDate:
                        def year(self):
                            return 2026
                        
                        def month(self):
                            return 1
                        
                        def day(self):
                            return 12
                    return MockDate()
                
                def time(self):
                    class MockTime:
                        def hour(self):
                            return 12
                        
                        def minute(self):
                            return 0
                    return MockTime()

            mock_datetime = MockQDateTime()

            # 执行导出
            result = self.service.export_to_gpx(route_points, mock_datetime, temp_file_path)

            # 验证导出成功
            self.assertTrue(result)

            # 验证文件存在
            self.assertTrue(os.path.exists(temp_file_path))

            # 验证文件内容包含海拔数据
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 从临时文件路径提取文件名
            expected_name = os.path.splitext(os.path.basename(temp_file_path))[0]
            
            # 验证包含metadata
            self.assertIn('<metadata>', content)
            self.assertIn(f'<name>{expected_name}</name>', content)
            self.assertIn('<author>', content)
            self.assertIn('<name>gpx.studio</name>', content)
            self.assertIn('<link href="https://gpx.studio"/>', content)

            # 验证包含trk和trkseg
            self.assertIn('<trk>', content)
            self.assertIn('<trkseg>', content)

            # 验证包含elevation数据
            self.assertIn('<ele>100.0</ele>', content)
            self.assertIn('<ele>150.0</ele>', content)
            self.assertIn('<ele>200.0</ele>', content)

        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_export_without_elevation(self):
        """测试导出不带海拔数据的GPX文件"""
        # 创建不带海拔的路线点
        route_points = [
            (39.9042, 116.4074),  # 不带海拔的点
            (39.9052, 116.4084),  # 不带海拔的点
            (39.9062, 116.4094),  # 不带海拔的点
        ]

        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.gpx', delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            # 模拟QDateTime对象
            class MockQDateTime:
                def date(self):
                    class MockDate:
                        def year(self):
                            return 2026
                        
                        def month(self):
                            return 1
                        
                        def day(self):
                            return 12
                    return MockDate()
                
                def time(self):
                    class MockTime:
                        def hour(self):
                            return 12
                        
                        def minute(self):
                            return 0
                    return MockTime()

            mock_datetime = MockQDateTime()

            # 执行导出
            result = self.service.export_to_gpx(route_points, mock_datetime, temp_file_path)

            # 验证导出成功
            self.assertTrue(result)

            # 验证文件存在
            self.assertTrue(os.path.exists(temp_file_path))

            # 验证文件内容不包含海拔数据
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 验证包含metadata
            self.assertIn('<metadata>', content)

            # 验证包含trk和trkseg
            self.assertIn('<trk>', content)
            self.assertIn('<trkseg>', content)

            # 验证不包含elevation数据
            self.assertNotIn('<ele>', content)

        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)


if __name__ == "__main__":
    unittest.main()

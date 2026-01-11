import unittest
from unittest.mock import patch, MagicMock

from services.osm.osm_routing import OsmRoutingService


class TestOsmRoutingService(unittest.TestCase):
    """OSM路线规划服务测试类"""

    def setUp(self):
        """setUp方法，在每个测试方法前执行"""
        self.service = OsmRoutingService()

    @patch('requests.get')
    def test_plan_route_success(self, mock_get):
        """测试成功规划路线"""
        # 模拟API响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'code': 'Ok',
            'routes': [{
                'geometry': {
                    'coordinates': [[116.4074, 39.9042], [116.4084, 39.9052], [116.4094, 39.9062]]
                },
                'duration': 1200,  # 20分钟，单位是秒
                'distance': 2000    # 2公里，单位是米
            }]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # 执行测试
        points = [(39.9042, 116.4074), (39.9062, 116.4094)]  # 起点和终点
        route_points, estimated_duration = self.service.plan_route(points, "驾车")

        # 验证结果
        self.assertIsInstance(route_points, list)
        self.assertGreater(len(route_points), 0)
        self.assertIsInstance(estimated_duration, int)
        self.assertGreater(estimated_duration, 0)
        
        # 验证路线点格式
        for point in route_points:
            self.assertIsInstance(point, tuple)
            self.assertEqual(len(point), 2)
            lat, lon = point
            self.assertIsInstance(lat, float)
            self.assertIsInstance(lon, float)

    @patch('requests.get')
    def test_plan_route_api_error(self, mock_get):
        """测试API错误时的处理"""
        # 模拟API错误响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'code': 'NoRoute',
            'message': '无法找到路线'
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # 执行测试
        points = [(90.0, 180.0), (89.0, 179.0)]  # 极端坐标，可能无路线
        route_points, estimated_duration = self.service.plan_route(points, "驾车")

        # 验证返回默认值
        self.assertIsInstance(route_points, list)
        self.assertEqual(len(route_points), 0)
        self.assertEqual(estimated_duration, 0)

    @patch('requests.get')
    def test_plan_route_network_error(self, mock_get):
        """测试网络错误时的处理"""
        # 模拟网络错误
        mock_get.side_effect = Exception("Network error")

        # 执行测试并验证异常处理
        points = [(39.9042, 116.4074), (39.9052, 116.4084)]
        route_points, estimated_duration = self.service.plan_route(points, "驾车")

        # 验证返回默认值而不是抛出异常
        self.assertIsInstance(route_points, list)
        self.assertEqual(len(route_points), 0)
        self.assertEqual(estimated_duration, 0)

    def test_calculate_distance(self):
        """测试计算总距离功能"""
        # 创建一些测试路线点
        route_points = [
            (39.9042, 116.4074),  # 北京某点
            (39.9052, 116.4084),  # 相近点
        ]
        
        # 计算距离
        distance = self.service.calculate_distance(route_points)
        
        # 验证返回值类型
        self.assertIsInstance(distance, float)
        self.assertGreaterEqual(distance, 0.0)


if __name__ == '__main__':
    unittest.main()
import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# 添加src目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from services.gaode.gaode_routing import GaodeRoutingService


class TestGaodeRoutingServiceElevation(unittest.TestCase):
    """高德地图路线规划服务海拔功能测试类"""

    def setUp(self):
        """setUp方法，在每个测试方法前执行"""
        self.service = GaodeRoutingService(api_key="test_api_key")

    @patch('requests.post')
    def test_get_elevation_success(self, mock_post):
        """测试成功获取海拔数据"""
        # 模拟API响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"elevation": 100.0},
                {"elevation": 200.0},
                {"elevation": 300.0}
            ]
        }
        mock_post.return_value = mock_response

        # 执行测试
        points = [(39.9042, 116.4074), (39.9142, 116.4174), (39.9242, 116.4274)]
        points_with_elevation = self.service._get_elevation(points)

        # 验证结果
        self.assertEqual(len(points_with_elevation), 3)
        for i, (lat, lon, elevation) in enumerate(points_with_elevation):
            self.assertEqual(lat, points[i][0])
            self.assertEqual(lon, points[i][1])
            self.assertGreater(elevation, 0)

    @patch('requests.post')
    def test_get_elevation_failure(self, mock_post):
        """测试获取海拔数据失败"""
        # 模拟API响应异常
        mock_post.side_effect = Exception("API Error")

        # 执行测试
        points = [(39.9042, 116.4074), (39.9142, 116.4174)]
        points_with_elevation = self.service._get_elevation(points)

        # 验证结果（应该返回带默认海拔0.0的点）
        self.assertEqual(len(points_with_elevation), 2)
        for i, (lat, lon, elevation) in enumerate(points_with_elevation):
            self.assertEqual(lat, points[i][0])
            self.assertEqual(lon, points[i][1])
            self.assertEqual(elevation, 0.0)

    @patch('requests.get')
    @patch('services.gaode.gaode_routing.GaodeRoutingService._get_elevation')
    def test_plan_route_with_elevation(self, mock_get_elevation, mock_get):
        """测试规划路线时获取海拔数据"""
        # 模拟高德API响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'status': '1',
            'route': {
                'paths': [{
                    'duration': '1200',
                    'steps': [{
                        'polyline': '116.4074,39.9042;116.4084,39.9052;116.4094,39.9062'
                    }]
                }]
            }
        }
        mock_get.return_value = mock_response

        # 模拟海拔API响应
        mock_get_elevation.return_value = [
            (39.9042, 116.4074, 100.0),
            (39.9052, 116.4084, 150.0),
            (39.9062, 116.4094, 200.0)
        ]

        # 执行测试
        points = [(39.9042, 116.4074), (39.9062, 116.4094)]
        route_points, estimated_duration = self.service.plan_route(points, "驾车")

        # 验证结果
        self.assertIsInstance(route_points, list)
        self.assertGreater(len(route_points), 0)
        # 验证每个点都包含海拔数据
        for point in route_points:
            if point is not None:
                self.assertEqual(len(point), 3)
                self.assertIsInstance(point[2], float)
        self.assertIsInstance(estimated_duration, int)
        self.assertGreater(estimated_duration, 0)


if __name__ == "__main__":
    unittest.main()

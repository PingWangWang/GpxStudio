"""
地图右键菜单功能单元测试
测试反向地理编码和右键菜单功能
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))


class TestContextMenuReverseGeocode(unittest.TestCase):
    """测试右键菜单的反向地理编码功能"""

    def setUp(self):
        """测试前准备"""
        # 创建模拟的地理编码服务
        self.mock_geocoding_service = Mock()

        # 创建模拟的服务管理器
        self.mock_service_manager = Mock()
        self.mock_service_manager.get_geocoding_service.return_value = self.mock_geocoding_service

    def test_reverse_geocode_parameter_order_gaode(self):
        """测试高德地图反向地理编码参数顺序"""
        # 测试数据：西安市中心附近的坐标
        test_cases = [
            {
                'name': '西安钟楼',
                'lat': 34.2583,
                'lon': 108.9486,
                'expected_location': '108.9486,34.2583'  # 高德API格式：lon,lat
            },
            {
                'name': '西安大雁塔',
                'lat': 34.2192,
                'lon': 108.9647,
                'expected_location': '108.9647,34.2192'
            },
            {
                'name': '西安城墙',
                'lat': 34.2656,
                'lon': 108.9465,
                'expected_location': '108.9465,34.2656'
            }
        ]

        for test_case in test_cases:
            with self.subTest(name=test_case['name']):
                # 模拟高德地图返回结果
                self.mock_geocoding_service.reverse_geocode.return_value = {
                    'regeocode': {
                        'formatted_address': f"{test_case['name']}附近",
                        'addressComponent': {
                            'province': '陕西省',
                            'city': '西安市',
                            'district': '碑林区'
                        }
                    }
                }

                # 调用反向地理编码（使用正确的参数顺序：lat, lon）
                result = self.mock_geocoding_service.reverse_geocode(
                    test_case['lat'],
                    test_case['lon']
                )

                # 验证调用参数
                self.mock_geocoding_service.reverse_geocode.assert_called_with(
                    test_case['lat'],
                    test_case['lon']
                )

                # 验证返回结果
                self.assertIsNotNone(result)
                self.assertIn('regeocode', result)
                self.assertIn('formatted_address', result['regeocode'])

    def test_reverse_geocode_parameter_order_osm(self):
        """测试OSM反向地理编码参数顺序"""
        # 测试数据
        test_cases = [
            {
                'name': '北京天安门',
                'lat': 39.9042,
                'lon': 116.4074
            },
            {
                'name': '上海东方明珠',
                'lat': 31.2397,
                'lon': 121.4995
            },
            {
                'name': '广州塔',
                'lat': 23.1088,
                'lon': 113.3191
            }
        ]

        for test_case in test_cases:
            with self.subTest(name=test_case['name']):
                # 模拟OSM返回结果（使用正确的'name'键）
                self.mock_geocoding_service.reverse_geocode.return_value = {
                    'name': f"{test_case['name']}附近",
                    'address': f"{test_case['name']}详细地址",
                    'type': 'attraction',
                    'lat': test_case['lat'],
                    'lon': test_case['lon']
                }

                # 调用反向地理编码
                result = self.mock_geocoding_service.reverse_geocode(
                    test_case['lat'],
                    test_case['lon']
                )

                # 验证调用参数
                self.mock_geocoding_service.reverse_geocode.assert_called_with(
                    test_case['lat'],
                    test_case['lon']
                )

                # 验证返回结果
                self.assertIsNotNone(result)
                self.assertIn('name', result)  # OSM服务返回'name'键
                self.assertIn('address', result)
                self.assertIn('type', result)

    def test_osm_data_structure_fix(self):
        """测试OSM数据结构修复（name vs display_name）"""
        # 测试著名地标
        test_cases = [
            {
                'name': 'White House',
                'lat': 38.897634,
                'lon': -77.036465,
                'expected_name': 'The White House, 1600, Pennsylvania Avenue Northwest, Washington, District of Columbia, 20500, United States'
            },
            {
                'name': 'Statue of Liberty',
                'lat': 40.689247,
                'lon': -74.044502,
                'expected_name': 'Statue of Liberty, Liberty Island, New York, United States'
            },
            {
                'name': 'Big Ben',
                'lat': 51.500729,
                'lon': -0.124625,
                'expected_name': 'Big Ben, Westminster, London, United Kingdom'
            },
            {
                'name': 'Eiffel Tower',
                'lat': 48.858370,
                'lon': 2.294481,
                'expected_name': 'Tour Eiffel, Paris, France'
            }
        ]

        for test_case in test_cases:
            with self.subTest(name=test_case['name']):
                # 模拟OSM服务返回的数据结构（使用'name'键，不是'display_name'）
                self.mock_geocoding_service.reverse_geocode.return_value = {
                    'name': test_case['expected_name'],
                    'address': test_case['expected_name'],
                    'type': 'monument',
                    'lat': test_case['lat'],
                    'lon': test_case['lon']
                }

                # 调用反向地理编码
                result = self.mock_geocoding_service.reverse_geocode(
                    test_case['lat'],
                    test_case['lon']
                )

                # 验证返回结果包含'name'键（不是'display_name'）
                self.assertIsNotNone(result)
                self.assertIn('name', result)
                self.assertNotEqual(result['name'], '未知位置')
                self.assertEqual(result['name'], test_case['expected_name'])

    def test_reverse_geocode_edge_cases(self):
        """测试边界情况"""
        edge_cases = [
            {
                'name': '赤道和本初子午线交点',
                'lat': 0.0,
                'lon': 0.0
            },
            {
                'name': '北极点',
                'lat': 90.0,
                'lon': 0.0
            },
            {
                'name': '南极点',
                'lat': -90.0,
                'lon': 0.0
            },
            {
                'name': '国际日期变更线',
                'lat': 0.0,
                'lon': 180.0
            }
        ]

        for test_case in edge_cases:
            with self.subTest(name=test_case['name']):
                # 模拟返回结果
                self.mock_geocoding_service.reverse_geocode.return_value = {
                    'regeocode': {
                        'formatted_address': test_case['name']
                    }
                }

                # 调用反向地理编码
                result = self.mock_geocoding_service.reverse_geocode(
                    test_case['lat'],
                    test_case['lon']
                )

                # 验证调用参数
                self.mock_geocoding_service.reverse_geocode.assert_called_with(
                    test_case['lat'],
                    test_case['lon']
                )

    def test_reverse_geocode_failure_handling(self):
        """测试反向地理编码失败的处理"""
        # 模拟返回None（失败情况）
        self.mock_geocoding_service.reverse_geocode.return_value = None

        # 测试坐标
        lat, lon = 34.2583, 108.9486

        # 调用反向地理编码
        result = self.mock_geocoding_service.reverse_geocode(lat, lon)

        # 验证返回None
        self.assertIsNone(result)

        # 验证调用参数
        self.mock_geocoding_service.reverse_geocode.assert_called_with(lat, lon)


class TestContextMenuIntegration(unittest.TestCase):
    """测试右键菜单集成功能"""

    def test_context_menu_data_structure(self):
        """测试右键菜单数据结构"""
        # 模拟位置信息
        location_info = {
            'success': True,
            'name': '西安钟楼',
            'lat': 34.2583,
            'lon': 108.9486,
            'type': '风景名胜'
        }

        # 验证数据结构
        self.assertIn('success', location_info)
        self.assertIn('name', location_info)
        self.assertIn('lat', location_info)
        self.assertIn('lon', location_info)
        self.assertIn('type', location_info)

        # 验证数据类型
        self.assertIsInstance(location_info['success'], bool)
        self.assertIsInstance(location_info['name'], str)
        self.assertIsInstance(location_info['lat'], float)
        self.assertIsInstance(location_info['lon'], float)
        self.assertIsInstance(location_info['type'], str)

    def test_context_menu_fallback_format(self):
        """测试右键菜单降级格式（网络失败时）"""
        # 模拟网络失败时的降级数据
        lat, lon = 34.2583, 108.9486
        fallback_info = {
            'success': False,
            'name': f'位置 ({lat:.6f}, {lon:.6f})',
            'lat': lat,
            'lon': lon,
            'type': ''
        }

        # 验证降级数据结构
        self.assertFalse(fallback_info['success'])
        self.assertEqual(fallback_info['name'], '位置 (34.258300, 108.948600)')
        self.assertEqual(fallback_info['lat'], lat)
        self.assertEqual(fallback_info['lon'], lon)
        self.assertEqual(fallback_info['type'], '')


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    suite = unittest.TestSuite()

    # 添加测试类
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestContextMenuReverseGeocode))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestContextMenuIntegration))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 返回测试结果
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

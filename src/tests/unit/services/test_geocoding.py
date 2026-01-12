import unittest
from unittest.mock import patch, MagicMock

from services.gaode.gaode_geocoding import GaodeGeocodingService


class TestGaodeGeocodingService(unittest.TestCase):
    """高德地图地理编码服务测试类"""

    def setUp(self):
        """setUp方法，在每个测试方法前执行"""
        # 使用模拟的API密钥进行测试
        self.service = GaodeGeocodingService(api_key='test_api_key')

    @patch('requests.get')
    def test_search_location_success(self, mock_get):
        """测试成功搜索地理位置"""
        # 模拟API响应 - 高德地图文本搜索API使用pois字段
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'status': '1',
            'info': 'OK',
            'infocode': '10000',
            'count': '1',
            'pois': [
                {
                    'name': '北京市朝阳区',
                    'address': '北京市朝阳区',
                    'location': '116.4074,39.9042',
                    'type': '地名地址信息',
                    'typecode': '120000'
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # 执行测试
        results = self.service.search_location("北京市")

        # 验证结果
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertIn('name', result)
        self.assertIn('lat', result)
        self.assertIn('lon', result)
        self.assertEqual(result['name'], '北京市朝阳区')
        self.assertEqual(result['lat'], 39.9042)
        self.assertEqual(result['lon'], 116.4074)

    @patch('requests.get')
    def test_search_location_api_error(self, mock_get):
        """测试API错误时的处理"""
        # 模拟API错误响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'status': '0',
            'info': 'INVALID_KEY',
            'infocode': '10003'
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # 执行测试
        results = self.service.search_location("无效地址")

        # 验证返回None（根据实际实现）
        self.assertIsNone(results)

    @patch('requests.get')
    def test_search_location_network_error(self, mock_get):
        """测试网络错误时的处理"""
        # 模拟网络错误
        mock_get.side_effect = Exception("Network error")

        # 执行测试并验证异常处理
        results = self.service.search_location("测试地址")

        # 验证返回None而不是抛出异常
        self.assertIsNone(results)

    @patch('requests.get')
    def test_reverse_geocode_success(self, mock_get):
        """测试成功反向地理编码（坐标转地址）"""
        # 模拟API响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'status': '1',
            'info': 'OK',
            'regeocode': {
                'formatted_address': '北京市朝阳区测试街道',
                'addressComponent': {
                    'province': '北京市',
                    'city': '北京市',
                    'district': '朝阳区'
                }
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # 执行测试
        result = self.service.reverse_geocode(39.9042, 116.4074)

        # 验证结果
        self.assertIsInstance(result, dict)
        self.assertIn('full_address', result)
        self.assertIn('city', result)
        self.assertEqual(result['full_address'], '北京市朝阳区测试街道')

    @patch('requests.get')
    def test_reverse_geocode_api_error(self, mock_get):
        """测试反向地理编码API错误时的处理"""
        # 模拟API错误响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'status': '0',
            'info': 'OUT_OF_SERVICE',
            'infocode': '10009'
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # 执行测试
        result = self.service.reverse_geocode(999.0, 999.0)  # 无效坐标

        # 验证返回None
        self.assertIsNone(result)



    @patch('requests.get')
    def test_search_location_partial_match(self, mock_get):
        """测试部分匹配结果的处理"""
        # 模拟包含多个匹配结果的API响应        
        mock_response = MagicMock()
        mock_response.json.return_value = {    
            'status': '1',
            'info': 'OK',
            'infocode': '10000',
            'count': '3',
            'pois': [
                {
                    'name': '北京市朝阳区测试路1号',
                    'address': '北京市朝阳区测试路1号',
                    'location': '116.4074,39.9042',
                    'type': '地名地址信息',
                    'typecode': '120000'
                },
                {
                    'name': '北京市海淀区测试路2号',
                    'address': '北京市海淀区测试路2号',
                    'location': '116.3100,39.9900',
                    'type': '地名地址信息',
                    'typecode': '120000'
                },
                {
                    'name': '北京市丰台区测试路3号',
                    'address': '北京市丰台区测试路3号',
                    'location': '116.2800,39.8600',
                    'type': '地名地址信息',
                    'typecode': '120000'
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response  

        # 执行测试
        results = self.service.search_location("测试")

        # 验证返回多个结果
        self.assertIsInstance(results, list)   
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIn('name', result)
            self.assertIn('lat', result)
            self.assertIn('lon', result)


if __name__ == '__main__':
    unittest.main()
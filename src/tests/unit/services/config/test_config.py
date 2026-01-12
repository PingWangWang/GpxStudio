import unittest
import tempfile
import os
import json

from services.config.map_config import MapConfig


# 创建MapConfig的子类以覆盖_get_config_path方法
class TestableMapConfig(MapConfig):
    def __init__(self, config_path):
        self._test_config_path = config_path
        super().__init__()

    def _get_config_path(self):
        return self._test_config_path


class TestMapConfig(unittest.TestCase):
    """地图配置管理测试类"""

    def setUp(self):
        """setUp方法，在每个测试方法前执行"""
        # 使用临时目录进行测试
        self.temp_dir = tempfile.mkdtemp()
        self.temp_config_path = os.path.join(self.temp_dir, "map_config.json")
        
        # 创建测试配置内容
        test_config = {
            "map_source": "gaode",
            "api_key": "test_api_key",
            "security_key": "test_security_key",
            "tile_url": "https://test-tiles.com/{z}/{x}/{y}.png"
        }
        
        with open(self.temp_config_path, 'w', encoding='utf-8') as f:
            json.dump(test_config, f, ensure_ascii=False, indent=2)

        self.config = TestableMapConfig(self.temp_config_path)

    def tearDown(self):
        """清理临时文件"""
        if os.path.exists(self.temp_config_path):
            os.remove(self.temp_config_path)
        os.rmdir(self.temp_dir)

    def test_load_config(self):
        """测试加载配置"""
        # 配置已经在初始化时加载，所以直接测试属性
        self.assertEqual(self.config.map_source, 'gaode')
        self.assertEqual(self.config.api_key, 'test_api_key')
        self.assertEqual(self.config.security_key, 'test_security_key')
        self.assertTrue(self.config.is_configured)
        self.assertIn('map_source', self.config._config_data)
        self.assertIn('api_key', self.config._config_data)
        self.assertEqual(self.config._config_data['map_source'], 'gaode')
        self.assertEqual(self.config._config_data['api_key'], 'test_api_key')


if __name__ == '__main__':
    unittest.main()
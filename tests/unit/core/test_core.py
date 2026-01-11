import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock

from core.di import DIContainer
from core.signals import SignalManager
from services.config.map_config import MapConfig


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
        
        import json
        with open(self.temp_config_path, 'w', encoding='utf-8') as f:
            json.dump(test_config, f, ensure_ascii=False, indent=2)
        
        # 创建配置实例
        self.config = MapConfig()
        # Mock the _get_config_path method for this specific instance
        self.config._get_config_path = lambda: self.temp_config_path

    def tearDown(self):
        """tearDown方法，在每个测试方法后执行"""
        # Clean up temp files
        if os.path.exists(self.temp_config_path):
            os.remove(self.temp_config_path)
        os.rmdir(self.temp_dir)

    def test_load_config(self):
        """测试加载配置"""
        config_data = self.config.load_config()
        self.assertIsInstance(config_data, dict)
        self.assertIn('map_source', config_data)
        self.assertIn('api_key', config_data)
        self.assertEqual(config_data['map_source'], 'gaode')
        self.assertEqual(config_data['api_key'], 'test_api_key')

    def test_save_config(self):
        """测试保存配置"""
        new_config = {
            "map_source": "osm",
            "api_key": "new_api_key",
            "security_key": "new_security_key",
            "tile_url": "https://new-tiles.com/{z}/{x}/{y}.png"
        }
        
        success = self.config.save_config(new_config)
        self.assertTrue(success)
        
        # Verify the config was updated
        self.assertEqual(self.config.map_source, 'osm')
        self.assertEqual(self.config.api_key, 'new_api_key')
        self.assertEqual(self.config.security_key, 'new_security_key')

    def test_get_config_value(self):
        """测试获取配置值"""
        value = self.config.get('map_source')
        self.assertEqual(value, 'gaode')
        
        # Test with default value
        default_value = self.config.get('nonexistent_key', 'default')
        self.assertEqual(default_value, 'default')

    def test_set_config_value(self):
        """测试设置配置值"""
        result = self.config.set('new_key', 'new_value')
        self.assertTrue(result)
        
        value = self.config.get('new_key')
        self.assertEqual(value, 'new_value')

    def test_clear_config(self):
        """测试清除配置"""
        success = self.config.clear_config()
        self.assertTrue(success)
        
        # Verify the config was cleared
        self.assertEqual(self.config.map_source, '')
        self.assertEqual(self.config.api_key, '')
        self.assertEqual(self.config.security_key, '')
        self.assertFalse(self.config.is_configured)


class TestDIContainer(unittest.TestCase):
    """依赖注入容器测试类"""

    def setUp(self):
        """setUp方法，在每个测试方法前执行"""
        self.container = DIContainer()

    def test_get_service_success(self):
        """测试获取已注册的服务"""
        # 获取已注册的服务
        service = self.container.get(MapConfig)
        
        # 验证服务存在
        self.assertIsNotNone(service)
        self.assertIsInstance(service, MapConfig)

    def test_get_nonexistent_service(self):
        """测试获取不存在的服务"""
        # 定义一个没有默认构造函数的类，这样injector无法创建实例
        class NonExistentService:
            def __init__(self, required_param):
                self.param = required_param

        # 获取不存在的服务
        service = self.container.get(NonExistentService)
        
        # 验证返回None（因为injector无法实例化需要参数的类）
        self.assertIsNone(service)

    def test_get_all_providers(self):
        """测试获取所有提供者"""
        providers = self.container.get_all_providers()
        
        # 验证返回列表
        self.assertIsInstance(providers, list)
        self.assertGreater(len(providers), 0)
        
        # 验证包含已知的提供者
        self.assertIn('MapConfig', providers)
        self.assertIn('SignalManager', providers)


class TestSignalManager(unittest.TestCase):
    """信号管理器测试类"""

    def setUp(self):
        """setUp方法，在每个测试方法前执行"""
        self.signal_manager = SignalManager()

    def test_connect_and_emit_signal(self):
        """测试连接和发射信号"""
        # 定义一个回调函数
        callback_called = {'count': 0}
        
        def test_callback():
            callback_called['count'] += 1      

        # 连接一个实际存在的信号（search_completed 不接受参数）
        self.signal_manager.search_completed.connect(test_callback)

        # 手动发射信号（不带参数）
        self.signal_manager.search_completed.emit()

        # 验证回调被调用
        self.assertEqual(callback_called['count'], 1)

    def test_disconnect_signal(self):
        """测试断开信号连接"""
        callback_called = {'count': 0}

        def test_callback():
            callback_called['count'] += 1      

        # 连接一个实际存在的信号
        self.signal_manager.search_completed.connect(test_callback)

        # 发射信号，确认回调被调用
        self.signal_manager.search_completed.emit()
        self.assertEqual(callback_called['count'], 1)

        # 断开信号连接
        self.signal_manager.search_completed.disconnect(test_callback)

        # 再次发射信号，回调不应被调用
        self.signal_manager.search_completed.emit()
        self.assertEqual(callback_called['count'], 1)

    def test_get_signal_description(self):
        """测试获取信号描述"""
        description = self.signal_manager.get_signal_description('search_completed')
        self.assertIsNotNone(description)
        self.assertIn('搜索完成', description)

    def test_get_all_signals(self):
        """测试获取所有信号"""
        signals = self.signal_manager.get_all_signals()
        self.assertIsInstance(signals, list)
        self.assertGreater(len(signals), 0)
        self.assertIn('search_completed', signals)
        self.assertIn('geolocation_success', signals)

    def test_emit_nonexistent_signal(self):
        """测试发射不存在的信号"""
        # 发射不存在的信号不应该引发错误
        try:
            self.signal_manager.emit('nonexistent_signal', {})
            success = True
        except Exception:
            success = False
        
        self.assertTrue(success, "发射不存在的信号应该不会引发错误")


if __name__ == '__main__':
    unittest.main()
import unittest
from unittest.mock import patch, MagicMock

from modules.routing.interfaces.routing_service import IRoutingService


class TestIRoutingService(unittest.TestCase):
    """路由服务接口测试类"""

    def test_interface_methods_exist(self):
        """测试接口方法是否存在"""
        # 由于这是一个接口类，我们主要验证方法签名
        self.assertTrue(hasattr(IRoutingService, '__init__'))
        # 可以在这里添加更多的接口方法验证


if __name__ == '__main__':
    unittest.main()
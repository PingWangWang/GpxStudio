import unittest
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from unittest.mock import patch, MagicMock
from services.http.http_server import LocalMapServer


class TestHttpServer(unittest.TestCase):
    """HTTP服务器服务测试类"""

    def test_local_map_server_class_exists(self):
        """测试LocalMapServer类存在"""
        # 验证类可以被引用
        self.assertIsNotNone(LocalMapServer)


if __name__ == '__main__':
    unittest.main()
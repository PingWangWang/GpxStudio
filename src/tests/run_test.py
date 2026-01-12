#!/usr/bin/env python
"""运行单个测试模块"""

import unittest
import sys
import os

# 添加项目根目录到路径（从tests目录向上一级）
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 导入测试模块
from tests.unit.services.config.test_config import TestMapConfig

if __name__ == '__main__':
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestMapConfig)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 退出码基于测试结果
    sys.exit(0 if result.wasSuccessful() else 1)
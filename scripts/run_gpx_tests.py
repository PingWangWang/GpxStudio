#!/usr/bin/env python
"""运行GPX测试"""
import sys
import os

# 添加src目录到Python路径（从scripts目录回到项目根目录）
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))

# 运行unittest
import unittest

if __name__ == '__main__':
    # 发现并运行所有GPX测试
    loader = unittest.TestLoader()
    start_dir = os.path.join(project_root, 'src', 'tests', 'unit', 'modules', 'gpx')
    suite = loader.discover(start_dir, pattern='test_*.py')

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    sys.exit(0 if result.wasSuccessful() else 1)

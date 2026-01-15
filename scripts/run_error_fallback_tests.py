#!/usr/bin/env python
"""运行错误回退测试"""
import sys
import os

# 添加src目录到Python路径（从scripts目录回到项目根目录）
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))

# 运行单元测试
import unittest

# 导入测试类
from tests.unit.modules.gpx.test_gpx_export import TestGpxExportService

if __name__ == '__main__':
    # 创建测试套件
    suite = unittest.TestSuite()

    # 添加错误处理相关的测试
    suite.addTest(TestGpxExportService('test_timezonefinder_import_failure'))
    suite.addTest(TestGpxExportService('test_pytz_import_failure'))
    suite.addTest(TestGpxExportService('test_timezonefinder_returns_none'))
    suite.addTest(TestGpxExportService('test_invalid_timezone_name'))
    suite.addTest(TestGpxExportService('test_all_error_scenarios_log_warnings'))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 返回退出码
    sys.exit(0 if result.wasSuccessful() else 1)

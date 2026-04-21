"""
pytest 配置文件

将 src/ 加入 sys.path，使所有测试可直接 import 项目模块。
"""
import sys
import os

# 确保 src/ 在 Python 路径中
SRC_DIR = os.path.join(os.path.dirname(__file__), '..', 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, os.path.abspath(SRC_DIR))

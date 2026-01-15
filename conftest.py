"""
Root conftest.py - pytest 配置文件
自动配置 Python 路径，使测试能够正确导入 src 目录中的模块
"""
import sys
import os

# 获取 src 目录的绝对路径
src_path = os.path.join(os.path.dirname(__file__), 'src')

# 清理可能存在的重复路径
while src_path in sys.path:
    sys.path.remove(src_path)

# 清理项目根目录（避免导入冲突）
project_root = os.path.dirname(__file__)
while project_root in sys.path:
    sys.path.remove(project_root)

# 将 src 目录插入到搜索路径的最前面
sys.path.insert(0, src_path)

print(f"[CONFTEST] Added {src_path} to sys.path at position 0")
print(f"[CONFTEST] sys.path[:3] = {sys.path[:3]}")

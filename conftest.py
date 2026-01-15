"""
Root conftest.py - 导入config目录中的实际配置
"""
import sys
import os

# 导入config目录中的实际conftest配置
config_dir = os.path.join(os.path.dirname(__file__), 'config')
sys.path.insert(0, config_dir)

# 执行config/conftest.py中的配置
src_path = os.path.join(os.path.dirname(__file__), 'src')

# Remove it if it exists anywhere in sys.path
while src_path in sys.path:
    sys.path.remove(src_path)

# Also remove the project root if it's there (it interferes with imports)
project_root = os.path.dirname(__file__)
while project_root in sys.path:
    sys.path.remove(project_root)

# Insert src at position 0
sys.path.insert(0, src_path)

print(f"[CONFTEST ROOT] Added {src_path} to sys.path at position 0")
print(f"[CONFTEST ROOT] sys.path[:3] = {sys.path[:3]}")

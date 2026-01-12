import sys
import os

# 添加项目根目录到Python路径，确保可以导入项目模块
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 添加src目录到Python路径（如果存在）
src_path = os.path.join(project_root, 'src')
if os.path.isdir(src_path) and src_path not in sys.path:
    sys.path.insert(0, src_path)
import sys
import os

# 添加src目录到Python路径（tests目录的父目录）
# __file__ is src/tests/conftest.py
# dirname(__file__) is src/tests
# dirname(dirname(__file__)) is src
src_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Remove project root if it's in the path (it interferes)
project_root = os.path.dirname(src_root)
while project_root in sys.path:
    sys.path.remove(project_root)

# Remove src_root if it exists
while src_root in sys.path:
    sys.path.remove(src_root)

# Insert src at position 0
if src_root not in sys.path:
    sys.path.insert(0, src_root)

print(f"[CONFTEST] Added {src_root} to sys.path at position 0")
print(f"[CONFTEST] sys.path[:3] = {sys.path[:3]}")

# Verify the modules directory exists
modules_path = os.path.join(src_root, 'modules')
print(f"[CONFTEST] modules directory exists: {os.path.exists(modules_path)}")
print(f"[CONFTEST] modules/__init__.py exists: {os.path.exists(os.path.join(modules_path, '__init__.py'))}")
gpx_path = os.path.join(modules_path, 'gpx')
print(f"[CONFTEST] modules/gpx directory exists: {os.path.exists(gpx_path)}")
print(f"[CONFTEST] modules/gpx/__init__.py exists: {os.path.exists(os.path.join(gpx_path, '__init__.py'))}")
print(f"[CONFTEST] modules/gpx/gpx_export.py exists: {os.path.exists(os.path.join(gpx_path, 'gpx_export.py'))}")
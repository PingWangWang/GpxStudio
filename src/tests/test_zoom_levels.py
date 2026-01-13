import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from modules.map.map_renderer import MapRenderer

# 测试不同半径的缩放级别
test_radii = [
    ("元熙樾府 (小区入口)", 65),
    ("小型POI", 50),
    ("中型POI", 150),
    ("大型POI", 300),
    ("超大型POI", 500),
    ("公园", 1000),
    ("大学校园", 2000),
]

print("半径到缩放级别的映射:")
print("="*60)
for name, radius in test_radii:
    zoom = MapRenderer._calculate_zoom_from_radius(radius)
    print(f"{name:20s}: {radius:6.0f}米  →  缩放级别 {zoom}")

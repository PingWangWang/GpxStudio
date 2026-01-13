import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from modules.map.map_renderer import MapRenderer

# 测试案例
name = "元熙樾府营销中心"
type_info = "生活服务;生活服务场所;生活服务场所"
level_info = ""

print(f"测试地址: {name}")
print(f"类型: {type_info}")
print(f"级别: {level_info}")
print()

# 测试缩放级别计算
zoom = MapRenderer.get_zoom_by_level(level_info, type_info, radius=None)
print(f"计算得到的缩放级别: {zoom}")

# 分析匹配过程
print("\n分析:")
type_lower = type_info.lower()

if '住宅小区' in type_lower or '住宅区' in type_lower:
    print("- 匹配到住宅类")
elif '餐饮' in type_lower or '购物' in type_lower:
    print("- 匹配到商业POI")
elif '生活服务' in type_lower:
    print("- 包含'生活服务'关键词，但未被特殊处理")

# 检查名称中的关键词
name_lower = name.lower()
if '营销中心' in name_lower or '售楼处' in name_lower or '销售中心' in name_lower:
    print(f"- 名称包含建筑相关关键词: '{name}'")

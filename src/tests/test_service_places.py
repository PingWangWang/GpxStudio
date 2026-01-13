import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from modules.map.map_renderer import MapRenderer

# 测试各种生活服务场所
test_cases = [
    {
        'name': '元熙樾府营销中心',
        'type': '生活服务;生活服务场所;生活服务场所',
        'expected': 18,
        'description': '营销中心（建筑级）'
    },
    {
        'name': '链家地产',
        'type': '生活服务;生活服务场所;房地产',
        'expected': 18,
        'description': '房地产中介（建筑级）'
    },
    {
        'name': '小区物业',
        'type': '生活服务;生活服务场所;物业公司',
        'expected': 18,
        'description': '物业公司（建筑级）'
    },
    {
        'name': '元熙樾府',
        'type': '商务住宅;住宅区;住宅小区',
        'expected': 17,
        'description': '住宅小区（社区级）'
    },
]

print("="*80)
print("生活服务场所缩放级别测试")
print("="*80)

for case in test_cases:
    zoom = MapRenderer.get_zoom_by_level(
        level_info="",
        type_info=case['type'],
        radius=None
    )

    status = "✓" if zoom == case['expected'] else "✗"
    print(f"\n{status} {case['name']}")
    print(f"  类型: {case['type']}")
    print(f"  预期级别: {case['expected']} ({case['description']})")
    print(f"  实际级别: {zoom}")

    if zoom != case['expected']:
        print(f"  ⚠️  不匹配！")

print("\n" + "="*80)
print("测试完成")
print("="*80)

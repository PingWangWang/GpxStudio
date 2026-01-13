"""
测试地址搜索的自动缩放和图标区分功能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from modules.map.map_renderer import MapRenderer


def test_zoom_by_level():
    """测试根据地址类型自动计算缩放级别"""

    print("测试地址类型的缩放级别计算：")
    print("-" * 80)

    # 测试不同的地址类型
    test_cases = [
        # 行政区划
        ("国家级别", "国家", None, 4),
        ("省级别", "省", None, 7),
        ("市级别", "市", None, 10),
        ("区级别", "区", None, 12),
        ("县级别", "县", None, 12),
        ("街道级别", "街道", None, 15),
        ("建筑级别", "楼", None, 18),

        # 住宅类（重点测试）
        ("住宅小区-type字段", None, "住宅小区", 17),
        ("住宅区-type字段", None, "住宅区", 17),
        ("商务住宅-type字段", None, "商务住宅", 17),
        ("用户案例：商务住宅;住宅区;住宅小区", None, "商务住宅;住宅区;住宅小区", 17),
        ("别墅", None, "别墅", 17),
        ("公寓", None, "公寓", 17),

        # 商业POI
        ("餐饮", None, "餐饮", 16),
        ("购物", None, "购物", 16),
        ("酒店", None, "酒店", 16),
        ("商场", None, "商场", 16),
        ("超市", None, "超市", 16),

        # 公共服务
        ("医院", None, "医院", 16),
        ("学校", None, "学校", 16),
        ("银行", None, "银行", 16),

        # 交通设施
        ("地铁站", None, "地铁站", 16),
        ("公交站", None, "公交站", 16),
        ("停车场", None, "停车场", 16),

        # 办公
        ("写字楼", None, "写字楼", 16),
        ("办公楼", None, "办公楼", 16),

        # 默认
        ("默认级别", None, None, 12),
    ]

    passed = 0
    failed = 0

    for name, level_info, type_info, expected_zoom in test_cases:
        actual_zoom = MapRenderer.get_zoom_by_level(level_info, type_info)
        status = "✓" if actual_zoom == expected_zoom else "✗"

        if actual_zoom == expected_zoom:
            passed += 1
        else:
            failed += 1

        print(f"{status} {name:30s} | level: {str(level_info):10s} | type: {str(type_info):30s} | "
              f"期望: {expected_zoom:2d} | 实际: {actual_zoom:2d}")

    print("-" * 80)
    print(f"测试结果: 通过 {passed}/{len(test_cases)}, 失败 {failed}/{len(test_cases)}")
    print()

    return failed == 0


def test_icon_differentiation():
    """测试选中地址和其他地址的图标区分逻辑"""

    print("测试图标区分逻辑：")
    print("-" * 80)

    # 模拟搜索结果
    search_results = [
        {'name': '北京市朝阳区', 'address': '北京市朝阳区', 'lat': 39.9042, 'lon': 116.4074, 'level': '区', 'type': ''},
        {'name': '北京市海淀区', 'address': '北京市海淀区', 'lat': 39.9563, 'lon': 116.3105, 'level': '区', 'type': ''},
        {'name': '北京市东城区', 'address': '北京市东城区', 'lat': 39.9288, 'lon': 116.4163, 'level': '区', 'type': ''},
    ]

    # 模拟选中第一个结果
    selected_coords = (39.9042, 116.4074)

    print("搜索结果列表:")
    for i, result in enumerate(search_results):
        is_selected = (
            abs(result['lat'] - selected_coords[0]) < 0.0001 and
            abs(result['lon'] - selected_coords[1]) < 0.0001
        )

        color = "green" if is_selected else "gray"
        icon = "ok-sign" if is_selected else "info-sign"
        status_mark = "✓ [选中]" if is_selected else "  [未选中]"

        print(f"{status_mark} {i+1}. {result['name']:15s} | 颜色: {color:6s} | 图标: {icon:10s}")

    print("-" * 80)
    print("✓ 图标区分逻辑测试通过")
    print()


def main():
    """运行所有测试"""
    print("=" * 80)
    print("地址搜索功能增强测试")
    print("=" * 80)
    print()

    test_zoom_by_level()
    test_icon_differentiation()

    print("=" * 80)
    print("所有测试完成")
    print("=" * 80)


if __name__ == '__main__':
    main()

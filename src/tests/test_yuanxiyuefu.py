"""
测试用户案例：元熙樾府小区的地图缩放
验证小区类型的地址能够正确缩放到17级
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from modules.map.map_renderer import MapRenderer


def test_yuanxiyuefu():
    """测试元熙樾府小区的缩放级别"""

    print("=" * 80)
    print("用户案例测试：元熙樾府")
    print("=" * 80)
    print()

    # 用户的实际数据
    name = "元熙樾府"
    address = "石家街地铁站向东150米"
    location_type = "商务住宅;住宅区;住宅小区"
    coords = (34.291219, 109.001091)

    print(f"小区名称: {name}")
    print(f"地址: {address}")
    print(f"类型: {location_type}")
    print(f"坐标: {coords}")
    print()

    # 测试不同的参数组合
    test_cases = [
        ("只有type字段", None, location_type),
        ("type包含住宅小区", None, "住宅小区"),
        ("type包含住宅区", None, "住宅区"),
        ("type包含商务住宅", None, "商务住宅"),
    ]

    print("-" * 80)
    print("缩放级别测试：")
    print("-" * 80)

    all_passed = True
    expected_zoom = 17  # 小区应该缩放到17级

    for case_name, level_info, type_info in test_cases:
        actual_zoom = MapRenderer.get_zoom_by_level(level_info, type_info)
        passed = actual_zoom == expected_zoom
        status = "✓" if passed else "✗"

        if not passed:
            all_passed = False

        print(f"{status} {case_name:20s} | 期望缩放: {expected_zoom} | 实际缩放: {actual_zoom}")

    print("-" * 80)

    if all_passed:
        print()
        print("✅ 测试通过！")
        print(f"   '{name}' 小区现在会正确缩放到级别 {expected_zoom}")
        print(f"   用户可以清晰看到小区的布局和周边环境")
        print()

        # 显示缩放级别的含义
        print("缩放级别说明：")
        print("  - 级别 12：区县级别（较大范围）")
        print("  - 级别 14：默认级别（中等范围）")
        print("  - 级别 17：小区级别（可以看清小区布局）⭐")
        print("  - 级别 18：建筑级别（最详细）")
    else:
        print()
        print("❌ 测试失败！部分情况下缩放级别不正确")

    print()
    print("=" * 80)

    return all_passed


if __name__ == '__main__':
    success = test_yuanxiyuefu()
    exit(0 if success else 1)

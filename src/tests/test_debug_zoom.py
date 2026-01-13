"""
调试脚本：测试实际运行时的缩放计算
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from modules.map.map_renderer import MapRenderer


def test_real_scenarios():
    """测试真实场景的缩放级别"""

    print("=" * 80)
    print("实际运行调试测试")
    print("=" * 80)
    print()

    # 测试用例1：北京市
    print("测试1：搜索 '北京市'")
    print("-" * 80)
    zoom1 = MapRenderer.get_zoom_by_level(None, None)
    print(f"结果：缩放级别 = {zoom1}")
    print()

    # 测试用例2：元熙樾府（模拟真实数据）
    print("测试2：搜索 '元熙樾府'")
    print("-" * 80)
    # 模拟高德地图返回的数据
    zoom2 = MapRenderer.get_zoom_by_level("120302", "商务住宅;住宅区;住宅小区")
    print(f"结果：缩放级别 = {zoom2}")
    print()

    # 测试用例3：如果type_info为空字符串
    print("测试3：type_info 为空字符串")
    print("-" * 80)
    zoom3 = MapRenderer.get_zoom_by_level("120302", "")
    print(f"结果：缩放级别 = {zoom3}")
    print()

    # 测试用例4：北京市（带type）
    print("测试4：搜索 '北京市'（带type）")
    print("-" * 80)
    zoom4 = MapRenderer.get_zoom_by_level(None, "行政区")
    print(f"结果：缩放级别 = {zoom4}")
    print()

    # 测试用例5：北京市（带level和type）
    print("测试5：搜索 '北京市'（带level）")
    print("-" * 80)
    zoom5 = MapRenderer.get_zoom_by_level("北京市", "")
    print(f"结果：缩放级别 = {zoom5}")
    print()

    print("=" * 80)


if __name__ == '__main__':
    test_real_scenarios()

"""
测试智能缩放功能 - 完整演示
展示基于POI实际半径的智能缩放如何优化用户体验
"""

import sys
import os

# 添加项目根目录到系统路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from services.gaode.gaode_geocoding import GaodeGeocodingService
from services.config.map_config import MapConfig
from modules.map.map_renderer import MapRenderer

def demo_intelligent_zoom():
    """演示智能缩放功能"""

    # 获取API Key
    config_service = MapConfig()
    api_key = config_service.api_key

    if not api_key:
        print("错误：未配置高德地图API Key")
        print("请先在应用中配置高德地图API")
        return

    print("="*80)
    print("智能缩放功能演示")
    print("="*80)
    print("\n功能说明:")
    print("1. 系统会自动获取POI的入口坐标")
    print("2. 计算POI中心到入口的距离作为半径")
    print("3. 根据实际半径智能调整缩放级别")
    print("4. 确保POI在地图中占据合适的视野比例\n")

    # 创建地理编码服务
    geocoding = GaodeGeocodingService(api_key=api_key)

    # 测试案例
    test_cases = [
        {
            'keyword': '元熙樾府',
            'description': '住宅小区（用户提供的测试案例）',
            'expected_type': '住宅类',
        },
        {
            'keyword': '天安门',
            'description': '国家级景点',
            'expected_type': '大型建筑',
        },
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"测试案例 {i}: {case['keyword']} - {case['description']}")
        print('='*80)

        # 搜索地点
        print(f"正在搜索: {case['keyword']}...")
        results = geocoding.search_location(case['keyword'])

        if not results or len(results) == 0:
            print(f"❌ 搜索失败")
            continue

        poi = results[0]

        print(f"\n✓ 搜索成功")
        print(f"  名称: {poi.get('name')}")
        print(f"  类型: {poi.get('type')}")
        print(f"  地址: {poi.get('address')}")
        print(f"  坐标: ({poi.get('lat'):.6f}, {poi.get('lon'):.6f})")

        # 显示半径信息
        radius = poi.get('radius')
        if radius is not None:
            print(f"\n📏 POI范围测量:")
            print(f"  中心到入口距离: {radius:.2f} 米")

            # 计算基于半径的缩放级别
            zoom_with_radius = MapRenderer.get_zoom_by_level(
                level_info=poi.get('level'),
                type_info=poi.get('type'),
                radius=radius
            )

            # 计算基于类型的缩放级别（对比）
            zoom_by_type = MapRenderer.get_zoom_by_level(
                level_info=poi.get('level'),
                type_info=poi.get('type'),
                radius=None
            )

            print(f"\n🗺️  缩放级别对比:")
            print(f"  旧方案（仅基于类型）: 级别 {zoom_by_type}")
            print(f"  新方案（基于实际范围）: 级别 {zoom_with_radius}")

            if zoom_with_radius != zoom_by_type:
                diff = zoom_with_radius - zoom_by_type
                if diff > 0:
                    print(f"  ✓ 优化: 提高 {diff} 级，更清晰展示小型POI")
                else:
                    print(f"  ✓ 优化: 降低 {-diff} 级，更好展示大型POI全貌")
            else:
                print(f"  = 使用类型默认级别")

            # 显示视野范围
            view_radius = radius * 1.5
            print(f"\n👁️  视野范围:")
            print(f"  POI半径: {radius:.0f} 米")
            print(f"  建议视野: {view_radius:.0f} 米")
            print(f"  POI占比: 约 67%（确保周边环境清晰可见）")

        else:
            print(f"\n⚠️  未能获取POI半径（无入口坐标）")
            zoom = MapRenderer.get_zoom_by_level(
                level_info=poi.get('level'),
                type_info=poi.get('type'),
                radius=None
            )
            print(f"  使用类型默认缩放级别: {zoom}")

    print(f"\n{'='*80}")
    print("演示完成")
    print("="*80)
    print("\n💡 使用提示:")
    print("- 在应用中搜索地址后，点击搜索结果列表中的任一项")
    print("- 右侧地图会自动缩放到合适的级别")
    print("- 绿色图标表示当前选中的地址，灰色图标表示其他搜索结果")
    print("- 系统会优先使用POI实际范围，无法获取时使用类型默认级别\n")

if __name__ == "__main__":
    demo_intelligent_zoom()

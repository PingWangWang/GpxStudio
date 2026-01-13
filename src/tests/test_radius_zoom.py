"""
测试基于POI半径的智能缩放功能
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

def test_radius_based_zoom():
    """测试基于半径的缩放计算"""

    # 获取API Key
    config_service = MapConfig()
    api_key = config_service.api_key

    if not api_key:
        print("错误：未配置高德地图API Key")
        return

    # 创建地理编码服务
    geocoding = GaodeGeocodingService(api_key=api_key)

    # 测试不同类型的地址
    test_cases = [
        "元熙樾府",           # 住宅小区
        "北京市",             # 城市
        "天安门",             # 著名建筑
    ]

    for keyword in test_cases:
        print(f"\n{'='*80}")
        print(f"搜索: {keyword}")
        print('='*80)

        # 使用服务搜索
        results = geocoding.search_location(keyword)

        if results and len(results) > 0:
            poi = results[0]

            print(f"名称: {poi.get('name')}")
            print(f"类型: {poi.get('type')}")
            print(f"类型编码: {poi.get('level')}")
            print(f"坐标: ({poi.get('lat')}, {poi.get('lon')})")

            radius = poi.get('radius')
            if radius is not None:
                print(f"POI半径: {radius:.2f} 米")

                # 测试缩放级别计算
                zoom = MapRenderer.get_zoom_by_level(
                    level_info=poi.get('level'),
                    type_info=poi.get('type'),
                    radius=radius
                )
                print(f"推荐缩放级别: {zoom}")

                # 计算基于类型的缩放级别（对比）
                zoom_type = MapRenderer.get_zoom_by_level(
                    level_info=poi.get('level'),
                    type_info=poi.get('type'),
                    radius=None
                )
                print(f"基于类型的缩放级别: {zoom_type}")

                # 显示差异
                if zoom != zoom_type:
                    print(f"✓ 使用实际半径优化了缩放级别 (差异: {zoom - zoom_type})")
                else:
                    print(f"  使用类型默认级别")
            else:
                print("POI半径: 未获取到（可能无入口坐标）")
                zoom = MapRenderer.get_zoom_by_level(
                    level_info=poi.get('level'),
                    type_info=poi.get('type'),
                    radius=None
                )
                print(f"推荐缩放级别（基于类型）: {zoom}")
        else:
            print(f"搜索失败")

if __name__ == "__main__":
    test_radius_based_zoom()

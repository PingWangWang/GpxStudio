"""
测试高德地图API extensions=all参数返回的数据结构
"""

import sys
import os
import json

# 添加项目根目录到系统路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from services.gaode.gaode_geocoding import GaodeGeocodingService
from services.config.map_config import MapConfig

def test_poi_extensions():
    """测试不同类型POI返回的扩展信息"""

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
        "朝阳公园",           # 公园
        "王府井",             # 商业区
        "清华大学",           # 大学
    ]

    for keyword in test_cases:
        print(f"\n{'='*80}")
        print(f"搜索: {keyword}")
        print('='*80)

        # 直接调用API获取原始响应
        import requests
        params = {
            'key': api_key,
            'keywords': keyword,
            'city': '全国',
            'citylimit': 'false',
            'output': 'json',
            'offset': 1,
            'page': 1,
            'extensions': 'all'
        }

        response = requests.get(geocoding.GEOCODE_URL, params=params, timeout=10)
        data = response.json()

        if data.get('status') == '1' and data.get('pois'):
            poi = data['pois'][0]

            print(f"名称: {poi.get('name')}")
            print(f"类型: {poi.get('type')}")
            print(f"类型编码: {poi.get('typecode')}")
            print(f"地址: {poi.get('address')}")
            print(f"坐标: {poi.get('location')}")

            # 打印所有可能的扩展字段
            print("\n扩展字段:")
            extension_fields = [
                'entr_location',      # 入口坐标
                'exit_location',      # 出口坐标
                'navi_poiid',         # 导航POI ID
                'grid_code',          # 地理格网码
                'business_area',      # 商圈
                'shopinfo',           # 商铺信息
                'photos',             # 图片
                'children',           # 子POI
                'indoor_map',         # 室内地图
                'indoor_data',        # 室内数据
                'biz_ext',            # 扩展信息
                'match',              # 匹配度
                'recommend',          # 推荐
                'timestamp',          # 时间戳
            ]

            for field in extension_fields:
                if field in poi:
                    value = poi[field]
                    if isinstance(value, (dict, list)):
                        print(f"  {field}: {json.dumps(value, ensure_ascii=False, indent=4)}")
                    else:
                        print(f"  {field}: {value}")

            # 打印完整的POI数据（方便查看还有哪些字段）
            print("\n完整POI数据:")
            print(json.dumps(poi, ensure_ascii=False, indent=2))
        else:
            print(f"搜索失败: {data.get('info')}")

if __name__ == "__main__":
    test_poi_extensions()

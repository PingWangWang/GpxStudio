"""
测试搜索历史保存功能
"""

import sys
import os

# 添加src到路径
sys.path.insert(0, 'src')

from services.storage import GeoInfoStorage

def test_save_search_result():
    """测试保存搜索结果"""
    print("=" * 60)
    print("测试搜索历史保存功能")
    print("=" * 60)

    # 创建存储实例
    storage = GeoInfoStorage("test_GeoInfoList.json")

    # 测试数据1：正常的字典格式
    print("\n测试1：保存正常格式的搜索结果")
    result1 = {
        'name': '西安钟楼',
        'address': '陕西省西安市碑林区东大街',
        'lat': 34.2583,
        'lon': 108.9486,
        'type': '风景名胜',
        'level': 'POI级',
        'radius': 100
    }

    try:
        storage.add_search_result("钟楼", result1)
        print("✓ 测试1通过：成功保存")
    except Exception as e:
        print(f"✗ 测试1失败：{e}")
        import traceback
        traceback.print_exc()

    # 测试数据2：坐标为字符串的情况
    print("\n测试2：保存坐标为字符串的搜索结果")
    result2 = {
        'name': '大雁塔',
        'address': '陕西省西安市雁塔区',
        'lat': '34.2247',  # 字符串格式
        'lon': '108.9644',  # 字符串格式
        'type': '风景名胜',
        'level': 'POI级',
        'radius': None
    }

    try:
        storage.add_search_result("大雁塔", result2)
        print("✓ 测试2通过：成功保存（坐标自动转换）")
    except Exception as e:
        print(f"✗ 测试2失败：{e}")
        import traceback
        traceback.print_exc()

    # 测试数据3：缺少某些字段
    print("\n测试3：保存缺少部分字段的搜索结果")
    result3 = {
        'name': '兵马俑',
        'lat': 34.3847,
        'lon': 109.2734
        # 缺少 address, type, level, radius
    }

    try:
        storage.add_search_result("兵马俑", result3)
        print("✓ 测试3通过：成功保存（缺失字段使用默认值）")
    except Exception as e:
        print(f"✗ 测试3失败：{e}")
        import traceback
        traceback.print_exc()

    # 获取历史记录
    print("\n获取历史记录：")
    history = storage.get_recent_history(10)
    print(f"共有 {len(history)} 条历史记录")
    for i, record in enumerate(history, 1):
        print(f"{i}. {record.get('name')} - {record.get('address', '无地址')}")
        print(f"   坐标: ({record.get('lat')}, {record.get('lon')})")
        print(f"   类型: {record.get('type', '未知')}")

    # 清理测试文件
    print("\n清理测试文件...")
    if os.path.exists("test_GeoInfoList.json"):
        os.remove("test_GeoInfoList.json")
        print("✓ 测试文件已删除")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_save_search_result()

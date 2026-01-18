#!/usr/bin/env python3
"""
简单测试历史记录选择逻辑
"""

# 模拟历史记录数据
test_history = [
    {
        'start': '西安钟楼',
        'end': '大雁塔',
        'mode': 'driving',
        'search_count': 1,
        'start_coords': [108.9434, 34.2583],
        'end_coords': [108.9649, 34.2244],
        'distance': 8500,
        'duration': 1200,
        'route_points': []
    },
    {
        'start': '西安火车站',
        'end': '西安北站',
        'mode': 'driving',
        'search_count': 2,
        'start_coords': [108.9515, 34.2778],
        'end_coords': [108.9298, 34.3708],
        'distance': 12000,
        'duration': 1800,
        'route_points': []
    }
]

def test_history_matching():
    """测试历史记录匹配逻辑"""
    print("=== 测试历史记录匹配逻辑 ===")
    
    # 模拟选中的历史记录
    selected_history = test_history[0]
    
    print(f"选中的历史记录: {selected_history['start']} → {selected_history['end']}")
    
    # 模拟查找匹配的widget
    for i, history_data in enumerate(test_history):
        is_match = (history_data == selected_history)
        print(f"历史记录 {i+1}: {history_data['start']} → {history_data['end']}")
        print(f"  匹配: {is_match}")
        print(f"  应该选中: {is_match}")
        print(f"  应该启用导出按钮: {is_match}")
        print()

def test_dict_comparison():
    """测试字典比较"""
    print("=== 测试字典比较 ===")
    
    dict1 = test_history[0]
    dict2 = test_history[0].copy()  # 创建副本
    dict3 = test_history[1]
    
    print(f"dict1 == dict2 (副本): {dict1 == dict2}")
    print(f"dict1 is dict2 (同一对象): {dict1 is dict2}")
    print(f"dict1 == dict3 (不同记录): {dict1 == dict3}")
    
    # 测试部分修改后的比较
    dict2['extra_field'] = 'test'
    print(f"添加字段后 dict1 == dict2: {dict1 == dict2}")

if __name__ == '__main__':
    test_history_matching()
    test_dict_comparison()
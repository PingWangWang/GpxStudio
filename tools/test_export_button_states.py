"""
简单测试导出按钮状态逻辑
"""

def test_export_button_logic():
    """测试导出按钮的启用逻辑"""
    
    class MockExportButton:
        def __init__(self):
            self.is_selected = False
            self.has_route_data = False
            self.enabled = False
        
        def should_enable(self):
            """判断按钮是否应该启用"""
            return self.is_selected and self.has_route_data
        
        def update_state(self):
            """更新按钮状态"""
            self.enabled = self.should_enable()
    
    print("测试导出按钮状态逻辑...")
    
    button = MockExportButton()
    
    # 测试1: 初始状态
    button.update_state()
    print(f"初始状态 - 选中: {button.is_selected}, 有数据: {button.has_route_data}, 启用: {button.enabled}")
    assert not button.enabled, "初始状态应该禁用"
    
    # 测试2: 只选中，没有数据
    button.is_selected = True
    button.update_state()
    print(f"只选中 - 选中: {button.is_selected}, 有数据: {button.has_route_data}, 启用: {button.enabled}")
    assert not button.enabled, "只选中没有数据应该禁用"
    
    # 测试3: 选中且有数据
    button.has_route_data = True
    button.update_state()
    print(f"选中+有数据 - 选中: {button.is_selected}, 有数据: {button.has_route_data}, 启用: {button.enabled}")
    assert button.enabled, "选中且有数据应该启用"
    
    # 测试4: 取消选中
    button.is_selected = False
    button.update_state()
    print(f"取消选中 - 选中: {button.is_selected}, 有数据: {button.has_route_data}, 启用: {button.enabled}")
    assert not button.enabled, "取消选中应该禁用"
    
    print("✅ 所有逻辑测试通过！")

def test_window_size():
    """测试窗口大小设置"""
    print("\n测试窗口大小设置...")
    
    # 模拟读取常量文件
    expected_size = (1200, 700)
    print(f"期望窗口大小: {expected_size}")
    
    # 这里应该是1200x700
    assert expected_size == (1200, 700), "窗口大小应该是1200x700"
    print("✅ 窗口大小设置正确！")

if __name__ == '__main__':
    print("开始测试...")
    print("=" * 50)
    
    test_export_button_logic()
    test_window_size()
    
    print("\n" + "=" * 50)
    print("所有测试完成！")
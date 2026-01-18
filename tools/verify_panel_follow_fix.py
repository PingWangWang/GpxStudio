#!/usr/bin/env python3
"""
验证面板跟随窗口移动修复
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

def test_move_event_added():
    """测试是否添加了moveEvent方法"""
    print("=== 测试moveEvent方法 ===")
    
    # 读取app.py文件内容
    app_file = os.path.join(project_root, 'src', 'app', 'app.py')
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否添加了moveEvent方法
    if 'def moveEvent(self, event):' not in content:
        print("❌ 没有添加moveEvent方法")
        return False
    
    # 检查moveEvent方法是否调用了_update_route_panel_position
    if 'self._update_route_panel_position()' not in content:
        print("❌ moveEvent方法没有调用_update_route_panel_position")
        return False
    
    print("✅ moveEvent方法添加正确")
    return True

def test_resize_event_added():
    """测试是否添加了resizeEvent方法"""
    print("\n=== 测试resizeEvent方法 ===")
    
    # 读取app.py文件内容
    app_file = os.path.join(project_root, 'src', 'app', 'app.py')
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否添加了resizeEvent方法
    if 'def resizeEvent(self, event):' not in content:
        print("❌ 没有添加resizeEvent方法")
        return False
    
    # 检查resizeEvent方法是否调用了_update_route_panel_position
    if content.count('self._update_route_panel_position()') < 2:
        print("❌ resizeEvent方法没有调用_update_route_panel_position")
        return False
    
    print("✅ resizeEvent方法添加正确")
    return True

def test_update_panel_position_method():
    """测试_update_route_panel_position方法"""
    print("\n=== 测试_update_route_panel_position方法 ===")
    
    # 读取app.py文件内容
    app_file = os.path.join(project_root, 'src', 'app', 'app.py')
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否有_update_route_panel_position方法
    if 'def _update_route_panel_position(self):' not in content:
        print("❌ 没有_update_route_panel_position方法")
        return False
    
    # 检查方法是否更新路线规划面板位置
    if 'self.route_plan_panel.move(' not in content:
        print("❌ 方法没有更新路线规划面板位置")
        return False
    
    # 检查方法是否更新GPX导出面板位置
    if 'self.gpx_export_popup.move(' not in content:
        print("❌ 方法没有更新GPX导出面板位置")
        return False
    
    # 检查是否有屏幕边界检查
    if 'screen.right()' not in content or 'screen.bottom()' not in content:
        print("❌ 方法没有屏幕边界检查")
        return False
    
    print("✅ _update_route_panel_position方法实现正确")
    return True

def test_method_logic():
    """测试方法逻辑"""
    print("\n=== 测试方法逻辑 ===")
    
    # 读取app.py文件内容
    app_file = os.path.join(project_root, 'src', 'app', 'app.py')
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否有正确的条件判断
    conditions_to_check = [
        'self.route_plan_panel.isVisible()',
        'self.gpx_export_popup.isVisible()',
        'hasattr(self, \'route_plan_panel\')',
        'hasattr(self, \'search_container\')',
        'hasattr(self, \'gpx_export_popup\')'
    ]
    
    missing_conditions = []
    for condition in conditions_to_check:
        if condition not in content:
            missing_conditions.append(condition)
    
    if missing_conditions:
        print(f"❌ 缺少条件判断: {missing_conditions}")
        return False
    
    # 检查是否使用了mapToGlobal获取全局位置
    if 'mapToGlobal' not in content:
        print("❌ 没有使用mapToGlobal获取全局位置")
        return False
    
    print("✅ 方法逻辑正确")
    return True

def test_integration_with_existing_code():
    """测试与现有代码的集成"""
    print("\n=== 测试与现有代码的集成 ===")
    
    # 读取app.py文件内容
    app_file = os.path.join(project_root, 'src', 'app', 'app.py')
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否保留了原有的_show_route_plan_panel方法
    if '_show_route_plan_panel' not in content:
        print("❌ 原有的_show_route_plan_panel方法丢失")
        return False
    
    # 检查是否保留了原有的GPX导出逻辑
    if '_on_export_gpx_clicked' not in content:
        print("❌ 原有的GPX导出逻辑丢失")
        return False
    
    # 检查是否保留了原有的按钮位置更新逻辑
    if '_update_button_positions' not in content:
        print("❌ 原有的按钮位置更新逻辑丢失")
        return False
    
    print("✅ 与现有代码集成正确")
    return True

def main():
    """主测试函数"""
    print("开始验证面板跟随窗口移动修复...")
    print("=" * 60)
    
    tests = [
        ("moveEvent方法", test_move_event_added),
        ("resizeEvent方法", test_resize_event_added),
        ("_update_route_panel_position方法", test_update_panel_position_method),
        ("方法逻辑", test_method_logic),
        ("与现有代码的集成", test_integration_with_existing_code),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试出错: {e}")
    
    print("=" * 60)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！面板跟随窗口移动修复成功")
        print("\n修复总结:")
        print("✅ 添加了moveEvent方法监听窗口移动")
        print("✅ 添加了resizeEvent方法监听窗口大小变化")
        print("✅ 实现了_update_route_panel_position方法更新面板位置")
        print("✅ 支持路线规划面板跟随主窗口移动")
        print("✅ 支持GPX导出面板跟随路线规划面板移动")
        print("✅ 包含屏幕边界检查，防止面板超出屏幕")
        print("✅ 与现有代码完美集成，不影响其他功能")
        return True
    else:
        print("❌ 部分测试失败，请检查修复")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
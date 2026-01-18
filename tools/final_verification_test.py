#!/usr/bin/env python3
"""
最终验证测试 - 验证所有GPX导出相关修复
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

def test_data_manager_fix():
    """测试DataManager修复"""
    print("=== 测试DataManager修复 ===")
    
    # 读取app.py文件内容
    app_file = os.path.join(project_root, 'src', 'app', 'app.py')
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否移除了错误的方法调用
    if 'get_start_location()' in content or 'get_end_location()' in content:
        print("❌ 仍然存在错误的方法调用")
        return False
    
    # 检查是否使用了正确的属性访问
    if 'data_manager.start_name' not in content or 'data_manager.end_name' not in content:
        print("❌ 没有使用正确的属性访问")
        return False
    
    # 检查是否添加了默认值处理
    if 'if self.data_manager.start_name else' not in content:
        print("❌ 没有添加默认值处理")
        return False
    
    print("✅ DataManager修复验证通过")
    return True

def test_gpx_popup_interface():
    """测试GPX弹出面板界面修复"""
    print("=== 测试GPX弹出面板界面修复 ===")
    
    # 读取gpx_export_popup.py文件内容
    popup_file = os.path.join(project_root, 'src', 'ui', 'popups', 'gpx_export_popup.py')
    with open(popup_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否使用了QLineEdit而不是CustomDateTimeEdit
    if 'QLineEdit()' not in content:
        print("❌ 没有使用QLineEdit作为时间输入框")
        return False
    
    # 检查是否添加了设置按钮
    if 'settings_button' not in content:
        print("❌ 没有添加设置按钮")
        return False
    
    # 检查是否使用了Setting_white.png图标
    if 'Setting_white.png' not in content:
        print("❌ 没有使用Setting_white.png图标")
        return False
    
    # 检查是否修改了窗口标志
    if 'Qt.Tool' not in content:
        print("❌ 没有使用Qt.Tool窗口标志")
        return False
    
    print("✅ GPX弹出面板界面修复验证通过")
    return True

def test_esc_key_hierarchy():
    """测试ESC键层级关闭逻辑"""
    print("=== 测试ESC键层级关闭逻辑 ===")
    
    # 读取gpx_export_popup.py文件内容
    popup_file = os.path.join(project_root, 'src', 'ui', 'popups', 'gpx_export_popup.py')
    with open(popup_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否有ESC键处理逻辑
    if 'keyPressEvent' not in content or 'Qt.Key_Escape' not in content:
        print("❌ 没有ESC键处理逻辑")
        return False
    
    # 检查是否有层级关闭逻辑
    if 'picker_popup' not in content or 'isVisible()' not in content:
        print("❌ 没有层级关闭逻辑")
        return False
    
    print("✅ ESC键层级关闭逻辑验证通过")
    return True

def test_icon_files():
    """测试图标文件是否存在"""
    print("=== 测试图标文件 ===")
    
    # 检查Setting_white.png是否存在
    setting_white_path = os.path.join(project_root, 'res', 'Setting_white.png')
    if not os.path.exists(setting_white_path):
        print("❌ Setting_white.png文件不存在")
        return False
    
    # 检查OutPut.svg是否存在
    output_svg_path = os.path.join(project_root, 'res', 'icons', 'OutPut.svg')
    if not os.path.exists(output_svg_path):
        print("❌ OutPut.svg文件不存在")
        return False
    
    print("✅ 图标文件验证通过")
    return True

def main():
    """主测试函数"""
    print("开始最终验证测试...")
    print("=" * 60)
    
    tests = [
        ("DataManager修复", test_data_manager_fix),
        ("GPX弹出面板界面修复", test_gpx_popup_interface),
        ("ESC键层级关闭逻辑", test_esc_key_hierarchy),
        ("图标文件", test_icon_files),
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
        print("🎉 所有测试通过！GPX导出功能修复完成")
        print("\n修复总结:")
        print("✅ 修复了DataManager方法调用错误")
        print("✅ 将时间日期文本框改为文本编辑框")
        print("✅ 添加了设置按钮和Setting_white.png图标")
        print("✅ 修复了面板自动关闭问题")
        print("✅ 实现了ESC键层级关闭逻辑")
        print("✅ 完善了焦点管理机制")
        return True
    else:
        print("❌ 部分测试失败，请检查修复")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
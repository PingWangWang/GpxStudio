#!/usr/bin/env python3
"""
测试动画图标系统
"""

import sys
import os

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_icon_manager():
    """测试图标管理器"""
    print("测试图标管理器...")
    
    try:
        from ui.icons.icon_manager import icon_manager, create_icon_button
        
        # 测试图标注册
        print(f"已注册图标数量: {len(icon_manager.list_icons())}")
        print("已注册的图标:")
        for icon_name in icon_manager.list_icons():
            animation_type = icon_manager.get_animation_type(icon_name)
            print(f"  - {icon_name}: {animation_type}")
        
        # 测试图标路径
        test_icons = ['MapSetting', 'RouteSetting', 'Cancel', 'Search', 'Location']
        print("\n测试图标路径:")
        for icon_name in test_icons:
            path = icon_manager.get_icon_path(icon_name)
            exists = os.path.exists(path) if path else False
            print(f"  - {icon_name}: {path} ({'存在' if exists else '不存在'})")
        
        print("\n✓ 图标管理器测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 图标管理器测试失败: {e}")
        return False

def test_animation_buttons():
    """测试动画按钮类"""
    print("\n测试动画按钮类...")
    
    try:
        # 测试滑块动画按钮
        from ui.widgets.slider_animated_button import SliderAnimatedButton
        print("✓ SliderAnimatedButton 导入成功")
        
        # 测试路径绘制动画按钮
        from ui.widgets.path_draw_animated_button import PathDrawAnimatedButton
        print("✓ PathDrawAnimatedButton 导入成功")
        
        # 测试变换动画按钮
        from ui.widgets.transform_animated_button import TransformAnimatedButton
        print("✓ TransformAnimatedButton 导入成功")
        
        # 测试复杂动画按钮
        from ui.widgets.complex_animated_button import ComplexAnimatedButton
        print("✓ ComplexAnimatedButton 导入成功")
        
        # 测试SVG动画按钮
        from ui.widgets.svg_animated_button import LucideSvgButton
        print("✓ LucideSvgButton 导入成功")
        
        print("✓ 所有动画按钮类测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 动画按钮类测试失败: {e}")
        return False

def test_svg_files():
    """测试SVG文件"""
    print("\n测试SVG文件...")
    
    try:
        from core.resource_path import resource_path
        
        # 测试主要的SVG文件
        svg_files = [
            'res/icons/MapSetting.svg',
            'res/icons/RouteSetting.svg', 
            'res/icons/Cancel.svg',
            'res/icons/Search.svg',
            'res/icons/Location.svg',
            'res/icons/ZoomBig.svg',
            'res/icons/Route.svg',
            'res/icons/Yes.svg',
            'res/icons/History.svg',
            'res/icons/Loading.svg',
            'res/icons/Log.svg',
            'res/icons/About.svg',
            'res/icons/ZoomSmall.svg',
            'res/icons/Add.svg',
            'res/icons/Delete.svg'
        ]
        
        missing_files = []
        for svg_file in svg_files:
            full_path = resource_path(svg_file)
            if not os.path.exists(full_path):
                missing_files.append(svg_file)
            else:
                print(f"  ✓ {svg_file}")
        
        if missing_files:
            print(f"\n缺失的SVG文件:")
            for missing in missing_files:
                print(f"  ✗ {missing}")
            return False
        else:
            print("✓ 所有SVG文件测试通过")
            return True
            
    except Exception as e:
        print(f"✗ SVG文件测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("动画图标系统测试")
    print("=" * 50)
    
    tests = [
        test_icon_manager,
        test_animation_buttons,
        test_svg_files
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！动画图标系统准备就绪。")
        return True
    else:
        print("❌ 部分测试失败，请检查上述错误。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
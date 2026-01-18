#!/usr/bin/env python3
"""
测试导入是否有错误
"""

import sys
import os

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_imports():
    """测试所有模块导入"""
    print("测试模块导入...")
    
    try:
        # 测试图标管理器导入
        print("1. 测试图标管理器...")
        from ui.icons.icon_manager import icon_manager, create_icon_button
        print("   ✓ 图标管理器导入成功")
        
        # 测试所有动画按钮类导入
        print("2. 测试动画按钮类...")
        from ui.widgets.slider_animated_button import SliderAnimatedButton
        print("   ✓ SliderAnimatedButton")
        
        from ui.widgets.path_draw_animated_button import PathDrawAnimatedButton
        print("   ✓ PathDrawAnimatedButton")
        
        from ui.widgets.transform_animated_button import TransformAnimatedButton
        print("   ✓ TransformAnimatedButton")
        
        from ui.widgets.complex_animated_button import ComplexAnimatedButton
        print("   ✓ ComplexAnimatedButton")
        
        from ui.widgets.location_animated_button import LocationAnimatedButton
        print("   ✓ LocationAnimatedButton")
        
        from ui.widgets.svg_animated_button import LucideSvgButton
        print("   ✓ LucideSvgButton")
        
        # 测试widgets模块导入
        print("3. 测试widgets模块...")
        from ui.widgets import (
            SliderAnimatedButton, PathDrawAnimatedButton, 
            TransformAnimatedButton, ComplexAnimatedButton,
            LocationAnimatedButton, LucideSvgButton
        )
        print("   ✓ widgets模块导入成功")
        
        print("\n✅ 所有导入测试通过！")
        return True
        
    except ImportError as e:
        print(f"\n❌ 导入错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ 其他错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
测试Route和Location图标的动画逻辑
"""

import sys
import os

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_route_animation_logic():
    """测试Route图标动画逻辑"""
    print("测试Route图标动画逻辑:")
    print("=" * 40)
    
    # 模拟动画进度
    test_progress_values = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    
    # 路径元素的延迟设置
    paths = [
        ("左上连线", 1, 0.15),  # custom=1, delay=0.15
        ("水平连线", 2, 0.30),  # custom=2, delay=0.30  
        ("右下连线", 3, 0.45),  # custom=3, delay=0.45
    ]
    
    print("圆形元素 (custom=0, 无延迟):")
    for progress in test_progress_values:
        circle_alpha = min(1.0, progress)
        print(f"  进度 {progress:.1f}: 透明度 {circle_alpha:.2f}")
    
    print("\n路径元素动画:")
    for name, custom, delay in paths:
        print(f"\n{name} (custom={custom}, delay={delay}):")
        for progress in test_progress_values:
            # 路径长度动画
            if progress > delay:
                path_progress = min(1.0, (progress - delay) / (1.0 - delay))
            else:
                path_progress = 0.0
            
            # 透明度动画 (delay = 0.1 * custom)
            opacity_delay = 0.1 * custom
            if progress > opacity_delay:
                alpha_progress = min(1.0, (progress - opacity_delay) / (1.0 - opacity_delay))
            else:
                alpha_progress = 0.0
            
            print(f"    进度 {progress:.1f}: 路径长度 {path_progress:.2f}, 透明度 {alpha_progress:.2f}")

def test_location_animation_logic():
    """测试Location图标动画逻辑"""
    print("\n\n测试Location图标动画逻辑:")
    print("=" * 40)
    
    # 模拟动画进度
    test_progress_values = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    
    print("Y轴跳跃动画 (y: [0, -5, -3], times: [0, 0.6, 1]):")
    for progress in test_progress_values:
        if progress <= 0.6:
            # 0 -> -5 (前60%时间)
            y_offset = -5 * (progress / 0.6)
        else:
            # -5 -> -3 (后40%时间)
            y_offset = -5 + 2 * ((progress - 0.6) / 0.4)
        print(f"  进度 {progress:.1f}: Y偏移 {y_offset:.2f}")
    
    print("\n内圆动画 (延迟0.3秒, 持续0.5秒):")
    circle_delay = 0.3
    circle_duration = 0.5
    opacity_duration = 0.1
    
    for progress in test_progress_values:
        # 路径长度动画
        if progress > circle_delay:
            circle_progress = min(1.0, (progress - circle_delay) / circle_duration)
        else:
            circle_progress = 0.0
        
        # 透明度动画
        if progress > circle_delay:
            opacity_progress = min(1.0, (progress - circle_delay) / opacity_duration)
        else:
            opacity_progress = 0.0
        
        print(f"  进度 {progress:.1f}: 路径长度 {circle_progress:.2f}, 透明度 {opacity_progress:.2f}")

def analyze_tsx_animation_timing():
    """分析TSX动画时序"""
    print("\n\n分析TSX动画时序:")
    print("=" * 40)
    
    print("Route图标 (WaypointsIcon):")
    print("- 圆形: custom=0, 无延迟")
    print("- 路径: custom=1,2,3")
    print("- 路径延迟: delay = 0.15 * custom")
    print("- 透明度延迟: opacity.delay = 0.1 * custom")
    print("- 动画效果: 圆形立即出现，路径按顺序依次绘制")
    
    print("\nLocation图标 (MapPinIcon):")
    print("- 整体SVG: y: [0, -5, -3], times: [0, 0.6, 1], duration: 0.5s")
    print("- 内圆: pathLength: [0, 1], opacity: [0, 1]")
    print("- 内圆延迟: delay: 0.3s, duration: 0.5s")
    print("- 透明度: duration: 0.1s, delay: 0.3s")
    print("- 动画效果: 整体跳跃 + 内圆延迟出现")

def main():
    """主测试函数"""
    print("Route和Location图标动画逻辑分析")
    print("=" * 50)
    
    test_route_animation_logic()
    test_location_animation_logic()
    analyze_tsx_animation_timing()
    
    print("\n" + "=" * 50)
    print("✓ 动画逻辑分析完成")
    print("主要修正:")
    print("1. Route图标: 实现正确的延迟路径长度动画")
    print("2. Location图标: 实现Y轴跳跃 + 内圆延迟动画")

if __name__ == "__main__":
    main()
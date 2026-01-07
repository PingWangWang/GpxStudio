#!/usr/bin/env python3
"""
布局测试脚本
验证界面布局比例是否正确
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_layout_ratios():
    """测试布局比例"""
    print("=== 界面布局比例测试 ===")

    # 读取core/app.py文件，检查setStretchFactor设置
    app_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'core', 'app.py')

    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 查找setStretchFactor设置
    lines = content.split('\n')
    stretch_factors = []

    for i, line in enumerate(lines):
        if 'setStretchFactor' in line:
            # 提取因子值
            parts = line.split(',')
            if len(parts) >= 2:
                try:
                    factor = int(parts[1].strip()[:-1])  # 去掉最后的)
                    stretch_factors.append(factor)
                except:
                    pass

    print(f"找到的拉伸因子: {stretch_factors}")

    if len(stretch_factors) == 3:
        left, middle, right = stretch_factors
        total = left + middle + right

        print(f"左侧面板比例: {left}/{total} = {left/total:.1%}")
        print(f"中间面板比例: {middle}/{total} = {middle/total:.1%}")
        print(f"右侧面板比例: {right}/{total} = {right/total:.1%}")

        # 检查是否右侧面板更大
        if right > left and right > middle:
            print("✅ 布局优化成功：地图展示区（右侧）获得最大宽度")
        else:
            print("❌ 布局可能需要调整")

        # 检查setSizes设置
        sizes_found = False
        for line in lines:
            if 'setSizes([' in line and '300, 250, 1000' in line:
                sizes_found = True
                print("✅ 找到初始尺寸设置: [300, 250, 1000]")
                break

        if not sizes_found:
            print("⚠️  未找到预期的初始尺寸设置")

    else:
        print("❌ 未找到完整的拉伸因子设置")

    print()

def test_import():
    """测试模块导入"""
    print("=== 模块导入测试 ===")

    try:
        from core import GpxStudio
        print("✅ 核心模块导入成功")
    except Exception as e:
        print(f"❌ 核心模块导入失败: {e}")
        return

    try:
        from handlers import GeolocationHandler, ConsoleWebEnginePage
        print("✅ 处理器模块导入成功")
    except Exception as e:
        print(f"❌ 处理器模块导入失败: {e}")
        return

    try:
        from services import GeocodingService, RoutingService, GpxExportService
        print("✅ 服务模块导入成功")
    except Exception as e:
        print(f"❌ 服务模块导入失败: {e}")
        return

    try:
        from ui import UIStyles, PanelFactory
        print("✅ UI模块导入成功")
    except Exception as e:
        print(f"❌ UI模块导入失败: {e}")
        return

    try:
        from utils import MapRenderer, LocationHelper
        print("✅ 工具模块导入成功")
    except Exception as e:
        print(f"❌ 工具模块导入失败: {e}")
        return

    print("✅ 所有模块导入成功")

def main():
    """主测试函数"""
    print("GPX Studio 布局和模块测试")
    print("=" * 50)

    test_layout_ratios()
    test_import()

    print("\n" + "=" * 50)
    print("测试完成！")

if __name__ == "__main__":
    main()
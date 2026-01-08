#!/usr/bin/env python3
"""
地图初始化测试脚本
验证程序启动时地图是否能正常显示
"""

import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_map_initialization():
    """测试地图初始化逻辑"""
    print("=== 地图初始化测试 ===")

    # 检查代码中是否包含延迟加载逻辑
    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    app_file = os.path.join(project_root, 'app', 'app.py')

    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否包含QTimer.singleShot
    if 'QTimer.singleShot(500, self.show_initial_map)' in content:
        print("✅ 找到延迟加载地图的逻辑：QTimer.singleShot(500, self.show_initial_map)")
    else:
        print("❌ 未找到延迟加载地图的逻辑")
        return False

    # 检查show_initial_map方法是否存在（应该存在）
    if 'def show_initial_map(self):' in content:
        print("✅ show_initial_map() 方法存在")
    else:
        print("❌ show_initial_map() 方法不存在")
        return False

    # 检查create_right_panel中是否还有直接调用
    lines = content.split('\n')
    in_create_right_panel = False
    direct_call_found = False

    for line in lines:
        if 'def create_right_panel(self):' in line:
            in_create_right_panel = True
        elif line.startswith('    def ') and in_create_right_panel:
            in_create_right_panel = False
        elif in_create_right_panel and 'self.show_initial_map()' in line and '注意：' not in line:
            direct_call_found = True
            break

    if direct_call_found:
        print("❌ create_right_panel 中仍包含直接调用 show_initial_map()")
        return False
    else:
        print("✅ create_right_panel 中已移除直接调用，改为延迟加载")

    # 检查QTimer导入
    if 'from PyQt5.QtCore import Qt, QTimer' in content:
        print("✅ QTimer 已正确导入")
    else:
        print("❌ QTimer 导入缺失")
        return False

    return True

def test_module_import():
    """测试模块导入"""
    print("\n=== 模块导入测试 ===")

    try:
        from core import GpxStudio
        print("✅ 核心模块导入成功")
        return True
    except Exception as e:
        print(f"❌ 核心模块导入失败: {e}")
        return False

def main():
    """主测试函数"""
    print("GPX Studio 地图初始化测试")
    print("=" * 50)

    success = True

    if not test_map_initialization():
        success = False

    if not test_module_import():
        success = False

    print("\n" + "=" * 50)
    if success:
        print("✅ 所有测试通过！地图将在程序启动后500ms自动显示")
    else:
        print("❌ 测试失败，请检查代码修改")

    return success

if __name__ == "__main__":
    main()
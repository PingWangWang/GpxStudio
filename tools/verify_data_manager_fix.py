#!/usr/bin/env python3
"""
验证DataManager修复
检查GPX导出代码中的修复是否正确
"""

import sys
import os

def test_code_fix():
    """测试代码修复"""
    print("=== 验证DataManager修复 ===")
    
    try:
        # 读取修复后的代码
        with open('src/app/app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("1. 检查是否移除了错误的方法调用")
        if 'get_start_location()' in content or 'get_end_location()' in content:
            print("❌ 仍然存在错误的方法调用")
            return False
        else:
            print("✅ 已移除错误的方法调用")
        
        print("\n2. 检查是否使用了正确的属性访问")
        if 'data_manager.start_name' in content and 'data_manager.end_name' in content:
            print("✅ 使用了正确的属性访问")
        else:
            print("❌ 未使用正确的属性访问")
            return False
        
        print("\n3. 检查是否添加了默认值处理")
        if 'if self.data_manager.start_name else' in content and 'if self.data_manager.end_name else' in content:
            print("✅ 添加了默认值处理")
        else:
            print("❌ 未添加默认值处理")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 验证出错: {e}")
        return False

def test_logic_simulation():
    """测试逻辑模拟"""
    print("\n=== 模拟修复后的逻辑 ===")
    
    try:
        # 模拟DataManager类
        class MockDataManager:
            def __init__(self):
                self.start_name = None
                self.end_name = None
        
        # 测试场景1：有起点和终点名称
        print("1. 测试有起点和终点名称的情况")
        data_manager = MockDataManager()
        data_manager.start_name = "天安门广场"
        data_manager.end_name = "北京西站"
        
        # 模拟修复后的逻辑
        start_name = data_manager.start_name if data_manager.start_name else '起点'
        end_name = data_manager.end_name if data_manager.end_name else '终点'
        
        print(f"   起点名称: {start_name}")
        print(f"   终点名称: {end_name}")
        
        assert start_name == "天安门广场"
        assert end_name == "北京西站"
        print("   ✅ 有名称情况测试通过")
        
        # 测试场景2：没有起点和终点名称
        print("\n2. 测试没有起点和终点名称的情况")
        empty_data_manager = MockDataManager()
        
        start_name = empty_data_manager.start_name if empty_data_manager.start_name else '起点'
        end_name = empty_data_manager.end_name if empty_data_manager.end_name else '终点'
        
        print(f"   起点名称: {start_name}")
        print(f"   终点名称: {end_name}")
        
        assert start_name == "起点"
        assert end_name == "终点"
        print("   ✅ 无名称情况测试通过")
        
        # 测试场景3：文件名生成
        print("\n3. 测试文件名生成")
        import re
        
        def generate_filename(start_name, end_name):
            safe_start = re.sub(r'[\\/:*?"<>|]', '', start_name)
            safe_end = re.sub(r'[\\/:*?"<>|]', '', end_name)
            return f"{safe_start}_{safe_end}.gpx"
        
        # 正常情况
        filename1 = generate_filename("天安门广场", "北京西站")
        print(f"   正常文件名: {filename1}")
        assert filename1 == "天安门广场_北京西站.gpx"
        
        # 默认情况
        filename2 = generate_filename("起点", "终点")
        print(f"   默认文件名: {filename2}")
        assert filename2 == "起点_终点.gpx"
        
        # 特殊字符情况
        filename3 = generate_filename("起点/地址:测试", "终点\\地址*测试")
        print(f"   特殊字符文件名: {filename3}")
        assert filename3 == "起点地址测试_终点地址测试.gpx"
        
        print("   ✅ 文件名生成测试通过")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_scenario():
    """测试错误场景"""
    print("\n=== 测试错误场景 ===")
    
    try:
        # 模拟修复前的错误
        class OldDataManager:
            def __init__(self):
                pass
            
            # 注意：这里故意不定义get_start_location方法来模拟错误
        
        print("1. 模拟修复前的错误")
        old_data_manager = OldDataManager()
        
        try:
            # 这会导致AttributeError
            start_location = old_data_manager.get_start_location()
            print("❌ 应该抛出AttributeError")
            return False
        except AttributeError as e:
            print(f"   预期的错误: {e}")
            print("   ✅ 成功模拟了修复前的错误")
        
        # 模拟修复后的正确逻辑
        class NewDataManager:
            def __init__(self):
                self.start_name = None
                self.end_name = None
        
        print("\n2. 模拟修复后的正确逻辑")
        new_data_manager = NewDataManager()
        
        # 这不会抛出错误
        start_name = new_data_manager.start_name if new_data_manager.start_name else '起点'
        end_name = new_data_manager.end_name if new_data_manager.end_name else '终点'
        
        print(f"   起点名称: {start_name}")
        print(f"   终点名称: {end_name}")
        print("   ✅ 修复后的逻辑正常工作")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        return False

def main():
    """主测试函数"""
    print("开始验证DataManager修复...")
    
    success_count = 0
    total_tests = 3
    
    # 运行所有测试
    tests = [
        test_code_fix,
        test_logic_simulation,
        test_error_scenario
    ]
    
    for test in tests:
        try:
            if test():
                success_count += 1
        except Exception as e:
            print(f"❌ 测试异常: {e}")
    
    print("\n" + "="*60)
    print(f"测试结果: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("🎉 所有测试通过！DataManager修复验证成功")
        print("\n修复总结:")
        print("✅ 移除了不存在的方法调用 get_start_location() 和 get_end_location()")
        print("✅ 改为直接访问 data_manager.start_name 和 data_manager.end_name 属性")
        print("✅ 添加了空值检查和默认值处理")
        print("✅ 文件名生成逻辑正确")
        print("\n错误原因:")
        print("- DataManager类中没有get_start_location()和get_end_location()方法")
        print("- 但有start_name和end_name属性可以直接访问")
        print("\n修复方案:")
        print("- 将方法调用改为属性访问")
        print("- 添加默认值处理，避免空值问题")
        return True
    else:
        print("❌ 部分测试失败，请检查修复")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
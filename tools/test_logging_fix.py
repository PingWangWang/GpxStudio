#!/usr/bin/env python3
"""
测试日志修复 - 验证GPX导出服务的日志回调修复
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

def test_logging_callback_fix():
    """测试日志回调修复"""
    print("=== 测试日志回调修复 ===")
    
    # 模拟logger对象
    class MockLogger:
        def __init__(self):
            self.logs = []
        
        def info(self, message):
            self.logs.append(('INFO', message))
            print(f"INFO: {message}")
        
        def debug(self, message):
            self.logs.append(('DEBUG', message))
            print(f"DEBUG: {message}")
        
        def warning(self, message):
            self.logs.append(('WARNING', message))
            print(f"WARNING: {message}")
        
        def error(self, message):
            self.logs.append(('ERROR', message))
            print(f"ERROR: {message}")
        
        def log(self, level, message):
            # 这个方法期望level是整数，会导致错误
            raise TypeError("level must be an integer")
    
    # 测试修复前的错误逻辑
    print("1. 测试修复前的错误逻辑")
    mock_logger = MockLogger()
    
    def old_log_callback(level: str, message: str):
        try:
            # 这是修复前的错误代码
            mock_logger.log(getattr(mock_logger, level.lower(), mock_logger.info), f"[GPX导出] {message}")
        except Exception as e:
            print(f"   预期的错误: {e}")
            return False
        return True
    
    # 测试错误情况
    result = old_log_callback("INFO", "测试消息")
    if not result:
        print("   ✅ 成功重现了修复前的错误")
    else:
        print("   ❌ 未能重现修复前的错误")
    
    # 测试修复后的正确逻辑
    print("\n2. 测试修复后的正确逻辑")
    
    def new_log_callback(level: str, message: str):
        try:
            # 这是修复后的正确代码
            log_func = getattr(mock_logger, level.lower(), mock_logger.info)
            log_func(f"[GPX导出] {message}")
            return True
        except Exception as e:
            print(f"   意外的错误: {e}")
            return False
    
    # 测试各种日志级别
    test_cases = [
        ("INFO", "信息消息"),
        ("DEBUG", "调试消息"),
        ("WARNING", "警告消息"),
        ("ERROR", "错误消息"),
        ("UNKNOWN", "未知级别消息")  # 应该回退到info
    ]
    
    all_passed = True
    for level, message in test_cases:
        result = new_log_callback(level, message)
        if result:
            print(f"   ✅ {level} 级别测试通过")
        else:
            print(f"   ❌ {level} 级别测试失败")
            all_passed = False
    
    return all_passed

def test_gpx_service_integration():
    """测试GPX服务集成"""
    print("\n=== 测试GPX服务集成 ===")
    
    try:
        from modules.gpx.gpx_export import GpxExportService
        
        # 创建日志收集器
        logs = []
        def log_callback(level: str, message: str):
            logs.append((level, message))
            print(f"   {level}: {message}")
        
        # 创建GPX服务
        gpx_service = GpxExportService(logger=log_callback)
        
        # 测试日志功能
        gpx_service.log("INFO", "测试信息")
        gpx_service.log("DEBUG", "测试调试")
        gpx_service.log("WARNING", "测试警告")
        gpx_service.log("ERROR", "测试错误")
        
        if len(logs) == 4:
            print("✅ GPX服务日志功能正常")
            return True
        else:
            print(f"❌ GPX服务日志功能异常，期望4条日志，实际{len(logs)}条")
            return False
            
    except Exception as e:
        print(f"❌ GPX服务集成测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试日志修复...")
    print("=" * 60)
    
    tests = [
        ("日志回调修复", test_logging_callback_fix),
        ("GPX服务集成", test_gpx_service_integration),
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
        print("🎉 所有测试通过！日志修复成功")
        print("\n修复总结:")
        print("✅ 修复了日志回调中的level参数错误")
        print("✅ 将self.logger.log()改为直接调用对应的日志方法")
        print("✅ GPX导出服务日志功能正常")
        return True
    else:
        print("❌ 部分测试失败，请检查修复")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
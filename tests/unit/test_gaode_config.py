#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试高德地图配置保存和加载功能
"""

import os
import sys

# 将项目根目录添加到sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from services.config.gaode_config import gaode_config

# 获取用户主目录
user_home = os.path.expanduser("~")
config_path = os.path.join(user_home, "GPXStudio", "gaode_config.json")
print(f"配置文件路径: {config_path}")
print(f"配置文件是否存在: {os.path.exists(config_path)}")

# 测试保存配置
print("\n测试保存配置...")
test_config = {"api_key": "test_api_key_12345", "security_key": "test_security_key_67890"}
save_result = gaode_config.save_config(test_config)
print(f"保存配置结果: {save_result}")
print(f"配置文件是否存在: {os.path.exists(config_path)}")

# 测试加载配置
print("\n测试加载配置...")
print("加载前的API Key:", gaode_config.get_api_key())
# 创建新实例测试加载
from services.config.gaode_config import GaodeConfig
new_config = GaodeConfig()
print(f"新实例加载的API Key: {new_config.get_api_key()}")
print(f"新实例加载的Security Key: {new_config.get_security_key()}")

# 测试清除配置
print("\n测试清除配置...")
clear_result = gaode_config.clear_config()
print(f"清除配置结果: {clear_result}")
print(f"配置文件是否存在: {os.path.exists(config_path)}")

print("\n测试完成！")
#!/usr/bin/env python3
"""
测试高德地图API调用
"""

import requests
import os

# 从配置文件获取API密钥
API_KEY = ""
SECURITY_KEY = ""

# 测试点：北京的两个相邻点
start = (39.984104, 116.307499)  # 纬度, 经度
end = (39.984504, 116.308499)    # 纬度, 经度

# 测试不同的API版本和交通方式
test_cases = [
    # (API版本, 交通方式)
    ("v3", "driving"),
    ("v3", "walking"),
    ("v3", "bicycling"),
    ("v4", "driving"),
    ("v4", "walking"),
    ("v4", "bicycling"),
]

for version, mode in test_cases:
    print(f"\n=== 测试 {version}/{mode} ===")

    # 构建API URL
    url = f"https://restapi.amap.com/{version}/direction/{mode}"

    # 构建请求参数
    params = {
        "key": API_KEY,
        "origin": f"{start[1]},{start[0]}",  # 高德API使用：经度,纬度
        "destination": f"{end[1]},{end[0]}",  # 高德API使用：经度,纬度
        "output": "json"
    }

    # 如果有安全密钥，添加签名参数
    if SECURITY_KEY:
        import hashlib
        sorted_params = sorted(params.items())
        sign_str = SECURITY_KEY + ''.join(f"{k}{v}" for k, v in sorted_params)
        params["sig"] = hashlib.md5(sign_str.encode()).hexdigest()

    try:
        # 发送请求
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        print(f"状态码: {response.status_code}")
        print(f"API响应: {data}")

        # 检查响应状态
        if data.get("status") == "1":
            print("✓ 请求成功")
        else:
            print(f"✗ 请求失败: {data.get('info', '未知错误')}")

    except Exception as e:
        print(f"✗ 发生异常: {str(e)}")

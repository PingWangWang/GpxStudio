#!/usr/bin/env python3
"""
GPX Studio 服务模块测试脚本
用于调试和测试各个服务模块的功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.gaode_geocoding import GaodeGeocodingService
from services.gaode_routing import GaodeRoutingService
from modules.gpx.gpx_export import GpxExportService
from modules.geolocation.location_helper import LocationHelper
from datetime import datetime
from PyQt5.QtCore import QTime


def test_geocoding_service():
    """测试地理编码服务"""
    print("=== 测试地理编码服务 ===")

    service = GaodeGeocodingService()

    # 测试地点搜索
    print("1. 测试地点搜索...")
    locations = service.search_location("北京市")
    if locations:
        print(f"   找到 {len(locations)} 个结果")
        for i, loc in enumerate(locations[:3]):  # 只显示前3个
            print(f"   {i+1}. {loc.address} ({loc.latitude:.4f}, {loc.longitude:.4f})")
    else:
        print("   未找到结果")

    # 测试反向地理编码
    print("2. 测试反向地理编码...")
    address_info = service.reverse_geocode(39.9042, 116.4074)  # 北京坐标
    if address_info:
        print(f"   地址信息: {address_info}")
    else:
        print("   获取地址信息失败")


def test_routing_service():
    """测试路由规划服务"""
    print("\n=== 测试路由规划服务 ===")

    service = GaodeRoutingService()

    # 使用更近的测试坐标点，避免API调用限制
    points = [
        (39.9042, 116.4074),  # 北京天安门
        (39.9150, 116.4070),  # 北京故宫
    ]

    # 测试所有交通方式
    for mode in ["驾车", "步行", "骑行"]:
        print(f"\n1. 测试{mode}路线规划...")
        route_points, duration = service.plan_route(points, mode)
        if route_points:
            valid_points = [p for p in route_points if p is not None]
            print(f"   {mode}规划成功，路线点数: {len(valid_points)}")
            # 计算距离
            distance = service.calculate_distance(route_points)
            print(f"   总距离: {distance:.1f} 公里")
            print(f"   预估时间: {duration} 秒")
        else:
            print(f"   {mode}路线规划失败")


def test_location_helper():
    """测试定位辅助工具"""
    print("\n=== 测试定位辅助工具 ===")

    # 测试IP定位
    print("1. 测试IP定位...")
    ip_location = LocationHelper.get_ip_location()
    if ip_location:
        print(f"   IP定位结果: {ip_location}")
    else:
        print("   IP定位失败")

    # 测试坐标格式化
    print("2. 测试坐标格式化...")
    formatted = LocationHelper.format_coordinates(39.9042, 116.4074)
    print(f"   格式化坐标: {formatted}")


def test_gpx_export_service():
    """测试GPX导出服务"""
    print("\n=== 测试GPX导出服务 ===")

    service = GpxExportService()

    # 创建测试路线点
    route_points = [
        (39.9042, 116.4074),  # 北京
        (39.9050, 116.4080),  # 附近点
        (39.9060, 116.4090),  # 另一个点
    ]

    # 测试GPX信息获取
    print("1. 测试GPX信息获取...")
    info = service.get_gpx_info(route_points)
    print(f"   GPX信息: {info}")

    # 测试GPX导出
    print("2. 测试GPX导出...")
    start_time = QTime(8, 0)  # 早上8点
    success = service.export_to_gpx(route_points, start_time, "test_output.gpx")
    if success:
        print("   GPX导出成功: test_output.gpx")
        # 清理测试文件
        if os.path.exists("test_output.gpx"):
            os.remove("test_output.gpx")
            print("   测试文件已清理")
    else:
        print("   GPX导出失败")


def main():
    """主测试函数"""
    print("GPX Studio 服务模块测试")
    print("=" * 50)

    try:
        test_geocoding_service()
        test_routing_service()
        test_location_helper()
        test_gpx_export_service()

        print("\n" + "=" * 50)
        print("所有测试完成！")

    except Exception as e:
        print(f"\n测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
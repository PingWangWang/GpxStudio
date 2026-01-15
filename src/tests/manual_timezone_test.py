"""
手动测试脚本：测试不同地区的GPX导出时区功能

此脚本测试以下场景：
1. 中国路线（应使用Asia/Shanghai）
2. 美国路线（应使用America/New_York或其他美国时区）
3. 欧洲路线（应使用Europe/London或其他欧洲时区）
4. 跨时区路线（应使用起点时区）

需求: 1.1, 1.2, 2.1, 2.3
"""

import os
import sys
import re
from datetime import datetime
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modules.gpx.gpx_export import GpxExportService


class MockQDateTime:
    """模拟QDateTime对象用于测试"""
    def __init__(self, year, month, day, hour, minute):
        self._dt = datetime(year, month, day, hour, minute)

    def date(self):
        return self

    def time(self):
        return self

    def year(self):
        return self._dt.year

    def month(self):
        return self._dt.month

    def day(self):
        return self._dt.day

    def hour(self):
        return self._dt.hour

    def minute(self):
        return self._dt.minute


def extract_timezone_from_gpx(file_path):
    """从GPX文件中提取时区信息"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 查找所有时间戳
    timestamps = re.findall(r'<time>(.*?)</time>', content)

    if not timestamps:
        return None, []

    # 提取时区信息
    timezones = []
    for ts in timestamps:
        # 匹配 +HH:MM 或 -HH:MM 格式
        tz_match = re.search(r'([+-]\d{2}:\d{2})$', ts)
        if tz_match:
            timezones.append(tz_match.group(1))
        elif ts.endswith('Z'):
            timezones.append('Z')

    return timezones[0] if timezones else None, timezones


def verify_timezone_consistency(timezones):
    """验证所有时间戳使用相同的时区"""
    if not timezones:
        return False, "未找到时间戳"

    first_tz = timezones[0]
    all_same = all(tz == first_tz for tz in timezones)

    if all_same:
        return True, f"所有 {len(timezones)} 个时间戳使用相同时区: {first_tz}"
    else:
        unique_tzs = set(timezones)
        return False, f"发现不同的时区: {unique_tzs}"


def test_region(region_name, route_points, expected_tz_pattern, output_dir):
    """测试特定地区的路线导出"""
    print(f"\n{'='*60}")
    print(f"测试 {region_name}")
    print(f"{'='*60}")

    # 创建日志收集器
    logs = []
    def logger(level, message):
        logs.append(f"[{level}] {message}")
        print(f"[{level}] {message}")

    # 创建导出服务
    service = GpxExportService(logger=logger)

    # 创建测试时间
    start_time = MockQDateTime(2024, 1, 15, 12, 0)

    # 导出文件
    file_path = os.path.join(output_dir, f"{region_name.replace(' ', '_')}.gpx")
    success = service.export_to_gpx(
        route_points=route_points,
        start_datetime=start_time,
        file_path=file_path,
        start_name=f"{region_name}_起点",
        end_name=f"{region_name}_终点"
    )

    print(f"\n导出结果: {'成功' if success else '失败'}")

    if success:
        # 提取并验证时区信息
        first_tz, all_tzs = extract_timezone_from_gpx(file_path)

        print(f"\n时区信息:")
        print(f"  检测到的时区: {first_tz}")
        print(f"  总时间戳数: {len(all_tzs)}")

        # 验证时区一致性
        consistent, message = verify_timezone_consistency(all_tzs)
        print(f"  时区一致性: {message}")

        # 验证时区是否符合预期
        if expected_tz_pattern:
            if first_tz and expected_tz_pattern in first_tz:
                print(f"  ✓ 时区符合预期 (期望包含: {expected_tz_pattern})")
            else:
                print(f"  ✗ 时区不符合预期 (期望包含: {expected_tz_pattern}, 实际: {first_tz})")

        # 显示文件路径
        print(f"\n导出文件: {file_path}")

        # 显示前3个时间戳作为示例
        if all_tzs:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            timestamps = re.findall(r'<time>(.*?)</time>', content)[:3]
            print(f"\n示例时间戳:")
            for i, ts in enumerate(timestamps, 1):
                print(f"  {i}. {ts}")

        return success and consistent

    return False


def main():
    """主测试函数"""
    print("GPX时区导出 - 手动测试脚本")
    print("="*60)

    # 创建输出目录
    output_dir = "test_output_gpx"
    os.makedirs(output_dir, exist_ok=True)
    print(f"输出目录: {output_dir}\n")

    results = {}

    # 测试1: 中国路线（北京到上海）
    # 北京: 39.9042°N, 116.4074°E
    # 上海: 31.2304°N, 121.4737°E
    china_route = [
        (39.9042, 116.4074),  # 北京
        (39.5, 117.0),
        (38.0, 118.0),
        (36.0, 119.0),
        (34.0, 120.0),
        (31.2304, 121.4737),  # 上海
    ]
    results['中国路线'] = test_region(
        "中国路线",
        china_route,
        "+08:00",  # Asia/Shanghai 是 UTC+8
        output_dir
    )

    # 测试2: 美国路线（纽约到波士顿）
    # 纽约: 40.7128°N, -74.0060°W
    # 波士顿: 42.3601°N, -71.0589°W
    us_route = [
        (40.7128, -74.0060),  # 纽约
        (41.0, -73.5),
        (41.5, -73.0),
        (42.0, -72.0),
        (42.3601, -71.0589),  # 波士顿
    ]
    results['美国路线'] = test_region(
        "美国路线",
        us_route,
        "-05:00",  # America/New_York 是 UTC-5 (标准时间)
        output_dir
    )

    # 测试3: 欧洲路线（伦敦到巴黎）
    # 伦敦: 51.5074°N, -0.1278°W
    # 巴黎: 48.8566°N, 2.3522°E
    europe_route = [
        (51.5074, -0.1278),  # 伦敦
        (51.0, 0.5),
        (50.5, 1.0),
        (49.5, 1.5),
        (48.8566, 2.3522),  # 巴黎
    ]
    results['欧洲路线'] = test_region(
        "欧洲路线",
        europe_route,
        "+00:00",  # Europe/London 是 UTC+0 (标准时间)
        output_dir
    )

    # 测试4: 跨时区路线（从中国到日本）
    # 北京: 39.9042°N, 116.4074°E (Asia/Shanghai, UTC+8)
    # 东京: 35.6762°N, 139.6503°E (Asia/Tokyo, UTC+9)
    cross_timezone_route = [
        (39.9042, 116.4074),  # 北京 (起点)
        (38.0, 120.0),
        (37.0, 125.0),
        (36.0, 130.0),
        (35.6762, 139.6503),  # 东京
    ]
    results['跨时区路线'] = test_region(
        "跨时区路线",
        cross_timezone_route,
        "+08:00",  # 应使用起点时区 (Asia/Shanghai)
        output_dir
    )

    # 打印总结
    print(f"\n{'='*60}")
    print("测试总结")
    print(f"{'='*60}")

    for test_name, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{test_name}: {status}")

    all_passed = all(results.values())
    print(f"\n总体结果: {'所有测试通过' if all_passed else '部分测试失败'}")

    print(f"\n所有导出的GPX文件保存在: {output_dir}/")
    print("请使用文本编辑器或GPX查看器检查这些文件。")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

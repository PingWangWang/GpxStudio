"""
GPX文件验证脚本

此脚本验证导出的GPX文件：
1. 使用文本编辑器检查GPX文件内容
2. 验证时间戳格式正确（包含+HH:MM）
3. 验证所有时间戳使用相同时区
4. 使用GPX解析器验证文件兼容性

需求: 2.2, 2.3, 2.4, 5.2
"""

import os
import sys
import re
from pathlib import Path
import xml.etree.ElementTree as ET

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def verify_gpx_file(file_path):
    """验证单个GPX文件"""
    print(f"\n{'='*60}")
    print(f"验证文件: {os.path.basename(file_path)}")
    print(f"{'='*60}")

    if not os.path.exists(file_path):
        print(f"✗ 文件不存在: {file_path}")
        return False

    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"\n文件大小: {len(content)} 字节")

    # 1. 验证XML格式
    print("\n1. 验证XML格式...")
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        print("   ✓ XML格式有效")
    except Exception as e:
        print(f"   ✗ XML格式无效: {e}")
        return False

    # 2. 验证GPX结构
    print("\n2. 验证GPX结构...")

    # 检查命名空间
    namespace = {'gpx': 'http://www.topografix.com/GPX/1/1'}

    # 检查metadata
    metadata = root.find('gpx:metadata', namespace)
    if metadata is not None:
        name = metadata.find('gpx:name', namespace)
        author = metadata.find('gpx:author', namespace)
        print(f"   ✓ 找到metadata节点")
        if name is not None:
            print(f"     - 名称: {name.text}")
        if author is not None:
            author_name = author.find('gpx:name', namespace)
            if author_name is not None:
                print(f"     - 作者: {author_name.text}")

    # 检查track
    tracks = root.findall('gpx:trk', namespace)
    print(f"   ✓ 找到 {len(tracks)} 个轨迹")

    # 3. 提取并验证时间戳
    print("\n3. 验证时间戳格式...")

    # 查找所有时间戳
    timestamps = re.findall(r'<time>(.*?)</time>', content)
    print(f"   找到 {len(timestamps)} 个时间戳")

    if not timestamps:
        print("   ✗ 未找到时间戳")
        return False

    # 验证ISO 8601格式
    # 格式: YYYY-MM-DDTHH:MM:SS±HH:MM 或 YYYY-MM-DDTHH:MM:SSZ
    iso8601_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}([+-]\d{2}:\d{2}|Z)$'

    valid_count = 0
    invalid_timestamps = []

    for ts in timestamps:
        if re.match(iso8601_pattern, ts):
            valid_count += 1
        else:
            invalid_timestamps.append(ts)

    if valid_count == len(timestamps):
        print(f"   ✓ 所有时间戳符合ISO 8601格式")
    else:
        print(f"   ✗ {len(invalid_timestamps)} 个时间戳格式无效:")
        for ts in invalid_timestamps[:5]:  # 只显示前5个
            print(f"     - {ts}")
        return False

    # 4. 验证时区信息
    print("\n4. 验证时区信息...")

    # 提取时区偏移
    timezones = []
    for ts in timestamps:
        # 匹配 +HH:MM 或 -HH:MM 格式
        tz_match = re.search(r'([+-]\d{2}:\d{2})$', ts)
        if tz_match:
            timezones.append(tz_match.group(1))
        elif ts.endswith('Z'):
            timezones.append('Z')
        else:
            timezones.append(None)

    # 检查是否所有时间戳都包含时区信息
    has_timezone = [tz is not None for tz in timezones]
    if all(has_timezone):
        print(f"   ✓ 所有时间戳包含时区信息")
    else:
        missing_count = len([tz for tz in timezones if tz is None])
        print(f"   ✗ {missing_count} 个时间戳缺少时区信息")
        return False

    # 显示时区分布
    unique_tzs = set(timezones)
    print(f"   时区分布:")
    for tz in unique_tzs:
        count = timezones.count(tz)
        print(f"     - {tz}: {count} 个时间戳")

    # 5. 验证时区一致性
    print("\n5. 验证时区一致性...")

    if len(unique_tzs) == 1:
        print(f"   ✓ 所有时间戳使用相同时区: {list(unique_tzs)[0]}")
    else:
        print(f"   ✗ 发现多个不同的时区: {unique_tzs}")
        return False

    # 6. 显示示例时间戳
    print("\n6. 示例时间戳 (前5个):")
    for i, ts in enumerate(timestamps[:5], 1):
        print(f"   {i}. {ts}")

    # 7. 使用gpxpy验证兼容性
    print("\n7. 验证GPX解析器兼容性...")
    try:
        import gpxpy

        with open(file_path, 'r', encoding='utf-8') as f:
            gpx = gpxpy.parse(f)

        # 统计信息
        track_count = len(gpx.tracks)
        segment_count = sum(len(track.segments) for track in gpx.tracks)
        point_count = sum(
            len(segment.points)
            for track in gpx.tracks
            for segment in track.segments
        )

        print(f"   ✓ gpxpy成功解析文件")
        print(f"     - 轨迹数: {track_count}")
        print(f"     - 段数: {segment_count}")
        print(f"     - 点数: {point_count}")

        # 检查时间戳是否被正确解析
        has_time = False
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    if point.time is not None:
                        has_time = True
                        # 显示第一个点的时间信息
                        print(f"     - 第一个点的时间: {point.time}")
                        print(f"     - 时区感知: {point.time.tzinfo is not None}")
                        break
                if has_time:
                    break
            if has_time:
                break

        if has_time:
            print(f"   ✓ 时间戳被正确解析")
        else:
            print(f"   ✗ 未找到有效的时间戳")
            return False

    except ImportError:
        print("   ⚠ gpxpy未安装，跳过解析器验证")
    except Exception as e:
        print(f"   ✗ gpxpy解析失败: {e}")
        return False

    # 8. 显示完整的GPX文件内容（前50行）
    print("\n8. GPX文件内容预览 (前30行):")
    print("-" * 60)
    lines = content.split('\n')
    for i, line in enumerate(lines[:30], 1):
        print(f"{i:3d}: {line}")
    if len(lines) > 30:
        print(f"... (还有 {len(lines) - 30} 行)")
    print("-" * 60)

    return True


def main():
    """主验证函数"""
    print("GPX文件验证脚本")
    print("="*60)

    # 查找test_output_gpx目录中的所有GPX文件
    output_dir = "test_output_gpx"

    if not os.path.exists(output_dir):
        print(f"错误: 输出目录不存在: {output_dir}")
        print("请先运行 manual_timezone_test.py 生成测试文件")
        return 1

    gpx_files = [
        os.path.join(output_dir, f)
        for f in os.listdir(output_dir)
        if f.endswith('.gpx')
    ]

    if not gpx_files:
        print(f"错误: 在 {output_dir} 中未找到GPX文件")
        return 1

    print(f"找到 {len(gpx_files)} 个GPX文件\n")

    # 验证每个文件
    results = {}
    for file_path in gpx_files:
        file_name = os.path.basename(file_path)
        results[file_name] = verify_gpx_file(file_path)

    # 打印总结
    print(f"\n{'='*60}")
    print("验证总结")
    print(f"{'='*60}")

    for file_name, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{file_name}: {status}")

    all_passed = all(results.values())
    print(f"\n总体结果: {'所有文件验证通过' if all_passed else '部分文件验证失败'}")

    # 提供额外的验证建议
    print(f"\n{'='*60}")
    print("额外验证建议")
    print(f"{'='*60}")
    print("1. 使用文本编辑器打开GPX文件检查内容")
    print("2. 使用在线GPX查看器验证兼容性:")
    print("   - https://gpx.studio")
    print("   - https://www.gpsvisualizer.com")
    print("3. 使用GPS设备或应用导入文件测试")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

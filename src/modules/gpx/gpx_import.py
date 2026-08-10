# -*- coding: utf-8 -*-
"""
GPX 文件导入解析

使用 gpxpy 解析 GPX 文件，提取路线数据（起点/终点名称、路线点、
里程、耗时、海拔信息），供路线管理导入使用。

经纬度一律按国际标准 WGS-84 处理（需求：导入坐标默认国际标准）。
"""

import math
from typing import List, Optional


class GpxImportError(Exception):
    """GPX 解析异常"""


class GpxImportParser:
    """GPX 文件解析器（静态方法，无状态）"""

    @staticmethod
    def parse(file_path: str) -> dict:
        """解析单个 GPX 文件

        Args:
            file_path: GPX 文件路径

        Returns:
            dict: {
                'start': 起点名称,
                'end': 终点名称,
                'route_points': [(lat, lon, elevation?), ...]（多段以 None 分隔）,
                'distance': 总距离（米）,
                'duration': 总耗时（秒，无时间信息为 0）,
                'point_count': 有效路线点数,
                'has_elevation': 是否包含海拔,
            }

        Raises:
            GpxImportError: 文件无法解析或无有效路线点
        """
        import gpxpy

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                gpx = gpxpy.parse(f)
        except Exception as e:
            raise GpxImportError(f"GPX 文件解析失败: {e}")

        # 取第一个轨迹（无轨迹取路线 rte）
        track = gpx.tracks[0] if gpx.tracks else None
        route = gpx.routes[0] if gpx.routes else None

        segments = []
        if track is not None:
            for seg in track.segments:
                segments.append(seg.points)
        elif route is not None:
            segments.append(route.points)
        else:
            raise GpxImportError("GPX 文件中没有轨迹或路线数据")

        # 拼接路线点（多段之间插入 None 分隔，与项目路线点格式一致）
        route_points: List[Optional[tuple]] = []
        point_count = 0
        has_elevation = False
        for i, seg in enumerate(segments):
            if not seg:
                continue
            if i > 0 and route_points:
                route_points.append(None)  # 段分隔
            for pt in seg:
                lat, lon = pt.latitude, pt.longitude
                ele = pt.elevation
                if ele is not None:
                    has_elevation = True
                    route_points.append((lat, lon, float(ele)))
                else:
                    route_points.append((lat, lon))
                point_count += 1

        if point_count < 2:
            raise GpxImportError("路线有效点少于 2 个，无法导入")

        # 起终点名称：优先 track.name（导出的 GPX 为 "起点_终点"），
        # 其次 metadata.name / 文件名
        name_text = (track.name if track is not None else None) \
            or (route.name if route is not None else None) \
            or (gpx.metadata.name if gpx.metadata else None)
        start, end = GpxImportParser._split_name(name_text)

        # 里程：Haversine 逐段累计（跳过 None 分隔符）
        distance = 0.0
        prev = None
        for p in route_points:
            if p is None:
                prev = None
                continue
            if prev is not None:
                distance += GpxImportParser._haversine_m(prev[0], prev[1], p[0], p[1])
            prev = p

        # 耗时：首尾时间差（无时间信息为 0）
        duration = 0
        times = [p.time for p in segments[0]] if segments and segments[0] else []
        if len(times) >= 2 and times[0] is not None and times[-1] is not None:
            duration = max(0, int((times[-1] - times[0]).total_seconds()))

        return {
            'start': start,
            'end': end,
            'route_points': route_points,
            'distance': int(distance),
            'duration': duration,
            'point_count': point_count,
            'has_elevation': has_elevation,
        }

    @staticmethod
    def parse_files(file_paths: List[str]) -> List[dict]:
        """解析多个 GPX 文件（每个文件独立一条路线）

        Args:
            file_paths: GPX 文件路径列表

        Returns:
            解析结果列表；解析失败的文件跳过并输出警告
        """
        results = []
        for path in file_paths:
            try:
                results.append(GpxImportParser.parse(path))
            except GpxImportError as e:
                print(f"[GPX导入] 跳过文件 {path}: {e}")
        return results

    @staticmethod
    def _split_name(name_text: Optional[str]) -> tuple:
        """从名称文本拆分起点/终点（导出格式 "起点_终点"）"""
        if name_text and '_' in name_text:
            parts = [p.strip() for p in name_text.split('_') if p.strip()]
            if len(parts) >= 2:
                return parts[0], parts[-1]
            if len(parts) == 1:
                return parts[0], '终点'
        return '起点', '终点'

    @staticmethod
    def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """两点间球面距离（米，Haversine 公式）"""
        r = 6371000.0
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dp = math.radians(lat2 - lat1)
        dl = math.radians(lon2 - lon1)
        a = (math.sin(dp / 2) ** 2
             + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2)
        return 2 * r * math.asin(math.sqrt(a))

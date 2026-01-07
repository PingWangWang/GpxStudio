"""
GPX导出服务
将路线导出为GPX格式文件
"""

import gpxpy
from gpxpy.gpx import GPXTrack, GPXTrackSegment, GPXTrackPoint
from datetime import datetime, timedelta
from typing import Optional, Callable, Any


class GpxExportService:
    """GPX导出服务"""

    def __init__(self, logger: Optional[Callable] = None):
        self.logger = logger

    def log(self, level: str, message: str):
        """输出日志"""
        if self.logger:
            self.logger(level, message)

    def export_to_gpx(self, route_points, start_time, file_path):
        """
        导出路线为GPX文件

        Args:
            route_points: 路线点列表 [(lat, lon), ...], None表示段分隔
            start_time: 起始时间 (QTime对象)
            file_path: 保存路径

        Returns:
            bool: 是否成功
        """

        def log_cb(level: str, message: str):
            if self.logger:
                self.logger(level, message)

        try:
            log_cb("INFO", f"开始导出GPX文件: {file_path}")

            gpx = gpxpy.gpx.GPX()

            # 创建轨迹
            gpx_track = GPXTrack()
            gpx.tracks.append(gpx_track)

            # 创建轨迹段
            gpx_segment = GPXTrackSegment()
            gpx_track.segments.append(gpx_segment)

            # 设置起始时间
            current_time = datetime.now().replace(
                hour=start_time.hour(),
                minute=start_time.minute(),
                second=0,
                microsecond=0
            )

            log_cb("DEBUG", f"起始时间: {current_time}")

            # 添加轨迹点
            route_segment = []
            point_count = 0
            for point in route_points:
                if point is None:
                    # 处理完一个段
                    if len(route_segment) > 1:
                        for coord in route_segment:
                            gpx_point = GPXTrackPoint(
                                latitude=coord[0],
                                longitude=coord[1],
                                time=current_time
                            )
                            gpx_segment.points.append(gpx_point)
                            current_time += timedelta(seconds=10)
                            point_count += 1
                    route_segment = []
                    current_time += timedelta(minutes=5)  # 段间隔5分钟
                    log_cb("DEBUG", f"添加段分隔符，当前点数: {point_count}")
                else:
                    route_segment.append(point)

            # 处理最后一个段
            if len(route_segment) > 1:
                for coord in route_segment:
                    gpx_point = GPXTrackPoint(
                        latitude=coord[0],
                        longitude=coord[1],
                        time=current_time
                    )
                    gpx_segment.points.append(gpx_point)
                    current_time += timedelta(seconds=10)
                    point_count += 1

            log_cb("DEBUG", f"共添加 {point_count} 个轨迹点")

            # 保存文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(gpx.to_xml())

            log_cb("INFO", "GPX文件导出成功")
            return True

        except Exception as e:
            log_cb("ERROR", f"导出GPX文件失败: {str(e)}")
            return False

    @staticmethod
    def get_gpx_info(route_points):
        """
        获取GPX信息（点数、估计时长等）

        Args:
            route_points: 路线点列表

        Returns:
            dict: GPX信息
        """
        valid_points = [p for p in route_points if p is not None]
        segments = 1

        for point in route_points:
            if point is None:
                segments += 1

        # 估算时长（每10秒一个点 + 段间隔）
        estimated_duration = len(valid_points) * 10 + (segments - 1) * 300

        return {
            'total_points': len(valid_points),
            'segments': segments,
            'estimated_duration_seconds': estimated_duration
        }

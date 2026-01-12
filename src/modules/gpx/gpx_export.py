"""
GPX导出服务
将路线导出为GPX格式文件
"""

import gpxpy
from gpxpy.gpx import GPXTrack, GPXTrackSegment, GPXTrackPoint
from datetime import datetime, timedelta, timezone
from typing import Optional, Callable, Any, List, Dict

from modules.gpx.interfaces.gpx_export_service import IGpxExportService


class GpxExportService(IGpxExportService):
    """GPX导出服务"""

    def __init__(self, logger: Optional[Callable] = None):
        self.logger = logger

    def log(self, level: str, message: str):
        """输出日志"""
        if self.logger:
            self.logger(level, message)

    def export_to_gpx(self, route_points, start_datetime, file_path, start_name=None, end_name=None):
        """
        导出路线为GPX文件

        Args:
            route_points: 路线点列表 [(lat, lon), ...], None表示段分隔
            start_datetime: 起始时间 (QDateTime对象)
            file_path: 保存路径
            start_name: 起点名称
            end_name: 终点名称

        Returns:
            bool: 是否成功
        """

        def log_cb(level: str, message: str):
            if self.logger:
                self.logger(level, message)

        try:
            log_cb("INFO", f"开始导出GPX文件: {file_path}")

            gpx = gpxpy.gpx.GPX()

            # 生成轨迹名称
            import os
            if start_name and end_name:
                # 使用起点和终点名称生成轨迹名称，使用下划线作为连接符
                track_name = f"{start_name}_{end_name}"
            else:
                # 从文件路径提取轨迹名称
                track_name = os.path.splitext(os.path.basename(file_path))[0]

            # 清理轨迹名称，移除不必要的字符
            import re
            track_name = re.sub(r'[\\/:*?"<>|]', '', track_name)

            # 添加元数据
            gpx.name = track_name
            # gpxpy库使用不同的方式处理元数据，我们需要直接修改XML输出

            # 创建轨迹
            gpx_track = GPXTrack()
            gpx_track.name = track_name
            gpx.tracks.append(gpx_track)

            # 创建轨迹段
            gpx_segment = GPXTrackSegment()
            gpx_track.segments.append(gpx_segment)

            # 设置起始时间
            current_time = datetime(
                start_datetime.date().year(),
                start_datetime.date().month(),
                start_datetime.date().day(),
                start_datetime.time().hour(),
                start_datetime.time().minute(),
                0,
                0,
                tzinfo=timezone.utc
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
                            # 检查点是否包含海拔数据
                            if len(coord) >= 3:
                                gpx_point = GPXTrackPoint(
                                    latitude=coord[0],
                                    longitude=coord[1],
                                    elevation=coord[2],
                                    time=current_time
                                )
                            else:
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
                    # 检查点是否包含海拔数据
                    if len(coord) >= 3:
                        gpx_point = GPXTrackPoint(
                            latitude=coord[0],
                            longitude=coord[1],
                            elevation=coord[2],
                            time=current_time
                        )
                    else:
                        gpx_point = GPXTrackPoint(
                            latitude=coord[0],
                            longitude=coord[1],
                            time=current_time
                        )
                    gpx_segment.points.append(gpx_point)
                    current_time += timedelta(seconds=10)
                    point_count += 1

            log_cb("DEBUG", f"共添加 {point_count} 个轨迹点")

            # 生成XML并修改以添加所需的元数据结构
            xml_output = gpx.to_xml()
            
            # 替换XML头部，添加完整的元数据
            import re
            # 找到第一个<gpx>标签的结束位置
            gpx_start = xml_output.find('<gpx')
            gpx_end = xml_output.find('>', gpx_start)
            
            if gpx_end > 0:
                # 构建新的XML头部，包含完整的元数据
                new_header = xml_output[:gpx_end+1]
                metadata_section = f'''
  <metadata>
    <name>{track_name}</name>
    <author>
      <name>gpx.studio</name>
      <link href="https://gpx.studio"/>
    </author>
  </metadata>'''
                
                # 找到第一个<track>或<trk>标签的开始位置
                track_start = xml_output.find('<trk', gpx_end)
                if track_start > 0:
                    # 插入元数据
                    xml_output = new_header + metadata_section + '\n' + xml_output[track_start:]
            
            # 保存文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(xml_output)

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

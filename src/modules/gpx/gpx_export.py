"""
GPX导出服务
负责将路线数据导出为GPX文件格式
"""

from datetime import datetime, timedelta, timezone
from typing import List, Tuple, Optional, Callable
import gpxpy
import gpxpy.gpx
from gpxpy.gpx import GPXTrack, GPXTrackSegment, GPXTrackPoint
import requests


class GpxExportService:
    """
    GPX导出服务类
    负责将路线数据导出为GPX文件格式
    """

    def __init__(self, logger: Optional[Callable[[str, str], None]] = None):
        """
        初始化GPX导出服务

        Args:
            logger: 日志记录回调函数，格式为 logger(level, message)
        """
        self.logger = logger

    def _detect_timezone(self, latitude: float, longitude: float) -> timezone:
        """
        根据经纬度检测时区

        Args:
            latitude: 纬度
            longitude: 经度

        Returns:
            timezone: 检测到的时区对象
        """
        try:
            # 使用TimezoneFinder库检测时区
            from timezonefinder import TimezoneFinder
            tf = TimezoneFinder()
            tz_name = tf.timezone_at(lat=latitude, lng=longitude)

            if tz_name:
                import pytz
                return pytz.timezone(tz_name)
            else:
                # 时区检测失败，使用东八区（中国地区默认）
                return timezone(timedelta(hours=8))
        except Exception as e:
            # 任何异常都返回东八区（中国地区默认）
            if self.logger:
                self.logger("WARNING", f"时区检测失败: {str(e)}，使用东八区")
            return timezone(timedelta(hours=8))

    def export_to_gpx(self, route_points, start_datetime, file_path, start_name=None, end_name=None, export_elevation=False, total_duration_seconds=None, total_distance_meters=None, transport_mode=None, waypoint_names=None, description=None, cancel_check=None):
        """
        导出路线为GPX文件

        Args:
            route_points: 路线点列表 [(lat, lon), ...], None表示段分隔
            start_datetime: 起始时间 (QDateTime对象)
            file_path: 保存路径
            start_name: 起点名称
            end_name: 终点名称
            export_elevation: 是否导出海拔数据
            total_duration_seconds: 路线预估总时长（秒），用于计算每个点的时间。如果为None，则使用默认的10秒间隔
            total_distance_meters: 路线总距离（米），用于添加到GPX文件的extensions中
            transport_mode: 交通方式 (driving/cycling/walking)
            waypoint_names: 途径点名称列表
            description: 路线描述
            cancel_check: 取消检查回调，返回 True 时取消导出

        Returns:
            bool: 是否成功
        """

        def log_cb(level: str, message: str):
            if self.logger:
                self.logger(level, message)

        try:
            log_cb("INFO", f"开始导出GPX文件: {file_path}")

            # 检测时区：提取第一个非None路线点作为起点
            detected_tz = None
            first_point = None

            # 查找第一个有效的路线点
            for point in route_points:
                if point is not None and len(point) >= 2:
                    first_point = point
                    break

            # 如果找到有效起点，检测时区
            if first_point:
                latitude, longitude = first_point[0], first_point[1]
                detected_tz = self._detect_timezone(latitude, longitude)
                log_cb("INFO", f"使用起点坐标 ({latitude}, {longitude}) 检测时区")
            else:
                # 空路线点列表或全为None，使用UTC
                log_cb("WARNING", "未找到有效的路线点，使用UTC时区")
                try:
                    import pytz
                    detected_tz = pytz.UTC
                except ImportError:
                    detected_tz = timezone.utc

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

            # 如果提供了总距离，添加到轨迹的extensions中
            if total_distance_meters is not None:
                # gpxpy的Track对象支持extensions
                if not hasattr(gpx_track, 'extensions'):
                    gpx_track.extensions = {}
                log_cb("INFO", f"添加路线总距离: {total_distance_meters}米")

            # 创建轨迹段
            gpx_segment = GPXTrackSegment()
            gpx_track.segments.append(gpx_segment)

            # 设置起始时间 - 使用检测到的时区
            # 首先创建naive datetime
            naive_dt = datetime(
                start_datetime.date().year(),
                start_datetime.date().month(),
                start_datetime.date().day(),
                start_datetime.time().hour(),
                start_datetime.time().minute(),
                0,
                0
            )

            # 使用pytz的localize()方法创建时区感知的datetime
            try:
                import pytz
                if isinstance(detected_tz, pytz.tzinfo.BaseTzInfo):
                    # 使用pytz时区对象的localize方法
                    current_time = detected_tz.localize(naive_dt)
                else:
                    # 使用标准库的timezone对象
                    current_time = naive_dt.replace(tzinfo=detected_tz)
            except Exception as e:
                log_cb("WARNING", f"时区转换失败: {e}，使用UTC")
                current_time = naive_dt.replace(tzinfo=timezone.utc)

            log_cb("DEBUG", f"起始时间: {current_time}")

            # 统计所有有效点的数量（不包括段分隔符None）
            total_points = sum(1 for point in route_points if point is not None)
            log_cb("DEBUG", f"路线点总数: {total_points}")

            # 计算每个点的时间间隔
            # 如果提供了总时长，根据总时长计算每个点的时间间隔
            # 否则使用默认的10秒间隔
            if total_duration_seconds is not None and total_duration_seconds > 0 and total_points > 1:
                time_interval_seconds = total_duration_seconds / (total_points - 1)
                log_cb("INFO", f"使用预估总时长: {total_duration_seconds}秒，每个点间隔: {time_interval_seconds:.2f}秒")
            else:
                time_interval_seconds = 10
                log_cb("INFO", f"未提供预估总时长或点数不足，使用默认间隔: {time_interval_seconds}秒")

            # 添加轨迹点
            route_segment = []
            point_count = 0
            for point_idx, point in enumerate(route_points):
                # 每 500 个点检查一次取消标志
                if point_idx % 500 == 0 and cancel_check and cancel_check():
                    log_cb("INFO", f"用户取消了GPX导出（写入阶段，已处理 {point_count} 个点）")
                    return False
                if point is None:
                    # 处理完一个段
                    if len(route_segment) >= 1:
                        for coord in route_segment:
                            # 根据export_elevation参数决定是否包含海拔数据
                            if export_elevation and len(coord) >= 3:
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
                            current_time += timedelta(seconds=time_interval_seconds)
                            point_count += 1
                    route_segment = []
                    current_time += timedelta(minutes=5)  # 段间隔5分钟
                    log_cb("DEBUG", f"添加段分隔符，当前点数: {point_count}")
                else:
                    route_segment.append(point)

            # 处理最后一个段
            if len(route_segment) >= 1:
                for coord in route_segment:
                    # 根据export_elevation参数决定是否包含海拔数据
                    if export_elevation and len(coord) >= 3:
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
                    current_time += timedelta(seconds=time_interval_seconds)
                    point_count += 1

            log_cb("DEBUG", f"共添加 {point_count} 个轨迹点")

            # 生成XML并修改以添加所需的元数据结构
            xml_output = gpx.to_xml()

            # 确保UTC时区使用+00:00格式而不是Z，以保持一致性
            # gpxpy默认可能使用Z表示UTC，我们需要统一为+00:00格式
            import re
            # 替换所有的Z结尾时间戳为+00:00格式
            xml_output = re.sub(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})Z', r'\1+00:00', xml_output)

            # 添加totalDistance到轨迹的extensions中
            if total_distance_meters is not None:
                # 查找<trk>标签后面的位置，插入extensions
                trk_name_match = re.search(r'(<trk>\s*<name>.*?</name>)', xml_output, re.DOTALL)
                if trk_name_match:
                    insert_pos = trk_name_match.end()
                    extensions_xml = f'\n    <extensions>\n      <totalDistance>{int(total_distance_meters)}</totalDistance>\n    </extensions>'
                    xml_output = xml_output[:insert_pos] + extensions_xml + xml_output[insert_pos:]
                    log_cb("DEBUG", f"已在XML中添加totalDistance: {int(total_distance_meters)}米")

            # 替换XML头部，添加完整的元数据
            import re
            # 找到第一个<gpx>标签的结束位置
            gpx_start = xml_output.find('<gpx')
            gpx_end = xml_output.find('>', gpx_start)

            if gpx_end > 0:
                # 构建新的XML头部，包含完整的元数据
                new_header = xml_output[:gpx_end+1]
                
                # 构建交通方式显示名称
                transport_mode_display = {
                    'driving': '驾车',
                    'cycling': '骑行',
                    'walking': '步行'
                }.get(transport_mode, transport_mode or '未知')
                
                # 构建基本描述 - 使用版本号
                try:
                    from version import __version__
                    desc_text = f"Export from GPX Studio {__version__}"
                except:
                    desc_text = "Export from GPX Studio"
                
                # 构建关键词（交通方式）
                keywords = transport_mode_display
                
                # 构建扩展信息
                extensions_parts = []
                
                # 添加起点信息（包含国际坐标）
                if start_name and first_point:
                    extensions_parts.append(f'    <startPoint>')
                    extensions_parts.append(f'      <name>{start_name}</name>')
                    extensions_parts.append(f'      <lat>{first_point[0]:.6f}</lat>')
                    extensions_parts.append(f'      <lon>{first_point[1]:.6f}</lon>')
                    extensions_parts.append(f'    </startPoint>')
                
                # 添加途径点信息
                if waypoint_names and len(waypoint_names) > 0:
                    extensions_parts.append(f'    <waypoints>')
                    for i, wp_name in enumerate(waypoint_names, 1):
                        extensions_parts.append(f'      <waypoint>')
                        extensions_parts.append(f'        <name>{wp_name}</name>')
                        extensions_parts.append(f'        <index>{i}</index>')
                        extensions_parts.append(f'      </waypoint>')
                    extensions_parts.append(f'    </waypoints>')
                
                # 添加终点信息（找到最后一个有效点）
                last_point = None
                for point in reversed(route_points):
                    if point is not None and len(point) >= 2:
                        last_point = point
                        break
                if end_name and last_point:
                    extensions_parts.append(f'    <endPoint>')
                    extensions_parts.append(f'      <name>{end_name}</name>')
                    extensions_parts.append(f'      <lat>{last_point[0]:.6f}</lat>')
                    extensions_parts.append(f'      <lon>{last_point[1]:.6f}</lon>')
                    extensions_parts.append(f'    </endPoint>')
                
                # 添加总时间信息（分钟）
                if total_duration_seconds is not None:
                    total_minutes = total_duration_seconds / 60
                    extensions_parts.append(f'    <totalTime unit="minutes">{total_minutes:.1f}</totalTime>')
                
                # 添加交通方式信息
                if transport_mode:
                    extensions_parts.append(f'    <transportMode>{transport_mode}</transportMode>')
                
                extensions_xml = ''
                if extensions_parts:
                    extensions_xml = '\n    <extensions>\n' + '\n'.join(extensions_parts) + '\n    </extensions>'
                
                metadata_section = f'''
  <metadata>
    <name>{track_name}</name>
    <desc>{desc_text}</desc>
    <keywords>{keywords}</keywords>
    <author>
      <name>gpx.studio</name>
      <link href="https://gpx.studio"/>
    </author>{extensions_xml}
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

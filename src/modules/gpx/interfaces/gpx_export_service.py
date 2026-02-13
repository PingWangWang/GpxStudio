"""
GPX导出服务接口
定义GPX导出相关服务的契约
"""

from typing import Optional, List, Dict, Callable, Any


class IGpxExportService:
    """
    GPX导出服务接口
    定义了GPX文件导出的方法
    """

    def __init__(self, logger: Optional[Callable] = None):
        """
        初始化GPX导出服务

        Args:
            logger: 日志记录器函数，接收(level, message)参数
        """
        ...

    def export_to_gpx(self, route_points: List[Any], start_datetime: Any, file_path: str, start_name: Optional[str] = None, end_name: Optional[str] = None, export_elevation: bool = False, total_duration_seconds: Optional[float] = None, total_distance_meters: Optional[float] = None) -> bool:
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

        Returns:
            bool: 是否成功
        """
        ...

    def get_gpx_info(self, route_points: List[Any]) -> Dict[str, Any]:
        """
        获取GPX信息（点数、估计时长等）

        Args:
            route_points: 路线点列表

        Returns:
            dict: GPX信息
        """
        ...

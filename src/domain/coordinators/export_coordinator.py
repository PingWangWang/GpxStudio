"""
GPX 导出业务协调器

封装 GPX 导出的纯业务逻辑（不含 QFileDialog）：
- 文件名生成
- 城市名提取
- 调用 IGpxService.export_to_gpx()

不依赖任何 PyQt5 组件，可在无 Qt 环境下进行单元测试。
文件路径选择（QFileDialog）保留在 RouteManager 中（UI 层职责）。
"""

from typing import Callable, List, Optional, Tuple
import logging
import os
import json


logger = logging.getLogger(__name__)


class ExportCoordinator:
    """GPX 导出业务协调器

    职责
    ----
    * 生成默认 GPX 文件名
    * 从地点全称中提取城市名
    * 持久化"上次导出目录"
    * 调用 gpx_service.export_to_gpx() 并通过回调通知结果

    不依赖 Qt，可直接 mock ``gpx_service`` 进行单元测试。

    示例
    ----
    >>> coordinator = ExportCoordinator(
    ...     gpx_service=mock_svc,
    ...     config_dir='/path/to/config',
    ...     on_success=lambda path: ...,
    ...     on_error=lambda msg: ...,
    ... )
    >>> coordinator.export(route_points, start_dt, '/tmp/route.gpx',
    ...                    start_name='北京', end_name='上海',
    ...                    total_duration_seconds=3600,
    ...                    total_distance_meters=1200000)
    """

    def __init__(
        self,
        gpx_service,
        config_dir: str,
        on_success: Callable[[str], None],
        on_error: Callable[[str], None],
    ):
        """
        参数:
            gpx_service: 提供 ``export_to_gpx(...)`` 方法的服务实例
            config_dir: 持久化配置目录（用于读写 ``export_config.json``）
            on_success: 导出成功回调，接收文件完整路径
            on_error: 导出失败回调，接收错误描述字符串
        """
        self._gpx_service = gpx_service
        self._config_dir = config_dir
        self._on_success = on_success
        self._on_error = on_error

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def export(
        self,
        route_points: list,
        start_datetime,
        file_path: str,
        start_name: str = '起点',
        end_name: str = '终点',
        total_duration_seconds: Optional[float] = None,
        total_distance_meters: Optional[float] = None,
        export_elevation: bool = False,
    ) -> None:
        """执行 GPX 导出。

        参数:
            route_points: 路线坐标点列表
            start_datetime: 起始时间（QDateTime 或 datetime，传给 gpx_service）
            file_path: 完整目标文件路径
            start_name: 起点名称（可包含城市全称，内部会提取城市名）
            end_name: 终点名称
            total_duration_seconds: 预估总时长（秒），用于计算各点时间戳
            total_distance_meters: 路线总距离（米）
            export_elevation: 是否导出高程信息
        """
        logger.info(f"[ExportCoordinator] 开始导出GPX: {file_path}")

        try:
            start_city = self._extract_city_name(start_name or '起点')
            end_city = self._extract_city_name(end_name or '终点')

            success = self._gpx_service.export_to_gpx(
                route_points,
                start_datetime,
                file_path,
                start_name=start_city,
                end_name=end_city,
                export_elevation=export_elevation,
                total_duration_seconds=total_duration_seconds,
                total_distance_meters=total_distance_meters,
            )

            # 持久化导出目录
            export_dir = os.path.dirname(file_path)
            if os.path.isdir(export_dir):
                self._save_last_export_path(export_dir)

            if success:
                logger.info("[ExportCoordinator] GPX导出成功")
                self._on_success(file_path)
            else:
                logger.warning("[ExportCoordinator] GPX导出失败（service返回False）")
                self._on_error("导出GPX文件失败")

        except Exception as e:
            logger.error(f"[ExportCoordinator] 导出GPX文件出错: {e}")
            self._on_error(str(e))

    def generate_filename(
        self,
        start_name: str,
        end_name: str,
        start_datetime,
        time_format: str = 'yyyyMMdd_hhmm',
    ) -> str:
        """生成默认 GPX 文件名。

        参数:
            start_name: 起点名称
            end_name: 终点名称
            start_datetime: QDateTime 实例（使用 toString(time_format)）
            time_format: Qt 时间格式字符串

        返回:
            形如 ``起点_终点_20240101_0800.gpx`` 的文件名
        """
        start_city = self._extract_city_name(start_name or '起点')
        end_city = self._extract_city_name(end_name or '终点')
        time_str = start_datetime.toString(time_format)
        return f"{start_city}_{end_city}_{time_str}.gpx"

    def get_last_export_path(self) -> Optional[str]:
        """读取上次导出目录。"""
        try:
            config_path = os.path.join(self._config_dir, 'export_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f).get('last_export_path')
        except Exception as e:
            logger.error(f"[ExportCoordinator] 读取上次导出路径失败: {e}")
        return None

    # ──────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _extract_city_name(self, full_name: str) -> str:
        """从完整地点名称中提取城市名。

        规则：截取第一个分号 / 逗号之前的部分。
        """
        city_name = full_name.split(';')[0].split(',')[0].strip()
        return city_name

    def _save_last_export_path(self, export_path: str) -> None:
        """持久化上次导出目录。"""
        try:
            config_path = os.path.join(self._config_dir, 'export_config.json')
            config: dict = {}
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            config['last_export_path'] = export_path
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.debug(f"[ExportCoordinator] 已保存上次导出路径: {export_path}")
        except Exception as e:
            logger.error(f"[ExportCoordinator] 保存上次导出路径失败: {e}")

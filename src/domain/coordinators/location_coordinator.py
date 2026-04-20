"""
定位业务协调器

封装定位优先级链的纯业务逻辑：
  1. Windows 原生位置服务（精度最高）
  2. 浏览器/高德在线定位（返回特殊标记由调用方处理）
  3. 公共 IP 定位（最终备选）

不依赖任何 PyQt5 组件，可在无 Qt 环境下进行单元测试。
"""

from typing import Callable, Optional
import logging


logger = logging.getLogger(__name__)


class LocationCoordinator:
    """定位业务协调器

    职责
    ----
    * 按优先级尝试各种定位方式
    * 通过回调通知结果，与 UI 框架完全解耦

    返回结构（传给 on_success）
    --------------------------
    ``{'type': 'native'|'browser'|'ip', 'data': ..., 'source': str}``

    * ``native``  — Windows 原生定位，``data`` 为 ``{latitude, longitude, accuracy}``
    * ``browser`` — 浏览器定位触发标记，``data`` 为 ``None``（由调用方触发 JS）
    * ``ip``      — 公共 IP 定位，``data`` 为坐标字典

    示例
    ----
    >>> coordinator = LocationCoordinator(
    ...     windows_location_service=mock_win_svc,
    ...     location_helper=MockLocationHelper,
    ...     gaode_configured_check=lambda: True,
    ...     on_success=lambda result: ...,
    ...     on_error=lambda msg: ...,
    ... )
    >>> coordinator.get_location(map_source='gaode')
    """

    def __init__(
        self,
        windows_location_service,
        location_helper,
        on_success: Callable[[dict], None],
        on_error: Callable[[str], None],
        gaode_configured_check: Optional[Callable[[], bool]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None,
        log_callback: Optional[Callable[[str, str], None]] = None,
    ):
        """
        参数:
            windows_location_service: 提供 ``is_available()`` / ``get_location(timeout)``
            location_helper: 提供静态方法 ``get_ip_location(logger)``
            on_success: 定位成功回调，接收定位结果字典
            on_error: 定位失败回调，接收错误描述
            gaode_configured_check: 可选；高德 API 已配置检查函数
            cancel_check: 可选；返回 True 时中断定位流程
            progress_callback: 可选；接收 (percent, message)
            log_callback: 可选；接收 (level, message)
        """
        self._win_svc = windows_location_service
        self._location_helper = location_helper
        self._on_success = on_success
        self._on_error = on_error
        self._gaode_check = gaode_configured_check
        self._cancel_check = cancel_check or (lambda: False)
        self._progress = progress_callback or (lambda p, m: None)
        self._log = log_callback or (lambda lvl, msg: logger.log(
            logging.getLevelName(lvl) if isinstance(lvl, str) else lvl, msg
        ))

    def get_location(self, map_source: str = '') -> None:
        """按优先级链尝试定位。

        参数:
            map_source: 当前地图源标识（'gaode' / 'osm'）
        """
        try:
            self._log("INFO", "开始定位流程")
            self._progress(0, "正在初始化定位服务...")

            if self._cancel_check():
                self._log("WARNING", "定位任务已取消")
                return

            # ── 1. Windows 原生定位（精度最高）──────────────────────────────
            win_available = self._win_svc.is_available()
            self._log("DEBUG", f"Windows位置服务可用: {win_available}")

            if not win_available:
                self._log("INFO", "提示: Windows位置服务未开启或无权限")
                self._log("INFO", "建议: 设置 → 隐私 → 位置 → 开启'允许应用访问你的位置'")

            if win_available:
                self._progress(10, "正在使用Windows原生定位...")
                self._log("INFO", "尝试使用Windows原生位置服务...")

                if self._cancel_check():
                    self._log("WARNING", "定位任务已取消")
                    return

                location_info = self._win_svc.get_location(timeout=10)
                if location_info:
                    self._progress(100, "Windows原生定位成功")
                    self._log("INFO", "Windows原生定位成功")
                    self._on_success({'type': 'native', 'data': location_info})
                    return
                else:
                    self._log("WARNING", "Windows原生定位未获取到位置信息")

            # ── 2. 浏览器 / 高德在线定位 ─────────────────────────────────────
            self._log("INFO", "Windows定位不可用，尝试其他方式")
            self._progress(30, "Windows定位不可用，尝试其他方式...")

            if self._cancel_check():
                self._log("WARNING", "定位任务已取消")
                return

            if map_source == "gaode" and self._gaode_check and self._gaode_check():
                self._progress(50, "正在使用高德地图在线定位...")
                self._log("INFO", "尝试使用高德地图在线定位（浏览器定位）...")
                # 浏览器定位需在主线程触发，返回特殊标记
                self._on_success({'type': 'browser', 'data': None})
                return

            # ── 3. 公共 IP 定位（最终备选）───────────────────────────────────
            self._progress(60, "正在使用公共IP定位...")
            self._log("INFO", "尝试使用公共IP定位...")

            if self._cancel_check():
                self._log("WARNING", "定位任务已取消")
                return

            def _ip_log(level: str, message: str):
                self._log(level, f"[公共IP定位] {message}")

            location_info = self._location_helper.get_ip_location(logger=_ip_log)

            if location_info:
                self._progress(100, "公共IP定位成功")
                self._log("INFO", "公共IP定位成功")
                self._on_success({
                    'type': 'ip',
                    'data': location_info,
                    'source': '公共IP定位',
                })
                return

            # 所有方式均失败
            self._progress(100, "定位失败")
            self._log("ERROR", "所有定位方式均失败")
            self._on_error("所有定位方式均失败，请检查网络连接或位置权限设置")

        except Exception as e:
            logger.error(f"[LocationCoordinator] 定位流程异常: {e}")
            self._on_error(str(e))

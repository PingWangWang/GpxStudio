"""
地图视图模型

持有地图层的 UI 状态（加载动画、缩放级别、视口中心等），
通过 Qt 信号驱动视图更新。

当前阶段迁移的状态：
- 加载动画（loading_changed）→ 替代 show_loading / hide_loading 直接调用
"""

from PyQt5.QtCore import QObject, pyqtSignal
from typing import Optional, Tuple


class MapViewModel(QObject):
    """地图视图模型

    信号说明
    --------
    loading_changed(bool)
        地图加载状态变化（True = 开始加载，False = 加载完成/停止）。
        连接方：``GpxStudio._on_map_loading_changed``
    zoom_changed(int)
        地图缩放级别变化
    center_changed(float, float)
        地图中心点变化（lat, lon）
    """

    loading_changed = pyqtSignal(bool)
    zoom_changed    = pyqtSignal(int)
    center_changed  = pyqtSignal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_loading: bool = False
        self._zoom: int = 12
        self._center: Tuple[float, float] = (0.0, 0.0)

    # ── 只读属性 ──────────────────────────────────────────────────────────

    @property
    def is_loading(self) -> bool:
        return self._is_loading

    @property
    def zoom(self) -> int:
        return self._zoom

    @property
    def center(self) -> Tuple[float, float]:
        return self._center

    # ── 写入方法 ──────────────────────────────────────────────────────────

    def set_loading(self, loading: bool) -> None:
        """设置加载状态并发射 loading_changed 信号。

        参数:
            loading: True 表示正在加载，False 表示加载结束
        """
        if self._is_loading != loading:
            self._is_loading = loading
            self.loading_changed.emit(loading)

    def set_zoom(self, zoom: int) -> None:
        """更新缩放级别并发射 zoom_changed 信号。"""
        if self._zoom != zoom:
            self._zoom = zoom
            self.zoom_changed.emit(zoom)

    def set_center(self, lat: float, lon: float) -> None:
        """更新地图中心点并发射 center_changed 信号。"""
        self._center = (lat, lon)
        self.center_changed.emit(lat, lon)

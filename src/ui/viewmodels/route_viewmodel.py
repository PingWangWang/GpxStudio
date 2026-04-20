"""
路线视图模型

持有路线规划相关的 UI 状态，通过 Qt 信号驱动路线面板更新。
"""

from typing import List, Optional
from PyQt5.QtCore import QObject, pyqtSignal


class RouteViewModel(QObject):
    """路线视图模型

    信号说明
    --------
    route_ready(list, int)
        路线规划成功，携带备选路线列表和默认选中索引
    loading_changed(bool)
        路线规划加载状态变化
    error_occurred(str)
        路线规划失败，携带错误描述
    alternatives_updated(list)
        备选路线列表更新（切换备选路线时）
    selected_index_changed(int)
        当前选中备选路线索引变化
    """

    route_ready             = pyqtSignal(list, int)   # (alternatives, default_index)
    loading_changed         = pyqtSignal(bool)
    error_occurred          = pyqtSignal(str)
    alternatives_updated    = pyqtSignal(list)
    selected_index_changed  = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._alternatives: List[dict] = []
        self._selected_index: int = 0
        self._is_loading: bool = False

    # ── 只读属性 ──────────────────────────────────────────────────────────

    @property
    def alternatives(self) -> List[dict]:
        return self._alternatives

    @property
    def selected_index(self) -> int:
        return self._selected_index

    @property
    def is_loading(self) -> bool:
        return self._is_loading

    # ── 写入方法 ──────────────────────────────────────────────────────────

    def set_route(self, alternatives: List[dict], default_index: int = 0) -> None:
        """设置路线规划结果并发射 route_ready 信号。

        参数:
            alternatives: 备选路线列表
            default_index: 默认选中的备选路线索引
        """
        self._alternatives = alternatives
        self._selected_index = default_index
        self.route_ready.emit(alternatives, default_index)

    def set_loading(self, loading: bool) -> None:
        """设置加载状态并发射 loading_changed 信号。"""
        if self._is_loading != loading:
            self._is_loading = loading
            self.loading_changed.emit(loading)

    def set_error(self, message: str) -> None:
        """发射路线规划错误信号。"""
        self.error_occurred.emit(message)

    def select_alternative(self, index: int) -> None:
        """切换选中的备选路线。"""
        if self._selected_index != index:
            self._selected_index = index
            self.selected_index_changed.emit(index)

    def clear(self) -> None:
        """清空路线状态。"""
        self._alternatives = []
        self._selected_index = 0
        self.alternatives_updated.emit([])

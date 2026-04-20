"""
搜索视图模型

持有搜索相关的 UI 状态，通过 Qt 信号通知视图层更新。
视图层（SearchPanel / SearchResultsPopup）只需连接信号，
无需主动轮询或持有业务对象引用。
"""

from typing import List
from PyQt5.QtCore import QObject, pyqtSignal


class SearchViewModel(QObject):
    """搜索视图模型

    信号说明
    --------
    results_changed(list)
        搜索结果列表更新。每个元素为格式化后的搜索结果字典：
        {'name', 'address', 'lat', 'lon', 'type', 'level', 'radius',
         'coord_system', 'data_source'}
    loading_changed(bool)
        搜索加载状态变化（True = 正在搜索，False = 搜索完成/空闲）
    error_occurred(str)
        搜索出错时发出，携带错误描述字符串
    query_changed(str)
        当前搜索关键词变化
    """

    results_changed = pyqtSignal(list)   # List[dict]
    loading_changed = pyqtSignal(bool)
    error_occurred  = pyqtSignal(str)
    query_changed   = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._results: List[dict] = []
        self._is_loading: bool = False
        self._query: str = ''

    # ── 只读属性 ──────────────────────────────────────────────────────────

    @property
    def results(self) -> List[dict]:
        return self._results

    @property
    def is_loading(self) -> bool:
        return self._is_loading

    @property
    def query(self) -> str:
        return self._query

    # ── 写入方法（供 SearchManager 调用） ────────────────────────────────

    def set_results(self, results: List[dict]) -> None:
        """设置搜索结果并发射 results_changed 信号。

        参数:
            results: 格式化后的搜索结果列表
        """
        self._results = results
        self.results_changed.emit(results)

    def set_loading(self, loading: bool) -> None:
        """设置加载状态并发射 loading_changed 信号。

        参数:
            loading: True 表示正在加载，False 表示加载结束
        """
        if self._is_loading != loading:
            self._is_loading = loading
            self.loading_changed.emit(loading)

    def set_error(self, message: str) -> None:
        """发射错误信号。

        参数:
            message: 错误描述
        """
        self.error_occurred.emit(message)

    def set_query(self, query: str) -> None:
        """更新搜索关键词并发射 query_changed 信号。

        参数:
            query: 当前搜索关键词
        """
        if self._query != query:
            self._query = query
            self.query_changed.emit(query)

    def clear(self) -> None:
        """清空搜索结果并停止加载状态。"""
        self._results = []
        self.results_changed.emit([])
        if self._is_loading:
            self._is_loading = False
            self.loading_changed.emit(False)

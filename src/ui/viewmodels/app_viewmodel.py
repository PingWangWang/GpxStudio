"""
应用视图模型（AppViewModel）

汇聚全局 UI 状态，作为所有子 ViewModel 的容器。
主窗口通过持有 AppViewModel 实例来访问各子 ViewModel，
各管理器（SearchManager 等）只需接收对应的子 ViewModel。
"""

from PyQt5.QtCore import QObject

from .search_viewmodel import SearchViewModel
from .map_viewmodel import MapViewModel
from .route_viewmodel import RouteViewModel


class AppViewModel(QObject):
    """应用全局视图模型

    包含子视图模型
    --------------
    search_vm : SearchViewModel
        搜索功能的 UI 状态（结果列表、加载状态、搜索词）
    map_vm : MapViewModel
        地图的 UI 状态（加载动画、缩放级别、中心点）
    route_vm : RouteViewModel
        路线规划的 UI 状态（备选路线、加载状态、错误信息）
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_vm = SearchViewModel(self)
        self.map_vm    = MapViewModel(self)
        self.route_vm  = RouteViewModel(self)

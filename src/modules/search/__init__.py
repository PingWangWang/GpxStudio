"""
搜索模块

完整的搜索功能模块，包含：
- UI组件：搜索历史下拉列表、搜索结果下拉列表
- 存储：地理信息持久化存储
- 管理器：搜索业务逻辑管理

使用示例：
    from modules.search import SearchManager, SearchHistoryPopup, SearchResultsPopup, GeoInfoStorage
"""

from .ui import SearchHistoryPopup, SearchResultsPopup
from .storage import GeoInfoStorage
from .managers import SearchManager

__all__ = [
    # UI组件
    'SearchHistoryPopup',
    'SearchResultsPopup',

    # 存储
    'GeoInfoStorage',

    # 管理器
    'SearchManager',
]

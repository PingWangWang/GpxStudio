"""
UI组件模块

注意：搜索相关的UI组件已移动到 modules.search.ui
为了向后兼容，这里保留导入
"""

# 为了向后兼容，从新位置导入
from modules.search.ui import SearchHistoryPopup, SearchResultsPopup

__all__ = ['SearchHistoryPopup', 'SearchResultsPopup']

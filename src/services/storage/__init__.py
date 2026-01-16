"""
存储服务模块

注意：GeoInfoStorage 已移动到 modules.search.storage
为了向后兼容，这里保留导入
"""

# 为了向后兼容，从新位置导入
from modules.search.storage import GeoInfoStorage

__all__ = ['GeoInfoStorage']

"""
应用管理器模块

包含应用程序的所有核心管理器类：
- WindowManager: 窗口和系统托盘管理
- ServiceManager: 各种服务实例管理和初始化
- DataManager: 应用数据状态管理
- LocationManager: 地理定位和位置获取
- MapManager: 地图显示和交互
- RouteManager: 路线规划和GPX导出
- TimeManager: 时间计算和日期/时间面板管理

注意：SearchManager 已移动到 modules.search.managers
"""

from .window_manager import WindowManager
from .service_manager import ServiceManager
from .data_manager import DataManager
from .location_manager import LocationManager
from .map_manager import MapManager
from .route_manager import RouteManager
from .time_manager import TimeManager

# 为了向后兼容，从新位置导入 SearchManager
from modules.search.managers import SearchManager

__all__ = [
    'WindowManager',
    'ServiceManager',
    'DataManager',
    'LocationManager',
    'SearchManager',  # 保留以保持向后兼容
    'MapManager',
    'RouteManager',
    'TimeManager'
]


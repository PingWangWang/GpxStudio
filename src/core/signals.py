"""
信号管理器
统一管理所有应用程序信号，提高代码的可维护性和可扩展性
"""

import logging
from typing import Any, Dict, List, Optional
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

# 设置日志
logger = logging.getLogger(__name__)


class SignalManager(QObject):
    """
    信号管理器类，集中管理所有应用程序信号
    使用单例模式确保全局只有一个信号管理器实例
    """

    # 地理定位相关信号
    geolocation_success = pyqtSignal(float, float, float)  # 纬度, 经度, 精度
    geolocation_error = pyqtSignal(str)  # 错误信息

    # 地图相关信号
    map_zoom_changed = pyqtSignal(int)  # 缩放级别
    map_loaded = pyqtSignal()  # 无参数
    map_center_changed = pyqtSignal(float, float)  # 纬度, 经度
    map_right_click = pyqtSignal(float, float)  # 纬度, 经度 - 地图右键点击

    # 搜索相关信号
    search_results_updated = pyqtSignal(list, str)  # 搜索结果列表, 搜索类型
    search_completed = pyqtSignal()  # 无参数

    # 路线规划相关信号
    route_planned = pyqtSignal(dict)  # 路线规划结果
    route_failed = pyqtSignal(str)  # 路线规划失败原因
    route_clear = pyqtSignal()  # 无参数

    # GPX导出相关信号
    gpx_exported = pyqtSignal(str)  # 导出文件路径
    gpx_export_failed = pyqtSignal(str)  # 导出失败原因

    # 配置相关信号
    config_updated = pyqtSignal(str, object)  # 配置名称, 配置数据

    def __init__(self):
        """初始化信号管理器"""
        super().__init__()

        # 信号注册表，用于存储所有信号信息
        self._signal_registry = {
            # 地理定位相关信号
            'geolocation_success': {
                'signal': self.geolocation_success,
                'description': '地理定位成功时发射'
            },
            'geolocation_error': {
                'signal': self.geolocation_error,
                'description': '地理定位失败时发射'
            },

            # 地图相关信号
            'map_zoom_changed': {
                'signal': self.map_zoom_changed,
                'description': '地图缩放级别改变时发射'
            },
            'map_loaded': {
                'signal': self.map_loaded,
                'description': '地图加载完成时发射'
            },
            'map_center_changed': {
                'signal': self.map_center_changed,
                'description': '地图中心点改变时发射'
            },
            'map_right_click': {
                'signal': self.map_right_click,
                'description': '地图右键点击时发射'
            },

            # 搜索相关信号
            'search_results_updated': {
                'signal': self.search_results_updated,
                'description': '搜索结果更新时发射'
            },
            'search_completed': {
                'signal': self.search_completed,
                'description': '搜索完成时发射'
            },

            # 路线规划相关信号
            'route_planned': {
                'signal': self.route_planned,
                'description': '路线规划成功时发射'
            },
            'route_failed': {
                'signal': self.route_failed,
                'description': '路线规划失败时发射'
            },
            'route_clear': {
                'signal': self.route_clear,
                'description': '清除路线时发射'
            },

            # GPX导出相关信号
            'gpx_exported': {
                'signal': self.gpx_exported,
                'description': 'GPX导出成功时发射'
            },
            'gpx_export_failed': {
                'signal': self.gpx_export_failed,
                'description': 'GPX导出失败时发射'
            },

            # 配置相关信号
            'config_updated': {
                'signal': self.config_updated,
                'description': '配置更新时发射'
            },
        }

        # 连接日志信号
        self._connect_log_signals()

        logger.debug("信号管理器初始化完成")

    def _initialize_signals(self):
        """初始化所有信号（已不再需要，因为信号是类属性）"""
        pass

    def _connect_log_signals(self):
        """连接日志信号，记录信号的发射"""
        # 可以在这里添加全局日志记录器
        pass

    def emit(self, signal_name: str, *args, **kwargs):
        """
        发射指定名称的信号

        查找并发射指定名称的信号，同时记录信号发射日志。
        如果信号不存在，则记录警告日志。

        参数:
            signal_name: 要发射的信号名称
            *args: 传递给信号的参数列表
            **kwargs: 传递给信号的关键字参数
        """
        if signal_name in self._signal_registry:
            signal = getattr(self, signal_name)
            logger.debug(f"发射信号: {signal_name}, 参数: {args}, 关键字参数: {kwargs}")
            signal.emit(*args)
        else:
            logger.warning(f"信号不存在: {signal_name}")

    def connect(self, signal_name: str, slot: callable):
        """
        连接指定名称的信号到槽函数

        将指定名称的信号连接到给定的槽函数，当信号被发射时，槽函数将被调用。
        如果信号不存在，则记录警告日志。

        参数:
            signal_name: 要连接的信号名称
            slot: 当信号发射时要调用的槽函数
        """
        if signal_name in self._signal_registry:
            signal = getattr(self, signal_name)
            signal.connect(slot)
            logger.debug(f"连接信号: {signal_name} 到槽函数: {slot.__name__}")
        else:
            logger.warning(f"信号不存在: {signal_name}")

    def disconnect(self, signal_name: str, slot: callable):
        """
        断开信号与槽函数的连接

        Args:
            signal_name: 信号名称
            slot: 槽函数
        """
        if signal_name in self._signal_registry:
            signal = getattr(self, signal_name)
            try:
                signal.disconnect(slot)
                logger.debug(f"断开信号: {signal_name} 与槽函数: {slot.__name__} 的连接")
            except TypeError:
                logger.warning(f"信号: {signal_name} 与槽函数: {slot.__name__} 未连接")
        else:
            logger.warning(f"信号不存在: {signal_name}")

    def get_signal_description(self, signal_name: str) -> Optional[str]:
        """
        获取信号的描述

        Args:
            signal_name: 信号名称

        Returns:
            信号描述，如果信号不存在则返回None
        """
        if signal_name in self._signal_registry:
            return self._signal_registry[signal_name]['description']
        else:
            return None

    def get_all_signals(self) -> List[str]:
        """
        获取所有信号名称

        Returns:
            信号名称列表
        """
        return list(self._signal_registry.keys())

    def add_signal(self, signal_name: str, signal_type: type, description: str = ""):
        """
        添加自定义信号

        Args:
            signal_name: 信号名称
            signal_type: 信号类型（pyqtSignal）
            description: 信号描述
        """
        if signal_name not in self._signal_registry:
            self._signal_registry[signal_name] = {
                'signal': signal_type,
                'description': description
            }
            setattr(self, signal_name, signal_type)
            logger.debug(f"添加自定义信号: {signal_name}, 描述: {description}")
        else:
            logger.warning(f"信号已存在: {signal_name}")

    def remove_signal(self, signal_name: str):
        """
        移除自定义信号

        Args:
            signal_name: 信号名称
        """
        if signal_name in self._signal_registry:
            del self._signal_registry[signal_name]
            delattr(self, signal_name)
            logger.debug(f"移除自定义信号: {signal_name}")
        else:
            logger.warning(f"信号不存在: {signal_name}")

    def clear_all_connections(self):
        """清除所有信号的连接"""
        for signal_name in self.get_all_signals():
            signal = getattr(self, signal_name)
            try:
                signal.disconnect()
                logger.debug(f"清除信号: {signal_name} 的所有连接")
            except TypeError:
                pass

    # 移除__del__方法，避免在不适当的时候销毁C++对象
    # def __del__(self):
    #     """析构函数，确保资源正确释放"""
    #     self.clear_all_connections()
    #     logger.debug("信号管理器已销毁")

    def __enter__(self):
        """进入上下文管理器"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文管理器"""
        self.clear_all_connections()


# 创建全局信号管理器实例
signal_manager = SignalManager()

# 确保全局实例不会被垃圾回收
global_signal_manager = signal_manager
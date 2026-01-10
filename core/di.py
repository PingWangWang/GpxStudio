"""
依赖注入容器
使用injector库实现依赖注入，降低模块间耦合度
"""

import logging
from injector import Injector, singleton, Module
from typing import Optional

# 导入需要注入的服务和组件
from services.gaode_geocoding import GaodeGeocodingService
from services.gaode_routing import GaodeRoutingService
from services.osm_geocoding import OsmGeocodingService
from services.config.map_config import MapConfig
from core.signals import SignalManager

# 设置日志
logger = logging.getLogger(__name__)


class AppModule(Module):
    """应用程序依赖模块"""

    def configure(self, binder):
        """配置依赖绑定"""
        # 绑定单例实例
        config = MapConfig()
        binder.bind(MapConfig, to=config, scope=singleton)

        signal_manager = SignalManager()
        binder.bind(SignalManager, to=signal_manager, scope=singleton)

        # 绑定服务实现
        gaode_geocoding_service = GaodeGeocodingService(
            api_key=config.api_key,
            security_key=config.security_key
        )
        binder.bind(GaodeGeocodingService, to=gaode_geocoding_service, scope=singleton)

        osm_geocoding_service = OsmGeocodingService()
        binder.bind(OsmGeocodingService, to=osm_geocoding_service, scope=singleton)

        routing_service = GaodeRoutingService(
            api_key=config.api_key,
            security_key=config.security_key
        )
        binder.bind(GaodeRoutingService, to=routing_service, scope=singleton)


class DIContainer:
    """依赖注入容器"""

    def __init__(self):
        """初始化依赖注入容器"""
        self.module = AppModule()
        self.injector = Injector([self.module])
        logger.debug("依赖注入容器初始化完成")

    def get(self, interface_type: type) -> Optional[object]:
        """
        获取指定类型的实例

        Args:
            interface_type: 接口类型

        Returns:
            指定类型的实例，如果不存在则返回None
        """
        try:
            instance = self.injector.get(interface_type)
            logger.debug(f"获取实例: {interface_type.__name__}")
            return instance
        except Exception as e:
            logger.error(f"获取实例失败: {interface_type.__name__}, 错误: {e}")
            return None

    def get_all_providers(self) -> list:
        """
        获取所有提供者

        Returns:
            提供者列表
        """
        # 返回所有已定义的提供者名称
        return [
            'MapConfig',
            'SignalManager',
            'GaodeGeocodingService',
            'OsmGeocodingService',
            'GaodeRoutingService'
        ]


# 创建全局依赖注入容器实例
di_container = DIContainer()


def inject_dependencies(cls):
    """
    依赖注入装饰器

    Args:
        cls: 需要注入依赖的类

    Returns:
        注入依赖后的类
    """
    # 使用injector库的inject装饰器
    from injector import inject as injector_inject
    return injector_inject(cls)

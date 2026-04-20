"""
依赖注入容器
使用injector库实现依赖注入，降低模块间耦合度
"""

import logging
from injector import Injector, singleton, Module
from typing import Optional

# 导入需要注入的服务和组件
from services.gaode.gaode_geocoding import GaodeGeocodingService
from services.gaode.gaode_routing import GaodeRoutingService
from services.osm.osm_geocoding import OsmGeocodingService
from services.osm.osm_routing import OsmRoutingService
from services.config.map_config import MapConfig
from core.signals import SignalManager

# 导入领域服务接口
from domain.services.geocoding_service import IGeocodingService
from domain.services.routing_service import IRoutingService
from domain.services.location_service import ILocationService

# 设置日志
logger = logging.getLogger(__name__)


class AppModule(Module):
    """应用程序依赖模块"""

    def configure(self, binder):
        """配置依赖绑定"""
        # ── 基础配置 ──────────────────────────────────────────────────────────
        config = MapConfig()
        binder.bind(MapConfig, to=config, scope=singleton)

        signal_manager = SignalManager()
        binder.bind(SignalManager, to=signal_manager, scope=singleton)

        api_key = config.get_api_key()
        security_key = config.get_security_key()

        # ── 具体服务实例（全部绑定，支持按需获取） ──────────────────────────
        gaode_geocoding = GaodeGeocodingService(
            api_key=api_key,
            security_key=security_key,
        )
        gaode_routing = GaodeRoutingService(
            api_key=api_key,
            security_key=security_key,
        )
        osm_geocoding = OsmGeocodingService()
        osm_routing = OsmRoutingService()

        binder.bind(GaodeGeocodingService, to=gaode_geocoding, scope=singleton)
        binder.bind(GaodeRoutingService, to=gaode_routing, scope=singleton)
        binder.bind(OsmGeocodingService, to=osm_geocoding, scope=singleton)
        binder.bind(OsmRoutingService, to=osm_routing, scope=singleton)

        # ── 接口绑定：根据当前地图源动态选择实现 ────────────────────────────
        map_source = config.get_map_source()
        if map_source == 'gaode':
            binder.bind(IGeocodingService, to=gaode_geocoding, scope=singleton)
            binder.bind(IRoutingService, to=gaode_routing, scope=singleton)
        else:
            binder.bind(IGeocodingService, to=osm_geocoding, scope=singleton)
            binder.bind(IRoutingService, to=osm_routing, scope=singleton)


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
            interface_type: 接口类型或具体类

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

    def rebind_for_map_source(self, map_source: str):
        """切换地图源后重新绑定 IGeocodingService / IRoutingService。

        Args:
            map_source: 目标地图源（'gaode' 或 'osm'）
        """
        try:
            if map_source == 'gaode':
                geocoding = self.get(GaodeGeocodingService)
                routing = self.get(GaodeRoutingService)
            else:
                geocoding = self.get(OsmGeocodingService)
                routing = self.get(OsmRoutingService)

            # injector 不直接支持重绑定，使用内部 _bindings 覆盖
            from injector import InstanceProvider
            self.injector.binder._bindings[IGeocodingService] = InstanceProvider(geocoding)
            self.injector.binder._bindings[IRoutingService] = InstanceProvider(routing)
            logger.info(f"DI 容器已重新绑定接口 → {map_source} 实现")
        except Exception as e:
            logger.error(f"rebind_for_map_source 失败: {e}")

    def get_all_providers(self) -> list:
        """获取所有已注册的提供者名称"""
        return [
            'MapConfig',
            'SignalManager',
            'IGeocodingService',
            'IRoutingService',
            'GaodeGeocodingService',
            'GaodeRoutingService',
            'OsmGeocodingService',
            'OsmRoutingService',
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

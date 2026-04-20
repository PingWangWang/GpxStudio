"""
领域服务接口层

定义所有外部服务的抽象接口（ABC），与具体实现解耦。
"""
from .geocoding_service import IGeocodingService
from .routing_service import IRoutingService
from .location_service import ILocationService
from .config_service import IConfigService

__all__ = [
    'IGeocodingService',
    'IRoutingService',
    'ILocationService',
    'IConfigService',
]

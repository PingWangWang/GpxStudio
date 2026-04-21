"""
services.gaode — 向后兼容 shim

真实实现已迁移到 ``infrastructure.api.gaode``。
"""
from infrastructure.api.gaode import GaodeGeocodingService, GaodeRoutingService  # noqa: F401

__all__ = ['GaodeGeocodingService', 'GaodeRoutingService']

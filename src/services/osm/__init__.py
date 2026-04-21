"""
services.osm — 向后兼容 shim

真实实现已迁移到 ``infrastructure.api.osm``。
"""
from infrastructure.api.osm import OsmGeocodingService, OsmRoutingService  # noqa: F401

__all__ = ['OsmGeocodingService', 'OsmRoutingService']

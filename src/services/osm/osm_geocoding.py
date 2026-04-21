"""
services.osm.osm_geocoding — 向后兼容 shim

真实实现已迁移到 ``infrastructure.api.osm.osm_geocoding``。
"""
from infrastructure.api.osm.osm_geocoding import OsmGeocodingService  # noqa: F401

__all__ = ['OsmGeocodingService']

"""
services.osm.osm_routing — 向后兼容 shim

真实实现已迁移到 ``infrastructure.api.osm.osm_routing``。
"""
from infrastructure.api.osm.osm_routing import OsmRoutingService  # noqa: F401

__all__ = ['OsmRoutingService']

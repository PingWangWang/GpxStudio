"""
services.config.map_config — 向后兼容 shim

真实实现已迁移到 ``infrastructure.config.map_config``。
"""
from infrastructure.config.map_config import MapConfig, map_config  # noqa: F401

__all__ = ['MapConfig', 'map_config']

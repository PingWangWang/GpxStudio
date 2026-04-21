"""
services.config — 向后兼容 shim

真实实现已迁移到 ``infrastructure.config``。
"""
from infrastructure.config.map_config import MapConfig, map_config  # noqa: F401
from infrastructure.config.about_config import AboutConfig  # noqa: F401
from infrastructure.config.about_config import about_config as about_config  # noqa: F401
import infrastructure.config.about_config as about_config_module  # noqa: F401

__all__ = ['MapConfig', 'map_config', 'AboutConfig', 'about_config']

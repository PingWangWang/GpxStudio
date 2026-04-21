"""
services.config.about_config — 向后兼容 shim

真实实现已迁移到 ``infrastructure.config.about_config``。
"""
from infrastructure.config.about_config import AboutConfig  # noqa: F401

__all__ = ['AboutConfig']

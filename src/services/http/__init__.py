"""
services.http — 向后兼容 shim

真实实现已迁移到 ``infrastructure.http``。
"""
from infrastructure.http import LocalMapServer  # noqa: F401

__all__ = ['LocalMapServer']

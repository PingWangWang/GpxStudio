"""
services.http.http_server — 向后兼容 shim

真实实现已迁移到 ``infrastructure.http.http_server``。
"""
from infrastructure.http.http_server import LocalMapServer  # noqa: F401

__all__ = ['LocalMapServer']

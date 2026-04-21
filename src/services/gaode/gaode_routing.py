"""
services.gaode.gaode_routing — 向后兼容 shim

真实实现已迁移到 ``infrastructure.api.gaode.gaode_routing``。
此文件保留以兼容现有 import 路径，新代码请使用新路径。
"""
from infrastructure.api.gaode.gaode_routing import GaodeRoutingService  # noqa: F401

__all__ = ['GaodeRoutingService']

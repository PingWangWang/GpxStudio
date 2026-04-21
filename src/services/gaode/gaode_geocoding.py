"""
services.gaode.gaode_geocoding — 向后兼容 shim

真实实现已迁移到 ``infrastructure.api.gaode.gaode_geocoding``。
此文件保留以兼容现有 import 路径，新代码请使用新路径。
"""
from infrastructure.api.gaode.gaode_geocoding import GaodeGeocodingService  # noqa: F401

__all__ = ['GaodeGeocodingService']

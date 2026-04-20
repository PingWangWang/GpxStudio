"""
位置服务接口（向后兼容 shim）

此文件保留以兼容旧 import 路径。
新代码请使用 ``from domain.services.location_service import ILocationService``。
"""
from domain.services.location_service import ILocationService  # noqa: F401

__all__ = ['ILocationService']

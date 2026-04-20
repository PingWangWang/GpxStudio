"""
路线规划服务接口（向后兼容 shim）

此文件保留以兼容旧 import 路径。
新代码请使用 `from domain.services.routing_service import IRoutingService`。
"""
from domain.services.routing_service import IRoutingService  # noqa: F401

__all__ = ['IRoutingService']

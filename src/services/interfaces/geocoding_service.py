"""
地理编码服务接口（向后兼容 shim）

此文件保留以兼容旧 import 路径。
新代码请使用 `from domain.services.geocoding_service import IGeocodingService`。
"""
from domain.services.geocoding_service import IGeocodingService  # noqa: F401

__all__ = ['IGeocodingService']

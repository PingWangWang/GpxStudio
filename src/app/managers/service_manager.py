"""
服务管理器
负责初始化和管理各种服务实例
"""

from services.gaode.gaode_geocoding import GaodeGeocodingService
from services.gaode.gaode_routing import GaodeRoutingService
from services.osm.osm_geocoding import OsmGeocodingService
from services.osm.osm_routing import OsmRoutingService
from modules.gpx.gpx_export import GpxExportService
from modules.geolocation.windows_location import WindowsLocationService
from services.config.map_config import map_config


class ServiceManager:
    """服务管理器
    
    负责初始化、管理和提供各种服务实例：
    - 地理编码服务（高德和OSM）
    - 路线规划服务（高德和OSM）
    - GPX导出服务
    - Windows定位服务
    
    根据配置选择合适的服务实例提供给其他管理器使用。
    """

    def __init__(self, logger_callback):
        """
        初始化服务管理器

        参数:
            logger_callback: 日志回调函数字典，包含不同服务的日志回调函数
        """
        self.logger_callbacks = logger_callback
        self.gaode_geocoding_service = None
        self.gaode_routing_service = None
        self.osm_geocoding_service = None
        self.osm_routing_service = None
        self.gpx_service = None
        self.windows_location_service = None

    def initialize_services(self):
        """初始化所有服务
        
        创建并配置所有服务实例，包括：
        - 高德地理编码服务
        - 高德路线规划服务
        - OSM地理编码服务
        - OSM路线规划服务
        - GPX导出服务
        """
        print("开始初始化服务")

        # 获取配置信息
        api_key = map_config.get_api_key()
        security_key = map_config.get_security_key()
        print(f"API Key 配置: {'已配置' if api_key else '未配置'}")
        print(f"Security Key 配置: {'已配置' if security_key else '未配置'}")

        # 初始化高德地理编码服务
        print("初始化高德地理编码服务")
        self.gaode_geocoding_service = GaodeGeocodingService(
            api_key=api_key,
            security_key=security_key,
            logger=self.logger_callbacks.get('geocoding')
        )

        # 初始化高德路线规划服务
        print("初始化高德路线规划服务")
        self.gaode_routing_service = GaodeRoutingService(
            api_key=api_key,
            security_key=security_key,
            logger=self.logger_callbacks.get('routing')
        )

        # 初始化OSM地理编码服务
        print("初始化OSM地理编码服务")
        self.osm_geocoding_service = OsmGeocodingService(
            logger=self.logger_callbacks.get('geocoding')
        )

        # 初始化OSM路线规划服务
        print("初始化OSM路线规划服务")
        self.osm_routing_service = OsmRoutingService(
            logger=self.logger_callbacks.get('routing')
        )

        # 初始化GPX导出服务
        print("初始化GPX导出服务")
        self.gpx_service = GpxExportService(
            logger=self.logger_callbacks.get('gpx')
        )

        print("服务初始化完成")

    def initialize_windows_location_service(self):
        """延迟初始化Windows定位服务
        
        Windows定位服务需要在日志器完全初始化后才能创建，
        因此使用单独的方法进行延迟初始化。
        """
        print("初始化Windows定位服务")
        self.windows_location_service = WindowsLocationService(
            logger=self.logger_callbacks.get('service')
        )

    def update_gaode_config(self, api_key: str, security_key: str):
        """更新高德地图配置
        
        更新高德地图服务的API密钥和安全密钥配置。
        
        参数:
            api_key: 高德地图API密钥
            security_key: 高德地图安全密钥
        """
        if self.gaode_geocoding_service:
            self.gaode_geocoding_service.api_key = api_key
            self.gaode_geocoding_service.security_key = security_key

        if self.gaode_routing_service:
            self.gaode_routing_service.api_key = api_key
            self.gaode_routing_service.security_key = security_key

    def get_geocoding_service(self, map_source: str):
        """获取地理编码服务
        
        根据指定的地图源返回对应的地理编码服务实例。
        
        参数:
            map_source: 地图源（gaode/osm）
            
        返回:
            对应的地理编码服务实例
        """
        if map_source == "gaode":
            return self.gaode_geocoding_service
        else:
            return self.osm_geocoding_service

    def get_routing_service(self, map_source: str):
        """获取路线规划服务
        
        根据指定的地图源返回对应的路线规划服务实例。
        
        参数:
            map_source: 地图源（gaode/osm）
            
        返回:
            对应的路线规划服务实例
        """
        if map_source == "gaode":
            return self.gaode_routing_service
        else:
            return self.osm_routing_service

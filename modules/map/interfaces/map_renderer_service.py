"""
地图渲染服务接口
定义地图渲染相关服务的契约
"""

from typing import Optional, List, Dict, Callable, Tuple


class IMapRendererService:
    """
    地图渲染服务接口
    定义了地图渲染的方法
    """
    
    def __init__(self, logger: Optional[Callable] = None):
        """
        初始化地图渲染服务
        
        Args:
            logger: 日志记录器函数，接收(level, message)参数
        """
        ...
    
    def create_map(self, center: Tuple[float, float] = (39.9042, 116.4074), zoom: int = 13) -> Any:
        """
        创建地图实例
        
        Args:
            center: 地图中心点坐标 (lat, lon)
            zoom: 地图初始缩放级别
            
        Returns:
            Any: 地图实例
        """
        ...
    
    def add_marker(self, map_instance: Any, location: Tuple[float, float], popup: str = "", 
                  icon: Optional[Any] = None, tooltip: Optional[str] = None) -> None:
        """
        在地图上添加标记
        
        Args:
            map_instance: 地图实例
            location: 标记位置 (lat, lon)
            popup: 弹出信息
            icon: 标记图标
            tooltip: 提示信息
        """
        ...
    
    def add_route(self, map_instance: Any, route_points: List[Tuple[float, float]], 
                 color: str = "blue", weight: int = 5, opacity: float = 0.8) -> None:
        """
        在地图上添加路线
        
        Args:
            map_instance: 地图实例
            route_points: 路线点列表 [(lat, lon), ...]
            color: 路线颜色
            weight: 路线宽度
            opacity: 路线透明度
        """
        ...
    
    def save_map(self, map_instance: Any, file_path: str) -> bool:
        """
        保存地图为HTML文件
        
        Args:
            map_instance: 地图实例
            file_path: 保存文件路径
            
        Returns:
            bool: 保存是否成功
        """
        ...
    
    def add_tile_layer(self, map_instance: Any, tile_url: str, name: str, attribution: str) -> None:
        """
        添加瓦片图层
        
        Args:
            map_instance: 地图实例
            tile_url: 瓦片URL模板
            name: 图层名称
            attribution: 版权信息
        """
        ...

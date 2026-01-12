"""
位置服务接口
定义位置获取相关服务的契约
"""

from typing import Optional, Dict, Any, Callable


class ILocationService:
    """
    位置服务接口
    定义了获取当前位置的方法
    """
    
    def __init__(self, logger: Optional[Callable] = None):
        """
        初始化位置服务
        
        Args:
            logger: 日志记录器函数，接收(level, message)参数
        """
        ...
    
    def is_available(self) -> bool:
        """
        检查位置服务是否可用
        
        Returns:
            bool: 服务是否可用
        """
        ...
    
    def get_location(self, timeout: float = 10.0) -> Optional[Dict[str, Any]]:
        """
        获取当前位置（同步接口）
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            dict: 位置信息字典，包含latitude, longitude, accuracy等字段
                  失败返回None
        """
        ...
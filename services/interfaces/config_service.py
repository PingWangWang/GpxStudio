"""
配置服务接口
定义配置相关服务的契约
"""

from typing import Optional, Dict, Any


class IConfigService:
    """
    配置服务接口
    定义了配置管理的方法
    """
    
    def __init__(self, config_file: str):
        """
        初始化配置服务
        
        Args:
            config_file: 配置文件路径
        """
        ...
    
    def load_config(self) -> Dict[str, Any]:
        """
        加载配置
        
        Returns:
            dict: 配置数据
        """
        ...
    
    def save_config(self, config_data: Dict[str, Any]) -> bool:
        """
        保存配置
        
        Args:
            config_data: 配置数据
            
        Returns:
            bool: 保存是否成功
        """
        ...
    
    def get(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        """
        获取配置项
        
        Args:
            key: 配置项键名
            default: 默认值
            
        Returns:
            Any: 配置项值
        """
        ...
    
    def set(self, key: str, value: Any) -> bool:
        """
        设置配置项
        
        Args:
            key: 配置项键名
            value: 配置项值
            
        Returns:
            bool: 设置是否成功
        """
        ...

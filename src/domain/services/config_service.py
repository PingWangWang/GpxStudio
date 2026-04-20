"""
配置服务接口（ABC）

替代 src/services/interfaces/config_service.py 的非抽象版本。
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class IConfigService(ABC):
    """配置服务抽象基类

    所有配置管理服务必须实现此接口。
    """

    @abstractmethod
    def load_config(self) -> Dict[str, Any]:
        """加载配置

        Returns:
            配置数据字典。
        """

    @abstractmethod
    def save_config(self, config_data: Dict[str, Any]) -> bool:
        """保存配置

        Args:
            config_data: 要保存的配置字典

        Returns:
            保存成功返回 True，失败返回 False。
        """

    @abstractmethod
    def get(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        """读取单个配置项

        Args:
            key: 配置键名
            default: 键不存在时的默认值

        Returns:
            配置值，不存在则返回 default。
        """

    @abstractmethod
    def set(self, key: str, value: Any) -> bool:
        """写入单个配置项

        Args:
            key: 配置键名
            value: 配置值

        Returns:
            写入成功返回 True，失败返回 False。
        """

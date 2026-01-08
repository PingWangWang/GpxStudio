"""
高德地图配置管理
提供API配置保存和加载功能
"""

import os
import json
from typing import Optional, Dict, Any

from services.interfaces.config_service import IConfigService


class GaodeConfig(IConfigService):
    """高德地图配置类"""

    CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'gaode_config.json')

    def __init__(self):
        self.api_key = ""
        self.security_key = ""
        self.is_configured = False
        self._config_data = {}
        self._load_config()

    def _load_config(self):
        """从配置文件加载配置"""
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self._config_data = json.load(f)
                    self.api_key = self._config_data.get('api_key', '')
                    self.security_key = self._config_data.get('security_key', '')
                    self.is_configured = bool(self.api_key)
        except Exception:
            self.is_configured = False

    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        self._load_config()
        return self._config_data

    def save_config(self, config_data: Dict[str, Any]) -> bool:
        """保存配置到文件"""
        try:
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            self.api_key = config_data.get('api_key', '')
            self.security_key = config_data.get('security_key', '')
            self.is_configured = bool(self.api_key)
            self._config_data = config_data
            return True
        except Exception:
            return False

    def clear_config(self):
        """清除配置"""
        try:
            if os.path.exists(self.CONFIG_FILE):
                os.remove(self.CONFIG_FILE)
            self.api_key = ""
            self.security_key = ""
            self.is_configured = False
            self._config_data = {}
            return True
        except Exception:
            return False

    def get(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        """获取配置项"""
        return self._config_data.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        """设置配置项"""
        try:
            self._config_data[key] = value
            return self.save_config(self._config_data)
        except Exception:
            return False

    def get_api_key(self) -> str:
        """获取API Key"""
        return self.api_key

    def get_security_key(self) -> str:
        """获取安全密钥"""
        return self.security_key

    def is_available(self) -> bool:
        """检查配置是否可用"""
        return self.is_configured


gaode_config = GaodeConfig()

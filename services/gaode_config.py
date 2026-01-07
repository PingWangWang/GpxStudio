"""
高德地图配置管理
提供API配置保存和加载功能
"""

import os
import json
from typing import Optional


class GaodeConfig:
    """高德地图配置类"""

    CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'gaode_config.json')

    def __init__(self):
        self.api_key = ""
        self.security_key = ""
        self.is_configured = False
        self._load_config()

    def _load_config(self):
        """从配置文件加载配置"""
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.api_key = config.get('api_key', '')
                    self.security_key = config.get('security_key', '')
                    self.is_configured = bool(self.api_key)
        except Exception:
            self.is_configured = False

    def save_config(self, api_key: str, security_key: str = ""):
        """保存配置到文件"""
        config = {
            'api_key': api_key,
            'security_key': security_key
        }
        try:
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            self.api_key = api_key
            self.security_key = security_key
            self.is_configured = bool(api_key)
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
            return True
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

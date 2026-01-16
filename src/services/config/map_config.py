"""
地图配置管理
提供地图数据源配置保存和加载功能
"""

import os
import json
import sys
from typing import Optional, Dict, Any

from services.interfaces.config_service import IConfigService


class MapConfig(IConfigService):
    """地图配置类"""

    def _get_config_path(self):
        """获取配置文件路径"""
        from app.data_paths import get_map_config_file
        return get_map_config_file()

    def __init__(self):
        self.map_source = ""  # 首次运行时默认无地图源
        self.api_key = ""
        self.security_key = ""
        self.is_configured = False
        self._config_data = {}
        self._load_config()

    def _load_config(self):
        """从配置文件加载配置"""
        try:
            config_file = self._get_config_path()
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    try:
                        self._config_data = json.load(f)
                    except json.JSONDecodeError:
                        # 如果JSON解析失败，使用默认配置
                        self._config_data = {}
                    self.map_source = self._config_data.get('map_source', '')
                    self.api_key = self._config_data.get('api_key', '')
                    self.security_key = self._config_data.get('security_key', '')
                    self.is_configured = True
        except Exception:
            self._config_data = {}
            self.is_configured = False

    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        self._load_config()
        return self._config_data

    def save_config(self, config_data: Dict[str, Any]) -> bool:
        """保存配置到文件"""
        try:
            # 合并配置数据，保留现有的其他配置项
            merged_config = self._config_data.copy()
            merged_config.update(config_data)

            config_file = self._get_config_path()
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(merged_config, f, ensure_ascii=False, indent=2)

            self.map_source = merged_config.get('map_source', '')
            self.api_key = merged_config.get('api_key', '')
            self.security_key = merged_config.get('security_key', '')
            self.is_configured = True
            self._config_data = merged_config
            return True
        except Exception:
            return False

    def clear_config(self):
        """清除配置"""
        try:
            config_file = self._get_config_path()
            if os.path.exists(config_file):
                os.remove(config_file)
            self.map_source = ""
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

    def get_map_source(self) -> str:
        """获取地图数据源"""
        return self.map_source

    def get_api_key(self) -> str:
        """获取API Key"""
        return self.api_key

    def get_security_key(self) -> str:
        """获取安全密钥"""
        return self.security_key

    def is_gaode_configured(self) -> bool:
        """检查高德地图配置是否可用"""
        return bool(self.api_key)

    def is_available(self) -> bool:
        """检查配置是否可用"""
        return self.is_configured


map_config = MapConfig()
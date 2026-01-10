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
        """获取配置文件路径，保存在用户目录下"""
        if hasattr(sys, '_MEIPASS'):
            # 打包后的环境
            app_dir = os.path.join(os.path.expanduser("~"), "GPXStudio")
        else:
            # 开发环境
            app_dir = os.path.join(os.path.expanduser("~"), "GPXStudio")

        # 创建应用程序目录（如果不存在）
        if not os.path.exists(app_dir):
            os.makedirs(app_dir)

        return os.path.join(app_dir, "map_config.json")

    def __init__(self):
        self.map_source = "osm"  # 默认使用OSM
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
                    self._config_data = json.load(f)
                    self.map_source = self._config_data.get('map_source', 'osm')
                    self.api_key = self._config_data.get('api_key', '')
                    self.security_key = self._config_data.get('security_key', '')
                    self.is_configured = True
        except Exception:
            self.is_configured = False

    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        self._load_config()
        return self._config_data

    def save_config(self, config_data: Dict[str, Any]) -> bool:
        """保存配置到文件"""
        try:
            config_file = self._get_config_path()
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            self.map_source = config_data.get('map_source', 'osm')
            self.api_key = config_data.get('api_key', '')
            self.security_key = config_data.get('security_key', '')
            self.is_configured = True
            self._config_data = config_data
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
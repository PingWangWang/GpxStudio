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

    def _ensure_complete_config(self):
        """确保配置文件包含所有必要的配置项"""
        config_updated = False
        
        # 检查并添加缺失的路线优化配置
        if 'route_optimization' not in self._config_data:
            self._config_data['route_optimization'] = {
                'enabled': True,
                'max_points_per_segment': 500,
                'auto_zoom_calculation': True
            }
            config_updated = True
            print("[地图配置] 添加缺失的路线优化配置")
        else:
            # 检查路线优化子配置项
            route_opt = self._config_data['route_optimization']
            if 'enabled' not in route_opt:
                route_opt['enabled'] = True
                config_updated = True
            if 'max_points_per_segment' not in route_opt:
                route_opt['max_points_per_segment'] = 500
                config_updated = True
            if 'auto_zoom_calculation' not in route_opt:
                route_opt['auto_zoom_calculation'] = True
                config_updated = True
        
        # 如果配置有更新，保存到文件
        if config_updated:
            try:
                config_file = self._get_config_path()
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(self._config_data, f, ensure_ascii=False, indent=2)
                print("[地图配置] ✅ 已更新运行时配置文件，添加缺失配置项")
            except Exception as e:
                print(f"[地图配置] ❌ 保存配置失败: {e}")

    def _load_config(self):
        """从运行时配置文件加载配置（仅使用用户配置）"""
        try:
            config_file = self._get_config_path()
            print(f"[地图配置] 配置文件路径: {config_file}")
            
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    try:
                        self._config_data = json.load(f)
                        print(f"[地图配置] ✅ 成功加载运行时配置")
                    except json.JSONDecodeError as e:
                        print(f"[地图配置] ❌ JSON解析失败: {e}")
                        self._config_data = {}
                    
                    # 更新实例属性
                    self.map_source = self._config_data.get('map_source', '')
                    self.api_key = self._config_data.get('api_key', '')
                    self.security_key = self._config_data.get('security_key', '')
                    self.is_configured = True
                    
                    print(f"[地图配置] 当前配置 - 地图源: {self.map_source}, API配置: {'已配置' if self.api_key else '未配置'}")
            else:
                print(f"[地图配置] ⚠ 运行时配置文件不存在，使用空配置")
                self._config_data = {}
                self.map_source = ""
                self.api_key = ""
                self.security_key = ""
                self.is_configured = False
                
        except Exception as e:
            print(f"[地图配置] ❌ 加载配置失败: {e}")
            self._config_data = {}
            self.map_source = ""
            self.api_key = ""
            self.security_key = ""
            self.is_configured = False
        
        # 确保配置文件包含所有必要的配置项
        self._ensure_complete_config()

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

    # 路线优化相关配置方法
    def is_route_optimization_enabled(self) -> bool:
        """检查是否启用路线优化"""
        route_opt = self._config_data.get('route_optimization', {})
        return route_opt.get('enabled', True)  # 默认启用（会通过_ensure_complete_config自动添加）

    def get_max_points_per_segment(self) -> int:
        """获取每段路线的最大点数"""
        route_opt = self._config_data.get('route_optimization', {})
        return route_opt.get('max_points_per_segment', 500)

    def is_auto_zoom_calculation_enabled(self) -> bool:
        """检查是否启用自动缩放级别计算"""
        route_opt = self._config_data.get('route_optimization', {})
        return route_opt.get('auto_zoom_calculation', True)  # 默认启用（会通过_ensure_complete_config自动添加）

    def set_route_optimization_enabled(self, enabled: bool) -> bool:
        """设置路线优化开关"""
        try:
            if 'route_optimization' not in self._config_data:
                self._config_data['route_optimization'] = {}
            self._config_data['route_optimization']['enabled'] = enabled
            return self.save_config(self._config_data)
        except Exception:
            return False

    def set_max_points_per_segment(self, max_points: int) -> bool:
        """设置每段路线的最大点数"""
        try:
            if 'route_optimization' not in self._config_data:
                self._config_data['route_optimization'] = {}
            self._config_data['route_optimization']['max_points_per_segment'] = max_points
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
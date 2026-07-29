"""
地图配置管理
提供地图数据源配置保存和加载功能
"""

import os
import json
import sys
import threading
from typing import Optional, Dict, Any

from domain.services.config_service import IConfigService


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
        self._config_lock = threading.RLock()  # 添加线程锁保护配置数据
        self._load_config()

    def _ensure_complete_config(self):
        """确保配置文件包含所有必要的配置项"""
        config_updated = False

        # 确保配置文件包含地图源配置和各个地图的配置
        if 'map_source' not in self._config_data:
            self._config_data['map_source'] = ""
            config_updated = True

        # 确保包含地图模式配置
        if 'map_mode' not in self._config_data:
            self._config_data['map_mode'] = "roadmap"
            config_updated = True

        # 确保包含卫星地图路网开关配置
        if 'satellite_show_roads' not in self._config_data:
            self._config_data['satellite_show_roads'] = True  # 默认显示路网
            config_updated = True

        # 确保包含关闭动作配置
        if 'close_action' not in self._config_data:
            self._config_data['close_action'] = "exit"  # 默认为直接退出
            config_updated = True

        # 确保包含海拔数据获取优化开关
        if 'elevation_optimize' not in self._config_data:
            self._config_data['elevation_optimize'] = True  # 默认启用优化（最多1000点）
            config_updated = True

        # 确保包含高德地图配置
        if 'gaode' not in self._config_data:
            self._config_data['gaode'] = {
                "api_key": "",
                "security_key": ""
            }
            config_updated = True
        else:
            # 确保高德地图配置包含必要的键
            if 'api_key' not in self._config_data['gaode']:
                self._config_data['gaode']['api_key'] = ""
                config_updated = True
            if 'security_key' not in self._config_data['gaode']:
                self._config_data['gaode']['security_key'] = ""
                config_updated = True

        # 确保包含OSM地图配置
        if 'osm' not in self._config_data:
            self._config_data['osm'] = {
                "api_key": "",
                "security_key": ""
            }
            config_updated = True
        else:
            # 确保OSM地图配置包含必要的键
            if 'api_key' not in self._config_data['osm']:
                self._config_data['osm']['api_key'] = ""
                config_updated = True
            if 'security_key' not in self._config_data['osm']:
                self._config_data['osm']['security_key'] = ""
                config_updated = True

        # 确保包含最后地图中心点配置
        if 'last_center_lat' not in self._config_data:
            self._config_data['last_center_lat'] = None
            config_updated = True
        if 'last_center_lon' not in self._config_data:
            self._config_data['last_center_lon'] = None
            config_updated = True
        if 'last_zoom_level' not in self._config_data:
            self._config_data['last_zoom_level'] = None
            config_updated = True
        if 'last_map_source' not in self._config_data:
            self._config_data['last_map_source'] = None
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
        with self._config_lock:
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
                        # 根据当前地图源加载对应的API Key和安全密钥
                        if self.map_source == 'gaode':
                            self.api_key = self._config_data.get('gaode', {}).get('api_key', '')
                            self.security_key = self._config_data.get('gaode', {}).get('security_key', '')
                            print(f"[地图配置] 🔍 加载高德配置 - API Key: {self.api_key[:10] if self.api_key else '(空)'}... (长度: {len(self.api_key)})")
                        else:
                            self.api_key = self._config_data.get('osm', {}).get('api_key', '')
                            self.security_key = self._config_data.get('osm', {}).get('security_key', '')
                        self.is_configured = True

                        print(f"[地图配置] 当前配置 - 地图源: {self.map_source}, API配置: {'已配置' if self.api_key else '未配置'}")
                        if self.map_source == 'gaode' and self.api_key:
                            print(f"[地图配置] ✅ 高德API已配置")
                        elif self.map_source == 'gaode' and not self.api_key:
                            print(f"[地图配置] ⚠️ 高德地图已选择但API未配置")
                            print(f"[地图配置] ⚠️ gaode配置内容: {self._config_data.get('gaode', {})}")
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
            with self._config_lock:
                # 合并配置数据，保留现有的其他配置项
                merged_config = self._config_data.copy()
                merged_config.update(config_data)

                # 处理API Key和安全密钥的保存
                map_source = merged_config.get('map_source', '')
                
                # 关键修复：如果传入的config_data中没有api_key和security_key，
                # 则从现有配置的gaode/osm子对象中获取，避免覆盖丢失
                if 'api_key' in config_data:
                    api_key = merged_config.get('api_key', '')
                else:
                    # 从现有配置中获取对应地图源的API Key
                    if map_source == 'gaode':
                        api_key = merged_config.get('gaode', {}).get('api_key', '')
                    elif map_source == 'osm':
                        api_key = merged_config.get('osm', {}).get('api_key', '')
                    else:
                        api_key = ''
                
                if 'security_key' in config_data:
                    security_key = merged_config.get('security_key', '')
                else:
                    # 从现有配置中获取对应地图源的Security Key
                    if map_source == 'gaode':
                        security_key = merged_config.get('gaode', {}).get('security_key', '')
                    elif map_source == 'osm':
                        security_key = merged_config.get('osm', {}).get('security_key', '')
                    else:
                        security_key = ''

                # 打印保存前的配置数据
                print(f"[地图配置] 📝 保存配置 - map_source: {map_source}, api_key: {api_key[:10] if api_key else '(空)'}...")
                
                # 根据地图源将API Key和安全密钥保存到对应的配置中
                if map_source == 'gaode':
                    if 'gaode' not in merged_config:
                        merged_config['gaode'] = {}
                    merged_config['gaode']['api_key'] = api_key
                    merged_config['gaode']['security_key'] = security_key
                    print(f"[地图配置] 💾 保存高德配置 - API Key: {api_key[:10] if api_key else '(空)'}... (长度: {len(api_key)})")
                    print(f"[地图配置] 💾 merged_config['gaode']: {merged_config['gaode']}")
                elif map_source == 'osm':
                    if 'osm' not in merged_config:
                        merged_config['osm'] = {}
                    merged_config['osm']['api_key'] = api_key
                    merged_config['osm']['security_key'] = security_key
                    print(f"[地图配置] 💾 保存OSM配置 - API Key: {api_key[:10] if api_key else '(空)'}...")

                # 从顶层移除api_key和security_key，避免混淆
                if 'api_key' in merged_config:
                    del merged_config['api_key']
                if 'security_key' in merged_config:
                    del merged_config['security_key']

                config_file = self._get_config_path()
                print(f"[地图配置] 💾 保存到文件: {config_file}")
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(merged_config, f, ensure_ascii=False, indent=2)

                # 更新实例属性
                self.map_source = map_source
                if map_source == 'gaode':
                    self.api_key = merged_config.get('gaode', {}).get('api_key', '')
                    self.security_key = merged_config.get('gaode', {}).get('security_key', '')
                    print(f"[地图配置] 🔄 内存更新 - self.api_key: {self.api_key[:10] if self.api_key else '(空)'}... (长度: {len(self.api_key)})")
                else:
                    self.api_key = merged_config.get('osm', {}).get('api_key', '')
                    self.security_key = merged_config.get('osm', {}).get('security_key', '')
                self.is_configured = True
                self._config_data = merged_config
                
                print(f"[地图配置] ✅ 配置已保存并同步到内存 - 地图源: {map_source}, API已配置: {bool(self.api_key)}")
                return True
        except Exception as e:
            print(f"[地图配置] ❌ 保存配置失败: {e}")
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

    # ── 地图视口状态持久化 ────────────────────────────────────────

    def get_last_view_center(self):
        """
        获取上次保存的地图中心点坐标及当时的地图源

        返回:
            (lat, lon, map_source) 三元组，或 None（从未保存过）
            map_source 为 'gaode'/'osm' 等，用于加载时判断坐标系
        """
        lat = self._config_data.get('last_center_lat')
        lon = self._config_data.get('last_center_lon')
        ms = self._config_data.get('last_map_source')
        if lat is not None and lon is not None:
            return (lat, lon, ms)
        return None

    def get_last_view_zoom(self) -> Optional[int]:
        """
        获取上次保存的地图缩放级别

        返回:
            缩放级别整数，或 None（从未保存过）
        """
        return self._config_data.get('last_zoom_level')

    def set_last_view_state(self, lat: float, lon: float, zoom: Optional[int], map_source: Optional[str] = None) -> bool:
        """
        保存地图视口状态（中心点 + 缩放级别 + 地图源）

        参数:
            lat:        中心点纬度
            lon:        中心点经度
            zoom:       缩放级别（可能为 None）
            map_source: 当前地图源（'gaode'/'osm' 等），用于加载时判断坐标系

        返回:
            True 保存成功，False 保存失败
        """
        try:
            return self.save_config({
                'last_center_lat': lat,
                'last_center_lon': lon,
                'last_zoom_level': zoom,
                'last_map_source': map_source
            })
        except Exception:
            return False

    # 路线优化相关配置方法
    def get_map_source(self) -> str:
        """获取地图数据源"""
        return self.map_source

    def get_api_key(self) -> str:
        """获取API Key"""
        with self._config_lock:
            # 根据当前地图源返回对应的API Key
            if self.map_source == 'gaode':
                return self._config_data.get('gaode', {}).get('api_key', '')
            elif self.map_source == 'osm':
                return self._config_data.get('osm', {}).get('api_key', '')
            return ''

    def get_security_key(self) -> str:
        """获取安全密钥"""
        with self._config_lock:
            # 根据当前地图源返回对应的安全密钥
            if self.map_source == 'gaode':
                return self._config_data.get('gaode', {}).get('security_key', '')
            elif self.map_source == 'osm':
                return self._config_data.get('osm', {}).get('security_key', '')
            return ''

    def is_gaode_configured(self) -> bool:
        """检查高德地图配置是否可用"""
        with self._config_lock:
            # 直接从配置数据中获取高德地图的API Key
            gaode_api_key = self._config_data.get('gaode', {}).get('api_key', '')
            is_configured = bool(gaode_api_key)
            
            # 添加调试日志
            if not is_configured:
                print(f"[地图配置] ⚠️ 高德API配置检查失败 - gaode配置: {self._config_data.get('gaode', {})}")
                print(f"[地图配置] ⚠️ 完整配置数据: {self._config_data}")
            
            return is_configured

    def is_available(self) -> bool:
        """检查配置是否可用"""
        return self.is_configured

    def get_map_mode(self) -> str:
        """获取地图模式"""
        return self._config_data.get('map_mode', 'roadmap')

    def set_map_mode(self, map_mode: str) -> bool:
        """设置地图模式"""
        try:
            # 只传递需要修改的字段，避免覆盖API Key等其他配置
            return self.save_config({'map_mode': map_mode})
        except Exception:
            return False

    def get_satellite_show_roads(self) -> bool:
        """获取卫星地图是否显示路网"""
        return self._config_data.get('satellite_show_roads', True)

    def set_satellite_show_roads(self, show: bool) -> bool:
        """设置卫星地图是否显示路网"""
        try:
            # 只传递需要修改的字段，避免覆盖API Key等其他配置
            return self.save_config({'satellite_show_roads': show})
        except Exception:
            return False

    def get_close_action(self) -> str:
        """获取关闭动作"""
        return self._config_data.get('close_action', 'exit')

    def set_close_action(self, action: str) -> bool:
        """设置关闭动作"""
        try:
            # 只传递需要修改的字段，避免覆盖API Key等其他配置
            return self.save_config({'close_action': action})
        except Exception:
            return False

    def get_elevation_optimize(self) -> bool:
        """获取海拔数据获取优化开关（True=最多1000点，False=按实际点数）"""
        return self._config_data.get('elevation_optimize', True)

    def set_elevation_optimize(self, enabled: bool) -> bool:
        """设置海拔数据获取优化开关"""
        try:
            return self.save_config({'elevation_optimize': enabled})
        except Exception:
            return False


map_config = MapConfig()
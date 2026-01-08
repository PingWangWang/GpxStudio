"""
高德地图地理编码服务
使用高德地图API进行地点搜索和反向地理编码
"""

import requests
import hashlib
import json
from typing import Optional, Callable, List, Dict

from services.interfaces.geocoding_service import IGeocodingService


class GaodeGeocodingService(IGeocodingService):
    """高德地图地理编码服务"""

    GEOCODE_URL = "https://restapi.amap.com/v3/place/text"
    REVERSE_GEOCODE_URL = "https://restapi.amap.com/v3/geocode/regeo"

    def __init__(self, api_key: str = "", security_key: str = "", logger: Optional[Callable] = None):
        self.api_key = api_key
        self.security_key = security_key
        self.logger = logger

    def log(self, level: str, message: str):
        """输出日志"""
        if self.logger:
            self.logger(level, message)

    def _sign(self, params: dict) -> str:
        """生成签名"""
        if not self.security_key:
            return ""
        sorted_params = sorted(params.items())
        sign_str = self.security_key + ''.join(f"{k}{v}" for k, v in sorted_params)
        return hashlib.md5(sign_str.encode()).hexdigest()

    def search_location(self, search_text: str) -> Optional[List[dict]]:
        """
        搜索地点

        Args:
            search_text: 搜索文本

        Returns:
            list: 搜索结果列表，每个结果包含name, address, lat, lon
        """
        def log_cb(level, message):
            if self.logger:
                self.logger(level, message)

        if not self.api_key:
            log_cb("WARNING", "高德地图API Key未配置")
            return None

        try:
            log_cb("DEBUG", f"搜索地点: {search_text}")

            params = {
                'key': self.api_key,
                'keywords': search_text,
                'city': '全国',
                'citylimit': 'false',
                'output': 'json',
                'offset': 10,
                'page': 1
            }

            if self.security_key:
                params['sig'] = self._sign(params)

            response = requests.get(self.GEOCODE_URL, params=params, timeout=10)
            data = response.json()

            if data.get('status') == '1' and data.get('pois'):
                results = []
                for poi in data['pois'][:5]:
                    location = poi.get('location', '').split(',')
                    if len(location) == 2:
                        results.append({
                            'name': poi.get('name', ''),
                            'address': poi.get('address', '') or poi.get('pname', '') + poi.get('city', ''),
                            'lat': float(location[1]),
                            'lon': float(location[0]),
                            'type': poi.get('type', ''),
                            'level': poi.get('typecode', '')
                        })

                log_cb("INFO", f"搜索成功，找到 {len(results)} 个结果")
                return results
            else:
                error_msg = data.get('info', '未知错误')
                log_cb("WARNING", f"搜索失败: {error_msg}")
                return None

        except Exception as e:
            log_cb("ERROR", f"搜索异常: {str(e)}")
            return None

    def reverse_geocode(self, lat: float, lon: float) -> Optional[dict]:
        """
        反向地理编码

        Args:
            lat: 纬度
            lon: 经度

        Returns:
            dict: 地址信息字典
        """
        def log_cb(level, message):
            if self.logger:
                self.logger(level, message)

        if not self.api_key:
            log_cb("WARNING", "高德地图API Key未配置")
            return None

        try:
            log_cb("DEBUG", f"反向地理编码: {lat}, {lon}")

            params = {
                'key': self.api_key,
                'location': f"{lon},{lat}",
                'output': 'json',
                'radius': 100
            }

            if self.security_key:
                params['sig'] = self._sign(params)

            response = requests.get(self.REVERSE_GEOCODE_URL, params=params, timeout=10)
            data = response.json()

            if data.get('status') == '1':
                regeocode = data.get('regeocode', {})
                address = regeocode.get('formatted_address', '')
                city = regeocode.get('addressComponent', {}).get('city', '') or \
                       regeocode.get('addressComponent', {}).get('district', '')

                result = {
                    'city': city,
                    'full_address': address
                }
                log_cb("INFO", f"反向地理编码成功: {address}")
                return result
            else:
                error_msg = data.get('info', '未知错误')
                log_cb("WARNING", f"反向地理编码失败: {error_msg}")
                return None

        except Exception as e:
            log_cb("ERROR", f"反向地理编码异常: {str(e)}")
            return None

    def get_ip_location(self) -> Optional[dict]:
        """
        使用高德地图IP定位API获取当前位置

        Returns:
            dict: 定位信息 {'lat': float, 'lon': float, 'city': str, 'source': str}
                 失败返回None
        """
        def log_cb(level, message):
            if self.logger:
                self.logger(level, message)

        if not self.api_key:
            log_cb("WARNING", "高德地图API Key未配置，无法使用IP定位")
            return None

        try:
            log_cb("DEBUG", "正在使用高德地图IP定位...")

            params = {
                'key': self.api_key,
                'output': 'json'
            }

            if self.security_key:
                params['sig'] = self._sign(params)

            response = requests.get('https://restapi.amap.com/v3/ip', params=params, timeout=10)
            data = response.json()

            if data.get('status') == '1':
                adcode = data.get('adcode', '')
                rectangle = data.get('rectangle', '')

                if rectangle:
                    coords = rectangle.split(';')
                    if len(coords) == 2:
                        lon1, lat1 = coords[0].split(',')
                        lon2, lat2 = coords[1].split(',')
                        center_lon = (float(lon1) + float(lon2)) / 2
                        center_lat = (float(lat1) + float(lat2)) / 2

                        log_cb("INFO", f"高德IP定位成功: {data.get('city', '')}")
                        return {
                            'lat': center_lat,
                            'lon': center_lon,
                            'city': data.get('city', ''),
                            'province': data.get('province', ''),
                            'adcode': adcode,
                            'source': 'gaode_ip'
                        }

                log_cb("WARNING", "高德IP定位未返回有效坐标")
                return None
            else:
                error_msg = data.get('info', '未知错误')
                log_cb("WARNING", f"高德IP定位失败: {error_msg}")
                return None

        except Exception as e:
            log_cb("ERROR", f"高德IP定位异常: {str(e)}")
            return None

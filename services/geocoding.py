"""
地理编码服务
使用Nominatim进行地点搜索和反向地理编码
"""

from geopy.geocoders import Nominatim
from typing import Optional, Callable


class GeocodingService:
    """地理编码服务，负责地点搜索"""

    def __init__(self, logger: Optional[Callable] = None):
        self.geolocator = Nominatim(
            user_agent="gpx_studio",
            timeout=10,
            domain='nominatim.openstreetmap.org'
        )
        self.logger = logger

    def log(self, level: str, message: str):
        """输出日志"""
        if self.logger:
            self.logger(level, message)

    def search_location(self, search_text):
        """
        搜索地点，使用多种策略提高搜索成功率

        Args:
            search_text: 搜索文本

        Returns:
            list: 搜索结果列表，如果未找到则返回None
        """
        locations = None

        def log_cb(level, message):
            if self.logger:
                self.logger(level, message)

        # 多种搜索策略
        search_strategies = [
            {'text': search_text, 'lang': None},
            {'text': search_text, 'lang': 'zh'},
            {'text': search_text + ' 中国', 'lang': None},
            {'text': search_text + ' China', 'lang': None},
            {'text': search_text + ' 省', 'lang': 'zh'},
        ]

        for i, strategy in enumerate(search_strategies):
            try:
                log_cb("DEBUG", f"尝试搜索策略 {i+1}: {strategy['text']} (语言: {strategy['lang']})")
                locations = self.geolocator.geocode(
                    strategy['text'],
                    exactly_one=False,
                    limit=5,
                    language=strategy['lang']
                )

                if locations:
                    log_cb("INFO", f"搜索成功，找到 {len(locations)} 个结果")
                    break
            except Exception as e:
                log_cb("WARNING", f"策略 {i+1} 失败: {str(e)}")
                continue

        if not locations:
            log_cb("WARNING", f"未找到地点: {search_text}")

        return locations

    def reverse_geocode(self, lat, lon):
        """
        反向地理编码，根据坐标获取地址信息

        Args:
            lat: 纬度
            lon: 经度

        Returns:
            dict: 地址信息字典
        """
        import urllib.request
        import json

        def log_cb(level, message):
            if self.logger:
                self.logger(level, message)

        try:
            url = f'https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&accept-language=zh-CN'
            log_cb("DEBUG", f"反向地理编码请求URL: {url}")
            response = urllib.request.urlopen(url, timeout=5)
            data = json.loads(response.read())
            log_cb("DEBUG", f"反向地理编码响应数据: {data}")

            city = data.get('address', {}).get('city', '')
            if not city:
                city = data.get('address', {}).get('town', '')
            if not city:
                city = data.get('address', {}).get('village', '')
            country = data.get('address', {}).get('country', '')

            log_cb("INFO", f"反向地理编码成功: {city}, {country}")
            return {
                'city': city,
                'country': country,
                'full_address': data.get('display_name', '')
            }
        except Exception as e:
            log_cb("ERROR", f"反向地理编码失败: {str(e)}")
            return None

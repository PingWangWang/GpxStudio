"""
定位辅助工具
提供IP定位等辅助功能
"""

import urllib.request
import json


class LocationHelper:
    """定位辅助工具"""

    @staticmethod
    def get_ip_location():
        """
        使用IP地址获取定位

        Returns:
            dict: 定位信息 {'lat': float, 'lon': float, 'city': str, 'country': str}
                 失败返回None
        """
        try:
            url = 'http://ip-api.com/json/'
            response = urllib.request.urlopen(url, timeout=10)
            data = json.loads(response.read())

            if data.get('status') == 'success':
                return {
                    'lat': data.get('lat'),
                    'lon': data.get('lon'),
                    'city': data.get('city', ''),
                    'country': data.get('country', '')
                }
            return None
        except Exception as e:
            print(f"[IP定位] 失败: {str(e)}")
            return None

    @staticmethod
    def format_coordinates(lat, lon, precision=4):
        """
        格式化坐标显示

        Args:
            lat: 纬度
            lon: 经度
            precision: 精度（小数位数）

        Returns:
            str: 格式化的坐标字符串
        """
        return f"{lat:.{precision}f}, {lon:.{precision}f}"

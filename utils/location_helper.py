"""
定位辅助工具
提供IP定位等辅助功能
"""

import urllib.request
import json
import requests
from typing import Optional, Callable


class LocationHelper:
    """定位辅助工具"""

    @staticmethod
    def get_ip_location(logger: Optional[Callable] = None):
        """
        使用IP地址获取定位

        Args:
            logger: 日志回调函数

        Returns:
            dict: 定位信息 {'lat': float, 'lon': float, 'city': str, 'country': str, 'source': str}
                 失败返回None
        """
        def log(level: str, message: str):
            if logger:
                logger(level, message)

        try:
            url = 'http://ip-api.com/json/'
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('status') == 'success':
                log("INFO", f"IP定位成功: {data.get('city', '')}, {data.get('country', '')}")
                return {
                    'lat': data.get('lat'),
                    'lon': data.get('lon'),
                    'city': data.get('city', ''),
                    'country': data.get('country', ''),
                    'region': data.get('regionName', ''),
                    'isp': data.get('isp', ''),
                    'source': 'ip_api'
                }
            log("WARNING", f"IP定位失败: {data.get('message', '未知错误')}")
            return None
        except requests.exceptions.RequestException as e:
            log("ERROR", f"网络请求失败: {str(e)}")
            return None
        except Exception as e:
            log("ERROR", f"IP定位失败: {str(e)}")
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

    @staticmethod
    def extract_coords(location_result):
        """
        从定位结果中提取坐标

        Args:
            location_result: 定位结果字典

        Returns:
            tuple: (纬度, 经度) 或 None
        """
        if location_result and 'lat' in location_result and 'lon' in location_result:
            return (location_result['lat'], location_result['lon'])
        return None

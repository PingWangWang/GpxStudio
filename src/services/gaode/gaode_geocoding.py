"""
高德地图地理编码服务模块

该模块实现了高德地图地理编码服务的封装，提供以下功能：
1. 地点搜索：根据关键词搜索地点信息
2. 反向地理编码：根据经纬度获取地址信息
3. IP定位：根据IP地址获取地理位置信息
4. 签名生成：支持安全密钥签名验证

依赖：
- requests：用于发送HTTP请求
- hashlib：用于生成MD5签名
- json：用于解析API响应
- typing：用于类型注解

接口规范遵循高德地图Web服务API官方文档：
- 地点搜索：https://lbs.amap.com/api/webservice/guide/api/search
- 反向地理编码：https://lbs.amap.com/api/webservice/guide/api/georegeo
- IP定位：https://lbs.amap.com/api/webservice/guide/api/ipconfig
"""

import requests
import hashlib
import json
from typing import Optional, Callable, List, Dict

from services.interfaces.geocoding_service import IGeocodingService


class GaodeGeocodingService(IGeocodingService):
    """高德地图地理编码服务实现类

    该类实现了IGeocodingService接口，封装了高德地图地理编码相关的API调用
    """

    # 地点搜索API地址
    GEOCODE_URL = "https://restapi.amap.com/v3/place/text"

    # 反向地理编码API地址
    REVERSE_GEOCODE_URL = "https://restapi.amap.com/v3/geocode/regeo"

    # IP定位API地址
    IP_LOCATION_URL = "https://restapi.amap.com/v3/ip"

    def __init__(self, api_key: str = "", security_key: str = "", logger: Optional[Callable] = None):
        """
        初始化高德地理编码服务

        Args:
            api_key (str): 高德地图Web服务API密钥
            security_key (str): 高德地图安全密钥（可选，用于生成签名）
            logger (Callable): 日志记录回调函数，格式为logger(level: str, message: str)
        """
        # 存储API密钥
        self.api_key = api_key
        # 存储安全密钥（用于签名生成）
        self.security_key = security_key
        # 存储日志记录器
        self.logger = logger

    def log(self, level: str, message: str):
        """
        记录日志信息

        Args:
            level (str): 日志级别，如"DEBUG", "INFO", "WARNING", "ERROR"
            message (str): 日志内容
        """
        if self.logger:
            self.logger(level, message)

    def _sign(self, params: dict) -> str:
        """
        根据高德地图API签名规则生成请求签名

        签名生成规则（遵循高德官方文档）：
        1. 将请求参数按键名升序排列
        2. 将安全密钥作为前缀
        3. 拼接所有"key+value"字符串
        4. 使用MD5加密生成32位小写十六进制签名

        Args:
            params (dict): 请求参数字典

        Returns:
            str: 生成的签名字符串，安全密钥为空时返回空字符串
        """
        if not self.security_key:
            return ""

        # 1. 参数按键名升序排序
        sorted_params = sorted(params.items())

        # 2. 拼接安全密钥和参数键值对
        sign_str = self.security_key + ''.join(f"{k}{v}" for k, v in sorted_params)

        # 3. 生成MD5签名并返回
        return hashlib.md5(sign_str.encode()).hexdigest()

    def search_location(self, search_text: str) -> Optional[List[dict]]:
        """
        根据关键词搜索地点信息

        使用高德地图地点搜索API，根据输入的关键词搜索相关地点，并返回格式化的结果列表

        Args:
            search_text (str): 搜索关键词，可以是地点名称、地址等

        Returns:
            Optional[List[dict]]: 搜索结果列表，每个结果包含以下字段：
                - name: 地点名称
                - address: 地点地址
                - lat: 纬度（float）
                - lon: 经度（float）
                - type: 地点类型
                - level: 地点类型编码
            搜索失败或无结果时返回None
        """
        def log_cb(level, message):
            if self.logger:
                self.logger(level, message)

        if not self.api_key:
            log_cb("WARNING", "高德地图API Key未配置")
            return None

        try:
            log_cb("DEBUG", f"搜索地点: {search_text}")

            # 构建请求参数
            params = {
                'key': self.api_key,                 # API密钥
                'keywords': search_text,              # 搜索关键词
                'city': '全国',                       # 搜索城市范围，全国表示不限制
                'citylimit': 'false',                 # 是否限制在指定城市内搜索
                'output': 'json',                     # 返回格式为JSON
                'offset': 10,                         # 每页结果数
                'page': 1,                            # 页码
                'extensions': 'all'                   # 获取详细信息（包含边界、入口等）
            }

            # 如果配置了安全密钥，生成签名
            if self.security_key:
                params['sig'] = self._sign(params)

            # 发送GET请求到高德地点搜索API
            response = requests.get(self.GEOCODE_URL, params=params, timeout=10)
            # 解析JSON响应
            data = response.json()

            # 检查请求是否成功（status=1表示成功）且返回了POI数据
            if data.get('status') == '1' and data.get('pois'):
                results = []

                # 处理前5个搜索结果
                for poi in data['pois'][:5]:
                    # 解析经纬度信息（格式："lon,lat"）
                    location = poi.get('location', '').split(',')
                    if len(location) == 2:
                        # 解析入口坐标（用于计算POI范围）
                        entr_location_str = poi.get('entr_location', '')
                        entr_lat, entr_lon = None, None
                        if entr_location_str and ',' in entr_location_str:
                            entr_parts = entr_location_str.split(',')
                            if len(entr_parts) == 2:
                                try:
                                    entr_lon = float(entr_parts[0])
                                    entr_lat = float(entr_parts[1])
                                except ValueError:
                                    pass

                        # 计算POI半径（中心到入口的距离，单位：米）
                        poi_radius = None
                        if entr_lat is not None and entr_lon is not None:
                            poi_radius = self._calculate_distance(
                                float(location[1]), float(location[0]),
                                entr_lat, entr_lon
                            )

                        # 构造结果字典
                        results.append({
                            'name': poi.get('name', ''),                      # 地点名称
                            'address': poi.get('address', '') or poi.get('pname', '') + poi.get('city', ''),  # 地点地址
                            'lat': float(location[1]),                          # 纬度
                            'lon': float(location[0]),                          # 经度
                            'type': poi.get('type', ''),                        # 地点类型
                            'level': poi.get('typecode', ''),                   # 地点类型编码
                            'radius': poi_radius                                # POI半径（米）
                        })

                log_cb("INFO", f"搜索成功，找到 {len(results)} 个结果")
                return results
            else:
                # 获取错误信息
                error_msg = data.get('info', '未知错误')
                log_cb("WARNING", f"搜索失败: {error_msg}")
                return None

        except Exception as e:
            # 捕获网络异常、JSON解析异常等
            log_cb("ERROR", f"搜索异常: {str(e)}")
            return None

    @staticmethod
    def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        使用Haversine公式计算两点之间的距离（单位：米）

        Args:
            lat1: 第一个点的纬度
            lon1: 第一个点的经度
            lat2: 第二个点的纬度
            lon2: 第二个点的经度

        Returns:
            float: 两点之间的距离（米）
        """
        from math import radians, sin, cos, sqrt, atan2

        # 地球平均半径（千米）
        R = 6371.0

        # 将角度转换为弧度
        lat1_rad = radians(lat1)
        lon1_rad = radians(lon1)
        lat2_rad = radians(lat2)
        lon2_rad = radians(lon2)

        # 计算差值
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        # Haversine公式
        a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        # 计算距离（米）
        distance = R * c * 1000

        return distance

    def reverse_geocode(self, lat: float, lon: float) -> Optional[dict]:
        """
        根据经纬度进行反向地理编码

        使用高德地图反向地理编码API，根据输入的经纬度获取详细的地址信息

        Args:
            lat (float): 纬度
            lon (float): 经度

        Returns:
            Optional[dict]: 地址信息字典，包含以下字段：
                - city: 城市名称
                - full_address: 格式化的完整地址
            编码失败时返回None
        """
        def log_cb(level, message):
            if self.logger:
                self.logger(level, message)

        if not self.api_key:
            log_cb("WARNING", "高德地图API Key未配置")
            return None

        try:
            log_cb("DEBUG", f"反向地理编码: {lat}, {lon}")

            # 构建请求参数
            params = {
                'key': self.api_key,                 # API密钥
                'location': f"{lon},{lat}",          # 经纬度坐标，格式："lon,lat"
                'output': 'json',                     # 返回格式为JSON
                'radius': 100                        # 搜索半径（米）
            }

            # 如果配置了安全密钥，生成签名
            if self.security_key:
                params['sig'] = self._sign(params)

            # 发送GET请求到高德反向地理编码API
            response = requests.get(self.REVERSE_GEOCODE_URL, params=params, timeout=10)
            # 解析JSON响应
            data = response.json()

            # 检查请求是否成功
            if data.get('status') == '1':
                # 获取反向地理编码结果
                regeocode = data.get('regeocode', {})

                # 获取格式化地址
                address = regeocode.get('formatted_address', '')

                # 获取城市信息，如果城市为空则使用区县信息
                city = regeocode.get('addressComponent', {}).get('city', '') or \
                       regeocode.get('addressComponent', {}).get('district', '')

                # 构造结果字典
                result = {
                    'city': city,                # 城市名称
                    'full_address': address      # 完整地址
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
        使用高德地图IP定位API获取当前IP的地理位置

        该方法会获取发送请求的客户端IP地址对应的地理位置信息

        Returns:
            Optional[dict]: 定位信息字典，包含以下字段：
                - lat: 纬度（float）
                - lon: 经度（float）
                - city: 城市名称
                - province: 省份名称
                - adcode: 行政区划代码
                - source: 数据源标识（固定为"gaode_ip"）
            定位失败时返回None
        """
        def log_cb(level, message):
            if self.logger:
                self.logger(level, message)

        if not self.api_key:
            log_cb("WARNING", "高德地图API Key未配置，无法使用IP定位")
            return None

        try:
            log_cb("DEBUG", "正在使用高德地图IP定位...")

            # 构建请求参数
            params = {
                'key': self.api_key,                 # API密钥
                'output': 'json'                     # 返回格式为JSON
                # 注意：未指定ip参数时，默认使用请求者的IP地址
            }

            # 如果配置了安全密钥，生成签名
            if self.security_key:
                params['sig'] = self._sign(params)

            # 发送GET请求到高德IP定位API
            response = requests.get(self.IP_LOCATION_URL, params=params, timeout=10)
            # 解析JSON响应
            data = response.json()

            # 检查请求是否成功
            if data.get('status') == '1':
                # 获取行政区划代码
                adcode = data.get('adcode', '')

                # 获取定位矩形区域（格式："min_lon,min_lat;max_lon,max_lat"）
                rectangle = data.get('rectangle', '')

                if rectangle:
                    # 解析矩形区域坐标
                    coords = rectangle.split(';')
                    if len(coords) == 2:
                        # 获取左下角和右上角坐标
                        lon1, lat1 = coords[0].split(',')
                        lon2, lat2 = coords[1].split(',')

                        # 计算矩形区域中心点坐标作为定位结果
                        center_lon = (float(lon1) + float(lon2)) / 2
                        center_lat = (float(lat1) + float(lat2)) / 2

                        log_cb("INFO", f"高德IP定位成功: {data.get('city', '')}")

                        # 返回定位结果
                        return {
                            'lat': center_lat,               # 纬度
                            'lon': center_lon,               # 经度
                            'city': data.get('city', ''),    # 城市名称
                            'province': data.get('province', ''),  # 省份名称
                            'adcode': adcode,                # 行政区划代码
                            'source': 'gaode_ip'             # 数据源标识
                        }

                # 未获取到有效坐标信息
                log_cb("WARNING", "高德IP定位未返回有效坐标")
                return None
            else:
                # 获取错误信息
                error_msg = data.get('info', '未知错误')
                log_cb("WARNING", f"高德IP定位失败: {error_msg}")
                return None

        except Exception as e:
            # 捕获网络异常、JSON解析异常等
            log_cb("ERROR", f"高德IP定位异常: {str(e)}")
            return None

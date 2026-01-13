"""
OSM地理编码服务
使用Nominatim API实现OSM地图的地点搜索和反向地理编码功能
"""

import requests
from typing import Optional, List, Dict, Callable
from services.interfaces.geocoding_service import IGeocodingService


class OsmGeocodingService(IGeocodingService):
    """
    OSM地理编码服务
    使用Nominatim API实现地理编码功能
    """

    def __init__(self, api_key: str = "", security_key: str = "", logger: Optional[Callable] = None):
        """
        初始化OSM地理编码服务

        Args:
            api_key: API密钥（OSM不需要，保留参数以兼容接口）
            security_key: 安全密钥（OSM不需要，保留参数以兼容接口）
            logger: 日志记录器函数，接收(level, message)参数
        """
        self.logger = logger
        self.base_url = "https://nominatim.openstreetmap.org"
        # Nominatim要求提供有效的User-Agent，包含应用名称和联系方式
        # 参考：https://operations.osmfoundation.org/policies/nominatim/
        self.headers = {
            "User-Agent": "GPXStudio/1.2.0 (Route Planning Application; https://github.com/gpxstudio)",
            "Referer": "https://github.com/gpxstudio"
        }
        import time
        self.last_request_time = 0
        self.min_request_interval = 1.5  # 最小请求间隔，单位秒，增加到1.5秒更安全

    def _log(self, level: str, message: str):
        """
        记录日志

        Args:
            level: 日志级别
            message: 日志消息
        """
        if self.logger:
            self.logger(level, message)

    def search_location(self, search_text: str) -> Optional[List[Dict]]:
        """
        使用Nominatim API搜索地点

        Args:
            search_text: 搜索文本

        Returns:
            list: 搜索结果列表，每个结果包含name, address, lat, lon
        """
        try:
            # 多种搜索策略，提高搜索成功率
            search_strategies = [
                {'text': search_text, 'lang': None},
                {'text': search_text, 'lang': 'zh'},
                {'text': search_text + ' 中国', 'lang': None},
                {'text': search_text + ' China', 'lang': None},
                {'text': search_text + ' 省', 'lang': 'zh'},
            ]

            for i, strategy in enumerate(search_strategies):
                try:
                    # 控制请求间隔
                    import time
                    current_time = time.time()
                    time_since_last_request = current_time - self.last_request_time
                    if time_since_last_request < self.min_request_interval:
                        time_to_wait = self.min_request_interval - time_since_last_request
                        time.sleep(time_to_wait)
                    self.last_request_time = time.time()

                    params = {
                        "q": strategy['text'],
                        "format": "json",
                        "limit": 10,
                        "addressdetails": 1
                    }

                    # 添加语言参数
                    if strategy['lang']:
                        params['accept-language'] = strategy['lang']

                    self._log("INFO", f"OSM搜索请求 {i+1}/{len(search_strategies)}: {strategy['text']} (语言: {strategy['lang']})")
                    response = requests.get(
                        f"{self.base_url}/search",
                        params=params,
                        headers=self.headers,
                        timeout=15
                    )

                    if response.status_code == 200:
                        results = response.json()
                        if results:
                            formatted_results = []
                            for item in results:
                                name = item.get('display_name', '')
                                lat = float(item.get('lat', 0))
                                lon = float(item.get('lon', 0))

                                # 构建地址信息
                                address_parts = []
                                address = item.get('address', {})

                                # 优先获取具体地点名称
                                if 'name' in address:
                                    name = address['name']
                                    address_parts.append(address.get('house_number', ''))
                                    address_parts.append(address.get('road', ''))
                                elif 'shop' in address:
                                    name = address['shop']
                                    address_parts.append(address.get('house_number', ''))
                                    address_parts.append(address.get('road', ''))
                                elif 'amenity' in address:
                                    name = address['amenity']
                                    address_parts.append(address.get('house_number', ''))
                                    address_parts.append(address.get('road', ''))

                                # 添加其他地址信息
                                address_parts.append(address.get('suburb', ''))
                                address_parts.append(address.get('city', ''))
                                address_parts.append(address.get('county', ''))
                                address_parts.append(address.get('state', ''))
                                address_parts.append(address.get('country', ''))

                                # 过滤空值
                                address_parts = [part for part in address_parts if part]
                                full_address = ", ".join(address_parts)

                                # 如果没有具体名称，使用完整地址作为名称
                                if not name:
                                    name = full_address

                                formatted_results.append({
                                    'name': name,
                                    'address': full_address,
                                    'lat': lat,
                                    'lon': lon,
                                    'level': self._get_location_level(address),
                                    'type': self._get_location_type(address)
                                })

                            self._log("INFO", f"OSM搜索成功，找到{len(formatted_results)}个结果")
                            return formatted_results
                    elif response.status_code == 418:
                        # 418 I'm a teapot - Nominatim的速率限制或User-Agent问题
                        # 参考：https://operations.osmfoundation.org/policies/nominatim/
                        self._log("WARNING", f"OSM搜索被限流(418) - Nominatim要求每秒最多1个请求")
                        self._log("INFO", f"当前User-Agent: {self.headers.get('User-Agent')}")
                        self._log("INFO", "等待5秒后重试...")
                        # 增加等待时间到5秒
                        time.sleep(5)
                        # 更新最后请求时间
                        self.last_request_time = time.time()
                        continue
                    else:
                        self._log("WARNING", f"OSM搜索请求失败: {response.status_code}")
                        # 继续尝试下一个策略
                        continue
                except Exception as e:
                    self._log("WARNING", f"OSM搜索策略 {i+1} 失败: {str(e)}")
                    # 继续尝试下一个策略
                    continue

            # 所有策略都失败了
            self._log("INFO", "OSM搜索无结果")
            return []
        except Exception as e:
            self._log("ERROR", f"OSM搜索异常: {str(e)}")
            return []

    def reverse_geocode(self, lat: float, lon: float) -> Optional[Dict]:
        """
        使用Nominatim API进行反向地理编码

        Args:
            lat: 纬度
            lon: 经度

        Returns:
            dict: 地址信息，包含name, address, lat, lon
        """
        try:
            # 控制请求间隔
            import time
            current_time = time.time()
            time_since_last_request = current_time - self.last_request_time
            if time_since_last_request < self.min_request_interval:
                time_to_wait = self.min_request_interval - time_since_last_request
                time.sleep(time_to_wait)
            self.last_request_time = time.time()

            params = {
                "lat": lat,
                "lon": lon,
                "format": "json",
                "addressdetails": 1
            }

            self._log("INFO", f"OSM反向地理编码请求: {lat}, {lon}")
            response = requests.get(
                f"{self.base_url}/reverse",
                params=params,
                headers=self.headers,
                timeout=15
            )

            if response.status_code == 200:
                result = response.json()
                if result:
                    address = result.get('address', {})
                    name = result.get('display_name', '')

                    # 构建地址信息
                    address_parts = []
                    address_parts.append(address.get('house_number', ''))
                    address_parts.append(address.get('road', ''))
                    address_parts.append(address.get('suburb', ''))
                    address_parts.append(address.get('city', ''))
                    address_parts.append(address.get('county', ''))
                    address_parts.append(address.get('state', ''))
                    address_parts.append(address.get('country', ''))

                    # 过滤空值
                    address_parts = [part for part in address_parts if part]
                    full_address = ", ".join(address_parts)

                    # 如果没有具体名称，使用完整地址作为名称
                    if not name:
                        name = full_address

                    return {
                        'name': name,
                        'address': full_address,
                        'lat': lat,
                        'lon': lon,
                        'level': self._get_location_level(address),
                        'type': self._get_location_type(address)
                    }
                else:
                    self._log("INFO", "OSM反向地理编码无结果")
                    return None
            elif response.status_code == 418:
                self._log("WARNING", f"OSM反向地理编码被限流(418) - Nominatim要求每秒最多1个请求")
                self._log("INFO", f"当前User-Agent: {self.headers.get('User-Agent')}")
                self._log("INFO", "请稍后再试，或检查网络连接")
                return None
            else:
                self._log("ERROR", f"OSM反向地理编码请求失败: {response.status_code}")
                return None
        except Exception as e:
            self._log("ERROR", f"OSM反向地理编码异常: {str(e)}")
            return None

    def get_ip_location(self) -> Optional[Dict]:
        """
        使用IP定位获取当前位置
        OSM Nominatim不直接提供IP定位，这里返回None

        Returns:
            dict: 定位信息 {'lat': float, 'lon': float, 'city': str, 'source': str}
                 失败返回None
        """
        self._log("INFO", "OSM不支持IP定位")
        return None

    def _get_location_level(self, address: Dict) -> str:
        """
        根据地址信息获取地点级别

        Args:
            address: 地址信息字典

        Returns:
            str: 地点级别
        """
        if 'house_number' in address:
            return "建筑物"
        elif 'road' in address:
            return "街道"
        elif 'suburb' in address:
            return "社区"
        elif 'city' in address:
            return "城市"
        elif 'county' in address:
            return "县"
        elif 'state' in address:
            return "省"
        elif 'country' in address:
            return "国家"
        else:
            return "未知"

    def _get_location_type(self, address: Dict) -> str:
        """
        根据地址信息获取地点类型

        Args:
            address: 地址信息字典

        Returns:
            str: 地点类型
        """
        if 'shop' in address:
            return "商店"
        elif 'amenity' in address:
            return "公共设施"
        elif 'building' in address:
            return "建筑物"
        elif 'highway' in address:
            return "道路"
        elif 'natural' in address:
            return "自然地物"
        elif 'landuse' in address:
            return "土地利用"
        else:
            return "未知"

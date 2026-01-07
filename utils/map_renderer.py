"""
地图渲染工具
使用Folium生成HTML地图
"""

import folium
from folium.plugins import FloatImage
import tempfile
from PyQt5.QtCore import QUrl

from .gaode_tiles import GaodeTileService


class MapRenderer:
    """地图渲染工具，负责生成和显示地图"""

    @staticmethod
    def create_base_map(center, zoom_start=10, map_type='roadmap'):
        """
        创建基础地图

        Args:
            center: 中心点 [lat, lon]
            zoom_start: 初始缩放级别
            map_type: 地图类型 ('roadmap', 'satellite', 'hybrid')

        Returns:
            folium.Map: 地图对象
        """
        m = folium.Map(location=center, zoom_start=zoom_start, tiles=None)

        tile_urls = {
            'roadmap': 'https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
            'satellite': 'https://webst01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=6&x={x}&y={y}&z={z}',
            'hybrid': 'https://webst01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}'
        }

        tile_url = tile_urls.get(map_type, tile_urls['roadmap'])

        folium.TileLayer(
            tiles=tile_url,
            attr='© 高德地图',
            name='高德地图',
            overlay=False,
            control=False
        ).add_to(m)

        scale_control = """
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(function() {
                var mapElement = document.querySelector('.leaflet-container');
                if (mapElement && mapElement._leaflet_map) {
                    L.control.scale({
                        position: 'bottomright',
                        imperial: false,
                        metric: true
                    }).addTo(mapElement._leaflet_map);
                }
            }, 500);
        });
        </script>
        """
        m.get_root().html.add_child(folium.Element(scale_control))

        return m

    @staticmethod
    def add_marker(map_obj, location, popup_text, color='blue', icon='info-sign'):
        """
        添加标记点

        Args:
            map_obj: folium地图对象
            location: 位置 [lat, lon]
            popup_text: 弹出文本
            color: 颜色
            icon: 图标
        """
        folium.Marker(
            location=location,
            popup=popup_text,
            icon=folium.Icon(color=color, icon=icon)
        ).add_to(map_obj)

    @staticmethod
    def add_route(map_obj, route_points, color='blue', weight=5, opacity=0.7):
        """
        添加路线

        Args:
            map_obj: folium地图对象
            route_points: 路线点列表，None表示段分隔
            color: 线条颜色
            weight: 线条宽度
            opacity: 透明度
        """
        route_segment = []
        for point in route_points:
            if point is None:
                if len(route_segment) > 1:
                    folium.PolyLine(
                        locations=route_segment,
                        color=color,
                        weight=weight,
                        opacity=opacity
                    ).add_to(map_obj)
                route_segment = []
            else:
                route_segment.append(point)

        # 处理最后一个段
        if len(route_segment) > 1:
            folium.PolyLine(
                locations=route_segment,
                color=color,
                weight=weight,
                opacity=opacity
            ).add_to(map_obj)

    @staticmethod
    def save_and_get_url(map_obj, use_http_server=False):
        """
        保存地图到临时文件并返回URL

        Args:
            map_obj: folium地图对象
            use_http_server: 是否使用HTTP服务器（解决地理定位限制）

        Returns:
            QUrl: 本地文件URL或HTTP URL
        """
        if use_http_server:
            from .http_server import get_map_server
            import uuid
            server = get_map_server()
            filename = f"map_{uuid.uuid4().hex[:8]}.html"
            url_str = server.save_map(map_obj, filename)
            return QUrl(url_str)
        else:
            html_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
            map_obj.save(html_file.name)
            return QUrl.fromLocalFile(html_file.name)

    @staticmethod
    def calculate_zoom_level(points):
        """
        根据点的范围计算合适的缩放级别

        Args:
            points: 坐标点列表 [(lat, lon), ...]

        Returns:
            int: 缩放级别
        """
        if not points:
            return 10

        valid_points = [p for p in points if p is not None]
        if not valid_points:
            return 10

        min_lat = min(p[0] for p in valid_points)
        max_lat = max(p[0] for p in valid_points)
        min_lon = min(p[1] for p in valid_points)
        max_lon = max(p[1] for p in valid_points)

        lat_diff = max_lat - min_lat
        lon_diff = max_lon - min_lon
        max_diff = max(lat_diff, lon_diff)

        if max_diff < 0.01:
            return 14
        elif max_diff < 0.1:
            return 12
        elif max_diff < 0.5:
            return 10
        elif max_diff < 1:
            return 8
        elif max_diff < 2:
            return 6
        else:
            return 4

    @staticmethod
    def add_geolocation_script(map_obj):
        """
        添加浏览器定位脚本

        Args:
            map_obj: folium地图对象
        """
        geolocation_script = """
        <script>
        console.log('[初始化] 定位脚本已加载');
        console.log('[初始化] 页面协议: ' + window.location.protocol);
        console.log('[初始化] 页面URL: ' + window.location.href);

        function getLocation() {
            console.log('[定位] 开始定位...');
            console.log('[定位] navigator.geolocation 可用性: ' + (!!navigator.geolocation));

            if (navigator.geolocation) {
                console.log('[定位] 浏览器支持定位，准备调用getCurrentPosition');

                var options = {
                    enableHighAccuracy: true,
                    timeout: 30000,
                    maximumAge: 0
                };
                console.log('[定位] 定位选项: ' + JSON.stringify(options));

                navigator.geolocation.getCurrentPosition(
                    function(position) {
                        console.log('[定位] ✅ 定位回调触发 - 成功');
                        var lat = position.coords.latitude;
                        var lon = position.coords.longitude;
                        var accuracy = position.coords.accuracy;

                        // 使用处理器期望的格式输出日志
                        console.log('定位成功: ' + lat + ', ' + lon + ', ' + accuracy);

                        // 在地图上显示标记
                        if (window.map) {
                            var marker = L.marker([lat, lon]).addTo(window.map);
                            marker.bindPopup('我的位置<br>定位方式: 电脑定位服务<br>精度: ' + Math.round(accuracy) + ' 米').openPopup();
                            window.map.setView([lat, lon], 13);
                        }
                    },
                    function(error) {
                        console.log('[定位] ❌ 定位回调触发 - 失败');
                        console.log('[定位] 错误代码: ' + error.code);
                        console.log('[定位] 错误消息: ' + error.message);

                        var errorMsg = '';
                        switch(error.code) {
                            case error.PERMISSION_DENIED:
                                errorMsg = '用户拒绝了定位请求 (code: 1)';
                                break;
                            case error.POSITION_UNAVAILABLE:
                                errorMsg = '位置信息不可用 (code: 2)';
                                break;
                            case error.TIMEOUT:
                                errorMsg = '请求超时，请检查网络连接或定位权限 (code: 3)';
                                break;
                            default:
                                errorMsg = '未知错误 (code: ' + error.code + '): ' + error.message;
                                break;
                        }
                        // 使用处理器期望的格式输出错误日志
                        console.log('定位失败: ' + errorMsg);
                    },
                    options
                );

                console.log('[定位] getCurrentPosition 已调用，等待回调...');
            } else {
                console.log('定位失败: 浏览器不支持定位');
            }
        }

        document.addEventListener('DOMContentLoaded', function() {
            console.log('[定位] DOM加载完成');
            setTimeout(function() {
                var container = document.querySelector('.leaflet-container');
                if (container && container._leaflet_map) {
                    window.map = container._leaflet_map;
                    console.log('[定位] 地图对象获取成功，开始定位');
                    getLocation();
                } else {
                    console.log('定位失败: 无法获取地图对象');
                }
            }, 1000);
        });
        </script>
        """
        map_obj.get_root().html.add_child(folium.Element(geolocation_script))

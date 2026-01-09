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

    ZOOM_LEVELS = {
        'country': 4,
        'province': 7,
        'city': 10,
        'district': 12,
        'street': 15,
        'community': 17,
        'building': 18,
        'poi': 16
    }

    @staticmethod
    def get_zoom_by_level(level_info: str = None, type_info: str = None) -> int:
        """
        根据地址类型获取合适的缩放级别

        Args:
            level_info: 高德返回的地址级别信息
            type_info: POI类型信息

        Returns:
            int: 缩放级别
        """
        if not level_info and not type_info:
            return 12

        level_lower = (level_info or '').lower()
        type_lower = (type_info or '').lower()

        if any(kw in level_lower for kw in ['国家', 'country']):
            return MapRenderer.ZOOM_LEVELS['country']
        elif any(kw in level_lower for kw in ['省', 'province']):
            return MapRenderer.ZOOM_LEVELS['province']
        elif any(kw in level_lower for kw in ['市', 'city', '自治区']):
            return MapRenderer.ZOOM_LEVELS['city']
        elif any(kw in level_lower for kw in ['区', '县', 'district', 'county']):
            return MapRenderer.ZOOM_LEVELS['district']
        elif any(kw in level_lower for kw in ['街道', '路', 'street', 'road']):
            return MapRenderer.ZOOM_LEVELS['street']
        elif any(kw in level_lower for kw in ['社区', '小区', 'community', 'residential']):
            return MapRenderer.ZOOM_LEVELS['community']
        elif any(kw in level_lower for kw in ['楼', '建筑', 'building']):
            return MapRenderer.ZOOM_LEVELS['building']
        elif any(kw in type_lower for kw in ['兴趣点', 'poi', '餐饮', '购物', '酒店', '医院', '学校']):
            return MapRenderer.ZOOM_LEVELS['poi']
        elif any(kw in type_lower for kw in ['住宅', '住宅区', 'community']):
            return MapRenderer.ZOOM_LEVELS['community']

        return 14

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

        scroll_zoom_script = """
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            var checkCount = 0;
            var maxChecks = 30;
            var checkInterval = setInterval(function() {
                checkCount++;
                // 查找以map_开头的全局变量
                var map = null;
                for (var key in window) {
                    if (key.startsWith('map_') && window[key] && window[key].scrollWheelZoom) {
                        map = window[key];
                        break;
                    }
                }
                if (map) {
                    clearInterval(checkInterval);
                    map.scrollWheelZoom.enable();
                    console.log('[地图] 滚轮缩放已启用');
                } else if (checkCount >= maxChecks) {
                    clearInterval(checkInterval);
                    console.log('[地图] 滚轮缩放启用超时');
                }
            }, 100);
        });
        </script>
        """
        m.get_root().html.add_child(folium.Element(scroll_zoom_script))

        scale_script = """
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            var checkCount = 0;
            var maxChecks = 20;
            var checkInterval = setInterval(function() {
                checkCount++;
                var mapElement = document.querySelector('.leaflet-container');
                if (mapElement && mapElement._leaflet_map) {
                    clearInterval(checkInterval);
                    var map = mapElement._leaflet_map;
                    if (!map.hasControl('scale')) {
                        L.control.scale({
                            position: 'bottomright',
                            imperial: false,
                            metric: true
                        }).addTo(map);
                    }
                } else if (checkCount >= maxChecks) {
                    clearInterval(checkInterval);
                }
            }, 100);
        });
        </script>
        """
        m.get_root().html.add_child(folium.Element(scale_script))

        # 添加缩放监听脚本
        zoom_listener_script = """
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            var checkCount = 0;
            var maxChecks = 50;
            var checkInterval = setInterval(function() {
                checkCount++;
                // 查找以map_开头的全局变量
                var map = null;
                for (var key in window) {
                    if (key.startsWith('map_') && window[key] && window[key].getZoom) {
                        map = window[key];
                        break;
                    }
                }
                if (map) {
                    clearInterval(checkInterval);

                    // 初始化缩放级别并立即发送
                    var currentZoom = map.getZoom();
                    console.log('[地图缩放] 初始缩放级别: ' + currentZoom);
                    console.log('缩放变化:' + currentZoom);

                    // 监听缩放结束事件
                    map.on('zoomend', function() {
                        var newZoom = map.getZoom();
                        console.log('[地图缩放] 缩放级别变化: ' + newZoom);
                        // 输出格式化消息供Qt应用捕获
                        console.log('缩放变化:' + newZoom);
                    });

                    // 监听缩放开始事件
                    map.on('zoomstart', function() {
                        console.log('[地图缩放] 开始缩放操作');
                    });
                } else if (checkCount >= maxChecks) {
                    clearInterval(checkInterval);
                    console.log('[地图缩放] 初始化超时');
                }
            }, 100);
        });
        </script>
        """
        m.get_root().html.add_child(folium.Element(zoom_listener_script))

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
    def fit_bounds(map_obj, points):
        """
        自动调整地图以显示所有点

        Args:
            map_obj: folium地图对象
            points: 坐标点列表 [(lat, lon), ...]
        """
        valid_points = [p for p in points if p is not None]
        if not valid_points:
            return

        min_lat = min(p[0] for p in valid_points)
        max_lat = max(p[0] for p in valid_points)
        min_lon = min(p[1] for p in valid_points)
        max_lon = max(p[1] for p in valid_points)

        lat_diff = max_lat - min_lat
        lon_diff = max_lon - min_lon
        max_diff = max(lat_diff, lon_diff)

        if max_diff < 0.001:
            max_zoom = 18
            min_zoom = 17
        elif max_diff < 0.005:
            max_zoom = 18
            min_zoom = 16
        elif max_diff < 0.01:
            max_zoom = 17
            min_zoom = 15
        elif max_diff < 0.02:
            max_zoom = 17
            min_zoom = 14
        elif max_diff < 0.05:
            max_zoom = 16
            min_zoom = 13
        elif max_diff < 0.1:
            max_zoom = 15
            min_zoom = 12
        elif max_diff < 0.2:
            max_zoom = 14
            min_zoom = 11
        elif max_diff < 0.5:
            max_zoom = 13
            min_zoom = 10
        elif max_diff < 1:
            max_zoom = 12
            min_zoom = 9
        elif max_diff < 2:
            max_zoom = 10
            min_zoom = 7
        elif max_diff < 5:
            max_zoom = 9
            min_zoom = 6
        elif max_diff < 10:
            max_zoom = 8
            min_zoom = 5
        elif max_diff < 20:
            max_zoom = 7
            min_zoom = 4
        else:
            max_zoom = 5
            min_zoom = 3

        bounds = [[min_lat, min_lon], [max_lat, max_lon]]

        # 使用更简单的方式生成JavaScript脚本，避免语法错误
        from folium import Element

        # 创建一个简单的fit_bounds调用，使用folium的内置功能
        # folium已经有fit_bounds方法，我们可以直接使用它
        # 这里我们增加一个延迟执行，确保路线绘制完成
        map_obj.fit_bounds([(min_lat, min_lon), (max_lat, max_lon)], padding=(80, 80))

        # 添加额外的JavaScript来确保地图正确显示
        extra_script = Element('''
        <script>
        // 延迟执行，确保路线绘制完成后再调整一次
        setTimeout(function() {
            var mapElement = document.querySelector('.leaflet-container');
            if (mapElement && mapElement._leaflet_map) {
                // 重新获取当前地图边界并应用
                var bounds = mapElement._leaflet_map.getBounds();
                mapElement._leaflet_map.fitBounds(bounds, { padding: [80, 80] });
                console.log('[地图] 二次边界调整完成');
            }
        }, 1500);
        </script>
        ''')

        map_obj.get_root().html.add_child(extra_script)

        # 不需要单独的fit_bounds_script，因为我们已经使用了folium的内置fit_bounds方法

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

"""
地图渲染工具
使用Folium生成HTML地图
"""

import folium
from folium.plugins import FloatImage
import tempfile
from PyQt5.QtCore import QUrl

from .gaode_tiles import GaodeTileService
from services.config.map_config import map_config


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
    def _calculate_zoom_from_radius(radius: float) -> int:
        """
        根据POI半径计算合适的缩放级别

        策略：确保POI在视野中占据合理比例（约50-70%）

        高德地图缩放级别对应的地面距离参考（赤道附近）：
        - zoom 3:  40,000 km (全球视野)
        - zoom 4:  20,000 km (洲级)
        - zoom 5:  10,000 km
        - zoom 6:  5,000 km
        - zoom 7:  2,500 km (省级)
        - zoom 8:  1,250 km
        - zoom 9:  625 km
        - zoom 10: 312 km (市级)
        - zoom 11: 156 km
        - zoom 12: 78 km (区级)
        - zoom 13: 39 km
        - zoom 14: 19.5 km
        - zoom 15: 10 km (街道级)
        - zoom 16: 5 km (POI级)
        - zoom 17: 2.5 km (社区级)
        - zoom 18: 1.25 km (建筑级)
        - zoom 19: 625 m
        - zoom 20: 312 m

        Args:
            radius: POI半径（米）

        Returns:
            int: 建议的缩放级别
        """
        if radius is None or radius <= 0:
            return 16  # 默认POI级别

        # 为了让POI占据合理视野（约60%），视野范围应为POI直径的1.5-2倍
        # 视野半径 = POI半径 * 1.5 (留出适当空间)
        view_radius = radius * 1.5

        # 根据视野半径选择缩放级别（单位：米）
        # 每级缩放，视野缩小约一半
        if view_radius >= 20000000:  # > 20000 km
            return 4
        elif view_radius >= 10000000:  # > 10000 km
            return 5
        elif view_radius >= 5000000:   # > 5000 km
            return 6
        elif view_radius >= 2500000:   # > 2500 km
            return 7
        elif view_radius >= 1250000:   # > 1250 km
            return 8
        elif view_radius >= 625000:    # > 625 km
            return 9
        elif view_radius >= 312000:    # > 312 km
            return 10
        elif view_radius >= 156000:    # > 156 km
            return 11
        elif view_radius >= 78000:     # > 78 km
            return 12
        elif view_radius >= 39000:     # > 39 km
            return 13
        elif view_radius >= 19500:     # > 19.5 km
            return 14
        elif view_radius >= 10000:     # > 10 km
            return 15
        elif view_radius >= 5000:      # > 5 km
            return 16
        elif view_radius >= 2500:      # > 2.5 km
            return 17
        elif view_radius >= 1250:      # > 1.25 km
            return 18
        elif view_radius >= 625:       # > 625 m
            return 19
        else:
            return 20

    @staticmethod
    def get_zoom_by_level(level_info: str = None, type_info: str = None, radius: float = None) -> int:
        """
        根据地址类型获取合适的缩放级别

        优化策略：
        1. 优先检查type_info（中文描述），因为它包含更详细的类型信息
        2. 其次检查level_info（类型编码）
        3. 使用更精确的关键词匹配
        4. 对于住宅类地址，优先使用高缩放级别以显示细节

        Args:
            level_info: 高德返回的地址级别信息（typecode）
            type_info: POI类型信息（中文描述）
            radius: POI半径（米），如果提供则优先使用

        Returns:
            int: 缩放级别
        """
        # 优先级1：如果提供了POI半径，基于实际范围计算缩放级别
        if radius is not None and radius > 0:
            zoom = MapRenderer._calculate_zoom_from_radius(radius)
            return zoom

        if not level_info and not type_info:
            return 12

        level_lower = (level_info or '').lower()
        type_lower = (type_info or '').lower()

        # 第一优先级：检查type_info（中文描述），因为它更准确
        # 住宅类（最高优先级，需要看清小区布局）
        if any(kw in type_lower for kw in ['住宅小区', '住宅区', '商务住宅', '别墅', '公寓']):
            return MapRenderer.ZOOM_LEVELS['community']  # 17

        # 商业POI（需要看清周边环境）
        if any(kw in type_lower for kw in ['餐饮', '购物', '酒店', '宾馆', '商场', '超市', '便利店']):
            return MapRenderer.ZOOM_LEVELS['poi']  # 16

        # 公共服务设施（需要看清位置）
        if any(kw in type_lower for kw in ['医院', '诊所', '学校', '幼儿园', '大学', '银行', '邮局']):
            return MapRenderer.ZOOM_LEVELS['poi']  # 16

        # 交通设施（需要看清站点）
        if any(kw in type_lower for kw in ['地铁站', '公交站', '停车场', '加油站']):
            return MapRenderer.ZOOM_LEVELS['poi']  # 16

        # 办公楼宇
        if any(kw in type_lower for kw in ['写字楼', '商务楼', '办公楼', '科技园']):
            return MapRenderer.ZOOM_LEVELS['poi']  # 16

        # 建筑物和特定场所（营销中心、售楼处等）
        if any(kw in type_lower for kw in ['生活服务场所', '房地产', '中介', '物业']):
            return MapRenderer.ZOOM_LEVELS['building']  # 18

        # 风景名胜和景点（优先于行政区划检查）
        if any(kw in type_lower for kw in ['风景名胜', '景点', '兴趣点', 'poi', '公园', '广场', '纪念', '博物馆', '展览']):
            return MapRenderer.ZOOM_LEVELS['poi']  # 16

        # 第二优先级：检查level_info和type_info中的行政区划关键词
        combined = level_lower + ' ' + type_lower

        # 国家级（但排除"国家级景点"这类POI）
        if any(kw in combined for kw in ['国家', 'country']) and '景点' not in type_lower and '风景' not in type_lower:
            return MapRenderer.ZOOM_LEVELS['country']  # 4

        # 省级
        if any(kw in combined for kw in ['省', 'province']):
            return MapRenderer.ZOOM_LEVELS['province']  # 7

        # 市级（注意：要在"社区"、"小区"之后检查）
        if any(kw in combined for kw in ['市', 'city', '自治区']):
            return MapRenderer.ZOOM_LEVELS['city']  # 10

        # 街道级
        if any(kw in combined for kw in ['街道', '街', '路', 'street', 'road', '巷', '弄']):
            return MapRenderer.ZOOM_LEVELS['street']  # 15

        # 社区/小区（要在"区"之前检查）
        if any(kw in combined for kw in ['社区', '小区', 'community', 'residential']):
            return MapRenderer.ZOOM_LEVELS['community']  # 17

        # 区/县级
        if any(kw in combined for kw in ['区', '县', 'district', 'county']):
            return MapRenderer.ZOOM_LEVELS['district']  # 12

        # 建筑级
        if any(kw in combined for kw in ['楼', '栋', '建筑', 'building', '大厦']):
            return MapRenderer.ZOOM_LEVELS['building']  # 18

        # 默认返回14（介于区级12和街道级15之间）
        return 14

    @staticmethod
    def create_base_map(center, zoom_start=10, map_type='roadmap', map_source='osm'):
        """
        创建基础地图

        Args:
            center: 中心点 [lat, lon]
            zoom_start: 初始缩放级别
            map_type: 地图类型 ('roadmap', 'satellite', 'hybrid')
            map_source: 地图数据源 ('osm', 'gaode')

        Returns:
            folium.Map: 地图对象
        """
        # 使用Canvas renderer实现高性能路线渲染（参考GPXStudio官方）
        # Canvas对大量点的渲染性能远超SVG，能流畅处理数万个点
        m = folium.Map(
            location=center,
            zoom_start=zoom_start,
            tiles=None,
            zoom_control=False,  # 禁用默认的缩放控件
            prefer_canvas=True   # 使用Canvas渲染器而非SVG（高性能）
        )

        if map_source == 'gaode':
            # 确保服务器已启动以获取端口
            from .http_server import get_map_server
            server = get_map_server()
            server.start()
            port = server.port
            
            # 使用本地代理URL
            # 格式: http://127.0.0.1:{port}/tiles/{source}/{style}/{z}/{x}/{y}
            proxy_url_base = f'http://127.0.0.1:{port}/tiles/gaode'
            
            tile_urls = {
                'roadmap': f'{proxy_url_base}/roadmap/{{z}}/{{x}}/{{y}}',
                'satellite': f'{proxy_url_base}/satellite/{{z}}/{{x}}/{{y}}',
                'hybrid': f'{proxy_url_base}/hybrid/{{z}}/{{x}}/{{y}}'
            }

            tile_url = tile_urls.get(map_type, tile_urls['roadmap'])

            # 添加卫星地图瓦片图层
            folium.TileLayer(
                tiles=tile_urls['satellite'] if map_type in ['satellite', 'hybrid'] else tile_url,
                attr='© 高德地图',
                name='高德卫星地图',
                overlay=False,
                control=False
            ).add_to(m)
            
            # 如果是卫星地图或混合地图，添加标注图层
            # 注意：混合图的标注也需要走代理，但目前先只代理底图，标注暂不处理或者也走hybrid
            if map_type in ['satellite', 'hybrid']:
                # 标注层通常是透明png，也可以缓存，这里假设它使用hybrid样式
                # 高德webst01其实包含标注，或者用专门的标注服务。这里为了简化，暂不走缓存代理避免复杂
                # 或者，简单地也指向代理
                folium.TileLayer(
                    # 使用直连，或者可以配置为 proxy_url_base + '/roadmap/...' (高德标注通常和路网类似)
                    tiles='https://webst01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
                    attr='© 高德地图',
                    name='高德地图标注',
                    overlay=True,
                    control=False
                ).add_to(m)
        else:
            # 使用OSM地图瓦片（通过代理服务器缓存）
            from .http_server import get_map_server
            server = get_map_server()
            server.start()
            port = server.port
            
            # 使用本地代理URL，实现OSM瓦片缓存
            # 格式: http://127.0.0.1:{port}/tiles/{source}/{style}/{z}/{x}/{y}
            proxy_url_base = f'http://127.0.0.1:{port}/tiles/osm'
            
            osm_tile_urls = {
                'roadmap': f'{proxy_url_base}/roadmap/{{z}}/{{x}}/{{y}}',
                'satellite': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                'hybrid': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
            }
            
            tile_url = osm_tile_urls.get(map_type, osm_tile_urls['roadmap'])
            
            if map_type == 'roadmap':
                folium.TileLayer(
                    tiles=tile_url,
                    attr='© OpenStreetMap contributors',
                    name='OpenStreetMap',
                    overlay=False,
                    control=False
                ).add_to(m)
            else:
                # 添加卫星地图瓦片图层
                folium.TileLayer(
                    tiles=tile_url,
                    attr='© Esri',
                    name='Satellite',
                    overlay=False,
                    control=False
                ).add_to(m)
                
                # 添加OpenStreetMap标注图层（使用CartoDB的标注服务）
                folium.TileLayer(
                    tiles='https://{s}.basemaps.cartocdn.com/rastertiles/voyager_only_labels/{z}/{x}/{y}{r}.png',
                    attr='© OpenStreetMap contributors, © CartoDB',
                    name='OpenStreetMap Labels',
                    overlay=True,
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

        # 添加CSS样式，禁用地图的手型光标
        cursor_style = """
        <style>
        .leaflet-container {
            cursor: default !important;
        }
        .leaflet-grab {
            cursor: default !important;
        }
        .leaflet-dragging .leaflet-grab {
            cursor: default !important;
        }
        .leaflet-dragging .leaflet-container {
            cursor: default !important;
        }
        </style>
        """
        m.get_root().html.add_child(folium.Element(cursor_style))

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

        # 添加缩放监听和右键菜单脚本
        map_interaction_script = """
        <script>
        // 直接在全局作用域中添加地图交互监听
        (function() {
            var map = null;
            var initAttempts = 0;
            var maxInitAttempts = 30;

            function initMapListener() {
                initAttempts++;

                // 尝试获取地图对象
                // 方法1: 通过leaflet-container元素
                var mapElement = document.querySelector('.leaflet-container');
                if (mapElement && mapElement._leaflet_map) {
                    map = mapElement._leaflet_map;
                    console.log('[地图交互] 成功通过.leaflet-container找到地图');
                    setupMapListeners();
                    return;
                }

                // 方法2: 查找所有可能的地图对象
                for (var key in window) {
                    if (window[key] && typeof window[key] === 'object' &&
                        window[key].getZoom && typeof window[key].getZoom === 'function' &&
                        window[key].on && typeof window[key].on === 'function') {
                        map = window[key];
                        console.log('[地图交互] 成功通过全局对象找到地图: ' + key);
                        setupMapListeners();
                        return;
                    }
                }

                // 如果还是没找到，继续尝试
                if (initAttempts < maxInitAttempts) {
                    setTimeout(initMapListener, 200);
                } else {
                    console.log('[地图交互] 初始化失败，无法找到地图对象');
                }
            }

            function setupMapListeners() {
                if (!map) return;

                // 保存地图对象到全局变量，供其他功能使用
                window.map = map;
                console.log('[地图交互] 已将地图对象保存到 window.map');
                console.log('[地图交互] 开始设置地图监听器');

                // 1. 禁用默认右键菜单
                var container = map.getContainer();
                container.addEventListener('contextmenu', function(e) {
                    e.preventDefault();
                    return false;
                });
                console.log('[地图交互] 已禁用默认右键菜单');

                // 2. 设置缩放监听
                var currentZoom = map.getZoom();
                console.log('[地图缩放] 当前缩放级别: ' + currentZoom);
                console.log('缩放变化:' + currentZoom);

                map.on('zoomend', function() {
                    var zoomLevel = map.getZoom();
                    console.log('[地图缩放] 缩放级别变化: ' + zoomLevel);
                    console.log('缩放变化:' + zoomLevel);
                });

                // 3. 设置右键点击监听
                map.on('contextmenu', function(e) {
                    var lat = e.latlng.lat;
                    var lon = e.latlng.lng;
                    console.log('[地图右键] 右键点击位置: ' + lat + ', ' + lon);
                    console.log('右键点击:' + lat + ',' + lon);
                });

                // 4. 设置移动结束监听
                map.on('moveend', function() {
                    var center = map.getCenter();
                    var bounds = map.getBounds();
                    // 只记录小数点后4位，足够精确
                    console.log('[地图移动] 移动结束，中心点: [' + center.lat.toFixed(4) + ', ' + center.lng.toFixed(4) + ']');
                    console.log('[地图移动] 视口范围: SW[' + bounds.getSouthWest().lat.toFixed(4) + ',' + bounds.getSouthWest().lng.toFixed(4) + 
                                '] - NE[' + bounds.getNorthEast().lat.toFixed(4) + ',' + bounds.getNorthEast().lng.toFixed(4) + ']');
                                
                    // 发送视口信息到后端HTTP服务器
                    var sw = bounds.getSouthWest();
                    var ne = bounds.getNorthEast();
                    var port = window.location.port;
                    if (port) {
                        var url = 'http://127.0.0.1:' + port + '/update_viewport?sw_lat=' + sw.lat + '&sw_lon=' + sw.lng + '&ne_lat=' + ne.lat + '&ne_lon=' + ne.lng + '&zoom=' + map.getZoom();
                        fetch(url).catch(err => console.error('Failed to update viewport:', err));
                    }
                });

                // 首次加载也发送一次
                setTimeout(function() {
                    var bounds = map.getBounds();
                    var sw = bounds.getSouthWest();
                    var ne = bounds.getNorthEast();
                    var port = window.location.port;
                    if (port) {
                        var url = 'http://127.0.0.1:' + port + '/update_viewport?sw_lat=' + sw.lat + '&sw_lon=' + sw.lng + '&ne_lat=' + ne.lat + '&ne_lon=' + ne.lng + '&zoom=' + map.getZoom();
                        fetch(url).catch(err => console.error('Failed to update viewport:', err));
                    }
                }, 1000);

                // 5. 设置瓦片加载监听 (针对所有TileLayer)
                map.eachLayer(function(layer) {
                     if (layer instanceof L.TileLayer) {
                         // 避免重复绑定
                         if (layer._gpx_listeners_attached) return;
                         
                         layer.on('tileloadstart', function(e) {
                             // 计算瓦片坐标 (z/x/y)
                             if (e.coords) {
                                 console.log('[地图瓦片] 开始加载瓦片: z=' + e.coords.z + ', x=' + e.coords.x + ', y=' + e.coords.y);
                             }
                         });
                         
                         layer.on('load', function(e) {
                             console.log('[地图瓦片] 当前视口瓦片加载完成');
                         });

                         layer._gpx_listeners_attached = true;
                     }
                });

                // 监听新添加的图层，也加上瓦片监听
                map.on('layeradd', function(e) {
                    if (e.layer instanceof L.TileLayer && !e.layer._gpx_listeners_attached) {
                         e.layer.on('tileloadstart', function(ev) {
                             if (ev.coords) {
                                 console.log('[地图瓦片] 开始加载瓦片: z=' + ev.coords.z + ', x=' + ev.coords.x + ', y=' + ev.coords.y);
                             }
                         });
                         e.layer._gpx_listeners_attached = true;
                    }
                });

                console.log('[地图交互] 地图监听器设置完成');
            }

            // 页面加载完成后初始化
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', initMapListener);
            } else {
                initMapListener();
            }
        })();
        </script>
        """
        m.get_root().html.add_child(folium.Element(map_interaction_script))

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
        if not route_points:
            return

        # 快速分割路线段，避免中间列表操作
        route_segments = []
        current_segment = []

        for point in route_points:
            if point is None:
                if len(current_segment) > 1:
                    route_segments.append(current_segment)
                current_segment = []
            else:
                # 提取点的前两个元素（纬度和经度），忽略海拔数据
                if len(point) >= 2:
                    lat_lon_point = [point[0], point[1]]
                else:
                    lat_lon_point = point
                current_segment.append(lat_lon_point)

        # 添加最后一段路线
        if len(current_segment) > 1:
            route_segments.append(current_segment)

        # 批量添加所有路线段
        if route_segments:
            # 优化：使用更高效的PolyLine参数
            polyline_options = {
                'smoothFactor': 1.5,  # 增加平滑因子，减少渲染点数
                'noClip': True,  # 启用裁剪，减少可视区域外的渲染
            }

            # 优化：直接添加多段路线，避免FeatureGroup开销
            for segment in route_segments:
                folium.PolyLine(
                    locations=segment,
                    color=color,
                    weight=weight,
                    opacity=opacity,
                    smooth_factor=polyline_options['smoothFactor'],
                    no_clip=polyline_options['noClip'],
                    tooltip=""
                ).add_to(map_obj)
    @staticmethod
    def save_and_get_url(map_obj, use_http_server=True):
        """
        保存地图到临时文件并返回URL

        Args:
            map_obj: folium地图对象
            use_http_server: 是否使用HTTP服务器（解决地理定位限制和本地文件访问问题）

        Returns:
            QUrl: 本地文件URL或HTTP URL
        """
        import logging
        logger = logging.getLogger(__name__)

        try:
            if use_http_server:
                from .http_server import get_map_server
                import uuid
                import os

                server = get_map_server()
                filename = f"map_{uuid.uuid4().hex[:8]}.html"
                url_str = server.save_map(map_obj, filename)

                # 检查返回的是HTTP URL还是本地文件路径
                if url_str.startswith('http://') or url_str.startswith('https://'):
                    logger.debug(f"使用HTTP服务器提供地图: {url_str}")
                    return QUrl(url_str)
                else:
                    # 返回的是本地文件路径，创建本地文件URL
                    logger.debug(f"HTTP服务器返回本地文件路径: {url_str}")
                    return QUrl.fromLocalFile(url_str)
            else:
                import os
                # 优化：直接使用路径创建，避免文件对象操作
                import tempfile
                temp_path = tempfile.mktemp(suffix='.html')

                map_obj.save(temp_path)
                logger.debug(f"保存地图到临时文件: {temp_path}")

                # 确保文件存在且可访问
                if os.path.exists(temp_path):
                    logger.debug(f"临时文件大小: {os.path.getsize(temp_path)} bytes")
                    return QUrl.fromLocalFile(temp_path)
                else:
                    logger.error(f"临时文件创建失败: {temp_path}")
                    # 回退到HTTP服务器方式
                    from .http_server import get_map_server
                    import uuid
                    server = get_map_server()
                    filename = f"map_{uuid.uuid4().hex[:8]}.html"
                    url_str = server.save_map(map_obj, filename)

                    # 检查返回的是HTTP URL还是本地文件路径
                    if url_str.startswith('http://') or url_str.startswith('https://'):
                        logger.debug(f"回退到HTTP服务器: {url_str}")
                        return QUrl(url_str)
                    else:
                        logger.debug(f"HTTP服务器回退返回本地文件路径: {url_str}")
                        return QUrl.fromLocalFile(url_str)
        except Exception as e:
            logger.error(f"保存地图失败: {str(e)}")
            # 出错时回退到简单的本地文件
            try:
                import os
                import tempfile
                temp_path = tempfile.mktemp(suffix='.html')

                map_obj.save(temp_path)
                logger.debug(f"出错时回退到临时文件: {temp_path}")

                if os.path.exists(temp_path):
                    logger.debug(f"临时文件大小: {os.path.getsize(temp_path)} bytes")
                    return QUrl.fromLocalFile(temp_path)
                else:
                    logger.error(f"临时文件创建失败: {temp_path}")
                    # 最后回退：创建一个简单的本地文件URL
                    temp_path = tempfile.mktemp(suffix='.html')
                    map_obj.save(temp_path)
                    return QUrl.fromLocalFile(temp_path)
            except Exception as fallback_error:
                logger.error(f"最后回退也失败: {str(fallback_error)}")
                # 最极端的情况：返回一个无效的URL，但至少不会崩溃
                return QUrl()

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

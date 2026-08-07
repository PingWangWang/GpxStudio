"""
地图渲染工具
使用Folium生成HTML地图
"""

import folium
from folium.plugins import FloatImage
import tempfile
from PyQt5.QtCore import QUrl

from .gaode_tiles import GaodeTileService
from modules.geolocation import CoordinateTransform
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
    def create_base_map(center, zoom_start=10, map_type='roadmap', map_source='osm', coord_system='WGS-84'):
        """
        创建基础地图

        Args:
            center: 中心点 [lat, lon]
            zoom_start: 初始缩放级别
            map_type: 地图类型 ('roadmap', 'satellite', 'hybrid')
            map_source: 地图数据源 ('osm', 'gaode')
            coord_system: 输入坐标系统 ('WGS-84', 'GCJ-02')

        Returns:
            folium.Map: 地图对象
        """
        # 只在坐标系统不匹配时进行转换
        map_center = center
        target_system = 'GCJ-02' if map_source == 'gaode' else 'WGS-84'
        if coord_system != target_system:
            converted = CoordinateTransform.convert(center[0], center[1], coord_system, target_system)
            map_center = list(converted)
        # 否则直接使用（坐标系统匹配）
        
        # 使用Canvas renderer实现高性能路线渲染（参考GPXStudio官方）
        # Canvas对大量点的渲染性能远超SVG，能流畅处理数万个点
        m = folium.Map(
            location=map_center,
            zoom_start=zoom_start,
            tiles=None,
            zoom_control=False,  # 禁用默认的缩放控件
            prefer_canvas=True   # 使用Canvas渲染器而非SVG（高性能）
        )

        if map_source == 'gaode':
            # 直接使用高德地图在线瓦片URL
            tile_urls = {
                'roadmap': 'https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
                'satellite': 'https://webst01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=6&x={x}&y={y}&z={z}',
                'hybrid': 'https://webst01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}'
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
            
            # 如果是卫星地图或混合地图，始终添加标注图层
            if map_type in ['satellite', 'hybrid']:
                road_layer = folium.TileLayer(
                    tiles='https://webst01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
                    attr='© 高德地图',
                    name='高德地图标注',
                    overlay=True,
                    control=False
                )
                road_layer.add_to(m)
        else:
            # 直接使用OSM地图在线瓦片URL
            osm_tile_urls = {
                'roadmap': 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                'satellite': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                'hybrid': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'  # hybrid使用satellite瓦片
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
                
                # 始终添加OpenStreetMap标注图层
                road_layer = folium.TileLayer(
                    tiles='https://{s}.basemaps.cartocdn.com/rastertiles/voyager_only_labels/{z}/{x}/{y}{r}.png',
                    attr='© OpenStreetMap contributors, © CartoDB',
                    name='OpenStreetMap Labels',
                    overlay=True,
                    control=False
                )
                road_layer.add_to(m)

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
                    
                    // 初始化路网图层的显示状态和缓存
                    var showRoads = """ + str(map_config.get_satellite_show_roads()).lower() + """;
                    var isSatelliteMode = """ + str(map_type in ('satellite', 'hybrid')).lower() + """;
                    var roadLayersFound = [];

                    // 初始化路网图层缓存
                    if (!map._roadLayers) {
                        map._roadLayers = [];
                    }

                    // 仅在卫星/混合模式下识别路网图层，避免误伤街道底图
                    // 注意：folium 不会将 name/overlay 序列化进图层 options，
                    // 因此只能通过 URL 特征识别（高德 style=8 标注层、CartoDB labels 层）
                    if (isSatelliteMode) {
                        map.eachLayer(function(layer) {
                            if (layer instanceof L.TileLayer) {
                                var layerUrl = layer._url || '';

                                // 识别路网图层：URL 含路网标注特征（高德 style=8、CartoDB voyager_only_labels）
                                // 街道底图虽同样含 style=8，但此处仅在卫星模式下执行，不会误伤
                                if (layerUrl.indexOf('style=8') !== -1 ||
                                    layerUrl.indexOf('voyager_only_labels') !== -1) {

                                    roadLayersFound.push(layer);
                                    map._roadLayers.push(layer);

                                    if (!showRoads) {
                                        // 如果配置为不显示路网，移除图层（引用保留在缓存中，可随时恢复）
                                        if (map.hasLayer(layer)) {
                                            map.removeLayer(layer);
                                            console.log('[地图] 初始化：路网图层已隐藏 -', layerUrl);
                                        }
                                    } else {
                                        console.log('[地图] 初始化：路网图层已显示 -', layerUrl);
                                    }
                                }
                            }
                        });
                    }
                    
                    if (roadLayersFound.length === 0) {
                        console.warn('[地图] 初始化：未找到路网图层（可能不是卫星地图模式）');
                    } else {
                        console.log('[地图] 初始化：找到并缓存了', roadLayersFound.length, '个路网图层');
                    }
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

                // 3.1 中键双击检测（→ 自动缩放，效果与工具栏按钮一致）
                // 浏览器 dblclick 事件仅对主按钮（左键）触发，中键双击需自行计数：
                // DOM 原生 mousedown（button=1）两次点击间隔 < 500ms 判定为双击
                var middleContainer = map.getContainer();
                var lastMiddleDown = 0;
                middleContainer.addEventListener('mousedown', function(e) {
                    if (e.button === 1) {
                        var now = Date.now();
                        if (now - lastMiddleDown < 500) {
                            console.log('中键双击缩放');
                            lastMiddleDown = 0;  // 重置，避免三连击重复触发
                        } else {
                            lastMiddleDown = now;
                        }
                    }
                });

                // 4. 设置移动结束监听
                map.on('moveend', function() {
                    var center = map.getCenter();
                    var bounds = map.getBounds();
                    // 只记录小数点后4位，足够精确
                    console.log('[地图移动] 移动结束，中心点: [' + center.lat.toFixed(4) + ', ' + center.lng.toFixed(4) + ']');
                    console.log('[地图移动] 视口范围: SW[' + bounds.getSouthWest().lat.toFixed(4) + ',' + bounds.getSouthWest().lng.toFixed(4) + 
                                '] - NE[' + bounds.getNorthEast().lat.toFixed(4) + ',' + bounds.getNorthEast().lng.toFixed(4) + ']');
                    // 结构化输出，供 webengine 解析回传后端
                    console.log('地图中心:' + center.lat.toFixed(6) + ',' + center.lng.toFixed(6));
                });

                // 5. 设置瓦片加载监听 (针对所有TileLayer)
                map.eachLayer(function(layer) {
                     if (layer instanceof L.TileLayer) {
                         // 避免重复绑定
                         if (layer._gpx_listeners_attached) return;
                         
                         layer.on('tileloadstart', function(e) {
                            // 计算瓦片坐标 (z/x/y)
                            if (e.coords) {
                                // 屏蔽日志，减少控制台输出
                                // console.log('[地图瓦片] 开始加载瓦片: z=' + e.coords.z + ', x=' + e.coords.x + ', y=' + e.coords.y);
                            }
                        });
                         
                         layer.on('tileerror', function(e) {
                             console.error('[地图瓦片] 瓦片加载失败:', e.coords, e.error);
                         });
                         
                         layer.on('load', function(e) {
                             // 屏蔽日志，减少控制台输出
                             // console.log('[地图瓦片] 当前视口瓦片加载完成');
                         });

                         layer._gpx_listeners_attached = true;
                     }
                });

                // 监听新添加的图层，也加上瓦片监听
                map.on('layeradd', function(e) {
                    if (e.layer instanceof L.TileLayer && !e.layer._gpx_listeners_attached) {
                         e.layer.on('tileloadstart', function(ev) {
                             if (ev.coords) {
                                 // 屏蔽日志，减少控制台输出
                                 // console.log('[地图瓦片] 开始加载瓦片: z=' + ev.coords.z + ', x=' + ev.coords.x + ', y=' + ev.coords.y);
                             }
                         });
                         e.layer.on('tileerror', function(ev) {
                             console.error('[地图瓦片] 瓦片加载失败:', ev.coords, ev.error);
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
    def _escape_popup_html(text: str) -> str:
        """
        转义将嵌入 popup HTML 的用户内容

        popup HTML 由 folium 以 JS 模板字符串（反引号）包裹内嵌，
        因此除 HTML 实体外还需转义反引号与 ${（模板插值起始），
        用 HTML 实体替代可同时保证 JS 语法安全与显示正确。

        Args:
            text: 原始文本

        Returns:
            str: 转义后的安全文本
        """
        import html as html_module
        return (html_module.escape(str(text))
                .replace('`', '&#96;')
                .replace('${', '&#36;&#123;'))

    @staticmethod
    def add_marker(map_obj, location, popup_text, color='blue', icon='info-sign', map_source='gaode', coord_system='WGS-84', number=None, star=False, fav_id=None, marker_type=None):
        """
        添加标记点

        Args:
            map_obj: folium地图对象
            location: 位置 [lat, lon]
            popup_text: 弹出文本
            color: 颜色
            icon: 图标
            map_source: 地图数据源
            coord_system: 输入坐标系统 ('WGS-84', 'GCJ-02')
            number: 标记序号（可选），用于在标记上显示数字
            star: 是否使用金色星形标记（收藏点专用）
            fav_id: 收藏点ID（可选），写入 Leaflet options（favId）供 JS 增量移除定位
            marker_type: 标记类型（可选），写入 Leaflet options（markerType）供 JS 按类型定位
        """
        # 只在坐标系统不匹配时进行转换
        marker_location = location
        target_system = 'GCJ-02' if map_source == 'gaode' else 'WGS-84'
        if coord_system != target_system:
            converted = CoordinateTransform.convert(location[0], location[1], coord_system, target_system)
            marker_location = list(converted)
        import logging as _lg; _lg.getLogger(__name__).info(
            f"[DEBUG漂移] 7_add_marker: input={location}, coord_system={coord_system}, "
            f"target={target_system}, converted={'是' if coord_system != target_system else '否'}, "
            f"result={marker_location}, number={number}")
        # 否则直接使用（坐标系统匹配）

        # 收藏点星形标记：金色五角星
        if star:
            html = '''
            <div style="
                font-size: 22px;
                line-height: 22px;
                color: #FFD700;
                text-shadow: 0 1px 3px rgba(0,0,0,0.4);
                user-select: none;
            ">★</div>
            '''
            marker_icon = folium.DivIcon(html=html, icon_anchor=(11, 11))
        # 如果提供了序号，使用自定义DivIcon显示带序号的标记
        elif number is not None:
            # 蓝色圆形标记，白色数字
            html = f'''
            <div style="
                background-color: #007bff;
                border: 2px solid white;
                border-radius: 50%;
                width: 30px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                font-size: 14px;
                color: white;
                box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            ">{number}</div>
            '''
            marker_icon = folium.DivIcon(html=html, icon_anchor=(15, 15))
        else:
            marker_icon = folium.Icon(color=color, icon=icon)
        
        marker_options = {}
        if fav_id is not None:
            marker_options['fav_id'] = fav_id  # folium 会自动转为 favId 写入 JS options
        if marker_type is not None:
            marker_options['marker_type'] = marker_type  # folium 会自动转为 markerType 写入 JS options

        folium.Marker(
            location=marker_location,
            popup=popup_text,
            icon=marker_icon,
            **marker_options
        ).add_to(map_obj)

    @staticmethod
    def add_favorites_markers(map_obj, favorites, map_source='gaode', visible=True):
        """
        在地图上添加收藏点标记（金色星形）

        Args:
            map_obj: folium地图对象
            favorites: 收藏点列表，每项含 id/name/address/lat/lon/created_at
            map_source: 地图数据源（'gaode'/'osm'），用于坐标转换
            visible: 是否显示收藏点（False时不添加任何标记）

        说明：
            收藏点统一以 WGS-84 坐标存储，渲染时交由 add_marker 按地图源自动转换。
            点击星形标记弹出详情（Leaflet 默认行为），详情内嵌删除按钮，
            按钮点击通过 window.GPXFavorites.deleteFav 输出 console 消息，
            由 webengine 拦截后转发给后端删除。
        """
        if not visible or not favorites:
            return

        import html as html_module

        # 注入收藏点交互脚本（供 popup 内删除按钮调用）
        favorites_script = """
        <script>
        // 收藏点交互全局对象：供收藏点 popup 内的删除按钮调用
        window.GPXFavorites = {
            deleteFav: function(id) {
                console.log('收藏删除:' + id);
            }
        };
        </script>
        """
        map_obj.get_root().html.add_child(folium.Element(favorites_script))

        for fav in favorites:
            fav_id = fav.get('id')
            if fav_id is None:
                continue

            name = fav.get('name', '') or '收藏点'
            address = fav.get('address', '') or ''
            lat = fav.get('lat', 0)
            lon = fav.get('lon', 0)
            created_at = (fav.get('created_at') or '')[:19].replace('T', ' ')

            # 转义用户内容（HTML 实体 + JS 模板字符串防护，见 _escape_popup_html）
            name_esc = MapRenderer._escape_popup_html(name)
            address_esc = MapRenderer._escape_popup_html(address)

            # 地址行：地址为空或与名称相同（高德场景名称即完整地址）时隐藏，避免显示"未知"
            address_line = ''
            if address and address != name:
                address_line = f'<span style="color:#888;">地址: {address_esc}</span><br>'

            popup_html = f"""
            <div style="font-family:'Microsoft YaHei','微软雅黑',sans-serif; font-size:13px; min-width:180px;">
                <b>{name_esc}</b><br>
                {address_line}
                <span style="color:#888;">坐标: {lat:.6f}, {lon:.6f}</span><br>
                <span style="color:#888;">收藏时间: {created_at or '未知'}</span><br>
                <button onclick="window.GPXFavorites.deleteFav({fav_id})" style="
                    margin-top:6px; background-color:#f5222d; color:white;
                    border:none; border-radius:3px; padding:3px 10px; cursor:pointer;">
                    删除收藏
                </button>
            </div>
            """

            MapRenderer.add_marker(
                map_obj, [lat, lon], popup_html,
                map_source=map_source,
                coord_system='WGS-84',  # 收藏点统一以 WGS-84 存储
                star=True,
                fav_id=fav_id  # 写入 Leaflet options（favId），供 JS 增量移除时定位星标
            )

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
            use_http_server: 是否使用HTTP服务器（默认使用）

        Returns:
            QUrl: 地图URL
        """
        import logging
        logger = logging.getLogger(__name__)

        try:
            # 优先使用HTTP服务器
            from .http_server import get_map_server
            map_server = get_map_server()
            
            # 生成唯一文件名
            import tempfile
            filename = f"map_{tempfile.mktemp(suffix='', prefix='', dir='')}.html"
            
            # 使用HTTP服务器保存地图并获取URL
            url_str = map_server.save_map(map_obj, filename)
            logger.debug(f"保存地图到HTTP服务器: {url_str}")
            
            # 检查返回的是否是HTTP URL
            if url_str.startswith('http://'):
                logger.info(f"成功获取HTTP URL: {url_str}")
                return QUrl(url_str)
            else:
                logger.warning(f"HTTP服务器返回非HTTP URL: {url_str}，回退到本地文件")
                return QUrl.fromLocalFile(url_str)
        except Exception as e:
            logger.error(f"使用HTTP服务器失败: {str(e)}")
            # 出错时回退到本地文件
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
        # 获取高德地图API密钥
        from services.config.map_config import map_config
        amap_api_key = map_config.get_api_key() or ""
        
        geolocation_script = """
        <script>
        console.log('[初始化] 定位脚本已加载');
        console.log('[初始化] 页面协议: ' + window.location.protocol);
        console.log('[初始化] 页面URL: ' + window.location.href);
        console.log('[初始化] navigator.geolocation: ' + navigator.geolocation);
        console.log('[初始化] navigator.permissions: ' + navigator.permissions);
        console.log('[初始化] navigator.onLine: ' + navigator.onLine);
        console.log('[初始化] 高德地图API密钥: ' + ('已配置' if API_KEY_PLACEHOLDER else '未配置'));

        // 检查地理位置权限状态
        if (navigator.permissions) {
            navigator.permissions.query({name:"geolocation"}).then(function(status) {
                console.log('[权限状态] 初始状态: ' + status.state);
                status.onchange = function() {
                    console.log('[权限状态] 状态变化: ' + status.state);
                };
            }).catch(function(error) {
                console.log('[权限状态] 检查权限状态失败: ' + error);
            });
        } else {
            console.log('[权限状态] 浏览器不支持Permissions API');
        }

        // 检查网络连接状态
        function checkNetworkStatus() {
            var online = navigator.onLine;
            console.log('[网络状态] 当前状态: ' + (online ? '在线' : '离线'));
            return online;
        }

        // 测试网络连接质量
        function testNetworkConnectivity() {
            return new Promise(function(resolve) {
                console.log('[网络测试] 开始测试网络连接质量...');
                var startTime = Date.now();
                var xhr = new XMLHttpRequest();
                xhr.open('GET', 'https://www.baidu.com', true);
                xhr.timeout = 5000;
                xhr.onload = function() {
                    var latency = Date.now() - startTime;
                    console.log('[网络测试] 连接成功，延迟: ' + latency + 'ms');
                    resolve({ success: true, latency: latency });
                };
                xhr.onerror = function() {
                    console.log('[网络测试] 连接失败');
                    resolve({ success: false });
                };
                xhr.ontimeout = function() {
                    console.log('[网络测试] 连接超时');
                    resolve({ success: false });
                };
                xhr.send();
            });
        }

        // 使用高德地图定位API
        function getLocationByAmap() {
            console.log('[高德定位] 开始使用高德地图定位API...');
            
            // 检查是否已加载高德地图API
            if (typeof AMap === 'undefined') {
                console.log('[高德定位] 加载高德地图API...');
                // 动态加载高德地图API
                var script = document.createElement('script');
                script.type = 'text/javascript';
                var apiKey = 'AMAP_API_KEY_PLACEHOLDER' || '';
                if (apiKey && apiKey !== 'AMAP_API_KEY_PLACEHOLDER') {
                    script.src = 'https://webapi.amap.com/maps?v=2.0&key=' + apiKey;
                    script.onload = function() {
                        console.log('[高德定位] 高德地图API加载成功');
                        performAmapLocation();
                    };
                    script.onerror = function() {
                        console.log('[高德定位] 高德地图API加载失败');
                        console.log('定位失败:高德地图API加载失败');
                    };
                    document.head.appendChild(script);
                } else {
                    console.log('[高德定位] 高德地图API密钥未配置');
                    console.log('定位失败:高德地图API密钥未配置');
                }
            } else {
                performAmapLocation();
            }
        }

        function performAmapLocation() {
            console.log('[高德定位] 执行高德地图定位...');
            
            if (typeof AMap === 'undefined') {
                console.log('[高德定位] 高德地图API未加载');
                console.log('定位失败:高德地图API未加载');
                return;
            }

            // 记录开始时间
            var startTime = Date.now();
            
            // 创建定位实例
            var geolocation = new AMap.Geolocation({
                enableHighAccuracy: true, // 是否使用高精度定位，默认:true
                timeout: 15000, // 超过15秒后停止定位，默认：无穷大
                maximumAge: 0, // 定位结果缓存0毫秒，默认：0
                convert: true, // 自动偏移坐标，偏移后的坐标为高德坐标，默认：true
                showButton: false, // 显示定位按钮，默认：true
                buttonPosition: 'RB', // 定位按钮停靠位置，默认：'LB'，左下角
                buttonOffset: new AMap.Pixel(10, 20), // 定位按钮与设置的停靠位置的偏移量，默认：Pixel(10, 20)
                showMarker: false, // 定位成功后在定位到的位置显示点标记，默认：true
                showCircle: false, // 定位成功后用圆圈表示定位精度范围，默认：true
                panToLocation: false, // 定位成功后将定位到的位置作为地图中心点，默认：true
                zoomToAccuracy: false // 定位成功后调整地图视野范围使定位位置及精度范围视野内可见，默认：false
            });

            // 监听定位成功事件
            geolocation.on('complete', function(data) {
                console.log('[高德定位] ✅ 定位成功');
                console.log('[高德定位] 耗时: ' + (Date.now() - startTime) + 'ms');
                console.log('[高德定位] 成功数据: ' + JSON.stringify(data));
                
                var lat = data.position.getLat();
                var lon = data.position.getLng();
                var accuracy = data.accuracy || 100; // 默认精度值
                var location_type = data.location_type;
                var location_detail = data.formattedAddress || '未知位置';
                
                console.log('[高德定位] 纬度: ' + lat);
                console.log('[高德定位] 经度: ' + lon);
                console.log('[高德定位] 精度: ' + accuracy + ' 米');
                console.log('[高德定位] 定位类型: ' + location_type);
                console.log('[高德定位] 位置详情: ' + location_detail);
                
                // 使用处理器期望的格式输出日志
                console.log('定位成功: ' + lat + ', ' + lon + ', ' + accuracy);
                
                // 在地图上显示标记
                if (window.map) {
                    var marker = L.marker([lat, lon]).addTo(window.map);
                    marker.bindPopup('我的位置<br>定位方式: 高德地图定位<br>精度: ' + Math.round(accuracy) + ' 米<br>位置: ' + location_detail).openPopup();
                    window.map.setView([lat, lon], 15); // 放大到更详细的级别
                }
            });

            // 监听定位失败事件
            geolocation.on('error', function(data) {
                console.log('[高德定位] ❌ 定位失败');
                console.log('[高德定位] 耗时: ' + (Date.now() - startTime) + 'ms');
                console.log('[高德定位] 错误数据: ' + JSON.stringify(data));
                
                var errorMsg = '高德地图定位失败: ' + (data.message || '未知错误');
                console.log('定位失败:' + errorMsg);
            });

            // 开始定位
            geolocation.getCurrentPosition();
        }

        // 综合定位函数
        function getLocation() {
            console.log('[定位] 开始综合定位...');
            console.log('[定位] navigator.geolocation 可用性: ' + (!!navigator.geolocation));

            // 检查网络连接
            if (!checkNetworkStatus()) {
                console.log('[定位] 网络离线，可能影响定位结果');
            }

            // 测试网络连接质量
            testNetworkConnectivity().then(function(networkResult) {
                if (networkResult.success) {
                    console.log('[定位] 网络连接良好，开始执行定位');
                    executeLocationFlow();
                } else {
                    console.log('[定位] 网络连接不稳定，尝试执行定位');
                    executeLocationFlow();
                }
            });
        }

        // 执行定位流程
        function executeLocationFlow() {
            var hasAmapApiKey = API_KEY_PLACEHOLDER;
            console.log('[定位] 高德地图API密钥状态: ' + (hasAmapApiKey ? '已配置' : '未配置'));

            // 优先尝试浏览器定位
            if (navigator.geolocation) {
                console.log('[定位] 浏览器支持定位，开始调用getCurrentPosition');

                var options = {
                    enableHighAccuracy: true,
                    timeout: 10000, // 缩短超时时间，快速失败
                    maximumAge: 0
                };
                console.log('[定位] 定位选项: ' + JSON.stringify(options));

                console.log('[定位] 正在调用getCurrentPosition...');
                
                // 记录开始时间
                var startTime = Date.now();
                
                navigator.geolocation.getCurrentPosition(
                    function(position) {
                        console.log('[定位] ✅ 浏览器定位成功');
                        console.log('[定位] 耗时: ' + (Date.now() - startTime) + 'ms');
                        
                        var lat = position.coords.latitude;
                        var lon = position.coords.longitude;
                        var accuracy = position.coords.accuracy;
                        var altitude = position.coords.altitude;
                        var altitudeAccuracy = position.coords.altitudeAccuracy;
                        var heading = position.coords.heading;
                        var speed = position.coords.speed;

                        console.log('[定位] 成功数据:');
                        console.log('[定位] 纬度: ' + lat);
                        console.log('[定位] 经度: ' + lon);
                        console.log('[定位] 精度: ' + accuracy + ' 米');
                        console.log('[定位] 海拔: ' + altitude);
                        console.log('[定位] 海拔精度: ' + altitudeAccuracy);
                        console.log('[定位] 方向: ' + heading);
                        console.log('[定位] 速度: ' + speed);

                        // 检查定位精度
                        if (accuracy > 1000) {
                            console.log('[定位] ⚠️ 浏览器定位精度较低，尝试使用高德地图定位提高精度');
                            getLocationByAmap();
                            return;
                        }

                        // 使用处理器期望的格式输出日志
                        console.log('定位成功: ' + lat + ', ' + lon + ', ' + accuracy);

                        // 在地图上显示标记
                        if (window.map) {
                            var marker = L.marker([lat, lon]).addTo(window.map);
                            marker.bindPopup('我的位置<br>定位方式: 浏览器定位<br>精度: ' + Math.round(accuracy) + ' 米').openPopup();
                            window.map.setView([lat, lon], 13);
                        }
                    },
                    function(error) {
                        console.log('[定位] ❌ 浏览器定位失败');
                        console.log('[定位] 耗时: ' + (Date.now() - startTime) + 'ms');
                        console.log('[定位] 错误代码: ' + error.code);
                        console.log('[定位] 错误消息: ' + error.message);
                        console.log('[定位] 错误对象: ' + JSON.stringify(error));

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
                        console.log('定位失败: ' + errorMsg);
                        
                        // 浏览器定位失败后，尝试使用高德地图定位API
                        console.log('[定位] 浏览器定位失败，尝试使用高德地图定位API...');
                        getLocationByAmap();
                    },
                    options
                );

                console.log('[定位] getCurrentPosition 已调用，等待回调...');
            } else {
                console.log('[定位] 浏览器不支持定位，直接尝试高德地图定位');
                getLocationByAmap();
            }
        }

        // 页面加载完成后测试
        window.testGeolocation = function() {
            console.log('[测试] 手动触发定位测试');
            getLocation();
        };

        // 尝试多次定位
        function tryMultipleLocationAttempts(maxAttempts = 3, delay = 2000) {
            let attempts = 0;
            
            function attemptLocation() {
                attempts++;
                console.log('[定位] 第 ' + attempts + ' 次尝试定位');
                
                getLocation();
                
                if (attempts < maxAttempts) {
                    setTimeout(attemptLocation, delay);
                }
            }
            
            attemptLocation();
        }

        document.addEventListener('DOMContentLoaded', function() {
            console.log('[定位] DOM加载完成');
            setTimeout(function() {
                var container = document.querySelector('.leaflet-container');
                if (container && container._leaflet_map) {
                    window.map = container._leaflet_map;
                    console.log('[定位] 地图对象获取成功，开始定位');
                    // 尝试多次定位以提高成功率
                    tryMultipleLocationAttempts(2, 3000);
                } else {
                    console.log('定位失败: 无法获取地图对象');
                }
            }, 1000);
        });
        </script>
        """
        map_obj.get_root().html.add_child(folium.Element(geolocation_script))

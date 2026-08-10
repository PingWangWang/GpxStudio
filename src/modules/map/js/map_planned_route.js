/**
 * 规划路线增量渲染：路线线 + 起终点/途径点标记（专用 LayerGroup，不重建地图页面）
 * 占位符：
 *   __ROUTE_JSON__   — 路线线段 JSON [[[lat,lng],...], ...]（GCJ-02，与地图渲染层一致）
 *   __MARKERS_JSON__ — 标记 JSON [{lat, lng, type: start|end|waypoint, label?, number?}, ...]
 *                      坐标 GCJ-02（gaode）/ WGS-84（其他地图源）
 *
 * window._plannedRouteLayer 复用：每次清空后重建"当前规划路线"图层，
 * 页面其他图层（收藏点/当前位置/库渲染路线）保持不动，避免全量重建 HTML 卡顿。
 */
(function () {
    try {
        var routeSegments = __ROUTE_JSON__;
        var markers = __MARKERS_JSON__;
        var map = window.map;
        if (!map) {
            var container = document.querySelector('.leaflet-container');
            if (container && container._leaflet_map) {
                map = window.map = container._leaflet_map;
            }
        }
        if (!map) {
            console.error('[规划路线] 无法获取地图对象');
            return false;
        }
        if (!window._plannedRouteLayer) {
            window._plannedRouteLayer = L.layerGroup().addTo(map);
        }
        window._plannedRouteLayer.clearLayers();

        // 路线线（保留分段结构，支持跨海/多段）
        if (routeSegments && routeSegments.length) {
            for (var i = 0; i < routeSegments.length; i++) {
                var seg = routeSegments[i];
                if (seg && seg.length >= 2) {
                    L.polyline(seg, {
                        color: '#459c50',
                        weight: 5,
                        opacity: 0.8,
                        smoothFactor: 1.5,  // 抽稀减少渲染点数（Leaflet 驼峰选项，缩放/平移性能关键）
                        noClip: true        // 不做 viewport 裁剪，降低 pan/zoom 逐帧开销
                    }).addTo(window._plannedRouteLayer);
                }
            }
        }

        // 起点/终点/途径点标记：统一为小圆点，不显示文字
        // 起点=绿 / 终点=红 / 途径点=蓝，白描边
        (markers || []).forEach(function (mk) {
            var bg = '#007bff';
            if (mk.type === 'start') {
                bg = '#28a745';
            } else if (mk.type === 'end') {
                bg = '#dc3545';
            }
            L.circleMarker([mk.lat, mk.lng], {
                radius: 5,
                color: '#ffffff',
                weight: 2,
                fillColor: bg,
                fillOpacity: 1,
                interactive: false  // 圆点无需鼠标交互，减少 pan/zoom 命中检测开销
            }).addTo(window._plannedRouteLayer);
        });
        return true;
    } catch (e) {
        console.error('[规划路线] 注入失败: ' + (e && e.message ? e.message : e));
        return false;
    }
})();

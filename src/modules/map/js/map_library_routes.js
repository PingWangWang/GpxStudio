/**
 * 路线管理库渲染路线：按路线 id 增量增删（每条路线独立 LayerGroup + id 索引）
 * 占位符：__PAYLOAD_JSON__ — JSON {add: [{id, coords, color, start, end, waypoints}], remove: [id]}
 *                            coords/start/end/waypoints 均为 GCJ-02（与地图渲染层一致）
 *
 * window._libRoutesLayer 复用总图层组，window._libRoutesById 记录 id → 该路线的 LayerGroup：
 * 渲染/取消渲染切换只移除取消的路线、只新增变化的路线，不再全量清空重建，
 * 渲染路线数量增大时开销恒定（仅随变化量），保持最优性能。
 */
(function () {
    function circleOpts(fill) {
        return {
            radius: 5,
            color: '#ffffff',
            weight: 2,
            fillColor: fill,
            fillOpacity: 1,
            interactive: false  // 圆点无需鼠标交互，减少 pan/zoom 命中检测开销
        };
    }

    try {
        var payload = __PAYLOAD_JSON__;
        var map = window.map;
        if (!map) {
            var container = document.querySelector('.leaflet-container');
            if (container && container._leaflet_map) {
                map = window.map = container._leaflet_map;
            }
        }
        if (!map) {
            console.error('[库路线] 无法获取地图对象');
            return false;
        }
        if (!window._libRoutesLayer) {
            window._libRoutesLayer = L.layerGroup().addTo(map);
        }
        if (!window._libRoutesById) {
            window._libRoutesById = {};
        }

        // 删除已取消渲染的路线（整组移除：折线 + 起终点/途径点圆点）
        var remove = payload.remove || [];
        for (var i = 0; i < remove.length; i++) {
            var rid = remove[i];
            if (window._libRoutesById[rid]) {
                window._libRoutesById[rid].remove();
                delete window._libRoutesById[rid];
            }
        }

        // 新增/更新渲染路线（仅操作变化的 id，已存在的跳过）
        var add = payload.add || [];
        for (var j = 0; j < add.length; j++) {
            var r = add[j];
            if (!r || !r.id || !r.coords || r.coords.length < 2) {
                continue;
            }
            if (window._libRoutesById[r.id]) {
                continue;
            }
            // 每条路线独立图层组：折线 + 起点（绿）/终点（红）/途径点（蓝）小圆点
            var group = L.layerGroup().addTo(window._libRoutesLayer);
            L.polyline(r.coords, {
                color: r.color || '#459c50',
                weight: 4,
                opacity: 0.8,
                smoothFactor: 1.5,  // 抽稀减少渲染点数（Leaflet 驼峰选项，缩放/平移性能关键）
                noClip: true        // 不做 viewport 裁剪，降低 pan/zoom 逐帧开销
            }).addTo(group);
            if (r.start) {
                L.circleMarker(r.start, circleOpts('#28a745')).addTo(group);
            }
            if (r.end) {
                L.circleMarker(r.end, circleOpts('#dc3545')).addTo(group);
            }
            (r.waypoints || []).forEach(function (w) {
                L.circleMarker(w, circleOpts('#007bff')).addTo(group);
            });
            window._libRoutesById[r.id] = group;
        }
        return true;
    } catch (e) {
        console.error('[库路线] 注入失败: ' + (e && e.message ? e.message : e));
        return false;
    }
})();

/**
 * 自动缩放：先判断当前视图是否已包含目标元素边界，未包含才执行适配
 * 占位符：__MIN_LAT__/__MIN_LNG__/__MAX_LAT__/__MAX_LNG__ — 目标边界（GCJ-02）
 *         __CENTER_LAT__/__CENTER_LNG__/__ZOOM__          — 单点回退中心/缩放
 *
 * 已包含 → 返回 'skip'（零开销，不刷新界面）；
 * 未包含 → fitBounds 精确适配（单点退化 setView 固定缩放），返回 'fitted'。
 */
(function () {
    function getMap() {
        if (window.map) {
            return window.map;
        }
        var container = document.querySelector('.leaflet-container');
        if (container && container._leaflet_map) {
            window.map = container._leaflet_map;
            return window.map;
        }
        return null;
    }

    // 边界面积（经纬度乘积）：Leaflet 1.9.3 的 LatLngBounds 无 getArea 方法
    // （曾在 1.x 早期移除，勿再使用），此处自行计算相对面积用于占比判断
    function areaOf(b) {
        var sw = b.getSouthWest(), ne = b.getNorthEast();
        return (ne.lat - sw.lat) * (ne.lng - sw.lng);
    }

    try {
        var map = getMap();
        if (!map) {
            console.error('[自动缩放] 无法获取地图对象');
            return false;
        }

        var target = L.latLngBounds(
            L.latLng(__MIN_LAT__, __MIN_LNG__),
            L.latLng(__MAX_LAT__, __MAX_LNG__)
        );
        var current = map.getBounds();
        console.log('[自动缩放] 目标: ' + target.toBBoxString() + ', 当前视野: ' + current.toBBoxString());

        // 判断是否需要刷新：仅"包含"不足——用户缩小视图后元素仍完整在视野内
        // （contains 恒真）会导致永远跳过；追加面积占比阈值：
        // 目标边界面积占当前视野 < 50% 说明视图被过度缩小，需重新适配放大
        var ratio = areaOf(target) / Math.max(areaOf(current), 1e-9);
        console.log('[自动缩放] 面积占比: ' + ratio.toFixed(3) + ', contains: ' + current.contains(target));
        if (current.contains(target) && ratio > 0.5) {
            console.log('[自动缩放] 视图已适配，跳过刷新');
            return 'skip';
        }

        // 单点退化：固定缩放级别；多点：fitBounds 精确适配（含 padding 余量）
        if (target.getSouthWest().equals(target.getNorthEast())) {
            map.setView(target.getCenter(), __ZOOM__);
            console.log('[自动缩放] 单点 setView 执行');
        } else {
            map.fitBounds(target, { padding: [20, 20] });
            console.log('[自动缩放] fitBounds 已执行');
        }
        return 'fitted';
    } catch (e) {
        console.error('[自动缩放] 执行异常: ' + (e && e.message ? e.message : e));
        return false;
    }
})();

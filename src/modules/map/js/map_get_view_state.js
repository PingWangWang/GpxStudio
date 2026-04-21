/**
 * 获取当前地图视图状态（中心点坐标 + 缩放级别）
 * 返回 {lat, lon, zoom} 或 null（地图对象未找到时）
 */
(function () {
    try {
        var map = null;
        for (var key in window) {
            if (key.startsWith('map_') && window[key] &&
                typeof window[key].getCenter === 'function' &&
                typeof window[key].getZoom === 'function') {
                map = window[key];
                break;
            }
        }
        if (!map) { return null; }
        var center = map.getCenter();
        var zoom = map.getZoom();
        return { lat: center.lat, lon: center.lng, zoom: zoom };
    } catch (e) {
        console.error('[视图状态] 获取失败:', e);
        return null;
    }
})();

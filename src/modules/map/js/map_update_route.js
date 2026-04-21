/**
 * 更新地图上的路线图层（保留当前视图位置）
 *
 * 占位符：
 *   __ROUTE_COORDS_JSON__  — JSON 数组，格式为 [[[lat,lon],...], ...]（多段线）
 *
 * 返回 true（成功）或 false（失败）
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

        if (!map) {
            console.log('[路线更新] 错误: 无法获取地图对象，稍后会自动重试');
            return false;
        }

        if (typeof L === 'undefined') {
            console.log('[路线更新] 错误: Leaflet库(L)未定义');
            return false;
        }

        var currentCenter = map.getCenter();
        var currentZoom = map.getZoom();
        console.log('[路线更新] 保存当前视图 - 中心: [' + currentCenter.lat.toFixed(6) + ', ' + currentCenter.lng.toFixed(6) + '], 缩放: ' + currentZoom);

        var layersToRemove = [];
        map.eachLayer(function (layer) {
            if (layer instanceof L.Polyline) { layersToRemove.push(layer); }
        });
        console.log('[路线更新] 找到 ' + layersToRemove.length + ' 个Polyline层，准备删除');
        layersToRemove.forEach(function (layer) { map.removeLayer(layer); });

        var routeSegments = __ROUTE_COORDS_JSON__;
        if (!Array.isArray(routeSegments) || routeSegments.length === 0) {
            console.log('[路线更新] 错误: 路线数据无效');
            return false;
        }

        var routeLine = L.polyline(routeSegments, {
            color: 'blue', weight: 5, opacity: 0.7,
            smoothFactor: 1.5, noClip: true
        });
        routeLine.addTo(map);
        map.setView(currentCenter, currentZoom, { animate: false });
        console.log('[路线更新] 已恢复视图位置');

        var totalPoints = 0;
        if (routeSegments.length > 0 && Array.isArray(routeSegments[0][0])) {
            routeSegments.forEach(function (seg) { totalPoints += seg.length; });
        } else {
            totalPoints = routeSegments.length;
        }
        console.log('[路线更新] ✅ 成功更新路线: ' + routeSegments.length + ' 段, 共 ' + totalPoints + ' 个点');
        return true;
    } catch (e) {
        console.log('[路线更新] ❌ 异常: ' + e.name + ' - ' + e.message);
        console.log('[路线更新] 堆栈: ' + e.stack);
        return false;
    }
})();

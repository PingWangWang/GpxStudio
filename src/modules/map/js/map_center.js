/**
 * 地图平移到指定中心点并添加箭头标记
 * 占位符：__LAT__  — 纬度（数值）
 *         __LON__  — 经度（数值）
 */
(function () {
    console.log('[地图中心] 开始执行设置中心点逻辑');
    console.log('[地图中心] 目标坐标: __LAT__, __LON__');

    function panToCenter() {
        console.log('[地图中心] panToCenter 函数被调用');

        var map = window.map;
        console.log('[地图中心] 检查 window.map: ' + (map ? '存在' : '不存在'));

        if (!map) {
            var container = document.querySelector('.leaflet-container');
            console.log('[地图中心] 尝试从 DOM 获取地图，container: ' + (container ? '存在' : '不存在'));
            if (container && container._leaflet_map) {
                map = container._leaflet_map;
                window.map = map;
                console.log('[地图中心] 从 DOM 成功获取地图对象');
            }
        }

        if (!map) {
            console.error('[地图中心] 无法获取地图对象');
            return false;
        }

        try {
            console.log('[地图中心] 地图对象已获取');

            var currentCenter = map.getCenter();
            var currentZoom = map.getZoom();
            console.log('[地图中心] 当前地图中心: ' + currentCenter.lat.toFixed(6) + ', ' + currentCenter.lng.toFixed(6) + ', 缩放: ' + currentZoom);

            var latLng = new L.LatLng(__LAT__, __LON__);
            console.log('[地图中心] 创建坐标对象成功: ' + latLng.lat + ', ' + latLng.lng);

            if (typeof map.panTo !== 'function') {
                console.error('[地图中心] map.panTo 不是一个函数');
                return false;
            }

            console.log('[地图中心] 调用 map.panTo()');
            map.panTo(latLng, { animate: true, duration: 1 });
            console.log('[地图中心] panTo 方法已调用');

            var moveEndHandler = function () {
                var newCenter = map.getCenter();
                console.log('[地图中心] moveend 事件触发，新中心: ' + newCenter.lat.toFixed(6) + ', ' + newCenter.lng.toFixed(6));
                map.off('moveend', moveEndHandler);
            };
            map.on('moveend', moveEndHandler);

            // 移除旧标记
            if (window.centerMarker) {
                map.removeLayer(window.centerMarker);
                console.log('[地图中心] 旧标记已移除');
            }

            // 创建水滴状定位图标（蓝色）
            var arrowIcon = L.icon({
                iconUrl: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><path d="M20 5C12.8 5 7 10.8 7 18c0 10 13 21 13 21s13-11 13-21c0-7.2-5.8-13-13-13zm0 20c-4.4 0-8-3.6-8-8s3.6-8 8-8 8 3.6 8 8-3.6 8-8 8z" fill="%231890ff"/><path d="M20 12c-2.2 0-4 1.8-4 4s1.8 4 4 4 4-1.8 4-4-1.8-4-4-4zm0 6c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2z" fill="white"/></svg>',
                iconSize: [40, 40],
                iconAnchor: [20, 40],
                popupAnchor: [0, -40]
            });
            console.log('[地图中心] 箭头图标已创建');

            window.centerMarker = L.marker(latLng, { icon: arrowIcon });
            window.centerMarker.addTo(map);
            console.log('[地图中心] 箭头标记已添加');

            setTimeout(function () {
                var finalCenter = map.getCenter();
                console.log('[地图中心] 100ms 后检查 - 地图中心: ' + finalCenter.lat.toFixed(6) + ', ' + finalCenter.lng.toFixed(6));
            }, 100);

            return true;
        } catch (e) {
            console.error('[地图中心] 执行失败:', e);
            console.error('[地图中心] 错误消息:', e.message);
            console.error('[地图中心] 错误堆栈:', e.stack);
            return false;
        }
    }

    // 立即尝试平移
    console.log('[地图中心] 立即尝试平移');
    if (!panToCenter()) {
        // 如果失败，在 500ms 后重试
        console.log('[地图中心] 第一次失败，将在 500ms 后重试');
        setTimeout(function () {
            console.log('[地图中心] 执行重试');
            panToCenter();
        }, 500);
    }
})();

/**
 * 地图缩放操作
 * 占位符：__DIRECTION__  — 'in' 放大 / 'out' 缩小
 */
(function () {
    var map = null;

    // 方法1: 通过 leaflet-container 元素
    var mapElement = document.querySelector('.leaflet-container');
    if (mapElement && mapElement._leaflet_map) {
        map = mapElement._leaflet_map;
    }

    // 方法2: 查找全局地图对象
    if (!map) {
        for (var key in window) {
            if (key.startsWith('map_') && window[key] && window[key].zoomIn) {
                map = window[key];
                break;
            }
        }
    }

    if (map) {
        if ('__DIRECTION__' === 'in') {
            map.zoomIn();
            console.log('[缩放] 放大地图成功，当前级别: ' + map.getZoom());
        } else {
            map.zoomOut();
            console.log('[缩放] 缩小地图成功，当前级别: ' + map.getZoom());
        }
    } else {
        console.log('[缩放] 未找到地图对象');
    }
})();

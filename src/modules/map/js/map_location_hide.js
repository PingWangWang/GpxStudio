/**
 * 增量隐藏当前位置标识
 * 返回 {success, message}：true 表示标识已移除
 *
 * 说明：定位标识渲染时携带 Leaflet options.markerType = 'location'
 * （来自 Python 侧 marker_type），遍历地图标记按类型精确匹配后移除，
 * 不触发页面重载，视图位置保持不变。
 */
(function () {
    var result = {
        success: false,
        message: ''
    };

    // 查找 Leaflet 地图实例
    var map = null;
    for (var key in window) {
        if (key.startsWith('map_') && window[key] && window[key].eachLayer) {
            map = window[key];
            break;
        }
    }

    if (!map) {
        result.message = '未找到地图实例';
        return result;
    }

    // 按 markerType 匹配并移除定位标识
    var removed = false;
    map.eachLayer(function (layer) {
        if (layer instanceof L.Marker &&
            layer.options && layer.options.markerType === 'location') {
            map.removeLayer(layer);
            removed = true;
            console.log('[定位标识] JS 增量隐藏标识');
        }
    });

    result.success = removed;
    result.message = removed ? '定位标识已隐藏' : '未找到定位标识';
    return result;
})();

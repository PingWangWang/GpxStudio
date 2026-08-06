/**
 * 增量移除单个收藏点星标
 * 占位符：__FAV_ID__ — 收藏点ID（整数）
 * 返回 {success, message}：true 表示星标已移除
 *
 * 说明：收藏星标渲染时携带 Leaflet options.favId（来自 Python 侧 fav_id），
 * 遍历地图标记按 favId 精确匹配后移除，不触发页面重载，视图位置保持不变。
 */
(function () {
    var favId = __FAV_ID__;
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

    // 按 favId 匹配并移除收藏星标
    var removed = false;
    map.eachLayer(function (layer) {
        if (layer instanceof L.Marker &&
            layer.options && layer.options.favId === favId) {
            map.removeLayer(layer);
            removed = true;
            console.log('[收藏点] JS 增量移除星标: id=' + favId);
        }
    });

    result.success = removed;
    result.message = removed ? '收藏星标已移除' : '未找到匹配的收藏星标';
    return result;
})();

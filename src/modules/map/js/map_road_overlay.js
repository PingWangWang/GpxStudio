/**
 * 路网图层显示/隐藏控制
 * 占位符：__SHOW_ROADS__  — 'true' 显示 / 'false' 隐藏
 */
(function () {
    var map = null;
    var result = {
        success: false,
        message: '',
        layerCount: 0,
        roadLayerFound: false
    };

    // 查找 Leaflet 地图实例
    for (var key in window) {
        if (key.startsWith('map_') && window[key] && window[key]._container) {
            map = window[key];
            result.mapFound = true;
            console.log('[路网切换] 找到地图实例: ' + key);
            break;
        }
    }

    if (!map) {
        console.error('[路网切换] 未找到地图实例');
        result.message = '未找到地图实例';
        return result;
    }

    var showRoads = __SHOW_ROADS__;

    // 初始化路网图层缓存（如果不存在）
    if (!map._roadLayers) {
        map._roadLayers = [];
    }

    // 首先尝试从缓存中获取路网图层
    if (map._roadLayers.length > 0) {
        console.log('[路网切换] 从缓存中找到', map._roadLayers.length, '个路网图层');
        result.roadLayerFound = true;

        map._roadLayers.forEach(function (layer) {
            var hasLayer = map.hasLayer(layer);
            console.log('[路网切换] 缓存图层状态 hasLayer:', hasLayer);

            if (showRoads) {
                if (!hasLayer) {
                    map.addLayer(layer);
                    console.log('[路网切换] 从缓存添加路网图层');
                }
            } else {
                if (hasLayer) {
                    map.removeLayer(layer);
                    console.log('[路网切换] 移除路网图层到缓存');
                }
            }
        });

        result.success = true;
        result.message = showRoads ? '路网图层已显示' : '路网图层已隐藏';
    } else {
        // 缓存为空，从地图中查找并缓存路网图层
        console.log('[路网切换] 缓存为空，开始查找路网图层');

        map.eachLayer(function (layer) {
            result.layerCount++;

            if (layer instanceof L.TileLayer) {
                var layerName = layer.options.name || '';
                var layerUrl = layer._url || '';

                // 通过名称或 URL 识别路网图层
                if (layerName.indexOf('标注') !== -1 ||
                    layerName.indexOf('Labels') !== -1 ||
                    layerUrl.indexOf('style=8') !== -1 ||
                    layerUrl.indexOf('voyager_only_labels') !== -1) {

                    console.log('[路网切换] 找到路网图层并加入缓存:', layerName || layerUrl);
                    map._roadLayers.push(layer);
                    result.roadLayerFound = true;

                    var hasLayer = map.hasLayer(layer);

                    if (showRoads) {
                        if (!hasLayer) {
                            map.addLayer(layer);
                            console.log('[路网切换] 执行 addLayer');
                        }
                    } else {
                        if (hasLayer) {
                            map.removeLayer(layer);
                            console.log('[路网切换] 执行 removeLayer');
                        }
                    }

                    result.success = true;
                }
            }
        });

        if (result.roadLayerFound) {
            result.message = showRoads ? '路网图层已显示' : '路网图层已隐藏';
        } else {
            result.message = '未找到路网图层（可能当前不是卫星模式）';
        }
    }

    console.log('[路网切换] 操作完成 - 缓存图层数:', map._roadLayers.length);

    return result;
})();

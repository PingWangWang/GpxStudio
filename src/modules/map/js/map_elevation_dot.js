/**
 * 海拔剖面图悬停联动：在地图路线上显示/更新当前位置圆点
 * 占位符：__LAT__  — 纬度（数值，GCJ-02）
 *         __LON__  — 经度（数值，GCJ-02）
 *
 * 圆点实例保存在 window.elevationDot：首次创建，后续 setLatLng 复用
 * （避免悬停移动时反复建/删图层）。
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

    var map = getMap();
    if (!map) {
        console.error('[海拔圆点] 无法获取地图对象');
        return false;
    }

    var latLng = new L.LatLng(__LAT__, __LON__);

    if (window.elevationDot) {
        // 已存在：直接移动圆点到新位置
        window.elevationDot.setLatLng(latLng);
    } else {
        // 首次：创建强调蓝实心圆点（高 zIndexOffset 确保显示在路线之上）
        window.elevationDot = L.circleMarker(latLng, {
            radius: 6,
            color: '#1890ff',
            weight: 2,
            fillColor: '#1890ff',
            fillOpacity: 0.9,
            zIndexOffset: 1000
        });
        window.elevationDot.addTo(map);
    }
    return true;
})();

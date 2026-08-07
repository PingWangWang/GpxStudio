/**
 * 海拔剖面图悬停联动：隐藏地图路线上的当前位置圆点
 * （鼠标离开折线图时调用，移除 window.elevationDot 图层）
 */
(function () {
    if (!window.elevationDot) {
        return true;
    }
    var container = document.querySelector('.leaflet-container');
    var map = window.map || (container && container._leaflet_map);
    if (map) {
        map.removeLayer(window.elevationDot);
    }
    window.elevationDot = null;
    return true;
})();

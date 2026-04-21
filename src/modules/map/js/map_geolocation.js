/**
 * 触发浏览器 Geolocation API 定位请求
 * 结果通过 console.log 上报给 Python 拦截层
 */
if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
        function (p) {
            console.log('定位成功:' + p.coords.latitude + ',' + p.coords.longitude + ',' + p.coords.accuracy);
        },
        function (e) {
            console.log('定位失败:' + e.message);
        },
        { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
    );
} else {
    console.log('定位失败: 浏览器不支持定位');
}

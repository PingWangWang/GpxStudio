#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地图 JavaScript 调用封装层

将所有 runJavaScript 调用集中到此模块，消除 app.py 中的内联 JS 字符串。
JS 代码存放在同目录的 js/ 子目录中，首次加载后缓存到内存。
"""

import json
import logging
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)

_JS_DIR = Path(__file__).parent / 'js'
_cache: dict = {}


def _load(filename: str) -> str:
    """加载 JS 文件内容，结果缓存到内存。"""
    if filename not in _cache:
        path = _JS_DIR / filename
        try:
            _cache[filename] = path.read_text(encoding='utf-8')
            logger.debug(f"[JsBridge] 已加载 JS 文件: {filename}")
        except FileNotFoundError:
            logger.error(f"[JsBridge] JS 文件不存在: {path}")
            raise
    return _cache[filename]


class MapJsBridge:
    """封装所有地图 JS 调用，统一管理 JavaScript 代码。

    所有方法均为类方法，接受 ``page`` 参数（QWebEnginePage 实例）。
    """

    # ------------------------------------------------------------------
    # 缩放
    # ------------------------------------------------------------------

    @classmethod
    def zoom_in(cls, page) -> None:
        """放大地图一级。"""
        js = _load('map_zoom.js').replace('__DIRECTION__', 'in')
        page.runJavaScript(js)

    @classmethod
    def zoom_out(cls, page) -> None:
        """缩小地图一级。"""
        js = _load('map_zoom.js').replace('__DIRECTION__', 'out')
        page.runJavaScript(js)

    # ------------------------------------------------------------------
    # 路网图层
    # ------------------------------------------------------------------

    @classmethod
    def set_road_overlay(
        cls,
        page,
        show: bool,
        callback: Optional[Callable] = None,
    ) -> None:
        """显示或隐藏卫星图上的路网标注图层。

        Args:
            page:     QWebEnginePage 实例。
            show:     True 显示路网，False 隐藏。
            callback: JS 执行完成后的回调，接收返回值 dict。
        """
        js = _load('map_road_overlay.js').replace('__SHOW_ROADS__', str(show).lower())
        if callback:
            page.runJavaScript(js, callback)
        else:
            page.runJavaScript(js)

    # ------------------------------------------------------------------
    # 自动缩放
    # ------------------------------------------------------------------

    @classmethod
    def fit_bounds(cls, page, bounds_json: str, center_lat: float, center_lng: float,
                   zoom: int) -> None:
        """自动缩放：当前视图已包含目标边界则跳过，否则精确适配（不重建地图）。

        JS 侧用 map.getBounds().contains() 判断是否需要刷新：
        已包含 → 零开销跳过；未包含 → fitBounds（单点退化 setView）。

        Args:
            page:        QWebEnginePage 实例。
            bounds_json: 目标边界 JSON [[min_lat, min_lng], [max_lat, max_lng]]（GCJ-02）。
            center_lat:  单点回退中心纬度（GCJ-02）。
            center_lng:  单点回退中心经度（GCJ-02）。
            zoom:        单点回退缩放级别。
        """
        b = json.loads(bounds_json)
        js = (
            _load('map_fit_bounds.js')
            .replace('__MIN_LAT__', str(b[0][0]))
            .replace('__MIN_LNG__', str(b[0][1]))
            .replace('__MAX_LAT__', str(b[1][0]))
            .replace('__MAX_LNG__', str(b[1][1]))
            .replace('__CENTER_LAT__', str(center_lat))
            .replace('__CENTER_LNG__', str(center_lng))
            .replace('__ZOOM__', str(zoom))
        )
        page.runJavaScript(js)

    # ------------------------------------------------------------------
    # 中心点平移
    # ------------------------------------------------------------------

    @classmethod
    def pan_to_center(cls, page, lat: float, lon: float) -> None:
        """将地图平移到指定坐标并添加箭头标记。

        Args:
            page: QWebEnginePage 实例。
            lat:  纬度。
            lon:  经度。
        """
        js = (
            _load('map_center.js')
            .replace('__LAT__', str(lat))
            .replace('__LON__', str(lon))
        )
        page.runJavaScript(js)

    # ------------------------------------------------------------------
    # 浏览器定位
    # ------------------------------------------------------------------

    @classmethod
    def trigger_browser_location(cls, page) -> None:
        """触发浏览器 Geolocation API 定位请求。

        结果通过 console.log 上报，由 ConsoleWebEnginePage 拦截处理。
        """
        page.runJavaScript(_load('map_geolocation.js'))

    # ------------------------------------------------------------------
    # 视图状态读取
    # ------------------------------------------------------------------

    @classmethod
    def get_view_state(cls, page, callback: Callable) -> None:
        """异步读取当前地图中心坐标和缩放级别。

        Args:
            page:     QWebEnginePage 实例。
            callback: 接收结果字典 ``{lat, lon, zoom}`` 或 ``None`` 的回调。
        """
        page.runJavaScript(_load('map_get_view_state.js'), callback)

    # ------------------------------------------------------------------
    # 路线更新
    # ------------------------------------------------------------------

    @classmethod
    def update_route(cls, page, coords_json: str, callback: Callable) -> None:
        """在地图上更新路线图层（保留当前视图位置）。

        Args:
            page:        QWebEnginePage 实例。
            coords_json: JSON 字符串，格式为 ``[[[lat,lon],...],...]``（多段线）。
            callback:    接收布尔结果（True=成功）的回调。
        """
        js = _load('map_update_route.js').replace('__ROUTE_COORDS_JSON__', coords_json)
        page.runJavaScript(js, callback)

    # ------------------------------------------------------------------
    # 收藏点
    # ------------------------------------------------------------------

    @classmethod
    def remove_favorite(cls, page, fav_id: int, callback: Optional[Callable] = None) -> None:
        """增量移除单个收藏点星标（不重载页面，保持视图位置）。

        Args:
            page:    QWebEnginePage 实例。
            fav_id:  收藏点ID（渲染时已写入星标 options.favId）。
            callback: 可选回调，接收结果字典 {success, message}。
        """
        js = _load('map_favorites_remove.js').replace('__FAV_ID__', str(fav_id))
        if callback:
            page.runJavaScript(js, callback)
        else:
            page.runJavaScript(js)

    # ------------------------------------------------------------------
    # 定位标识
    # ------------------------------------------------------------------

    @classmethod
    def hide_location_marker(cls, page, callback: Optional[Callable] = None) -> None:
        """增量隐藏当前位置标识（不重载页面，保持视图位置）。

        Args:
            page:    QWebEnginePage 实例。
            callback: 可选回调，接收结果字典 {success, message}。
        """
        js = _load('map_location_hide.js')
        if callback:
            page.runJavaScript(js, callback)
        else:
            page.runJavaScript(js)

    # ------------------------------------------------------------------
    # 海拔剖面悬停圆点
    # ------------------------------------------------------------------

    @classmethod
    def update_elevation_dot(cls, page, lat: float, lon: float) -> None:
        """在地图路线上更新/创建海拔悬停定位圆点（不重载页面）。

        折线图悬停时调用：首次创建圆点，后续 setLatLng 移动复用实例，
        避免高频悬停下反复建删图层。

        Args:
            page: QWebEnginePage 实例。
            lat:  纬度（GCJ-02）。
            lon:  经度（GCJ-02）。
        """
        js = (
            _load('map_elevation_dot.js')
            .replace('__LAT__', str(lat))
            .replace('__LON__', str(lon))
        )
        page.runJavaScript(js)

    @classmethod
    def hide_elevation_dot(cls, page) -> None:
        """隐藏海拔悬停定位圆点（鼠标离开折线图时调用）。"""
        page.runJavaScript(_load('map_elevation_dot_hide.js'))

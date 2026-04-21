#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地图 JavaScript 调用封装层

将所有 runJavaScript 调用集中到此模块，消除 app.py 中的内联 JS 字符串。
JS 代码存放在同目录的 js/ 子目录中，首次加载后缓存到内存。
"""

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

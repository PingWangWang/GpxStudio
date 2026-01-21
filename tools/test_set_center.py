#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试"设为地图中心点"功能的诊断脚本
"""

import sys
import json
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QSpinBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWebEngineWidgets import QWebEngineView

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestMapPanTo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("设为地图中心点功能测试")
        self.setGeometry(100, 100, 1400, 800)

        # 创建中央小部件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 创建地图视图
        self.map_view = QWebEngineView()
        layout.addWidget(self.map_view)

        # 创建控制面板
        control_layout = QVBoxLayout()

        # 纬度输入
        lat_layout = QVBoxLayout()
        lat_layout.addWidget(QLabel("目标纬度:"))
        self.lat_spin = QSpinBox()
        self.lat_spin.setRange(-90, 90)
        self.lat_spin.setValue(39)
        self.lat_spin.setDecimals(6) if hasattr(self.lat_spin, 'setDecimals') else None
        lat_layout.addWidget(self.lat_spin)
        control_layout.addLayout(lat_layout)

        # 经度输入
        lon_layout = QVBoxLayout()
        lon_layout.addWidget(QLabel("目标经度:"))
        self.lon_spin = QSpinBox()
        self.lon_spin.setRange(-180, 180)
        self.lon_spin.setValue(116)
        self.lon_spin.setDecimals(6) if hasattr(self.lon_spin, 'setDecimals') else None
        lon_layout.addWidget(self.lon_spin)
        control_layout.addLayout(lon_layout)

        # 测试按钮
        test_btn = QPushButton("测试平移到目标位置")
        test_btn.clicked.connect(self.test_pan_to)
        control_layout.addWidget(test_btn)

        # 重置按钮
        reset_btn = QPushButton("重置地图（回到北京）")
        reset_btn.clicked.connect(self.reset_map)
        control_layout.addWidget(reset_btn)

        # 状态标签
        self.status_label = QLabel("准备就绪")
        control_layout.addWidget(self.status_label)

        layout.addLayout(control_layout)

        # 加载地图
        self.load_initial_map()

    def load_initial_map(self):
        """加载初始地图"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" />
            <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
            <style>
                * { margin: 0; padding: 0; }
                html, body { height: 100%; }
                #map { height: 100%; }
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                console.log('[测试] 页面加载开始');

                // 创建地图
                window.map = L.map('map').setView([39.9042, 116.4074], 10);
                console.log('[测试] 地图对象创建成功');

                // 添加地图层
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '© OpenStreetMap contributors',
                    maxZoom: 19
                }).addTo(window.map);
                console.log('[测试] 地图瓦片加载完成');

                // 添加初始标记
                var initialMarker = L.marker([39.9042, 116.4074]).addTo(window.map);
                initialMarker.bindPopup('初始位置（北京中心）');
                console.log('[测试] 初始标记添加完成');

                // 监听地图事件
                window.map.on('move', function() {
                    console.log('[地图事件] 地图移动中...');
                });

                window.map.on('moveend', function() {
                    var center = window.map.getCenter();
                    console.log('[地图事件] 地图移动完成，中心: ' + center.lat.toFixed(4) + ', ' + center.lng.toFixed(4));
                });

                console.log('[测试] 页面加载完成，地图已就绪');
            </script>
        </body>
        </html>
        """

        self.map_view.setHtml(html_content)
        self.status_label.setText("地图已加载")
        logger.info("[测试] 初始地图已加载")

    def test_pan_to(self):
        """测试平移功能"""
        lat = self.lat_spin.value()
        lon = self.lon_spin.value()

        self.status_label.setText(f"正在平移到 ({lat}, {lon})...")
        logger.info(f"[测试] 开始平移到坐标: ({lat}, {lon})")

        # JavaScript 测试代码
        js_code = f"""
        (function() {{
            console.log('[测试平移] 开始执行平移逻辑');
            console.log('[测试平移] 目标坐标: {lat}, {lon}');

            function doTest() {{
                console.log('[测试平移] 检查地图对象');
                var map = window.map;

                if (!map) {{
                    console.error('[测试平移] window.map 不存在');
                    return false;
                }}

                console.log('[测试平移] 地图对象获取成功');
                console.log('[测试平移] 当前地图中心: ' + map.getCenter().lat + ', ' + map.getCenter().lng);
                console.log('[测试平移] 当前缩放级别: ' + map.getZoom());

                try {{
                    // 创建目标坐标
                    var targetLatLng = new L.LatLng({lat}, {lon});
                    console.log('[测试平移] 目标坐标对象创建成功');

                    // 调用 panTo
                    console.log('[测试平移] 调用 map.panTo()');
                    map.panTo(targetLatLng, {{animate: true, duration: 1}});
                    console.log('[测试平移] map.panTo() 方法已调用');

                    // 等待100ms后检查
                    setTimeout(function() {{
                        var newCenter = map.getCenter();
                        console.log('[测试平移] 平移后地图中心: ' + newCenter.lat.toFixed(6) + ', ' + newCenter.lng.toFixed(6));
                        console.log('[测试平移] 平移完成');
                    }}, 100);

                    // 添加标记
                    if (window.testMarker) {{
                        map.removeLayer(window.testMarker);
                    }}
                    window.testMarker = L.marker(targetLatLng, {{
                        icon: L.icon({{
                            iconUrl: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="40" height="40" fill="%232196F3"><path d="M7 10l5-5 5 5z"/></svg>',
                            iconSize: [40, 40],
                            iconAnchor: [20, 40],
                            popupAnchor: [0, -40]
                        }})
                    }});
                    window.testMarker.addTo(map);
                    window.testMarker.bindPopup('目标位置: {lat}, {lon}').openPopup();
                    console.log('[测试平移] 标记已添加');

                    return true;
                }} catch(e) {{
                    console.error('[测试平移] 执行出错:', e);
                    console.error('[测试平移] 错误: ' + e.message);
                    return false;
                }}
            }}

            // 立即执行测试
            console.log('[测试平移] 立即执行测试');
            var result = doTest();
            console.log('[测试平移] 测试结果: ' + (result ? '成功' : '失败'));

            // 如果失败，3秒后重试
            if (!result) {{
                console.log('[测试平移] 将在3秒后重试');
                setTimeout(function() {{
                    console.log('[测试平移] 执行重试');
                    doTest();
                }}, 3000);
            }}
        }})();
        """

        self.map_view.page().runJavaScript(js_code)

    def reset_map(self):
        """重置地图到北京"""
        self.status_label.setText("重置地图到北京...")
        logger.info("[测试] 重置地图")

        js_code = """
        (function() {
            console.log('[重置地图] 开始重置');
            if (window.map) {
                var beij = new L.LatLng(39.9042, 116.4074);
                window.map.panTo(beij);
                console.log('[重置地图] 地图已重置');
            }
        })();
        """

        self.map_view.page().runJavaScript(js_code)
        self.status_label.setText("地图已重置到北京")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TestMapPanTo()
    window.show()

    logger.info("[测试] 应用程序启动")
    sys.exit(app.exec_())

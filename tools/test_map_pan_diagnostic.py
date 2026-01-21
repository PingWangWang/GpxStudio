#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地图平移诊断工具 - 测试 panTo、setView 等不同的地图移动方法
"""

import sys
import time
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QDoubleSpinBox, QTextEdit)
from PyQt5.QtWebEngineWidgets import QWebEngineView


class MapPanDiagnostic(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("地图平移诊断工具")
        self.setGeometry(100, 100, 1600, 900)

        main_layout = QVBoxLayout()

        # 顶部控制面板
        control_box = QVBoxLayout()

        # 坐标输入
        coord_layout = QHBoxLayout()
        coord_layout.addWidget(QLabel("纬度:"))
        self.lat_spin = QDoubleSpinBox()
        self.lat_spin.setRange(-90, 90)
        self.lat_spin.setValue(40.194610)
        self.lat_spin.setDecimals(6)
        coord_layout.addWidget(self.lat_spin)

        coord_layout.addWidget(QLabel("经度:"))
        self.lon_spin = QDoubleSpinBox()
        self.lon_spin.setRange(-180, 180)
        self.lon_spin.setValue(117.012634)
        self.lon_spin.setDecimals(6)
        coord_layout.addWidget(self.lon_spin)
        control_box.addLayout(coord_layout)

        # 测试按钮
        button_layout = QHBoxLayout()
        pan_btn = QPushButton("panTo 测试")
        pan_btn.clicked.connect(self.execute_pan_test)
        button_layout.addWidget(pan_btn)

        setview_btn = QPushButton("setView 测试")
        setview_btn.clicked.connect(self.execute_setview_test)
        button_layout.addWidget(setview_btn)

        check_btn = QPushButton("检查地图状态")
        check_btn.clicked.connect(self.check_map_state)
        button_layout.addWidget(check_btn)

        reset_btn = QPushButton("重置到北京")
        reset_btn.clicked.connect(self.reset_to_beijing)
        button_layout.addWidget(reset_btn)

        clear_btn = QPushButton("清除日志")
        clear_btn.clicked.connect(self.clear_log)
        button_layout.addWidget(clear_btn)

        control_box.addLayout(button_layout)
        main_layout.addLayout(control_box)

        # 中间：地图区域
        self.map_view = QWebEngineView()
        main_layout.addWidget(self.map_view, stretch=2)

        # 底部：日志输出
        log_label = QLabel("控制台输出:")
        main_layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        self.log_text.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-family: 'Courier New';")
        main_layout.addWidget(self.log_text)

        self.setLayout(main_layout)

        # 加载地图（必须在 log_text 初始化后）
        self.load_map()

    def log(self, message):
        """添加日志"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_log(self):
        """清除日志"""
        self.log_text.clear()

    def load_map(self):
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
                console.log('[初始化] 页面加载开始');

                // 创建地图
                window.map = L.map('map').setView([39.9042, 116.4074], 10);
                console.log('[初始化] 地图对象创建成功');

                // 添加地图层
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '© OpenStreetMap contributors',
                    maxZoom: 19
                }).addTo(window.map);
                console.log('[初始化] 地图瓦片加载完成');

                // 添加初始标记
                window.initialMarker = L.marker([39.9042, 116.4074]).addTo(window.map);
                window.initialMarker.bindPopup('初始位置（北京）').openPopup();

                // 监听地图事件
                window.map.on('moveend', function() {
                    var center = window.map.getCenter();
                    console.log('[地图事件] moveend - 中心: ' + center.lat.toFixed(6) + ',' + center.lng.toFixed(6));
                });

                console.log('[初始化] 页面加载完成，地图已就绪');
            </script>
        </body>
        </html>
        """

        self.map_view.setHtml(html_content)
        self.log("[初始化] 地图已加载")

    def check_map_state(self):
        """检查地图状态"""
        self.log("[检查] 正在获取地图状态...")
        js_code = """
        (function() {
            if (!window.map) {
                console.log('[检查] 地图对象不存在');
                return;
            }

            var center = window.map.getCenter();
            var zoom = window.map.getZoom();
            console.log('[检查] 地图中心: ' + center.lat.toFixed(6) + ', ' + center.lng.toFixed(6));
            console.log('[检查] 缩放级别: ' + zoom);
            console.log('[检查] panTo 可用: ' + (typeof window.map.panTo === 'function'));
            console.log('[检查] setView 可用: ' + (typeof window.map.setView === 'function'));
        })();
        """
        self.map_view.page().runJavaScript(js_code)

    def execute_pan_test(self):
        """执行 panTo 测试"""
        lat = self.lat_spin.value()
        lon = self.lon_spin.value()

        self.log(f"[panTo] 开始测试，目标: ({lat}, {lon})")

        js_code = f"""
        (function() {{
            console.log('[panTo] 测试开始');

            if (!window.map) {{
                console.error('[panTo] 地图对象不存在');
                return;
            }}

            try {{
                var before = window.map.getCenter();
                console.log('[panTo] 当前中心: ' + before.lat.toFixed(6) + ', ' + before.lng.toFixed(6));

                var targetLatLng = new L.LatLng({lat}, {lon});
                console.log('[panTo] 调用 map.panTo()');
                window.map.panTo(targetLatLng, {{animate: true, duration: 1}});

                // 添加标记
                if (window.centerMarker) {{
                    window.map.removeLayer(window.centerMarker);
                }}
                window.centerMarker = L.marker(targetLatLng, {{
                    icon: L.icon({{
                        iconUrl: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="40" height="40" fill="%232196F3"><path d="M7 10l5-5 5 5z"/></svg>',
                        iconSize: [40, 40],
                        iconAnchor: [20, 40]
                    }})
                }});
                window.centerMarker.addTo(window.map);
                console.log('[panTo] 蓝色箭头标记已添加');
            }} catch(e) {{
                console.error('[panTo] 错误: ' + e.message);
            }}
        }})();
        """
        self.map_view.page().runJavaScript(js_code)

    def execute_setview_test(self):
        """执行 setView 测试（保持缩放）"""
        lat = self.lat_spin.value()
        lon = self.lon_spin.value()

        self.log(f"[setView] 开始测试，目标: ({lat}, {lon})")

        js_code = f"""
        (function() {{
            console.log('[setView] 测试开始');

            if (!window.map) {{
                console.error('[setView] 地图对象不存在');
                return;
            }}

            try {{
                var before = window.map.getCenter();
                var zoom = window.map.getZoom();
                console.log('[setView] 当前中心: ' + before.lat.toFixed(6) + ', ' + before.lng.toFixed(6) + ' 缩放: ' + zoom);

                var targetLatLng = new L.LatLng({lat}, {lon});
                console.log('[setView] 调用 setView');
                window.map.setView(targetLatLng, zoom, {{animate: true, duration: 1}});

                // 添加标记
                if (window.centerMarker) {{
                    window.map.removeLayer(window.centerMarker);
                }}
                window.centerMarker = L.marker(targetLatLng, {{
                    icon: L.icon({{
                        iconUrl: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="40" height="40" fill="%23FF5722"><path d="M7 10l5-5 5 5z"/></svg>',
                        iconSize: [40, 40],
                        iconAnchor: [20, 40]
                    }})
                }});
                window.centerMarker.addTo(window.map);
                console.log('[setView] 橙色箭头标记已添加');
            }} catch(e) {{
                console.error('[setView] 错误: ' + e.message);
            }}
        }})();
        """
        self.map_view.page().runJavaScript(js_code)

    def reset_to_beijing(self):
        """重置到北京"""
        self.log("[重置] 回到北京...")
        js_code = """
        (function() {
            if (window.map) {
                window.map.panTo(new L.LatLng(39.9042, 116.4074));
                console.log('[重置] 已返回北京');
            }
        })();
        """
        self.map_view.page().runJavaScript(js_code)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    diagnostic = MapPanDiagnostic()
    diagnostic.show()
    sys.exit(app.exec_())

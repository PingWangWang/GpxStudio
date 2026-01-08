"""
定位功能最终测试程序
使用HTTP服务器解决地理定位限制
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QTimer
from modules.geolocation.geolocation import GeolocationHandler
from modules.map.webengine import ConsoleWebEnginePage
from modules.map.map_renderer import MapRenderer


class FinalTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🧭 定位功能最终测试")
        self.resize(1200, 700)

        # 初始化处理器
        self.geolocation_handler = GeolocationHandler()
        self.geolocation_handler.geolocation_success.connect(self.on_location_success)
        self.geolocation_handler.geolocation_error.connect(self.on_location_error)

        # 创建UI
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 测试按钮
        test_btn = QPushButton("🚀 开始定位测试 (HTTP服务器)")
        test_btn.clicked.connect(self.test_location)
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(test_btn)

        # 日志显示
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                background-color: #1e1e1e;
                color: #d4d4d4;
            }
        """)
        layout.addWidget(self.log_text)

        # 地图视图
        self.map_view = QWebEngineView()
        self.web_page = ConsoleWebEnginePage()
        self.web_page.set_geolocation_handler(self.geolocation_handler)
        self.map_view.setPage(self.web_page)
        layout.addWidget(self.map_view, stretch=2)

        self.log("✅ 程序已启动")
        self.log("💡 点击上方按钮开始测试定位功能")
        self.log("")
        self.log("说明：")
        self.log("1. 程序使用HTTP服务器提供地图(解决file://协议限制)")
        self.log("2. 浏览器会请求地理定位权限")
        self.log("3. 定位成功后会在地图上显示位置")

    def log(self, message):
        """添加日志"""
        self.log_text.append(message)
        print(message)

    def test_location(self):
        """测试定位"""
        self.log("")
        self.log("="*60)
        self.log("🔍 开始定位测试...")
        self.log("="*60)

        try:
            # 创建带定位脚本的地图
            m = MapRenderer.create_base_map([39.9042, 116.4074], zoom_start=10)
            MapRenderer.add_geolocation_script(m)

            # 使用HTTP服务器
            url = MapRenderer.save_and_get_url(m, use_http_server=True)
            self.log(f"🌐 地图URL: {url.toString()}")

            # 加载地图
            self.map_view.setUrl(url)

            self.log("⏳ 正在加载地图...")
            self.log("⏳ 等待地理定位请求... (最多30秒)")
            self.log("")
            self.log("⚠️ 如果长时间无响应，请检查：")
            self.log("   1. Windows位置服务是否已启用")
            self.log("   2. 控制台是否有JavaScript输出")
            self.log("   3. 是否有权限请求弹窗")

        except Exception as e:
            self.log(f"❌ 错误: {e}")
            import traceback
            self.log(traceback.format_exc())

    def on_location_success(self, lat, lon, accuracy):
        """定位成功"""
        self.log("")
        self.log("="*60)
        self.log("🎉 定位成功！")
        self.log("="*60)
        self.log(f"📍 纬度: {lat:.6f}")
        self.log(f"📍 经度: {lon:.6f}")
        self.log(f"🎯 精度: ±{accuracy:.0f} 米")
        self.log("="*60)

    def on_location_error(self, error_msg):
        """定位失败"""
        self.log("")
        self.log("="*60)
        self.log(f"❌ 定位失败: {error_msg}")
        self.log("="*60)
        self.log("")
        self.log("💡 可能的原因：")
        self.log("   1. 用户拒绝了权限请求")
        self.log("   2. Windows位置服务未启用")
        self.log("   3. 网络或GPS硬件不可用")
        self.log("   4. 定位服务响应超时")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FinalTestWindow()
    window.show()
    sys.exit(app.exec_())

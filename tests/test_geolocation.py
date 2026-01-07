"""
测试定位功能
验证定位脚本和权限处理是否正常工作
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QTimer
from handlers.geolocation import GeolocationHandler
from handlers.webengine import ConsoleWebEnginePage
from utils.map_renderer import MapRenderer


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("定位功能测试")
        self.resize(1000, 600)

        # 初始化处理器
        self.geolocation_handler = GeolocationHandler()
        self.geolocation_handler.geolocation_success.connect(self.on_location_success)
        self.geolocation_handler.geolocation_error.connect(self.on_location_error)

        # 创建UI
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 测试按钮
        test_btn = QPushButton("🧪 测试定位")
        test_btn.clicked.connect(self.test_location)
        layout.addWidget(test_btn)

        # 日志显示
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        # 地图视图
        self.map_view = QWebEngineView()
        web_page = ConsoleWebEnginePage()
        web_page.set_geolocation_handler(self.geolocation_handler)

        # 连接页面信号来调试
        web_page.loadStarted.connect(lambda: self.log("📄 页面开始加载..."))
        web_page.loadProgress.connect(lambda p: self.log(f"📊 加载进度: {p}%"))
        web_page.loadFinished.connect(lambda ok: self.log(f"✅ 页面加载完成: {ok}"))

        self.map_view.setPage(web_page)
        layout.addWidget(self.map_view)

        self.log("程序已启动，点击'测试定位'按钮开始测试")

    def log(self, message):
        """添加日志"""
        self.log_text.append(message)
        print(message)

    def test_location(self):
        """测试定位"""
        self.log("\n" + "="*50)
        self.log("开始测试定位功能...")
        self.log("="*50)

        # 创建带定位脚本的地图
        m = MapRenderer.create_base_map([39.9042, 116.4074], zoom_start=10)
        MapRenderer.add_geolocation_script(m)

        # 使用HTTP服务器（重要！解决file://协议的地理定位限制）
        url = MapRenderer.save_and_get_url(m, use_http_server=True)
        self.log(f"🌐 地图URL: {url.toString()}")
        self.log(f"📋 URL scheme: {url.scheme()}")
        self.map_view.setUrl(url)

        self.log("地图已加载，等待定位结果...")
        self.log("如果30秒内无响应，请检查：")
        self.log("1. 浏览器是否弹出权限请求")
        self.log("2. Windows系统定位服务是否已启用")
        self.log("3. 控制台日志输出")

    def on_location_success(self, lat, lon, accuracy):
        """定位成功"""
        self.log("\n✅ 定位成功！")
        self.log(f"纬度: {lat}")
        self.log(f"经度: {lon}")
        self.log(f"精度: {accuracy}米")

    def on_location_error(self, error_msg):
        """定位失败"""
        self.log(f"\n❌ 定位失败: {error_msg}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_())

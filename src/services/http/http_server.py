"""
本地HTTP服务器
用于提供地图HTML文件，解决file://协议的地理定位限制
"""

import http.server
import socketserver
import threading
import tempfile
import os
from pathlib import Path


class LocalMapServer:
    """本地地图服务器"""

    def __init__(self, port=8765):
        self.port = port
        self.temp_dir = tempfile.mkdtemp(prefix='gpx_maps_')
        self.server = None
        self.thread = None
        self.running = False

    def start(self):
        """启动服务器"""
        if self.running:
            return

        try:
            os.chdir(self.temp_dir)
            handler = http.server.SimpleHTTPRequestHandler
            self.server = socketserver.TCPServer(("", self.port), handler)
            self.server.allow_reuse_address = True

            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            self.running = True

            print(f"[服务器] ✅ HTTP服务器已启动: http://localhost:{self.port}")
            print(f"[服务器] 📁 临时目录: {self.temp_dir}")

        except Exception as e:
            print(f"[服务器] ❌ 启动失败: {e}")
            raise

    def stop(self):
        """停止服务器"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.running = False
            print("[服务器] ⏹️ 服务器已停止")

    def save_map(self, map_obj, filename="map.html"):
        """
        保存地图到服务器目录

        Args:
            map_obj: folium地图对象
            filename: 文件名

        Returns:
            str: HTTP URL
        """
        filepath = os.path.join(self.temp_dir, filename)
        map_obj.save(filepath)
        url = f"http://localhost:{self.port}/{filename}"
        print(f"[服务器] 💾 地图已保存: {filename}")
        print(f"[服务器] 🔗 URL: {url}")
        return url

    def __del__(self):
        """析构时停止服务器"""
        self.stop()


# 全局服务器实例
_map_server = None


def get_map_server(port=8765):
    """
    获取或创建全局地图服务器实例

    Args:
        port: 端口号

    Returns:
        LocalMapServer: 服务器实例
    """
    global _map_server
    if _map_server is None or not _map_server.running:
        _map_server = LocalMapServer(port)
        _map_server.start()
    return _map_server

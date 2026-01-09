# HTTP服务器模块，用于解决地理定位限制
import http.server
import socketserver
import threading
import os
import tempfile

class MapServer:
    def __init__(self):
        self.port = 8000
        self.httpd = None
        self.thread = None
        self.base_dir = tempfile.mkdtemp(prefix='gpx_studio_map_')
        self.server_address = ('', self.port)

        # 创建自定义HTTP请求处理器
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=self.base_dir, **kwargs)

            def log_message(self, format, *args):
                # 禁用日志输出
                pass

        self.handler = Handler

    def start(self):
        if not self.httpd:
            self.httpd = socketserver.TCPServer(self.server_address, self.handler)
            self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
            self.thread.start()

    def save_map(self, map_obj, filename):
        if not self.httpd:
            self.start()

        file_path = os.path.join(self.base_dir, filename)
        map_obj.save(file_path)
        return f'http://localhost:{self.port}/{filename}'

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd = None

# 单例实例
_map_server = None

def get_map_server():
    global _map_server
    if _map_server is None:
        _map_server = MapServer()
    return _map_server

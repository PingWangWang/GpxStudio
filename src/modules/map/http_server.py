# HTTP服务器模块，用于解决地理定位限制
import http.server
import socketserver
import threading
import os
import tempfile
from app.data_paths import get_cache_dir

class MapServer:
    def __init__(self):
        self.port = 8000
        self.httpd = None
        self.thread = None
        # 创建应用程序缓存目录下的temp子目录
        cache_temp_dir = os.path.join(get_cache_dir(), 'Temp')
        os.makedirs(cache_temp_dir, exist_ok=True)
        # 在应用程序缓存目录下创建临时目录
        self.base_dir = tempfile.mkdtemp(prefix='gpx_studio_map_', dir=cache_temp_dir)
        self.server_address = ('', self.port)

        # 保存当前实例的引用
        server_instance = self

        # 创建自定义HTTP请求处理器
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=server_instance.base_dir, **kwargs)

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
        """
        保存地图到文件并返回HTTP URL
        
        Args:
            map_obj: folium地图对象
            filename: 文件名
            
        Returns:
            str: HTTP URL
        """
        import logging
        import os
        import tempfile
        import time
        
        logger = logging.getLogger(__name__)
        
        try:
            # 确保服务器已启动
            if not self.httpd:
                logger.debug("HTTP服务器未启动，正在启动...")
                self.start()
                # 给服务器一点时间启动
                time.sleep(0.1)
            
            # 确保端口已设置
            if not self.port:
                logger.error("HTTP服务器端口未设置")
                # 回退到临时文件方式
                cache_temp_dir = os.path.join(get_cache_dir(), 'temp')
                os.makedirs(cache_temp_dir, exist_ok=True)
                html_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html', dir=cache_temp_dir)
                temp_path = html_file.name
                html_file.close()
                map_obj.save(temp_path)
                logger.debug(f"回退到临时文件: {temp_path}")
                return temp_path
            
            # 保存地图文件
            file_path = os.path.join(self.base_dir, filename)
            logger.debug(f"保存地图到: {file_path}")
            map_obj.save(file_path)
            
            # 验证文件存在
            if not os.path.exists(file_path):
                logger.error(f"地图文件创建失败: {file_path}")
                # 回退到临时文件方式
                cache_temp_dir = os.path.join(get_cache_dir(), 'temp')
                os.makedirs(cache_temp_dir, exist_ok=True)
                html_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html', dir=cache_temp_dir)
                temp_path = html_file.name
                html_file.close()
                map_obj.save(temp_path)
                logger.debug(f"回退到临时文件: {temp_path}")
                return temp_path
            
            # 构建URL
            url_str = f'http://localhost:{self.port}/{filename}'
            logger.debug(f"返回HTTP URL: {url_str}")
            return url_str
        except Exception as e:
            logger.error(f"保存地图到HTTP服务器失败: {str(e)}")
            # 出错时回退到临时文件方式
            cache_temp_dir = os.path.join(get_cache_dir(), 'temp')
            os.makedirs(cache_temp_dir, exist_ok=True)
            html_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html', dir=cache_temp_dir)
            temp_path = html_file.name
            html_file.close()
            map_obj.save(temp_path)
            logger.debug(f"出错时回退到临时文件: {temp_path}")
            return temp_path

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

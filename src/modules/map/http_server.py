# HTTP服务器模块，用于解决地理定位限制和提供瓦片缓存代理
import http.server
import socketserver
import threading
import os
import tempfile
import time
import requests
import shutil
import math
from concurrent.futures import ThreadPoolExecutor
from app.data_paths import get_cache_dir, get_gaode_cache_dir, get_osm_cache_dir

import logging
# 瓦片源配置
TILE_SOURCES = {
    'gaode': {
        'roadmap': 'https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
        'satellite': 'https://webst01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=6&x={x}&y={y}&z={z}',
        'hybrid': 'https://webst01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}'
    },
    'osm': {
        'roadmap': 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
        # OSM其他源根据需要添加，这里主要支持roadmap作为示例
    }
}

class ThreadPoolTCPServer(socketserver.TCPServer):
    """
    使 ThreadPoolExecutor 处理请求的 TCPServer，避免频繁创建销毁线程带来的性能开销
    """
    # 增加连接队列大小，防止并在请求突发时(如地图整页加载)拒绝连接
    request_queue_size = 100

    def __init__(self, server_address, RequestHandlerClass, max_workers=10):
        super().__init__(server_address, RequestHandlerClass)
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="MapServerWorker")

    def process_request(self, request, client_address):
        self.executor.submit(self.process_request_thread, request, client_address)

    def process_request_thread(self, request, client_address):
        try:
            self.finish_request(request, client_address)
            self.shutdown_request(request)
        except Exception:
            self.handle_error(request, client_address)
            self.shutdown_request(request)
    
    def server_close(self):
        self.executor.shutdown(wait=False)
        super().server_close()

class MapServer:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MapServer, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.port = 8000
        self.httpd = None
        self.thread = None
        
        # 缓存目录配置 - 使用项目统一规划的目录
        self.gaode_cache_root = get_gaode_cache_dir()
        self.osm_cache_root = get_osm_cache_dir()
        
        self.logger = logging.getLogger('MapServer')
        
        # 当前视口信息
        self.viewport = {
            'sw': None, # (lat, lon)
            'ne': None, # (lat, lon)
            'zoom': None
        }
        self.viewport_completeness_cache = {} # Key: (source, style, z, x_range, y_range), Value: (timestamp, is_complete)
        
        # 临时文件目录
        cache_temp_dir = os.path.join(get_cache_dir(), 'Temp')
        os.makedirs(cache_temp_dir, exist_ok=True)
        self.base_dir = tempfile.mkdtemp(prefix='gpx_studio_map_', dir=cache_temp_dir)
        
        self.server_address = ('127.0.0.1', self.port) # 绑定到本地
        self._initialized = True

        # 后台下载线程池
        # 增加并发数，提高下载速度
        # 2026-02-11: 限制并发数为4，确保瓦片加载作为低优先级任务，不抢占路线规划和地理编码的网络资源
        self.download_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="TileDownloader")
        
        # 共享的Session对象，复用TCP连接，显著提升下载性能
        self.session = requests.Session()
        # 设置通用的User-Agent，不包含特定的Referer
        # 具体的Referer将在请求时根据瓦片源动态设置
        self.session.headers.update({
            'User-Agent': 'GPX Studio/2.0.10 (Windows; contact: 1341783770@qq.com)',
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Connection': 'keep-alive'
        })
        # 挂载Adapter以实现重试机制
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        # 限制连接池大小，避免同时对上游发起过多连接导致封禁
        # 前端并发可能很高(60+)，但我们只允许同时有16个连接去下载，其他的排队等待复用
        adapter = HTTPAdapter(pool_connections=16, pool_maxsize=16, max_retries=retries)
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)

        # 保存当前实例的引用供Handler使用
        server_instance = self

        # 创建自定义HTTP请求处理器
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=server_instance.base_dir, **kwargs)

            def log_message(self, format, *args):
                # 禁用常规日志输出，以免刷屏
                pass

            def do_GET(self):
                # 处理视口更新请求
                if self.path.startswith('/update_viewport?'):
                    self.handle_viewport_update()
                    return

                # 处理瓦片请求: /tiles/source/style/z/x/y
                if self.path.startswith('/tiles/'):
                    self.handle_tile_request()
                    return
                super().do_GET()

            def handle_viewport_update(self):
                """处理视口更新请求"""
                try:
                    from urllib.parse import urlparse, parse_qs
                    query = parse_qs(urlparse(self.path).query)
                    
                    sw_lat = float(query.get('sw_lat', [0])[0])
                    sw_lon = float(query.get('sw_lon', [0])[0])
                    ne_lat = float(query.get('ne_lat', [0])[0])
                    ne_lon = float(query.get('ne_lon', [0])[0])
                    zoom = int(query.get('zoom', [0])[0])
                    
                    server_instance.set_viewport(sw_lat, sw_lon, ne_lat, ne_lon)
                    server_instance.set_zoom(zoom)
                    
                    self.send_response(200)
                    self.end_headers()
                except Exception as e:
                    print(f"[MapServer] Error handling viewport update: {e}")
                    self.send_error(400, str(e))

            def handle_tile_request(self):
                """处理瓦片请求：缓存代理逻辑"""
                try:
                    # 路径格式: /tiles/gaode/roadmap/10/32/45
                    parts = self.path.strip('/').split('/')
                    if len(parts) < 5:
                        self.send_error(400, "Invalid tile request format")
                        return
                    
                    source = parts[1]
                    style = parts[2]
                    z, x, y = parts[3], parts[4], parts[5]
                    
                    # 选择正确的缓存根目录
                    if source == 'gaode':
                        base_path = server_instance.gaode_cache_root
                    elif source == 'osm':
                        base_path = server_instance.osm_cache_root
                    else:
                        base_path = os.path.join(get_cache_dir(), source)

                    # 构造缓存文件路径: [CacheRoot]/style/z/x/y
                    # 例如: .../GaoDeMapData/roadmap/10/32/45
                    cache_subdir = os.path.join(base_path, style, z, x)
                    cache_file = os.path.join(cache_subdir, y) # 文件名为y
                    
                    # 1. 检查缓存
                    if os.path.exists(cache_file):
                        # 检查有效期 (30天 = 30 * 24 * 3600 秒)
                        mtime = os.path.getmtime(cache_file)
                        if time.time() - mtime < 2592000:
                            # 缓存命中且有效，直接返回文件
                            with open(cache_file, 'rb') as f:
                                content = f.read()
                                
                                # 校验文件有效性 (检查PNG/JPG/GIF/WebP头)
                                is_valid = False
                                if len(content) > 4:
                                    # PNG: 89 50 4E 47
                                    if content.startswith(b'\x89PNG'):
                                        is_valid = True
                                    # JPG: FF D8
                                    elif content.startswith(b'\xff\xd8'):
                                        is_valid = True
                                    # WebP: RIFF ... WEBP
                                    elif content.startswith(b'RIFF') and content[8:12] == b'WEBP':
                                        is_valid = True
                                    # GIF: GIF8
                                    elif content.startswith(b'GIF8'):
                                        is_valid = True
                                
                                if is_valid:
                                    # 策略调整：只要本地缓存存在且校验通过，就直接返回
                                    # 之前的"视口完整性检查"会导致部分缓存时也强制走网络，造成地图灰白加载慢
                                    # 恢复为标准缓存策略：有则用，无则下
                                    
                                    self.send_response(200)
                                    self.send_header('Content-Type', 'image/png')
                                    self.send_header('Content-Length', str(len(content)))
                                    self.send_header('Cache-Control', 'max-age=2592000')
                                    self.end_headers()
                                    self.wfile.write(content)
                                    return
                                else:
                                    print(f"[TileCache] Invalid cache file detected (deleting): {cache_file}")
                                    try:
                                        os.remove(cache_file)
                                    except:
                                        pass
                    
                    # 2. 缓存未命中或过期 -> 构造原始URL
                    real_url = self._get_real_url(source, style, z, x, y)
                    if not real_url:
                        self.send_error(404, "Tile source not found")
                        return

                    # 3. 同步下载并代理返回 (Proxy Mode)
                    # 放弃Redirect模式，改为直接作为代理服务器
                    # 优点:隐藏Referer细节，利用Keep-Alive连接池加速，避免浏览器二次请求延迟
                    # 配合 max_workers=60 和 requests连接池限制，既能高并发响应浏览器，又能受控访问上游
                    
                    try:
                        # 复用 _download_and_cache 逻辑，但要求同步等待
                        # 注意：_download_and_cache 内部已去除了人为延迟
                        success = self.download_sync(real_url, cache_subdir, cache_file)
                        
                        if success and os.path.exists(cache_file):
                            with open(cache_file, 'rb') as f:
                                content = f.read()
                            
                            self.send_response(200)
                            self.send_header('Content-Type', 'image/png')
                            self.send_header('Content-Length', str(len(content)))
                            self.send_header('Cache-Control', 'max-age=2592000')
                            self.end_headers()
                            self.wfile.write(content)
                        else:
                            # 下载失败
                            self.send_error(404, "Tile fetch failed")

                    except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                        # 客户端断开连接，无需处理，直接返回
                        return
                    except Exception as e:
                        print(f"[TileCache] Proxy error: {e}")
                        try:
                            # 尝试发送错误，但如果连接已断开可能会失败，忽略二次错误
                            self.send_error(502, "Upstream error")
                        except:
                            pass

                except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                    return
                except Exception as e:
                    print(f"[TileCache] Error handling request: {e}")
                    try:
                         self.send_error(500, "Internal Server Error")
                    except:
                         pass

            def _check_neighbors(self, base_path, style, z, x, y):
                """检查4邻域瓦片是否存在，用于判断区域完整性"""
                # 将字符串转为整数进行计算
                try:
                    ix, iy = int(x), int(y)
                except ValueError:
                    return True # 如果转换失败，保守返回True，避免逻辑破坏
                
                # 检查上下左右4个邻居
                neighbors = [
                    (ix+1, iy), (ix-1, iy), (ix, iy+1), (ix, iy-1)
                ]
                
                for nx, ny in neighbors:
                    # 简单构建路径，不处理跨越日期变更线的情况(极少数情况)
                    # 路径结构: base_path/style/z/x/y
                    neighbor_path = os.path.join(base_path, style, z, str(nx), str(ny))
                    if not os.path.exists(neighbor_path):
                        return False
                return True

            def _get_real_url(self, source, style, z, x, y):
                """根据配置生成真实URL"""
                start_time = time.time()
                template = TILE_SOURCES.get(source, {}).get(style)
                if not template:
                    return None
                return template.format(x=x, y=y, z=z)

            def download_sync(self, url, cache_dir, cache_file):
                """同步下载 (包装 _download_and_cache)"""
                # 通过 download_executor 提交任务，限制同时进行的下载数量(max_workers=4)
                # 从而确保瓦片加载不会占用所有网络资源，实现"低优先级"效果
                try:
                    future = server_instance.download_executor.submit(
                        self._download_and_cache, url, cache_dir, cache_file
                    )
                    # 等待任务完成
                    future.result()
                    return os.path.exists(cache_file)
                except Exception as e:
                    print(f"Download sync error: {e}")
                    return False

            def _download_and_cache(self, url, cache_dir, cache_file):
                """后台下载并保存瓦片"""
                import time
                import random
                
                # 简单的重试机制
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        # 确保目录存在
                        os.makedirs(cache_dir, exist_ok=True)
                        
                        # 同步代理模式下，不需要人为延迟，速度优先
                        if attempt > 0:
                            time.sleep(0.2 * attempt)
                        
                        # 根据URL判断瓦片源，设置合适的Referer
                        headers = {}
                        if 'openstreetmap.org' in url:
                            # OpenStreetMap要求有效的Referer
                            headers['Referer'] = 'https://www.openstreetmap.org/'
                        elif 'autonavi.com' in url or 'amap.com' in url:
                            # 高德地图
                            headers['Referer'] = 'https://www.amap.com/'
                        
                        # 使用共享的session下载，传入特定的headers
                        response = server_instance.session.get(url, headers=headers, timeout=5)
                        
                        if response.status_code == 200:
                            # 写入临时文件再改名，保证原子性
                            temp_file = cache_file + '.tmp'
                            with open(temp_file, 'wb') as f:
                                f.write(response.content)
                            
                            # 移动/覆盖原文件
                            shutil.move(temp_file, cache_file)
                            # server_instance.logger.info(f"CACHED: {cache_file}")
                            return # 成功，退出重试循环
                        elif response.status_code in [403, 429, 500, 502, 503, 504]:
                            # 这种错误值得重试
                            if attempt < max_retries - 1:
                                continue
                            else:
                                print(f"[TileCache] Failed to download {url}: Status {response.status_code}")
                        else:
                            # 404等错误不重试
                            print(f"[TileCache] Failed to download {url}: Status {response.status_code}")
                            break
                            
                    except Exception as e:
                        if attempt < max_retries - 1:
                            # 如果是连接被重置，稍微多等一会
                            if 'ConnectionResetError' in str(e) or '10054' in str(e):
                                time.sleep(1)
                            continue
                        else:
                            print(f"[TileCache] Download exception for {url}: {e}")

        self.handler = Handler

    def start(self):
        if not self.httpd:
            # 使用现有端口，如果占用则+1 (简单重试)
            for i in range(10):
                try:
                    current_port = self.port + i
                    self.server_address = ('127.0.0.1', current_port)
                    # 使用 ThreadPoolTCPServer 限制最大并发线程数
                    # 提高并发数以处理浏览器对本地服务器的高频请求(瓦片加载可能瞬间数十个)
                    # 之前的 6 个线程限制加上默认的 backlog=5 导致大量请求被拒绝(Connection Refused)
                    self.httpd = ThreadPoolTCPServer(self.server_address, self.handler, max_workers=60)
                    self.port = current_port # 更新实际使用的端口
                    self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
                    self.thread.start()
                    print(f"[MapServer] Started at http://127.0.0.1:{self.port} (Cache Roots: GAODE={self.gaode_cache_root}, OSM={self.osm_cache_root})")
                    break
                except OSError:
                    continue
            else:
                print("[MapServer] Failed to bind port 8000-8009")

    def latlon2tile(self, lat, lon, zoom):
        """将经纬度转换为瓦片坐标"""
        lat_rad = math.radians(lat)
        n = 2.0 ** zoom
        xtile = int((lon + 180.0) / 360.0 * n)
        ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return (xtile, ytile)

    def set_viewport(self, sw_lat, sw_lon, ne_lat, ne_lon):
        """更新当前视口范围"""
        self.viewport['sw'] = (sw_lat, sw_lon)
        self.viewport['ne'] = (ne_lat, ne_lon)
        # print(f"[MapServer] Viewport updated: SW={self.viewport['sw']}, NE={self.viewport['ne']}")

    def set_zoom(self, zoom):
        """更新当前缩放级别"""
        self.viewport['zoom'] = zoom
        # print(f"[MapServer] Zoom updated: {zoom}")

    def is_viewport_fully_cached(self, source, style, z, base_path):
        """检查当前视口内的所有瓦片是否都已缓存"""
        # 如果视口信息不完整，无法判断，默认返回True(允许使用缓存)或False(保守策略)
        # 这里我们保守一点，如果不知道视口，就退化为局部检查，或者直接返回True(保持旧行为)
        if not self.viewport['sw'] or not self.viewport['ne'] or self.viewport['zoom'] is None:
            return True
            
        # 如果请求的Zoom和视口Zoom差异过大(例如预加载)，则不进行全量检查
        if abs(int(z) - int(self.viewport['zoom'])) > 1:
            return True

        sw_lat, sw_lon = self.viewport['sw']
        ne_lat, ne_lon = self.viewport['ne']
        
        # 计算视口覆盖的瓦片范围
        # 注意: 纬度越大y越小(北半球)
        min_x, max_y = self.latlon2tile(sw_lat, sw_lon, int(z))
        max_x, min_y = self.latlon2tile(ne_lat, ne_lon, int(z))
        
        # 修正x, y范围 (sw_lat < ne_lat -> max_y > min_y in tile coords? No.
        # lat: -90...90. tan(lat) increases. asinh increases. 1 - ... decreases.
        # So lat increases -> y decreases.
        # SW (min lat) -> Max Y
        # NE (max lat) -> Min Y
        
        start_x, end_x = min(min_x, max_x), max(min_x, max_x)
        start_y, end_y = min(min_y, max_y), max(min_y, max_y)
        
        # 缓存键，避免对每个瓦片请求都重算一遍整个视口 (1秒内有效)
        cache_key = (source, style, z, start_x, end_x, start_y, end_y)
        now = time.time()
        if cache_key in self.viewport_completeness_cache:
            ts, result = self.viewport_completeness_cache[cache_key]
            if now - ts < 2.0: # 缓存结果2秒
                return result
        
        # 遍历视口内所有瓦片
        # 限制检查数量，防止视口过大导致性能问题(例如缩放到全球)
        total_tiles = (end_x - start_x + 1) * (end_y - start_y + 1)
        if total_tiles > 100:
             # 如果瓦片太多，只检查中心和四角采样，或者直接放弃全量检查
             result = True
        else:
            all_cached = True
            for tx in range(start_x, end_x + 1):
                for ty in range(start_y, end_y + 1):
                    tile_path = os.path.join(base_path, style, z, str(tx), str(ty))
                    if not os.path.exists(tile_path):
                        all_cached = False
                        break
                if not all_cached:
                    break
            result = all_cached
            
        self.viewport_completeness_cache[cache_key] = (now, result)
        if not result:
             # print(f"[TileCache] Viewport region incomplete ({start_x},{start_y} to {end_x},{end_y}). Force refresh active.")
             pass
        return result

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
            if not self.httpd: # 如果此时还没有httpd，说明启动失败
                logger.error("HTTP服务器启动失败")
                return self._fallback_to_local_file(map_obj)
            
            # 保存地图文件
            file_path = os.path.join(self.base_dir, filename)
            # logger.debug(f"保存地图到: {file_path}")
            map_obj.save(file_path)
            
            # 验证文件存在
            if not os.path.exists(file_path):
                logger.error(f"地图文件创建失败: {file_path}")
                return self._fallback_to_local_file(map_obj)
            
            # 构建URL
            url_str = f'http://127.0.0.1:{self.port}/{filename}'
            logger.debug(f"返回HTTP URL: {url_str}")
            return url_str
            
        except Exception as e:
            logger.error(f"保存地图服务中出错: {e}")
            return self._fallback_to_local_file(map_obj)

    def _fallback_to_local_file(self, map_obj):
        """回退到本地文件模式"""
        import tempfile
        import os
        from app.data_paths import get_cache_dir
        cache_temp_dir = os.path.join(get_cache_dir(), 'Temp')
        os.makedirs(cache_temp_dir, exist_ok=True)
        html_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html', dir=cache_temp_dir)
        temp_path = html_file.name
        html_file.close()
        map_obj.save(temp_path)
        return temp_path

    def stop(self):
        print("[MapServer] Stopping server...")
        if self.download_executor:
            # 停止下载线程池，不等待未完成的任务，并尝试取消未开始的任务
            print("[MapServer] Shutting down download executor...")
            self.download_executor.shutdown(wait=False)
            
        if self.httpd:
            print("[MapServer] Shutting down HTTP server...")
            self.httpd.shutdown()
            self.httpd = None
        print("[MapServer] Server stopped")

# 单例实例
_map_server = None

def get_map_server():
    global _map_server
    if _map_server is None:
        _map_server = MapServer()
    return _map_server

"""
地图视图状态管理器
统一管理地图的中心点和缩放级别，提供多级降级策略
"""

import time
from typing import Optional, Dict, Tuple
from PyQt5.QtCore import QEventLoop, QTimer


class MapViewStateManager:
    """
    地图视图状态管理器
    
    负责统一管理地图的视图状态（中心点和缩放级别），提供以下功能：
    - 从JavaScript实时获取地图状态（最准确）
    - 从HTTP服务器获取视口缓存（较准确）
    - 使用内存缓存作为降级方案
    - 自动选择最佳获取策略
    """
    
    def __init__(self, map_view_getter, logger):
        """
        初始化视图状态管理器
        
        Args:
            map_view_getter: 获取地图视图组件的回调函数（返回当前的map_view）
            logger: 日志器
        """
        self.map_view_getter = map_view_getter
        self.logger = logger
        
        # 缓存的视图状态
        self._cached_center = None
        self._cached_zoom = None
        self._last_update_time = 0
        self._cache_valid_duration = 1.0  # 缓存有效期（秒）
    
    def get_current_view(self, prefer_js=True, timeout_ms=300) -> Dict:
        """
        获取当前地图的实时视图状态
        
        优先级：JavaScript > 缓存
        
        Args:
            prefer_js: 是否优先使用JavaScript获取（默认True，最准确）
            timeout_ms: JavaScript获取超时时间（毫秒，默认300ms）
            
        Returns:
            dict: 包含 center (list) 和 zoom (int/float) 的字典
                 例如: {'center': [39.9042, 116.4074], 'zoom': 10}
        """
        self.logger.info("[视图状态] 开始获取当前视图状态")
        
        # 获取当前的地图视图
        map_view = self.map_view_getter() if callable(self.map_view_getter) else self.map_view_getter
        
        # 如果优先使用JavaScript且地图视图可用
        if prefer_js and map_view:
            js_view = self._get_view_from_javascript(map_view, timeout_ms)
            if js_view:
                self._update_cache(js_view['center'], js_view['zoom'])
                self.logger.info(f"[视图状态] 成功从JavaScript获取: {js_view}")
                return js_view
            else:
                self.logger.warning("[视图状态] JavaScript获取失败，尝试降级策略")
        
        # 使用缓存的视图
        cached_view = self._get_cached_view()
        if cached_view:
            return cached_view
        
        # 最后的降级方案：返回默认值
        self.logger.warning("[视图状态] 无法获取当前视图，使用默认值")
        return {
            'center': [39.9042, 116.4074],
            'zoom': 10,
            'source': 'default'
        }
    
    def _get_view_from_javascript(self, map_view, timeout_ms: int = 300) -> Optional[Dict]:
        """
        从JavaScript获取实时视图（最准确）
        
        Args:
            map_view: 地图视图组件
            timeout_ms: 超时时间（毫秒，默认300ms）
            
        Returns:
            dict 或 None
        """
        if not map_view:
            self.logger.warning("[视图状态] map_view为None，无法从JS获取")
            return None
        
        js_code = """
        (function() {
            try {
                // 查找地图对象
                var map = null;
                for (var key in window) {
                    if (key.startsWith('map_') && window[key] && 
                        typeof window[key].getCenter === 'function' && 
                        typeof window[key].getZoom === 'function') {
                        map = window[key];
                        break;
                    }
                }
                
                if (!map) {
                    return null;
                }
                
                // 获取当前地图的中心点和缩放级别
                var center = map.getCenter();
                var zoom = map.getZoom();
                
                return {
                    lat: center.lat,
                    lon: center.lng,
                    zoom: zoom
                };
            } catch(e) {
                console.error('[视图状态] 获取失败:', e);
                return null;
            }
        })();
        """
        
        # 用于存储JavaScript返回的结果
        result_received = [False]
        view_info = [None]
        
        def on_result(result):
            """处理JavaScript返回的视图信息"""
            result_received[0] = True
            if result and isinstance(result, dict):
                view_info[0] = {
                    'center': [result.get('lat', 39.9042), result.get('lon', 116.4074)],
                    'zoom': result.get('zoom', 10),
                    'source': 'javascript'
                }
                self.logger.debug(f"[视图状态] 从JS获取: {view_info[0]}")
        
        try:
            self.logger.debug(f"[视图状态] 开始执行JavaScript获取视图，超时时间: {timeout_ms}ms")
            map_view.page().runJavaScript(js_code, on_result)
            
            # 等待JavaScript执行完成
            loop = QEventLoop()
            
            # 设置超时
            timeout_timer = QTimer()
            timeout_timer.setSingleShot(True)
            timeout_timer.timeout.connect(loop.quit)
            timeout_timer.start(timeout_ms)
            
            # 也可以通过结果接收来提前退出
            check_timer = QTimer()
            check_timer.setInterval(10)
            check_timer.timeout.connect(lambda: loop.quit() if result_received[0] else None)
            check_timer.start()
            
            loop.exec_()
            
            timeout_timer.stop()
            check_timer.stop()
            
            if result_received[0]:
                self.logger.debug(f"[视图状态] JavaScript成功返回结果")
            else:
                self.logger.warning(f"[视图状态] JavaScript超时（{timeout_ms}ms）未返回结果")
            
            return view_info[0]
        except Exception as e:
            self.logger.error(f"[视图状态] JS获取异常: {e}")
            return None
    

    
    def _get_cached_view(self) -> Optional[Dict]:
        """
        获取缓存的视图（降级方案）
        
        Returns:
            dict 或 None
        """
        # 检查缓存是否有效
        current_time = time.time()
        if (self._cached_center and self._cached_zoom and 
            current_time - self._last_update_time < self._cache_valid_duration):
            view = {
                'center': self._cached_center,
                'zoom': self._cached_zoom,
                'source': 'cache'
            }
            self.logger.debug(f"[视图状态] 使用缓存: {view}")
            return view
        
        return None
    
    def _update_cache(self, center: list, zoom: int):
        """
        更新缓存的视图状态
        
        Args:
            center: 中心点 [lat, lon]
            zoom: 缩放级别
        """
        self._cached_center = center
        self._cached_zoom = zoom
        self._last_update_time = time.time()
    
    def set_cache(self, center: list, zoom: int):
        """
        手动设置缓存（用于地图加载后立即缓存）
        
        Args:
            center: 中心点 [lat, lon]
            zoom: 缩放级别
        """
        self._update_cache(center, zoom)
        self.logger.debug(f"[视图状态] 手动设置缓存: center={center}, zoom={zoom}")
    
    def invalidate_cache(self):
        """使缓存失效"""
        self._last_update_time = 0
        self.logger.debug("[视图状态] 缓存已失效")

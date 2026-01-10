"""
自定义WebEngine页面
用于拦截JS控制台消息并处理定位信息和地图缩放事件
"""

from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineSettings
from PyQt5.QtCore import pyqtSignal

# 导入信号管理器
from core.signals import signal_manager


class ConsoleWebEnginePage(QWebEnginePage):
    """自定义WebEnginePage，拦截JS控制台消息"""

    def __init__(self, parent=None, signal_manager=None):
        super().__init__(parent)
        self.geolocation_handler = None
        self.signal_manager = signal_manager
        print("[ConsoleWebEnginePage] 初始化自定义WebEnginePage")

        # 连接权限请求信号
        self.featurePermissionRequested.connect(self.on_feature_permission_requested)
        print("[ConsoleWebEnginePage] 已连接权限请求信号")

        # 启用JavaScript和各种功能
        try:
            settings = self.settings()
            settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
            settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
            settings.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, True)
            settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
            settings.setAttribute(QWebEngineSettings.AllowRunningInsecureContent, True)
            print("[ConsoleWebEnginePage] ✅ 已启用JavaScript和LocalStorage")
        except Exception as e:
            print(f"[ConsoleWebEnginePage] ⚠️ 配置设置时出错: {e}")

    def set_geolocation_handler(self, handler):
        """设置定位处理器"""
        self.geolocation_handler = handler
        print(f"[ConsoleWebEnginePage] 设置定位处理器: {handler}")

        # 连接加载信号
        if not hasattr(self, '_signals_connected'):
            self.loadStarted.connect(lambda: print("[页面] 开始加载..."))
            self.loadProgress.connect(lambda p: print(f"[页面] 加载进度: {p}%") if p % 20 == 0 else None)
            self.loadFinished.connect(self.on_load_finished)
            self._signals_connected = True
            print("[ConsoleWebEnginePage] ✅ 已连接页面加载信号")

    def on_load_finished(self, success):
        """页面加载完成"""
        if success:
            print("[加载] ✅ 页面加载成功")
            print(f"[加载] URL: {self.url().toString()}")

            # 直接执行JavaScript来测试
            test_script = """
            console.log('[测试] JavaScript执行测试 - 如果你看到这个，说明JS工作正常');
            console.log('[测试] navigator.geolocation: ' + (!!navigator.geolocation));
            """
            self.runJavaScript(test_script, lambda result: print(f"[JS执行] 结果: {result}"))
        else:
            print("[加载] ❌ 页面加载失败")

    def on_feature_permission_requested(self, securityOrigin, feature):
        """处理功能权限请求信号（如地理定位）"""
        print(f"[权限] 收到权限请求! Origin: {securityOrigin.toString()}, Feature: {feature}")
        try:
            # 使用枚举值来判断和设置
            if feature == QWebEnginePage.Geolocation:
                print(f"[权限] 这是地理定位权限请求")
                self.setFeaturePermission(
                    securityOrigin,
                    QWebEnginePage.Geolocation,
                    QWebEnginePage.PermissionGrantedByUser
                )
                print("[权限] ✅ 已授予地理定位权限")
            else:
                print(f"[权限] ⚠️ 未知权限请求类型: {feature}")
                # 尝试也授予权限
                self.setFeaturePermission(
                    securityOrigin,
                    feature,
                    QWebEnginePage.PermissionGrantedByUser
                )
        except Exception as e:
            print(f"[权限] ❌ 处理权限请求时出错: {e}")
            import traceback
            traceback.print_exc()

    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        """处理JavaScript控制台消息"""
        print(f"[Console] [{level}] 行{line_number}: {message}")

        # 处理地图缩放变化消息
        if message.startswith('缩放变化:'):
            try:
                zoom_level = int(message[len('缩放变化:'):].strip())
                print(f"[地图缩放] 捕获到缩放级别: {zoom_level}")
                # 使用传入的信号管理器或全局信号管理器
                if self.signal_manager:
                    print("[地图缩放] 使用实例信号管理器发送信号")
                    self.signal_manager.map_zoom_changed.emit(zoom_level)
                else:
                    print("[地图缩放] 使用全局信号管理器发送信号")
                    signal_manager.map_zoom_changed.emit(zoom_level)
            except Exception as e:
                print(f"[地图缩放] 解析缩放级别失败: {e}")
                import traceback
                traceback.print_exc()

        if self.geolocation_handler:
            if message.startswith('定位成功:'):
                try:
                    parts = message[len('定位成功:'):].split(',')
                    lat = float(parts[0].strip())
                    lon = float(parts[1].strip())
                    accuracy = float(parts[2].strip()) if len(parts) > 2 else 0
                    print(f"[定位] 成功获取位置 - 纬度: {lat}, 经度: {lon}, 精度: {accuracy}米")
                    self.geolocation_handler.emit_geolocation_success(lat, lon, accuracy)
                except Exception as e:
                    print(f"[定位] 解析定位结果失败: {e}")
                    import traceback
                    traceback.print_exc()
                    self.geolocation_handler.emit_geolocation_error("定位结果解析失败")
            elif message.startswith('定位失败:'):
                error_msg = message[len('定位失败:'):].strip()
                print(f"[定位] 定位失败: {error_msg}")
                self.geolocation_handler.emit_geolocation_error(error_msg)
            elif '定位' in message or 'geolocation' in message.lower():
                print(f"[定位] 相关消息: {message}")

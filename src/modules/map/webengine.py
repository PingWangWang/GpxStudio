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
            # 启用地理定位功能（修复属性名错误）
            try:
                # 尝试使用GeolocationEnabled属性
                settings.setAttribute(QWebEngineSettings.GeolocationEnabled, True)
                print("[ConsoleWebEnginePage] ✅ 已启用JavaScript、LocalStorage和地理定位")
            except AttributeError:
                # 如果属性不存在，捕获错误并继续
                print("[ConsoleWebEnginePage] ⚠️ GeolocationEnabled属性不存在，但地理定位权限仍会通过featurePermissionRequested处理")
                # 继续执行其他设置
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
        url_str = self.url().toString()

        if success:
            print("[加载] ✅ 页面加载成功")
            print(f"[加载] URL: {url_str}")

            # 发射地图加载完成信号
            if self.signal_manager:
                self.signal_manager.map_loaded.emit()
                print("[加载] 已发射地图加载完成信号")

            # 直接执行JavaScript来测试
            test_script = """
            console.log('[测试] JavaScript执行测试 - 如果你看到这个，说明JS工作正常');
            console.log('[测试] navigator.geolocation: ' + (!!navigator.geolocation));
            """
            self.runJavaScript(test_script, lambda result: print(f"[JS执行] 结果: {result}"))
        else:
            # 更加宽容的处理：即使success为False，也尝试执行JavaScript来验证页面是否真的加载成功
            print("[加载] ⚠️ 页面加载状态为失败，但尝试验证页面是否可用...")
            print(f"[加载] URL: {url_str}")

            # 尝试执行JavaScript来测试页面是否真的加载成功
            test_script = """
            console.log('[测试] 尝试在加载状态为失败时执行JavaScript');
            '页面加载成功'  // 返回一个字符串表示成功
            """

            def on_js_result(result):
                if result == '页面加载成功':
                    print("[加载] ✅ 页面实际上加载成功，只是状态报告为失败")
                    # 即使状态报告失败，但实际成功时也发射信号
                    if self.signal_manager:
                        self.signal_manager.map_loaded.emit()
                        print("[加载] 已发射地图加载完成信号（状态修正）")
                else:
                    print(f"[加载] ❌ 页面加载失败，JavaScript执行结果: {result}")

            self.runJavaScript(test_script, on_js_result)

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
        # 只打印缩放、定位、路线更新、移动、瓦片加载相关的重要消息
        if any(keyword in message for keyword in ['缩放', '定位', '右键', '路线更新', '移动', '瓦片']):
            print(f"[Console] [{level}] 行{line_number}: {message}")

        # 处理地图缩放变化消息
        if message.startswith('缩放变化:'):
            print(f"[地图缩放] ========== 检测到缩放变化消息 ==========")
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

        # 处理地图中心变化消息（用户拖拽地图时触发）
        if message.startswith('地图中心:'):
            try:
                parts = message[len('地图中心:'):].split(',')
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                print(f"[地图中心] 捕获到中心点变化: {lat}, {lon}")
                if self.signal_manager:
                    self.signal_manager.map_center_changed.emit(lat, lon)
                else:
                    signal_manager.map_center_changed.emit(lat, lon)
            except Exception as e:
                print(f"[地图中心] 解析中心点坐标失败: {e}")
                import traceback
                traceback.print_exc()

        # 处理地图右键点击消息
        if message.startswith('右键点击:'):
            try:
                parts = message[len('右键点击:'):].split(',')
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                print(f"[地图右键] 捕获到右键点击: {lat}, {lon}")
                # 使用传入的信号管理器或全局信号管理器
                if self.signal_manager:
                    print("[地图右键] 使用实例信号管理器发送信号")
                    self.signal_manager.map_right_click.emit(lat, lon)
                else:
                    print("[地图右键] 使用全局信号管理器发送信号")
                    signal_manager.map_right_click.emit(lat, lon)
            except Exception as e:
                print(f"[地图右键] 解析右键点击位置失败: {e}")
                import traceback
                traceback.print_exc()

        # 处理收藏点删除消息（收藏点弹窗内的删除按钮触发）
        if message.startswith('收藏删除:'):
            try:
                fav_id = int(message[len('收藏删除:'):].strip())
                print(f"[收藏点] 捕获到删除收藏请求: id={fav_id}")
                if self.signal_manager:
                    print("[收藏点] 使用实例信号管理器发送信号")
                    self.signal_manager.favorite_delete_requested.emit(fav_id)
                else:
                    print("[收藏点] 使用全局信号管理器发送信号")
                    signal_manager.favorite_delete_requested.emit(fav_id)
            except Exception as e:
                print(f"[收藏点] 解析删除收藏请求失败: {e}")
                import traceback
                traceback.print_exc()

        # 处理地图中键双击消息（触发自动缩放）
        if message.startswith('中键双击缩放'):
            if self.signal_manager:
                self.signal_manager.map_middle_double_click.emit()
            else:
                signal_manager.map_middle_double_click.emit()

        # 处理定位标识隐藏消息（定位 popup 内的隐藏按钮触发）
        if message.startswith('隐藏定位标识'):
            print("[定位标识] 捕获到隐藏标识请求")
            if self.signal_manager:
                print("[定位标识] 使用实例信号管理器发送信号")
                self.signal_manager.location_marker_hidden.emit()
            else:
                print("[定位标识] 使用全局信号管理器发送信号")
                signal_manager.location_marker_hidden.emit()

        # 处理定位弹窗收藏消息（格式：收藏位置:lat,lon,名称，名称可能含逗号）
        if message.startswith('收藏位置:'):
            try:
                parts = message[len('收藏位置:'):].split(',')
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                name = ','.join(parts[2:]).strip()  # 名称含逗号时拼接恢复
                print(f"[定位标识] 捕获到收藏当前位置请求: ({lat}, {lon}) {name}")
                if self.signal_manager:
                    print("[定位标识] 使用实例信号管理器发送信号")
                    self.signal_manager.location_favorite_requested.emit(lat, lon, name)
                else:
                    print("[定位标识] 使用全局信号管理器发送信号")
                    signal_manager.location_favorite_requested.emit(lat, lon, name)
            except Exception as e:
                print(f"[定位标识] 解析收藏当前位置请求失败: {e}")
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

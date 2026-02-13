"""
定位管理器
负责各种定位功能（Windows原生、浏览器定位、IP定位）
支持后台线程执行和进度展示
"""

from typing import Optional, Callable
from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtCore import QObject, pyqtSlot
from modules.geolocation.location_helper import LocationHelper
from services.config.map_config import map_config
from core.background_task import TaskPriority


class LocationManager(QObject):
    """定位管理器

    负责管理各种定位功能，提供多级别定位服务：
    - Windows原生定位（高精度）
    - 浏览器Geolocation API定位
    - 高德在线定位
    - 高德IP定位
    - 公共IP定位（作为备选）

    定位优先级：Windows原生 → 浏览器定位 → 高德IP定位 → 公共IP定位

    支持后台线程异步执行，主线程快速响应用户操作
    """

    def __init__(self, service_manager, data_manager, ui_updater, logger, task_manager=None):
        """
        初始化定位管理器

        参数:
            service_manager: 服务管理器实例，提供各种定位服务
            data_manager: 数据管理器实例，用于存储定位结果
            ui_updater: UI更新回调函数字典，用于更新界面显示
            logger: 日志器，用于记录定位过程
            task_manager: 任务管理器实例，用于后台任务管理
        """
        super().__init__()
        self.service_manager = service_manager  # 服务管理器实例
        self.data_manager = data_manager  # 数据管理器实例
        self.ui_updater = ui_updater  # UI更新回调函数字典
        self.logger = logger  # 日志器
        self.task_manager = task_manager  # 任务管理器

    def get_current_location(self):
        """获取当前位置（按优先级依次尝试各种定位方式）

        定位优先级顺序：
        1. Windows原生定位（高精度）
        2. 浏览器Geolocation API定位
        3. 高德IP定位
        4. 公共IP定位

        使用后台线程异步执行，避免阻塞主线程
        """
        self.logger.info("=" * 80)
        self.logger.info("开始执行定位流程")
        self.logger.info("=" * 80)

        # 检查地图源是否已设置
        map_source = map_config.get_map_source()
        if not map_source:
            self.logger.warning("定位失败：未设置地图数据源")
            self.ui_updater['show_warning']("警告", "请先在地图配置中设置地图数据源")
            return

        # 如果有任务管理器，使用后台线程执行
        if self.task_manager:
            self.logger.info("使用后台线程执行定位任务")
            task_id = self.task_manager.submit_task(
                task_type="location",
                task_func=self._location_task_wrapper,
                priority=TaskPriority.HIGH,  # 用户操作优先级最高
                service_manager=self.service_manager,
                map_source=map_source
            )
            self.logger.debug(f"定位任务已提交: {task_id}")
        else:
            # 兼容模式：直接执行（不使用后台线程）
            self.logger.info("直接执行定位（兼容模式）")
            self._perform_location_sync()

    def _location_task_wrapper(self, service_manager, map_source,
                               progress_callback, log_callback, cancel_check):
        """定位任务包装器（用于后台线程执行）

        参数:
            service_manager: 服务管理器
            map_source: 地图源
            progress_callback: 进度回调函数 (percent, message)
            log_callback: 日志回调函数 (level, message)
            cancel_check: 取消检查函数，返回True表示需要取消

        返回:
            定位结果字典
        """
        try:
            log_callback("INFO", "开始定位流程")
            progress_callback(0, "正在初始化定位服务...")

            # 检查是否取消
            if cancel_check():
                log_callback("WARNING", "定位任务已取消")
                return None

            # 获取Windows位置服务
            windows_location = service_manager.windows_location_service
            log_callback("DEBUG", f"Windows位置服务可用: {windows_location.is_available()}")

            # 尝试 Windows 原生定位（优先级最高）
            if windows_location.is_available():
                progress_callback(10, "正在使用Windows原生定位...")
                log_callback("INFO", "尝试使用Windows原生位置服务...")

                # 检查是否取消
                if cancel_check():
                    log_callback("WARNING", "定位任务已取消")
                    return None

                # 获取Windows原生定位信息
                location_info = windows_location.get_location(timeout=10)
                if location_info:
                    progress_callback(100, "Windows原生定位成功")
                    log_callback("INFO", "Windows原生定位成功")
                    return {
                        'type': 'native',
                        'data': location_info
                    }

            # Windows定位不可用，尝试其他方式
            log_callback("INFO", "Windows定位不可用，尝试其他方式")
            progress_callback(30, "Windows定位不可用，尝试其他方式...")

            # 检查是否取消
            if cancel_check():
                log_callback("WARNING", "定位任务已取消")
                return None

            # 只有当当前地图源是高德时，才使用高德在线定位（浏览器定位）
            if map_source == "gaode" and map_config.is_gaode_configured():
                progress_callback(50, "正在使用高德地图在线定位...")
                log_callback("INFO", "尝试使用高德地图在线定位（浏览器定位）...")

                # 浏览器定位需要在主线程触发，所以这里返回特殊标记
                return {
                    'type': 'browser',
                    'data': None
                }

            # 尝试公共IP定位（最后备选）
            progress_callback(60, "正在使用公共IP定位...")
            log_callback("INFO", "尝试使用公共IP定位...")

            # 检查是否取消
            if cancel_check():
                log_callback("WARNING", "定位任务已取消")
                return None

            # 定义IP定位的日志回调函数
            def ip_log(level: str, message: str):
                log_callback(level, f"[公共IP定位] {message}")

            # 调用LocationHelper获取公共IP定位信息
            location_info = LocationHelper.get_ip_location(logger=ip_log)

            if location_info:
                progress_callback(100, "公共IP定位成功")
                log_callback("INFO", "公共IP定位成功")
                return {
                    'type': 'ip',
                    'data': location_info,
                    'source': '公共IP定位'
                }
            else:
                progress_callback(100, "定位失败")
                log_callback("ERROR", "所有定位方式均失败")
                return None

        except Exception as e:
            log_callback("ERROR", f"定位任务异常: {str(e)}")
            import traceback
            log_callback("DEBUG", traceback.format_exc())
            return None

    def _perform_location_sync(self):
        """同步执行定位（兼容模式，不使用后台线程）"""
        self.logger.info("开始定位流程")

        try:
            # 更新UI显示定位开始
            self.ui_updater['set_progress_indeterminate']()
            self.ui_updater['clear_results']()
            self.ui_updater['add_result']("正在定位...")

            # 获取Windows位置服务
            windows_location = self.service_manager.windows_location_service
            self.logger.debug(f"Windows位置服务可用: {windows_location.is_available()}")

            # 尝试 Windows 原生定位（优先级最高）
            if windows_location.is_available():
                self.ui_updater['add_result']("正在使用Windows原生定位...")
                self.logger.info("尝试使用Windows原生位置服务...")

                # 获取Windows原生定位信息
                location_info = windows_location.get_location(timeout=10)
                if location_info:
                    self.handle_native_location_success(location_info)
                    return

            # Windows定位不可用，尝试其他方式
            self.ui_updater['clear_results']()
            self.ui_updater['add_result']("Windows定位不可用")

            # 获取当前地图源
            current_map_source = map_config.get_map_source()

            # 只有当当前地图源是高德时，才使用高德在线定位
            if current_map_source == "gaode" and map_config.is_gaode_configured():
                self.ui_updater['add_result']("正在使用高德地图在线定位...")
                self.logger.info("尝试使用高德地图在线定位...")

                # 触发浏览器定位（异步，通过信号回调）
                self.ui_updater['trigger_browser_location']()
                return  # 等待信号回调

            # 尝试公共IP定位（最后备选）
            self._try_ip_location()

        except Exception as e:
            # 捕获定位过程中的异常
            self.logger.exception(f"定位流程异常: {str(e)}")
            self._handle_location_error(str(e))

        self.logger.info("定位流程完成")
        self.logger.info("=" * 80)

    @pyqtSlot(str, object)
    def on_location_task_completed(self, task_id: str, result):
        """处理定位任务完成（槽函数）

        参数:
            task_id: 任务ID
            result: 定位结果
        """
        self.logger.info(f"定位任务完成: {task_id}")

        if not result:
            # 定位失败
            self.ui_updater['clear_results']()
            self.ui_updater['add_result']("定位失败\n无法获取您的位置信息")
            self.logger.error("定位失败：无法获取您的位置信息")
            self.ui_updater['show_warning']("定位失败",
                "无法获取您的位置信息\n\n建议：\n1. 检查网络连接\n2. 确认Windows位置服务已开启（如适用）")
            return

        # 根据定位类型处理结果
        location_type = result.get('type')
        location_data = result.get('data')

        if location_type == 'native':
            # Windows原生定位成功
            self.handle_native_location_success(location_data)
        elif location_type == 'browser':
            # 需要触发浏览器定位
            self.ui_updater['clear_results']()
            self.ui_updater['add_result']("正在使用高德地图在线定位...")
            self.logger.info("触发浏览器定位...")
            self.ui_updater['trigger_browser_location']()
        elif location_type == 'ip':
            # IP定位成功
            source = result.get('source', 'IP地址定位')
            self.handle_ip_location_success(location_data, source)
        else:
            self.logger.error(f"未知的定位类型: {location_type}")

    @pyqtSlot(str, str)
    def on_location_task_failed(self, task_id: str, error: str):
        """处理定位任务失败（槽函数）

        参数:
            task_id: 任务ID
            error: 错误信息
        """
        self.logger.error(f"定位任务失败: {task_id} - {error}")
        self._handle_location_error(error)

    def _try_ip_location(self):
        """尝试公共IP定位（备选方案）

        当其他定位方式都失败时，使用公共IP定位作为最后的备选方案。
        公共IP定位精度较低，通常只能提供城市级别的位置信息。
        """
        self.ui_updater['clear_results']()
        self.ui_updater['add_result']("正在使用公共IP定位...")
        self.logger.warning("使用公共IP定位作为备选方案")

        # 定义IP定位的日志回调函数
        def ip_log(level: str, message: str):
            level_map = {
                "DEBUG": self.logger.debug,
                "INFO": self.logger.info,
                "WARNING": self.logger.warning,
                "ERROR": self.logger.error,
                "CRITICAL": self.logger.critical
            }
            log_func = level_map.get(level, self.logger.info)
            log_func(f"[公共IP定位] {message}")

        # 调用LocationHelper获取公共IP定位信息
        location_info = LocationHelper.get_ip_location(logger=ip_log)
        self.ui_updater['set_progress_complete']()

        if location_info:
            # IP定位成功，处理定位结果
            self.handle_ip_location_success(location_info, source="公共IP定位")
        else:
            # IP定位失败，显示错误信息
            self.ui_updater['clear_results']()
            self.ui_updater['add_result']("定位失败")
            self.ui_updater['add_result']("无法获取您的位置信息")
            self.logger.error("定位失败：无法获取您的位置信息")
            self.ui_updater['show_warning']("定位失败",
                "无法获取您的位置信息\n\n建议：\n1. 检查网络连接\n2. 确认Windows位置服务已开启（如适用）")

    def handle_browser_location_success(self, lat: float, lon: float, accuracy: float):
        """处理浏览器Geolocation API定位成功

        参数:
            lat: 纬度坐标
            lon: 经度坐标
            accuracy: 定位精度（单位：米）
        """
        self.logger.info(f"[LocationManager] 开始处理浏览器定位成功: {lat}, {lon}, 精度: {accuracy}m")

        # 根据当前地图源选择地理编码服务进行逆地理编码（将坐标转换为可读地址）
        address_info = None
        map_source = map_config.get_map_source()
        
        if map_source == 'gaode' and map_config.is_gaode_configured():
            self.logger.debug("[LocationManager] 使用高德地图进行逆地理编码...")
            geocoding_service = self.service_manager.gaode_geocoding_service
            address_info = geocoding_service.reverse_geocode(lat, lon)
        elif map_source == 'osm':
            self.logger.debug("[LocationManager] 使用 OSM 进行逆地理编码...")
            geocoding_service = self.service_manager.osm_geocoding_service
            address_info = geocoding_service.reverse_geocode(lat, lon)

        if address_info:
            # 解析地址信息
            city = address_info.get('city', '')  # 城市
            province = address_info.get('province', '')  # 省份
            district = address_info.get('district', '')  # 区县
            formatted_address = address_info.get('formatted_address', '')  # 详细地址

            # 更新UI显示定位成功信息
            self.ui_updater['set_progress_complete']()
            self.ui_updater['clear_results']()

            # 格式化位置信息
            location_parts = [province, city, district]
            location_text = "".join([part for part in location_parts if part])

            # 合并所有信息为一条结果，避免分散显示
            result_text = "定位成功！\n"
            result_text += "定位方式: 浏览器Geolocation API\n"

            if location_text:
                result_text += f"位置: {location_text}\n"
            if formatted_address:
                result_text += f"详细地址: {formatted_address}\n"

            result_text += f"坐标: {lat:.6f}, {lon:.6f}\n"
            result_text += f"精度: 约{accuracy:.0f}米"

            self.ui_updater['add_result'](result_text)

            # 准备地图上显示的弹出信息
            popup_text = f"我的位置\n{location_text}\n{formatted_address}\n定位方式: 浏览器定位\n精度: 约{accuracy:.0f}米"
            self.data_manager.current_location = (lat, lon)
            self.logger.debug(f"[LocationManager] 准备在地图上显示位置: {lat}, {lon}")
            # 在地图上显示定位结果
            self.ui_updater['show_location_on_map'](lat, lon, popup_text)
            self.logger.debug("[LocationManager] 地图显示完成")
            return

        # 如果逆地理编码失败，仅显示坐标信息
        self.ui_updater['set_progress_complete']()
        self.ui_updater['clear_results']()

        # 合并信息为一条结果，避免分散显示
        result_text = "定位成功！\n"
        result_text += "定位方式: 浏览器Geolocation API\n"
        result_text += f"坐标: {lat:.4f}, {lon:.4f}\n"
        result_text += f"精度: 约{accuracy:.0f}米"

        self.ui_updater['add_result'](result_text)

        # 准备地图上显示的弹出信息（无地址信息）
        popup_text = f"我的位置\n坐标: {lat:.4f}, {lon:.4f}\n定位方式: 浏览器定位\n精度: 约{accuracy:.0f}米"
        self.data_manager.current_location = (lat, lon)
        self.logger.debug(f"[LocationManager] 准备在地图上显示位置（无逆地理编码）: {lat}, {lon}")
        # 在地图上显示定位结果
        self.ui_updater['show_location_on_map'](lat, lon, popup_text)
        self.logger.debug("[LocationManager] 地图显示完成（无逆地理编码）")

    def handle_browser_location_error(self, error_msg: str):
        """处理浏览器定位失败

        参数:
            error_msg: 错误信息
        """
        self.logger.warning(f"浏览器定位失败: {error_msg}")

        # 浏览器定位失败后，尝试其他备选定位方式

        # 获取当前地图源
        current_map_source = map_config.get_map_source()

        # 只有当当前地图源是高德时，才尝试高德IP定位
        if current_map_source == "gaode" and map_config.is_gaode_configured():
            # 优先尝试高德IP定位
            self._try_gaode_ip_location()
        else:
            # 否则尝试公共IP定位
            self._try_ip_location()

    def _try_gaode_ip_location(self):
        """尝试高德IP定位（浏览器定位失败后的备选）

        当浏览器定位失败时，如果已配置高德地图API，则尝试使用高德IP定位服务。
        高德IP定位比公共IP定位精度更高。
        """
        self.ui_updater['clear_results']()
        self.ui_updater['add_result']("高德在线定位不可用")
        self.ui_updater['add_result']("正在使用高德地图IP定位...")
        self.logger.warning("高德地图在线定位失败，尝试高德IP定位")

        # 定义高德IP定位的日志回调函数
        def gaode_ip_log(level: str, message: str):
            level_map = {
                "DEBUG": self.logger.debug,
                "INFO": self.logger.info,
                "WARNING": self.logger.warning,
                "ERROR": self.logger.error,
                "CRITICAL": self.logger.critical
            }
            log_func = level_map.get(level, self.logger.info)
            log_func(f"[高德IP定位] {message}")

        # 调用LocationHelper获取高德IP定位信息
        location_info = LocationHelper.get_ip_location(
            use_gaode=True,  # 使用高德IP定位
            api_key=map_config.get_api_key() if map_config.is_gaode_configured() else None,  # 高德API密钥
            logger=gaode_ip_log  # 日志回调
        )

        self.ui_updater['set_progress_complete']()

        if location_info:
            # 高德IP定位成功，处理定位结果
            self.handle_ip_location_success(location_info, source="高德IP定位")
        else:
            # 高德IP定位失败，尝试公共IP定位
            self.ui_updater['clear_results']()
            self.ui_updater['add_result']("高德IP定位不可用")
            self.logger.warning("高德IP定位失败，尝试公共IP定位")
            self._try_ip_location()

    def handle_native_location_success(self, location_info: dict):
        """处理Windows原生定位成功

        Windows原生定位是精度最高的定位方式，使用Windows内置的位置服务API。

        参数:
            location_info: Windows定位服务返回的位置信息字典
        """
        self.logger.info("Windows原生定位成功")

        # 解析定位信息
        lat = location_info['latitude']  # 纬度
        lon = location_info['longitude']  # 经度
        accuracy = location_info.get('accuracy', 0)  # 精度（米）

        self.logger.debug(f"纬度: {lat}, 经度: {lon}, 精度: {accuracy}米")

        # 根据当前地图源选择地理编码服务进行逆地理编码（获取地址信息）
        address_info = None
        map_source = map_config.get_map_source()
        
        if map_source == 'gaode' and map_config.is_gaode_configured():
            # 使用高德地理编码服务
            geocoding_service = self.service_manager.gaode_geocoding_service
            address_info = geocoding_service.reverse_geocode(lat, lon)
        elif map_source == 'osm':
            # 使用 OSM 地理编码服务（Nominatim）
            geocoding_service = self.service_manager.osm_geocoding_service
            address_info = geocoding_service.reverse_geocode(lat, lon)

        # 保存当前位置信息
        self.data_manager.current_location = (lat, lon)

        # 更新UI显示定位成功
        self.ui_updater['set_progress_complete']()
        self.ui_updater['clear_results']()
        self.ui_updater['add_result']("定位成功！")
        self.ui_updater['add_result']("定位方式: Windows原生定位（高精度）")

        if address_info:
            # 格式化并显示地址信息
            location_text = self._format_address(address_info)
            self.ui_updater['add_result'](f"位置: {location_text}")
            popup_text = f"我的位置\n{location_text}\n定位方式: Windows原生定位\n精度: 约{accuracy:.0f}米"
        else:
            # 仅显示坐标信息
            popup_text = f"我的位置\n坐标: {lat:.4f}, {lon:.4f}\n定位方式: Windows原生定位\n精度: 约{accuracy:.0f}米"

        # 显示坐标和精度
        self.ui_updater['add_result'](f"坐标: {lat:.6f}, {lon:.6f}")
        self.ui_updater['add_result'](f"精度: 约{accuracy:.0f}米")

        self.logger.info(f"位置信息: {address_info if address_info else '仅坐标'}")
        # 在地图上显示位置
        self.ui_updater['show_location_on_map'](lat, lon, popup_text)

    def handle_ip_location_success(self, location_info: dict, source: str = "IP地址定位"):
        """处理IP定位成功

        IP定位精度较低，通常只能提供城市级别的位置信息。

        参数:
            location_info: IP定位返回的位置信息字典
            source: 定位来源名称（用于显示）
        """
        self.logger.info(f"{source}成功")

        # 解析定位信息
        lat = location_info.get('lat')  # 纬度
        lon = location_info.get('lon')  # 经度
        city = location_info.get('city', '')  # 城市
        country = location_info.get('country', '')  # 国家
        region = location_info.get('region', '')  # 地区
        isp = location_info.get('isp', '')  # 运营商
        source_key = location_info.get('source', '')  # 数据源标识

        # 仅城市级别定位（无坐标信息）
        if lat is None or lon is None:
            self.ui_updater['clear_results']()

            # 合并信息为一条结果，避免分散显示
            result_text = "定位成功！\n"
            result_text += f"定位方式: {source}（仅城市级别）\n"
            result_text += f"位置: {city}"

            self.ui_updater['add_result'](result_text)
            return

        self.logger.debug(f"纬度: {lat}, 经度: {lon}")
        self.logger.info(f"位置: {city}, {region}, {country}")

        # 保存当前位置信息
        self.data_manager.current_location = (lat, lon)

        # 更新UI显示定位成功
        self.ui_updater['clear_results']()

        # 合并所有信息为一条结果，避免分散显示
        result_text = "定位成功！\n"

        # 根据数据源标识显示不同的定位方式
        if source_key == 'gaode_ip':
            result_text += "定位方式: 高德IP定位（城市级精度）\n"
        else:
            result_text += f"定位方式: {source}（城市级精度）\n"

        # 格式化并显示位置信息
        location_text = ", ".join(filter(None, [city, region, country]))
        result_text += f"位置: {location_text}\n"
        result_text += f"坐标: {lat:.4f}, {lon:.4f}\n"

        # 显示运营商信息（如果有）
        if isp:
            result_text += f"运营商: {isp}"
            popup_text = f"我的位置\n{location_text}\n定位方式: {source}\n运营商: {isp}"
        else:
            result_text = result_text.rstrip("\n")  # 移除最后的换行符
            popup_text = f"我的位置\n{location_text}\n定位方式: {source}"

        self.ui_updater['add_result'](result_text)

        # 在地图上显示位置
        self.ui_updater['show_location_on_map'](lat, lon, popup_text)

    def _handle_location_error(self, error_msg: str):
        """处理定位错误

        当所有定位方式都失败或定位过程中发生异常时调用此方法。

        参数:
            error_msg: 错误信息
        """
        # 更新UI显示定位错误
        self.ui_updater['set_progress_complete']()
        self.ui_updater['clear_results']()

        # 合并错误信息为一条显示，避免分散
        result_text = f"定位出错\n错误信息: {error_msg}"
        self.ui_updater['add_result'](result_text)
        self.ui_updater['show_warning']("错误", f"定位出错: {error_msg}\n\n请检查网络连接")

    def _format_address(self, address_info: dict) -> str:
        """格式化地址信息

        将地址信息字典格式化为可读的地址字符串。

        参数:
            address_info: 地址信息字典，包含省、市、区县等信息

        返回:
            格式化后的地址字符串，格式为："省份城市区县"
        """
        province = address_info.get('province', '')  # 省份
        city = address_info.get('city', '')  # 城市
        district = address_info.get('district', '')  # 区县
        
        # 确保所有值都是字符串类型
        if isinstance(province, list):
            province = province[0] if province else ''
        if isinstance(city, list):
            city = city[0] if city else ''
        if isinstance(district, list):
            district = district[0] if district else ''
        
        # 转换为字符串（处理None等情况）
        province = str(province) if province else ''
        city = str(city) if city else ''
        district = str(district) if district else ''
        
        return "".join([province, city, district])  # 拼接成完整地址

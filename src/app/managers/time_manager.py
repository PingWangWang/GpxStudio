"""
时间管理器
负责时间计算和日期/时间面板管理
"""

from datetime import datetime
from PyQt5.QtCore import QDateTime, QTime


class TimeManager:
    """时间管理器
    
    负责时间计算和日期/时间面板管理：
    - 显示和管理日期选择面板
    - 显示和管理时间选择面板
    - 处理日期和时间选择事件
    - 根据起始时间和经历时间自动计算结束时间
    """

    def __init__(self, data_manager, ui_updater, logger):
        """
        初始化时间管理器

        参数:
            data_manager: 数据管理器实例，用于存储和获取时间数据
            ui_updater: UI更新回调函数字典，用于更新界面显示
            logger: 日志器，用于记录时间操作日志
        """
        self.data_manager = data_manager
        self.ui_updater = ui_updater
        self.logger = logger
        self.time_type = None  # 当前操作的时间类型

    def show_date_panel(self, time_type: str):
        """
        显示日期选择面板

        参数:
            time_type: 时间类型，目前只支持 "start"（起始时间）
        """
        # 自动关闭已打开的时间选择面板
        self.ui_updater['hide_time_panel']()

        self.time_type = time_type
        self.ui_updater['setup_date_panel_callback'](self.on_date_selected)

        # 设置当前选中的日期
        current_date = self.ui_updater['get_start_time']().date()

        # 显示日期面板
        self.ui_updater['show_date_panel'](current_date)

    def on_date_selected(self, selected_date):
        """
        日期选择回调

        参数:
            selected_date: 选择的日期（datetime对象）
        """
        # 只处理起始时间
        if self.time_type == "start":
            # 更新起始日期
            current_time = self.ui_updater['get_start_time']().time()
            new_datetime = QDateTime(
                selected_date.year, selected_date.month, selected_date.day,
                current_time.hour(), current_time.minute()
            )
            self.ui_updater['set_start_time'](new_datetime)

            # 自动计算结束时间
            self.calculate_times()

    def show_time_panel(self, time_type: str):
        """
        显示时间选择面板

        参数:
            time_type: 时间类型，目前只支持 "start"（起始时间）
        """
        # 自动关闭已打开的日期选择面板
        self.ui_updater['hide_date_panel']()

        self.time_type = time_type
        self.ui_updater['setup_time_panel_callback'](self.on_time_selected)

        # 设置当前选中的时间
        current_time = self.ui_updater['get_start_time']().time()

        # 显示时间面板
        self.ui_updater['show_time_panel'](current_time)

    def on_time_selected(self, selected_time):
        """
        时间选择回调

        参数:
            selected_time: 选择的时间（datetime对象）
        """
        # 只处理起始时间
        if self.time_type == "start":
            # 更新起始时间
            current_date = self.ui_updater['get_start_time']().date()
            new_datetime = QDateTime(
                current_date.year(), current_date.month(), current_date.day(),
                selected_time.hour, selected_time.minute
            )
            self.ui_updater['set_start_time'](new_datetime)

            # 自动计算结束时间
            self.calculate_times()

    def calculate_times(self):
        """计算时间
        
        根据起始时间和经历时间自动计算结束时间：
        - 获取起始时间和经历小时数
        - 计算结束时间（支持小数小时）
        - 更新结束时间显示
        
        异常处理：
        - 处理无效的经历时间格式
        - 记录计算过程中的错误
        """
        try:
            # 获取起始时间
            start_datetime = self.ui_updater['get_start_time']()

            # 从文本框获取经历小时数
            duration_text = self.ui_updater['get_duration']().strip()
            if not duration_text:
                duration_hours = 1  # 默认1小时
            else:
                try:
                    duration_hours = float(duration_text)
                except ValueError:
                    duration_hours = 1
                    self.logger.warning(f"无效的经历时间格式: {duration_text}，使用默认值1小时")

            # 计算结束时间（支持小数小时）
            duration_seconds = int(duration_hours * 3600)
            end_datetime = start_datetime.addSecs(duration_seconds)

            # 更新结束时间显示
            self.ui_updater['set_end_time'](end_datetime)

        except Exception as e:
            self.logger.warning(f"计算时间时出错: {str(e)}")

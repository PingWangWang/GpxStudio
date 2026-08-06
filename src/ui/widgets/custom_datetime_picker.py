"""
自定义日期时间选择器
左侧日历选择，右侧时间列表选择
"""

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QCalendarWidget,
                             QListWidget, QListWidgetItem, QLabel, QFrame, QPushButton, QSpinBox)
from PyQt5.QtCore import Qt, QDate, QTime, QDateTime, pyqtSignal, QLocale
from PyQt5.QtGui import QFont
from ui.theme import theme


class CustomDateTimePicker(QWidget):
    """自定义日期时间选择器"""

    dateTimeChanged = pyqtSignal(QDateTime)  # 日期时间改变信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_date = QDate.currentDate()
        self.current_time = QTime.currentTime()
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        # 设置焦点策略以接收键盘事件
        self.setFocusPolicy(Qt.StrongFocus)

        # 设置样式 - 与其他面板保持一致
        theme.set_theme_stylesheet(self, """
            QWidget {
                background-color: __PANEL_BG__;
                border-radius: 6px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QCalendarWidget {
                background-color: __INPUT_BG__;
                border: 1px solid __BORDER__;
                border-radius: 4px;
            }
            QCalendarWidget QToolButton {
                background-color: transparent;
                border: none;
                color: __TEXT__;
                font-size: 12px;
                padding: 4px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: __HOVER__;
                border-radius: 2px;
            }
            QCalendarWidget QMenu {
                background-color: __PANEL_BG__;
                border: 1px solid __BORDER__;
                color: __TEXT__;
            }
            QCalendarWidget QSpinBox {
                background-color: transparent;
                border: none;
                color: __TEXT__;
                padding: 2px;
            }
            QCalendarWidget QAbstractButton {
                background-color: transparent;
                border: none;
                color: __TEXT__;
                font-size: 12px;
            }
            QCalendarWidget QAbstractButton:hover {
                background-color: __HOVER__;
                border-radius: 2px;
            }
            QCalendarWidget QAbstractItemView {
                background-color: __INPUT_BG__;
                border: none;
                color: __TEXT__;
                selection-background-color: __ACCENT__;
                selection-color: __TEXT_ON_ACCENT__;
            }
            QListWidget {
                background-color: __INPUT_BG__;
                border: 1px solid __BORDER__;
                border-radius: 4px;
                color: __TEXT__;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid __DIVIDER__;
                color: __TEXT__;
            }
            QListWidget::item:hover {
                background-color: __HOVER_STRONG__;
                color: __TEXT__;
            }
            QListWidget::item:selected {
                background-color: __ACCENT__;
                color: __TEXT_ON_ACCENT__;
            }
            QLabel {
                color: __TEXT__;
                font-size: 12px;
                font-weight: bold;
                padding: 4px 0px;
            }
            QFrame {
                color: __DIVIDER__;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # 左侧：日历选择
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        # 日历控件
        self.calendar = QCalendarWidget()
        self.calendar.setSelectedDate(self.current_date)
        self.calendar.setGridVisible(True)
        self.calendar.setMinimumSize(280, 200)
        # 设置日历头部格式 - 中文显示
        self.calendar.setLocale(QLocale('zh_CN'))

        # 禁用日历导航栏的下拉选择功能并去除三角箭头
        # 获取导航栏的按钮
        nav_bar = self.calendar.findChild(QWidget, 'qt_calendar_navigationbar')
        if nav_bar:
            # 隐藏所有下拉按钮（包括月份选择的三角箭头）
            for button in nav_bar.findChildren(QPushButton):
                button.hide()
            # 禁用年份和月份的下拉选择
            for spinbox in nav_bar.findChildren(QSpinBox):
                spinbox.setReadOnly(True)

        # 添加样式来确保没有三角箭头显示
        theme.apply_to_sub(self.calendar, """
            QCalendarWidget QToolButton {
                background-color: transparent;
                border: none;
                color: __TEXT__;
                font-size: 12px;
                padding: 4px;
            }
            QCalendarWidget QToolButton::menu-indicator {
                image: none;
            }
            QCalendarWidget QAbstractButton {
                background-color: transparent;
                border: none;
                color: __TEXT__;
                font-size: 12px;
            }
            QCalendarWidget QAbstractButton::menu-indicator {
                image: none;
            }
        """)

        # 连接日历信号
        self.calendar.activated.connect(self._on_date_double_clicked)  # 双击
        # 启用单击选择，更新current_date但不发送信号
        self.calendar.clicked.connect(self._on_date_clicked)  # 单击

        left_layout.addWidget(self.calendar)
        layout.addWidget(left_container)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        theme.apply_to_sub(separator, "QFrame { color: __DIVIDER__; }")
        layout.addWidget(separator)

        # 右侧：时间选择
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # 时间列表
        self.time_list = QListWidget()
        self.time_list.setMinimumSize(120, 200)
        self.time_list.setMaximumWidth(150)

        # 生成30分钟间隔的时间列表
        self._populate_time_list()

        # 连接时间列表信号 - 只响应双击
        self.time_list.itemDoubleClicked.connect(self._on_time_double_clicked)  # 双击
        # 禁用单击选择效果（但保留视觉反馈）
        self.time_list.itemClicked.connect(lambda: None)  # 单击无响应

        right_layout.addWidget(self.time_list)
        layout.addWidget(right_container)

        # 设置初始选中的时间
        self._select_current_time()

    def _populate_time_list(self):
        """填充时间列表 - 30分钟间隔"""
        self.time_list.clear()

        # 生成24小时，每30分钟一个时间点
        for hour in range(24):
            for minute in [0, 30]:
                time = QTime(hour, minute)
                time_text = time.toString("hh:mm")

                item = QListWidgetItem(time_text)
                item.setData(Qt.UserRole, time)  # 存储QTime对象
                self.time_list.addItem(item)

    def _select_current_time(self):
        """选中当前时间（最接近的30分钟间隔）"""
        current_hour = self.current_time.hour()
        current_minute = self.current_time.minute()

        # 找到最接近的30分钟间隔
        if current_minute < 15:
            target_minute = 0
        elif current_minute < 45:
            target_minute = 30
        else:
            target_minute = 0
            current_hour = (current_hour + 1) % 24

        target_time = QTime(current_hour, target_minute)

        # 在列表中找到并选中对应项
        for i in range(self.time_list.count()):
            item = self.time_list.item(i)
            item_time = item.data(Qt.UserRole)
            if item_time == target_time:
                self.time_list.setCurrentRow(i)
                self.current_time = target_time
                break

    def _on_date_clicked(self, date):
        """日历单击事件 - 只更新日期，不发送信号"""
        self.current_date = date
        print(f"[日期选择] 单击选择日期: {date.toString('yyyy-MM-dd')}")

    def _on_date_double_clicked(self, date):
        """日历双击事件"""
        self.current_date = date
        self._emit_datetime_changed()
        print(f"[日期选择] 双击选择日期: {date.toString('yyyy-MM-dd')}")

    def _on_time_double_clicked(self, item):
        """时间列表双击事件"""
        time = item.data(Qt.UserRole)
        self.current_time = time
        self._emit_datetime_changed()
        print(f"[时间选择] 双击选择时间: {time.toString('hh:mm')}")

    def _emit_datetime_changed(self):
        """发送日期时间改变信号"""
        datetime = QDateTime(self.current_date, self.current_time)
        self.dateTimeChanged.emit(datetime)

    def setDateTime(self, datetime):
        """设置日期时间"""
        self.current_date = datetime.date()
        self.current_time = datetime.time()

        # 更新日历选择
        self.calendar.setSelectedDate(self.current_date)

        # 更新时间列表选择
        self._select_time_in_list(self.current_time)

    def _select_time_in_list(self, time):
        """在时间列表中选中指定时间"""
        for i in range(self.time_list.count()):
            item = self.time_list.item(i)
            item_time = item.data(Qt.UserRole)
            if item_time == time:
                self.time_list.setCurrentRow(i)
                break

    def dateTime(self):
        """获取当前日期时间"""
        return QDateTime(self.current_date, self.current_time)

    def date(self):
        """获取当前日期"""
        return self.current_date

    def time(self):
        """获取当前时间"""
        return self.current_time

    def keyPressEvent(self, event):
        """键盘按键事件"""
        if event.key() == Qt.Key_Escape:
            # 通知父级关闭弹出窗口
            parent_widget = self.parent()
            if parent_widget and hasattr(parent_widget, 'hide'):
                print("[日期时间选择器] ESC键关闭选择器")
                parent_widget.hide()
                event.accept()
                return

        super().keyPressEvent(event)
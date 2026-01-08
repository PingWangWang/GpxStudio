"""
日期时间选择面板
提供日期和时间的选择功能
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame, QCalendarWidget, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from datetime import datetime, timedelta


class DateSelectPanel(QWidget):
    """日期选择面板"""

    date_selected = pyqtSignal(datetime)

    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置为弹出窗口，不显示在任务栏
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)

        # 头部
        header_layout = QHBoxLayout()

        title_label = QLabel("日期选择")
        title_label.setStyleSheet("font-weight: bold; color: #000000;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        close_button = QPushButton("关闭")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #000000;
                border: 1px solid #cccccc;
                padding: 3px 10px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        close_button.clicked.connect(self.hide)
        header_layout.addWidget(close_button)

        layout.addLayout(header_layout)

        # 日历控件
        self.calendar = QCalendarWidget()
        self.calendar.setStyleSheet("""
            QCalendarWidget {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #cccccc;
            }
            QCalendarWidget QWidget {
                alternate-background-color: #f5f5f5;
            }
            QCalendarWidget QAbstractItemView {
                selection-background-color: #0078d4;
                selection-color: #ffffff;
            }
        """)
        self.calendar.activated.connect(self.on_date_selected)
        layout.addWidget(self.calendar)

    def on_date_selected(self, date):
        """日期选择（双击确认）"""
        selected_date = datetime(
            date.year(),
            date.month(),
            date.day()
        )
        self.date_selected.emit(selected_date)

        # 双击确认后隐藏面板
        self.hide()

    def show_panel(self, current_date=None, pos=None, button_height=None, panel_size=None):
        """显示面板

        Args:
            current_date: 当前日期
            pos: 显示位置
            button_height: 按钮高度（用于计算位置）
            panel_size: 自定义面板大小（QSize对象）
        """
        if current_date:
            self.calendar.setSelectedDate(current_date)

        # 设置面板大小
        if panel_size:
            self.resize(panel_size)
        else:
            self.resize(300, 300)  # 默认大小

        if pos:
            # 直接使用传入的位置，不再计算button_height
            x = pos.x()
            y = pos.y()

            # 确保面板不会超出屏幕边界
            from PyQt5.QtWidgets import QApplication
            screen_geometry = QApplication.desktop().availableGeometry()
            panel_width = self.width()
            panel_height = self.height()

            # 如果面板右侧超出屏幕，调整x坐标
            if x + panel_width > screen_geometry.width():
                x = screen_geometry.width() - panel_width

            # 如果面板底部超出屏幕，调整y坐标
            if y + panel_height > screen_geometry.height():
                y = screen_geometry.height() - panel_height

            # 确保面板不会显示在屏幕外
            x = max(x, 0)
            y = max(y, 0)

            self.move(x, y)

        self.show()
        self.raise_()
        self.activateWindow()


class TimeSelectPanel(QWidget):
    """时间选择面板"""

    time_selected = pyqtSignal(datetime)

    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置为弹出窗口，不显示在任务栏
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)

        # 头部
        header_layout = QHBoxLayout()

        title_label = QLabel("时间选择")
        title_label.setStyleSheet("font-weight: bold; color: #000000;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        close_button = QPushButton("关闭")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #000000;
                border: 1px solid #cccccc;
                padding: 3px 10px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        close_button.clicked.connect(self.hide)
        header_layout.addWidget(close_button)

        layout.addLayout(header_layout)

        # 时间列表
        self.time_list = QListWidget()
        self.time_list.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #cccccc;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
        """)
        self.time_list.itemClicked.connect(self.on_time_selected)
        self.time_list.itemDoubleClicked.connect(self.on_time_double_clicked)

        # 生成半小时间隔的时间列表
        self.generate_time_list()

        layout.addWidget(self.time_list)

    def generate_time_list(self):
        """生成半小时间隔的时间列表"""
        self.time_list.clear()

        # 从00:00到23:30，每30分钟一个时间点
        for hour in range(24):
            for minute in [0, 30]:
                time_str = f"{hour:02d}:{minute:02d}"
                item = QListWidgetItem(time_str)
                item.setFont(QFont("Consolas", 10))
                self.time_list.addItem(item)

    def on_time_selected(self, item):
        """时间选择"""
        time_str = item.text()
        time_obj = datetime.strptime(time_str, "%H:%M")
        self.time_selected.emit(time_obj)

    def on_time_double_clicked(self, item):
        """时间双击选择"""
        self.on_time_selected(item)
        self.hide()

    def show_panel(self, current_time=None, pos=None, button_height=None, panel_size=None):
        """显示面板

        Args:
            current_time: 当前时间
            pos: 显示位置
            button_height: 按钮高度（用于计算位置）
            panel_size: 自定义面板大小（QSize对象）
        """
        if current_time:
            # 查找最接近的时间项
            # 检查current_time是QTime还是datetime对象
            if hasattr(current_time, 'toString'):
                # QTime对象
                current_time_str = current_time.toString("HH:mm")
            else:
                # datetime对象
                current_time_str = current_time.strftime("HH:mm")

            for i in range(self.time_list.count()):
                if self.time_list.item(i).text() == current_time_str:
                    self.time_list.setCurrentRow(i)
                    break

        # 设置面板大小
        if panel_size:
            self.resize(panel_size)
        else:
            self.resize(200, 400)  # 默认大小

        if pos:
            # 计算面板显示位置
            if button_height:
                x = pos.x()
                y = pos.y() + button_height
            else:
                x = pos.x()
                y = pos.y()

            # 确保面板不会超出屏幕边界
            from PyQt5.QtWidgets import QApplication
            screen_geometry = QApplication.desktop().availableGeometry()
            panel_width = self.width()
            panel_height = self.height()

            # 如果面板右侧超出屏幕，调整x坐标
            if x + panel_width > screen_geometry.width():
                x = screen_geometry.width() - panel_width

            # 如果面板底部超出屏幕，调整y坐标
            if y + panel_height > screen_geometry.height():
                y = screen_geometry.height() - panel_height

            # 确保面板不会显示在屏幕外
            x = max(x, 0)
            y = max(y, 0)

            self.move(x, y)

        self.show()

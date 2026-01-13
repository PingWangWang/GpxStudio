"""
GPX Studio 启动画面
在应用程序加载时显示进度条，提升用户体验
"""

from PyQt5.QtWidgets import QSplashScreen, QVBoxLayout, QLabel, QProgressBar, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont
from typing import Optional

# 导入版本信息
from version import __version__


class SplashScreen(QSplashScreen):
    """启动画面类，显示应用加载进度"""

    def __init__(self, width: int = 500, height: int = 300):
        """
        初始化启动画面

        Args:
            width: 启动画面宽度
            height: 启动画面高度
        """
        # 创建一个空白pixmap
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(45, 45, 48))  # 深色背景

        super().__init__(pixmap)

        # 设置窗口属性
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        # 创建布局和组件
        self._init_ui()

    def _init_ui(self):
        """初始化UI组件"""
        # 创建主widget和布局
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # 标题标签
        self.title_label = QLabel("GPX Studio")
        self.title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #ffffff;")
        layout.addWidget(self.title_label)

        # 添加弹性空间
        layout.addStretch()

        # 状态标签
        self.status_label = QLabel("正在初始化...")
        self.status_label.setAlignment(Qt.AlignCenter)
        status_font = QFont()
        status_font.setPointSize(10)
        self.status_label.setFont(status_font)
        self.status_label.setStyleSheet("color: #b0b0b0;")
        layout.addWidget(self.status_label)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #3a3a3c;
            }
            QProgressBar::chunk {
                border-radius: 4px;
                background-color: #007acc;
            }
        """)
        layout.addWidget(self.progress_bar)

        # 版本标签
        self.version_label = QLabel(f"版本 {__version__}")
        self.version_label.setAlignment(Qt.AlignCenter)
        version_font = QFont()
        version_font.setPointSize(8)
        self.version_label.setFont(version_font)
        self.version_label.setStyleSheet("color: #808080;")
        layout.addWidget(self.version_label)

        # 设置布局
        widget.setLayout(layout)
        widget.setGeometry(0, 0, self.width(), self.height())

    def update_progress(self, value: int, message: str = ""):
        """
        更新进度

        Args:
            value: 进度值 (0-100)
            message: 状态消息
        """
        self.progress_bar.setValue(value)
        if message:
            self.status_label.setText(message)
        # 处理待处理的事件，确保界面更新
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()

    def finish_with_window(self, window):
        """
        在主窗口显示时关闭启动画面

        Args:
            window: 主窗口实例
        """
        self.finish(window)

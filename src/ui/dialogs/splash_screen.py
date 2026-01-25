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

    def _calculate_optimal_font_size(self, text, max_width, margin=40):
        """
        计算最佳字体大小，确保文字能在指定宽度内完全显示
        
        Args:
            text: 要显示的文字
            max_width: 最大可用宽度
            margin: 左右边距总和
            
        Returns:
            最佳字体大小（点）
        """
        available_width = max_width - (margin * 2)
        
        # 从大到小尝试字体大小
        for font_size in range(100, 10, -1):
            font = QFont()
            font.setPointSize(font_size)
            font.setBold(True)
            
            # 创建临时字体度量对象进行测量
            from PyQt5.QtGui import QFontMetrics
            metrics = QFontMetrics(font)
            text_width = metrics.width(text)
            
            if text_width <= available_width:
                return font_size
        
        return 10  # 最小字体大小

    def _init_ui(self):
        """初始化UI组件"""
        # 创建主widget和布局
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # 标题标签
        self.title_label = QLabel("GPX STUDIO")
        self.title_label.setAlignment(Qt.AlignCenter)
        
        # 计算最佳字体大小
        optimal_size = self._calculate_optimal_font_size("GPX STUDIO", self.width())
        
        title_font = QFont()
        title_font.setPointSize(optimal_size)
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

    def test_font_size_calculation(self):
        """
        测试不同窗口大小下的字体大小计算
        """
        test_widths = [300, 400, 500, 600, 700, 800, 900, 1000]
        
        print("测试不同窗口宽度下的最佳字体大小:")
        print("-" * 60)
        
        for width in test_widths:
            # 临时设置宽度
            original_width = self.width()
            self.setFixedWidth(width)
            
            # 计算字体大小
            font_size = self._calculate_optimal_font_size("GPX STUDIO", width)
            
            # 计算实际可用宽度
            available_width = width - 80  # 40px边距 * 2
            
            # 计算文字宽度
            from PyQt5.QtGui import QFontMetrics
            font = QFont()
            font.setPointSize(font_size)
            font.setBold(True)
            metrics = QFontMetrics(font)
            text_width = metrics.width("GPX STUDIO")
            
            print(f"窗口宽度: {width}px | 可用宽度: {available_width}px | 字体大小: {font_size}pt | 文字宽度: {text_width}px")
            
            # 恢复原宽度
            self.setFixedWidth(original_width)
        
        print("-" * 60)

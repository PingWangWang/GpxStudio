"""
进度显示面板
用于显示海拔数据获取和GPX文件导出的进度
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QPushButton, QFrame
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class ProgressPopup(QWidget):
    """进度显示面板"""

    # 信号定义
    cancel_requested = pyqtSignal()  # 取消请求信号
    closed = pyqtSignal()  # 面板关闭信号

    def __init__(self, parent=None):
        """
        初始化进度显示面板

        参数:
            parent: 父窗口
        """
        super().__init__(parent)
        self._init_ui()

        # 设置窗口标志 - 使用Tool窗口，无标题栏
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)  # 不透明背景

        # 设置焦点策略以接收键盘事件
        self.setFocusPolicy(Qt.StrongFocus)

        # 标志：是否已取消
        self._is_cancelled = False

    def _init_ui(self):
        """初始化UI"""
        # 设置面板样式 - 与GPX导出面板颜色统一
        self.setStyleSheet("""
            ProgressPopup {
                background-color: #3b4453;
                border-radius: 8px;
                border: 1px solid rgba(0, 0, 0, 0.15);
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QLabel {
                color: white;
                font-size: 13px;
            }
            QProgressBar {
                height: 8px;
                border-radius: 4px;
                background-color: rgba(255, 255, 255, 0.1);
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 4px;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.9);
                color: #3b4453;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: white;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.8);
            }
            QFrame {
                color: rgba(255, 255, 255, 0.3);
            }
        """)

        # 设置自动填充背景
        self.setAutoFillBackground(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 标题
        title_label = QLabel("正在处理...")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("QFrame { color: #e0e0e0; }")
        layout.addWidget(separator)

        # 进度信息标签
        self.progress_label = QLabel("准备中...")
        self.progress_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 12px;
            }
        """)
        layout.addWidget(self.progress_label)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # 按钮区域
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)

        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.7);
                color: #666666;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.85);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.6);
            }
        """)
        button_layout.addWidget(self.cancel_button)

        # 完成按钮（默认隐藏）
        self.complete_button = QPushButton("确认")
        self.complete_button.clicked.connect(self._on_complete_clicked)
        self.complete_button.setVisible(False)
        button_layout.addWidget(self.complete_button)

        layout.addWidget(button_container)

        # 设置固定宽度
        self.setFixedWidth(320)

    def set_progress(self, value, message):
        """
        设置进度值和消息

        参数:
            value: 进度值（0-100）
            message: 进度消息
        """
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)

    def set_indeterminate(self, message="处理中..."):
        """
        设置为不确定进度模式

        参数:
            message: 进度消息
        """
        self.progress_bar.setRange(0, 0)
        self.progress_label.setText(message)

    def set_complete(self, message="处理完成"):
        """
        设置为完成状态

        参数:
            message: 完成消息
        """
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.progress_label.setText(message)
        
        # 显示完成按钮，隐藏取消按钮
        self.complete_button.setVisible(True)
        self.cancel_button.setVisible(False)

    def is_cancelled(self):
        """
        检查是否已取消

        返回:
            bool: 是否已取消
        """
        return self._is_cancelled

    def _on_cancel_clicked(self):
        """取消按钮点击"""
        self._is_cancelled = True
        self.cancel_requested.emit()
        self.hide()
        self.closed.emit()

    def _on_complete_clicked(self):
        """完成按钮点击"""
        self.hide()
        self.closed.emit()

    def show_at_center(self):
        """
        在屏幕中央显示面板
        """
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        center_x = screen.center().x() - self.width() // 2
        center_y = screen.center().y() - self.height() // 2
        self.move(center_x, center_y)
        self.show()
        self.raise_()
        self.activateWindow()

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        super().mousePressEvent(event)
        event.accept()  # 接受事件，防止传播到父组件

    def keyPressEvent(self, event):
        """键盘按键事件"""
        if event.key() == Qt.Key_Escape:
            # 按ESC键关闭面板
            self.hide()
            self.closed.emit()
            event.accept()
        else:
            super().keyPressEvent(event)

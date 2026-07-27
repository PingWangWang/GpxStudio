"""
任务进度展示组件
提供丰富的任务执行信息展示
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QTextEdit, QPushButton, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QTextCursor
from datetime import datetime
from typing import Optional


class TaskProgressWidget(QWidget):
    """任务进度展示组件

    显示当前任务的详细信息：
    - 任务名称和类型
    - 进度条
    - 实时状态消息
    - 执行时间
    - 取消按钮
    """

    cancel_requested = pyqtSignal(str)  # 请求取消任务：任务ID

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_task_id: Optional[str] = None
        self.current_task_type: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.setup_ui()

        # 定时器用于更新执行时间
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_elapsed_time)

    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 任务信息行
        info_layout = QHBoxLayout()

        # 任务图标和名称
        self.task_icon = QLabel("⏳")
        self.task_icon.setStyleSheet("font-size: 9pt;")
        self.task_icon.setFixedWidth(30)  # 固定宽度，避免图标变化导致布局跳变
        info_layout.addWidget(self.task_icon)

        self.task_label = QLabel("准备就绪")
        self.task_label.setStyleSheet("font-weight: bold; color: #333333; font-size: 9pt;")
        info_layout.addWidget(self.task_label)

        info_layout.addStretch()

        # 执行时间
        self.time_label = QLabel("00:00")
        self.time_label.setStyleSheet("color: #666666; font-family: Consolas; font-size: 9pt;")
        self.time_label.setFixedWidth(50)  # 固定宽度，避免时间变化导致布局跳变
        info_layout.addWidget(self.time_label)

        # 取消按钮 - 使用固定宽度的占位符，避免显示/隐藏导致布局跳变
        cancel_container = QWidget()
        cancel_container.setFixedWidth(30)  # 固定宽度
        cancel_layout = QHBoxLayout(cancel_container)
        cancel_layout.setContentsMargins(0, 0, 0, 0)

        self.cancel_button = QPushButton("✕")
        self.cancel_button.setToolTip("取消任务")
        self.cancel_button.setFixedSize(24, 24)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                border-radius: 3px;
                font-weight: bold;
                color: #666666;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #ff6b6b;
                color: white;
                border-color: #ff6b6b;
            }
        """)
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        self.cancel_button.setVisible(False)
        cancel_layout.addWidget(self.cancel_button)

        info_layout.addWidget(cancel_container)

        layout.addLayout(info_layout)

        # 进度条 - 始终保持固定高度，避免显示/隐藏导致布局跳变
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(22)  # 固定高度
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 3px;
                text-align: center;
                background-color: #f5f5f5;
                font-size: 9pt;
            }
            QProgressBar::chunk {
                background-color: #3d93fd;
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # 状态消息 - 固定高度，避免内容变化导致布局跳变
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setFixedHeight(40)  # 固定高度，可容纳2行文本
        self.status_label.setStyleSheet("color: #666666; font-size: 9pt;")
        layout.addWidget(self.status_label)

        # 详细信息展示区 - 固定高度
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setFixedHeight(100)  # 使用固定高度而不是最小/最大高度
        self.detail_text.setFont(QFont("Consolas", 9))
        self.detail_text.setStyleSheet("""
            QTextEdit {
                background-color: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 3px;
                padding: 5px;
                color: #333333;
                font-size: 9pt;
            }
        """)
        layout.addWidget(self.detail_text)

        # 初始状态：进度条设置为0%而不是隐藏，避免布局跳变
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("")  # 空白格式，不显示百分比

    def start_task(self, task_id: str, task_type: str, task_name: str):
        """开始新任务"""
        self.current_task_id = task_id
        self.current_task_type = task_type
        self.start_time = datetime.now()

        # 更新UI
        self.task_icon.setText("⏳")
        self.task_label.setText(f"{task_name}")
        self.status_label.setText("正在初始化...")
        self.time_label.setText("00:00")

        # 显示取消按钮，进度条始终可见
        self.cancel_button.setVisible(True)

        # 设置进度条为不确定模式
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFormat("%p%")  # 显示百分比

        # 清空详细信息
        self.detail_text.clear()
        self._add_detail(f"▶ 开始执行: {task_name}", "#4A90E2")

        # 启动计时器
        self.timer.start(1000)  # 每秒更新

    def update_progress(self, percent: int, message: str):
        """更新进度"""
        if percent < 0:
            # 不确定进度
            self.progress_bar.setRange(0, 0)
        else:
            # 确定进度
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(percent)

        self.status_label.setText(message)
        self._add_detail(f"• {message}", "#666666")

    def task_completed(self, message: str = "任务完成"):
        """任务完成"""
        self.task_icon.setText("✓")
        self.task_label.setStyleSheet("font-weight: bold; color: #4caf50;")
        self.status_label.setText(message)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self._add_detail(f"✓ {message}", "#4caf50")

        # 停止计时器
        self.timer.stop()

        # 延迟隐藏取消按钮
        QTimer.singleShot(2000, lambda: self.cancel_button.setVisible(False))

    def task_failed(self, error_message: str):
        """任务失败"""
        self.task_icon.setText("✗")
        self.task_label.setStyleSheet("font-weight: bold; color: #f44336;")
        self.status_label.setText("任务失败")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self._add_detail(f"✗ 失败: {error_message}", "#f44336")

        # 停止计时器
        self.timer.stop()

        # 隐藏取消按钮
        self.cancel_button.setVisible(False)

    def task_cancelled(self):
        """任务取消"""
        self.task_icon.setText("⊗")
        self.task_label.setStyleSheet("font-weight: bold; color: #ff9800;")
        self.status_label.setText("任务已取消")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self._add_detail("⊗ 任务已取消", "#ff9800")

        # 停止计时器
        self.timer.stop()

        # 隐藏取消按钮
        self.cancel_button.setVisible(False)

    def reset(self):
        """重置为空闲状态"""
        self.current_task_id = None
        self.current_task_type = None
        self.start_time = None

        self.task_icon.setText("⏳")
        self.task_label.setText("准备就绪")
        self.task_label.setStyleSheet("font-weight: bold; color: #333333; font-size: 9pt;")
        self.status_label.setText("")
        self.time_label.setText("00:00")

        # 隐藏取消按钮，进度条保持可见但设置为0%
        self.cancel_button.setVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("")  # 空白格式，不显示百分比

        # 停止计时器
        self.timer.stop()

    def add_log(self, level: str, message: str):
        """添加日志信息"""
        color_map = {
            "DEBUG": "#999999",
            "INFO": "#333333",
            "WARNING": "#ff9800",
            "ERROR": "#f44336",
            "CRITICAL": "#f44336"
        }
        color = color_map.get(level, "#333333")

        icon_map = {
            "DEBUG": "◦",
            "INFO": "•",
            "WARNING": "⚠",
            "ERROR": "✗",
            "CRITICAL": "✗"
        }
        icon = icon_map.get(level, "•")

        self._add_detail(f"{icon} {message}", color)

    def _add_detail(self, text: str, color: str):
        """添加详细信息（内部方法）"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        html = f'<span style="color: #999999;">[{timestamp}]</span> <span style="color: {color};">{text}</span><br>'

        # 使用insertHtml而不是append，避免QTextCursor信号问题
        cursor = self.detail_text.textCursor()
        cursor.movePosition(cursor.End)
        self.detail_text.setTextCursor(cursor)
        self.detail_text.insertHtml(html)

        # 滚动到底部
        scrollbar = self.detail_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _update_elapsed_time(self):
        """更新执行时间"""
        if self.start_time:
            elapsed = datetime.now() - self.start_time
            seconds = int(elapsed.total_seconds())
            minutes = seconds // 60
            seconds = seconds % 60
            self.time_label.setText(f"{minutes:02d}:{seconds:02d}")

    def _on_cancel_clicked(self):
        """取消按钮点击"""
        if self.current_task_id:
            self.cancel_requested.emit(self.current_task_id)
            self.cancel_button.setEnabled(False)
            self.cancel_button.setText("⋯")


class TaskInfoPanel(QFrame):
    """任务信息面板

    集成任务进度展示组件，提供完整的任务信息界面
    """

    cancel_task_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        # 去除边框样式，使用简单的背景色
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: none;
            }
        """)

        # 设置固定最小高度，避免任务执行前后高度变化
        self.setMinimumHeight(250)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # 标题
        title_label = QLabel("任务执行状态")
        title_label.setStyleSheet("font-weight: bold; font-size: 9pt; color: #333333;")
        layout.addWidget(title_label)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #e0e0e0;")
        layout.addWidget(separator)

        # 任务进度组件
        self.progress_widget = TaskProgressWidget()
        self.progress_widget.cancel_requested.connect(
            lambda task_id: self.cancel_task_requested.emit(task_id)
        )
        layout.addWidget(self.progress_widget)

    def start_task(self, task_id: str, task_type: str, task_name: str):
        """开始任务"""
        self.progress_widget.start_task(task_id, task_type, task_name)

    def update_progress(self, percent: int, message: str):
        """更新进度"""
        self.progress_widget.update_progress(percent, message)

    def task_completed(self, message: str = "任务完成"):
        """任务完成"""
        self.progress_widget.task_completed(message)

    def task_failed(self, error: str):
        """任务失败"""
        self.progress_widget.task_failed(error)

    def task_cancelled(self):
        """任务取消"""
        self.progress_widget.task_cancelled()

    def add_log(self, level: str, message: str):
        """添加日志"""
        self.progress_widget.add_log(level, message)

    def reset(self):
        """重置"""
        self.progress_widget.reset()

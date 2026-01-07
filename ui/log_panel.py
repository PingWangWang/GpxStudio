"""
日志显示组件
提供带级别过滤的日志输出窗口
"""

import logging
from datetime import datetime
from typing import Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QComboBox,
    QLabel, QPushButton, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QTextCursor, QColor, QFont


LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

LOG_COLORS = {
    logging.DEBUG: QColor(128, 128, 128),
    logging.INFO: QColor(0, 0, 0),
    logging.WARNING: QColor(200, 150, 0),
    logging.ERROR: QColor(200, 0, 0),
    logging.CRITICAL: QColor(200, 0, 0)
}


class LogMessage:
    """日志消息封装类"""

    def __init__(self, level: int, message: str, timestamp: Optional[datetime] = None):
        self.level = level
        self.message = message
        self.timestamp = timestamp or datetime.now()

    def get_level_name(self) -> str:
        return logging.getLevelName(self.level)

    def get_level_short(self) -> str:
        return {logging.DEBUG: "D", logging.INFO: "I", logging.WARNING: "W", logging.ERROR: "E"}.get(self.level, "?")


class LogDisplayWidget(QTextEdit):
    """日志显示窗口组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setLineWrapMode(QTextEdit.NoWrap)
        self.setFont(QFont("Consolas", 9))
        self.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #cccccc;
                padding: 5px;
            }
        """)
        self.max_lines = 1000
        self.min_level = logging.INFO
        self.messages = []

    def add_message(self, message: LogMessage):
        """添加日志消息"""
        if message.level < self.min_level:
            return

        self.messages.append(message)
        if len(self.messages) > self.max_lines:
            self.messages.pop(0)

        self._append_formatted(message)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def _append_formatted(self, message: LogMessage):
        """格式化输出消息"""
        time_str = message.timestamp.strftime("%H:%M:%S")
        level_short = message.get_level_short()
        color = LOG_COLORS.get(message.level, QColor(0, 0, 0))

        html = f'''
        <span style="color: #008000;">[{time_str}]</span>
        <span style="color: {color.name()}; font-weight: bold;">[{level_short}]</span>
        <span style="color: #000000;">{message.message}</span><br>
        '''
        self.insertHtml(html)

    def clear_messages(self):
        """清空所有消息"""
        self.clear()
        self.messages = []

    def set_min_level(self, level: int):
        """设置最小显示级别"""
        self.min_level = level
        self._refresh_display()

    def _refresh_display(self):
        """刷新显示"""
        self.blockSignals(True)
        current_pos = self.verticalScrollBar().value()
        max_pos = self.verticalScrollBar().maximum()

        self.clear()
        for msg in self.messages:
            if msg.level >= self.min_level:
                self._append_formatted(msg)

        if max_pos > 0:
            self.verticalScrollBar().setValue(max_pos)
        self.blockSignals(False)


class LogPanel(QWidget):
    """日志面板组件"""

    message_logged = pyqtSignal(LogMessage)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.log_display = LogDisplayWidget()
        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)

        header_layout = QHBoxLayout()

        title_label = QLabel("程序日志")
        title_label.setStyleSheet("font-weight: bold; color: #000000;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        header_layout.addWidget(QLabel("显示级别:"))

        self.level_combo = QComboBox()
        self.level_combo.addItems(list(LOG_LEVELS.keys()))
        self.level_combo.setCurrentText("INFO")
        self.level_combo.setStyleSheet("""
            QComboBox {
                background-color: #f0f0f0;
                color: #000000;
                border: 1px solid #cccccc;
                padding: 3px 8px;
                min-width: 80px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #666;
            }
        """)
        self.level_combo.currentTextChanged.connect(self.on_level_changed)
        header_layout.addWidget(self.level_combo)

        clear_button = QPushButton("清空")
        clear_button.setStyleSheet("""
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
        clear_button.clicked.connect(self.log_display.clear_messages)
        header_layout.addWidget(clear_button)

        layout.addLayout(header_layout)
        layout.addWidget(self.log_display)

    def on_level_changed(self, level_name: str):
        """级别改变"""
        level = LOG_LEVELS.get(level_name, logging.INFO)
        self.log_display.set_min_level(level)

    def log(self, level: int, message: str):
        """记录日志"""
        msg = LogMessage(level, message)
        self.log_display.add_message(msg)
        self.message_logged.emit(msg)


class LogHandler(logging.Handler):
    """自定义日志处理器，输出到QTextEdit"""

    def __init__(self, log_panel: LogPanel):
        super().__init__()
        self.log_panel = log_panel
        self.setLevel(logging.DEBUG)

    def emit(self, record: logging.LogRecord):
        """发送日志记录"""
        try:
            msg = LogMessage(
                level=record.levelno,
                message=self.format(record)
            )
            self.log_panel.log(record.levelno, self.format(record))
        except Exception:
            pass

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        if record.levelno == logging.DEBUG:
            return f"[{record.name}] {record.getMessage()}"
        return record.getMessage()


def setup_logger(log_panel: LogPanel, name: str = "GpxStudio") -> logging.Logger:
    """设置应用日志系统"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    handler = LogHandler(log_panel)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    return logger

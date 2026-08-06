"""
自定义消息对话框
用于替代系统原生的QMessageBox，保持UI风格一致
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QApplication)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.theme import theme

class CustomMessageDialog(QDialog):
    """自定义消息对话框（替代QMessageBox，支持主题切换）"""

    def __init__(self, parent=None, title="", message="", informative_text="", 
                 show_cancel=True, ok_text="确定", cancel_text="取消"):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        self._init_ui(title, message, informative_text, show_cancel, ok_text, cancel_text)

    def _init_ui(self, title, message, informative_text, show_cancel, ok_text, cancel_text):
        theme.set_theme_stylesheet(self, """
            CustomMessageDialog {
                background-color: __PANEL_BG__;
                border-radius: 8px;
                border: 2px solid rgba(0, 123, 255, 0.2);
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QLabel {
                color: __TEXT__;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QPushButton {
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 13px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                min-width: 80px;
            }
            QPushButton#primaryButton {
                background-color: __BTN_PRIMARY_BG__;
                color: __BTN_PRIMARY_TEXT__;
                border: none;
                font-weight: bold;
            }
            QPushButton#primaryButton:hover {
                background-color: __BTN_PRIMARY_HOVER__;
            }
            QPushButton#primaryButton:pressed {
                background-color: __BTN_PRIMARY_PRESSED__;
            }
            QPushButton#secondaryButton {
                background-color: __BTN_SECONDARY_BG__;
                color: __BTN_SECONDARY_TEXT__;
                border: 1px solid __BTN_SECONDARY_BORDER__;
            }
            QPushButton#secondaryButton:hover {
                background-color: __BTN_SECONDARY_HOVER__;
            }
            QPushButton#secondaryButton:pressed {
                background-color: __BTN_SECONDARY_PRESSED__;
            }
            QPushButton#closeButton {
                background-color: transparent;
                border: none;
                font-size: 16px;
                color: __TEXT_SECONDARY__;
                min-width: 20px;
                padding: 0;
            }
            QPushButton#closeButton:hover {
                color: __TEXT__;
                background-color: __HOVER__;
                border-radius: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 20)
        layout.setSpacing(15)

        # 标题栏
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)
        
        # 标题
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # 关闭按钮
        close_btn = QPushButton("✕")
        close_btn.setToolTip("关闭")
        close_btn.setObjectName("closeButton")
        close_btn.setFixedSize(24, 24)
        close_btn.clicked.connect(self.reject)
        title_layout.addWidget(close_btn)
        
        layout.addLayout(title_layout)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        theme.apply_to_sub(line, "background-color: __BORDER__;")
        layout.addWidget(line)

        # 消息内容
        msg_label = QLabel(message)
        msg_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 5px;")
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)
        
        if informative_text:
            info_label = QLabel(informative_text)
            theme.apply_to_sub(info_label, "color: __TEXT_TERTIARY__; margin-bottom: 5px;")
            info_label.setWordWrap(True)
            layout.addWidget(info_label)

        layout.addStretch()

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        button_layout.addStretch()
        
        if show_cancel:
            cancel_btn = QPushButton(cancel_text)
            cancel_btn.setToolTip("取消")
            cancel_btn.setObjectName("secondaryButton")
            cancel_btn.clicked.connect(self.reject)
            button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton(ok_text)
        ok_btn.setToolTip("确认")
        ok_btn.setObjectName("primaryButton")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)

        # 设置最小宽度
        self.setMinimumWidth(350)
        self.setMaximumWidth(500)

    def _center_on_screen(self):
        """居中显示（在布局完成后调用）"""
        # 确保几何信息已更新
        self.updateGeometry()
        
        if self.parent() and self.parent().isVisible():
            # 居中于父窗口
            parent_geo = self.parent().geometry()
            x = parent_geo.x() + (parent_geo.width() - self.width()) // 2
            y = parent_geo.y() + (parent_geo.height() - self.height()) // 2
            self.move(x, y)
        else:
            # 居中于屏幕
            screen = QApplication.primaryScreen().geometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)
    
    def exec_(self):
        """重写exec_方法，在显示前居中"""
        # 在显示前居中，确保布局已完成
        self.adjustSize()  # 调整到合适的大小
        self._center_on_screen()
        return super().exec_()
            
    # 支持拖动窗口
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

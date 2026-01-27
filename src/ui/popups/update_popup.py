"""
更新提示弹出面板
用于显示新版本信息和发布说明
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QFrame, QWidget)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

class UpdatePopup(QDialog):
    """更新提示弹出面板"""

    # 返回值常量
    RESULT_UPDATE = 1
    RESULT_SKIP = 2
    RESULT_LATER = 0

    def __init__(self, parent=None, version="", release_notes=""):
        super().__init__(parent)
        self.version = version
        self.release_notes = release_notes
        self.result_code = self.RESULT_LATER
        
        self._init_ui()
        
        # 设置窗口标志 - 无边框对话框
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        # 居中显示
        self._center_on_screen()

    def _init_ui(self):
        """初始化UI"""
        # 设置面板样式 - 与其他弹出面板保持一致
        self.setStyleSheet("""
            UpdatePopup {
                background-color: #3b4453;
                border-radius: 8px;
                border: 2px solid rgba(0, 123, 255, 0.2);
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QLabel {
                color: white;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QTextEdit {
                background-color: rgba(0, 0, 0, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                color: #e0e0e0;
                font-size: 13px;
                padding: 5px;
                font-family: "Consolas", "Microsoft YaHei", monospace;
            }
            QPushButton {
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 13px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                min-width: 80px;
            }
            /* 主要按钮样式 */
            QPushButton#primaryButton {
                background-color: #4A90E2;
                color: white;
                border: none;
                font-weight: bold;
            }
            QPushButton#primaryButton:hover {
                background-color: #357ABD;
            }
            QPushButton#primaryButton:pressed {
                background-color: #2A629A;
            }
            /* 次要按钮样式 */
            QPushButton#secondaryButton {
                background-color: rgba(255, 255, 255, 0.1);
                color: #e0e0e0;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            QPushButton#secondaryButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
            QPushButton#secondaryButton:pressed {
                background-color: rgba(255, 255, 255, 0.15);
            }
            /* 关闭按钮样式 */
            QPushButton#closeButton {
                background-color: transparent;
                border: none;
                font-size: 16px;
                color: #aaaaaa;
                min-width: 20px;
                padding: 0;
            }
            QPushButton#closeButton:hover {
                color: white;
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 20)
        layout.setSpacing(15)

        # 标题栏区域
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)
        
        # 标题
        title_label = QLabel("发现新版本")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # 关闭按钮 (右上角)
        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeButton")
        close_btn.setFixedSize(24, 24)
        close_btn.clicked.connect(self.reject)
        title_layout.addWidget(close_btn)
        
        layout.addLayout(title_layout)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: rgba(255, 255, 255, 0.2);")
        layout.addWidget(line)

        # 版本信息
        version_info = QLabel(f"最新版本: v{self.version}")
        version_info.setStyleSheet("font-size: 14px; font-weight: bold; color: #4A90E2;")
        layout.addWidget(version_info)
        
        info_label = QLabel("建议您更新到最新版本以获取更好的体验。")
        info_label.setStyleSheet("color: #cccccc;")
        layout.addWidget(info_label)

        # Release Notes 区域
        if self.release_notes:
            notes_label = QLabel("更新内容:")
            notes_label.setStyleSheet("font-weight: bold; margin-top: 5px;")
            layout.addWidget(notes_label)
            
            self.notes_area = QTextEdit()
            self.notes_area.setReadOnly(True)
            self.notes_area.setText(self.release_notes)
            self.notes_area.setMinimumHeight(150)
            layout.addWidget(self.notes_area)

        # 底部按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 跳过按钮
        self.skip_btn = QPushButton("跳过此版本")
        self.skip_btn.setObjectName("secondaryButton")
        self.skip_btn.clicked.connect(self.on_skip_clicked)
        button_layout.addWidget(self.skip_btn)
        
        button_layout.addStretch()
        
        # 稍后按钮
        self.later_btn = QPushButton("稍后再说")
        self.later_btn.setObjectName("secondaryButton")
        self.later_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.later_btn)
        
        # 更新按钮
        self.update_btn = QPushButton("立即更新")
        self.update_btn.setObjectName("primaryButton")
        self.update_btn.clicked.connect(self.on_update_clicked)
        button_layout.addWidget(self.update_btn)
        
        layout.addLayout(button_layout)

        # 设置固定宽度，高度自适应
        self.setFixedWidth(450)

    def on_update_clicked(self):
        """点击立即更新"""
        self.result_code = self.RESULT_UPDATE
        self.accept()

    def on_skip_clicked(self):
        """点击跳过版本"""
        self.result_code = self.RESULT_SKIP
        self.accept()

    def exec_(self):
        """重写exec_方法，返回自定义结果码"""
        super().exec_()
        return self.result_code

    def _center_on_screen(self):
        """居中显示"""
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    # 支持拖动窗口
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()


class CustomMessageDialog(QDialog):
    """自定义消息对话框（替代QMessageBox）"""

    def __init__(self, parent=None, title="", message="", informative_text="", 
                 show_cancel=True, ok_text="确定", cancel_text="取消"):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        self._init_ui(title, message, informative_text, show_cancel, ok_text, cancel_text)
        self._center_on_screen()

    def _init_ui(self, title, message, informative_text, show_cancel, ok_text, cancel_text):
        self.setStyleSheet("""
            CustomMessageDialog {
                background-color: #3b4453;
                border-radius: 8px;
                border: 2px solid rgba(0, 123, 255, 0.2);
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QLabel {
                color: white;
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
                background-color: #4A90E2;
                color: white;
                border: none;
                font-weight: bold;
            }
            QPushButton#primaryButton:hover {
                background-color: #357ABD;
            }
            QPushButton#primaryButton:pressed {
                background-color: #2A629A;
            }
            QPushButton#secondaryButton {
                background-color: rgba(255, 255, 255, 0.1);
                color: #e0e0e0;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            QPushButton#secondaryButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
            QPushButton#secondaryButton:pressed {
                background-color: rgba(255, 255, 255, 0.15);
            }
            QPushButton#closeButton {
                background-color: transparent;
                border: none;
                font-size: 16px;
                color: #aaaaaa;
                min-width: 20px;
                padding: 0;
            }
            QPushButton#closeButton:hover {
                color: white;
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 20)
        layout.setSpacing(15)

        # 标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeButton")
        close_btn.setFixedSize(24, 24)
        close_btn.clicked.connect(self.reject)
        title_layout.addWidget(close_btn)
        layout.addLayout(title_layout)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: rgba(255, 255, 255, 0.2);")
        layout.addWidget(line)

        # 内容
        if message:
            msg_label = QLabel(message)
            msg_label.setStyleSheet("font-size: 14px; color: white;")
            msg_label.setWordWrap(True)
            layout.addWidget(msg_label)
            
        if informative_text:
            info_label = QLabel(informative_text)
            info_label.setStyleSheet("font-size: 12px; color: #cccccc;")
            info_label.setWordWrap(True)
            layout.addWidget(info_label)

        layout.addStretch()

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        if show_cancel:
            cancel_btn = QPushButton(cancel_text)
            cancel_btn.setObjectName("secondaryButton")
            cancel_btn.clicked.connect(self.reject)
            btn_layout.addWidget(cancel_btn)
            
        ok_btn = QPushButton(ok_text)
        ok_btn.setObjectName("primaryButton")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
        
        self.setFixedWidth(350)

    def _center_on_screen(self):
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

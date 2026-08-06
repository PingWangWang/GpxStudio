"""
更新提示弹出面板
用于显示新版本信息和发布说明
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QFrame, QWidget)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from ui.theme import theme

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

    def _init_ui(self):
        """初始化UI"""
        # 设置面板样式 - 与其他弹出面板保持一致
        theme.set_theme_stylesheet(self, """
            UpdatePopup {
                background-color: __PANEL_BG__;
                border-radius: 8px;
                border: 2px solid rgba(0, 123, 255, 0.2);
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QLabel {
                color: __TEXT__;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QTextEdit {
                background-color: __INPUT_BG__;
                border: 1px solid __BORDER__;
                border-radius: 4px;
                color: __TEXT__;
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
            /* 次要按钮样式 */
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
            /* 关闭按钮样式 */
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
        close_btn.setToolTip("关闭")
        close_btn.clicked.connect(self.reject)
        title_layout.addWidget(close_btn)
        
        layout.addLayout(title_layout)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        theme.apply_to_sub(line, "background-color: __DIVIDER__;")
        layout.addWidget(line)

        # 版本信息
        version_info = QLabel(f"最新版本: v{self.version}")
        theme.apply_to_sub(version_info, "font-size: 14px; font-weight: bold; color: __ACCENT__;")
        layout.addWidget(version_info)
        
        info_label = QLabel("建议您更新到最新版本以获取更好的体验。")
        theme.apply_to_sub(info_label, "color: __TEXT_TERTIARY__;")
        layout.addWidget(info_label)

        # Release Notes 区域
        if self.release_notes:
            notes_label = QLabel("更新内容:")
            notes_label.setStyleSheet("font-weight: bold; margin-top: 5px;")
            layout.addWidget(notes_label)
            
            self.notes_area = QTextEdit()
            self.notes_area.setReadOnly(True)
            self.notes_area.setText(self.release_notes)
            self.notes_area.setMinimumHeight(60)  # 缩小最小高度
            self.notes_area.setMaximumHeight(120)  # 限制最大高度
            layout.addWidget(self.notes_area)

        # 底部按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 跳过按钮
        self.skip_btn = QPushButton("跳过此版本")
        self.skip_btn.setObjectName("secondaryButton")
        self.skip_btn.setToolTip("跳过此版本，下次不再提示")
        self.skip_btn.clicked.connect(self.on_skip_clicked)
        button_layout.addWidget(self.skip_btn)
        
        button_layout.addStretch()
        
        # 稍后按钮
        self.later_btn = QPushButton("稍后再说")
        self.later_btn.setObjectName("secondaryButton")
        self.later_btn.setToolTip("稍后提醒我")
        self.later_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.later_btn)
        
        # 更新按钮
        self.update_btn = QPushButton("立即更新")
        self.update_btn.setObjectName("primaryButton")
        self.update_btn.setToolTip("立即下载并安装更新")
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
        # 在显示前居中，确保布局已完成
        self.adjustSize()  # 调整到合适的大小
        self._center_on_screen()
        super().exec_()
        return self.result_code

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


class DownloadProgressDialog(QDialog):
    """自定义下载进度对话框（暗色主题）"""
    
    # 信号：用户取消下载
    canceled = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_canceled = False
        self._init_ui()
        
        # 设置窗口标志 - 无边框对话框
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setModal(True)
    
    def _init_ui(self):
        """初始化UI"""
        # 设置样式 - 与其他弹出面板保持一致
        theme.set_theme_stylesheet(self, """
            DownloadProgressDialog {
                background-color: __PANEL_BG__;
                border-radius: 8px;
                border: 2px solid rgba(0, 123, 255, 0.2);
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QLabel {
                color: __TEXT__;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QProgressBar {
                border: 1px solid __BORDER__;
                border-radius: 4px;
                background-color: rgba(0, 0, 0, 0.3);
                text-align: center;
                color: __TEXT__;
                font-size: 12px;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: __ACCENT__;
                border-radius: 3px;
            }
            QPushButton {
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 13px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                min-width: 80px;
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
        title_label = QLabel("下载更新")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # 关闭按钮
        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeButton")
        close_btn.setFixedSize(24, 24)
        close_btn.setToolTip("关闭")
        close_btn.clicked.connect(self.on_cancel_clicked)
        title_layout.addWidget(close_btn)
        
        layout.addLayout(title_layout)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        theme.apply_to_sub(line, "background-color: __DIVIDER__;")
        layout.addWidget(line)
        
        # 提示文本
        self.message_label = QLabel("正在下载更新...")
        self.message_label.setStyleSheet("font-size: 13px; margin-top: 5px;")
        layout.addWidget(self.message_label)
        
        # 进度条
        from PyQt5.QtWidgets import QProgressBar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        layout.addSpacing(10)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.setToolTip("取消更新")
        cancel_btn.clicked.connect(self.on_cancel_clicked)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # 设置固定宽度
        self.setFixedWidth(450)
    
    def set_value(self, value):
        """设置进度值"""
        self.progress_bar.setValue(value)
    
    def set_message(self, message):
        """设置提示消息"""
        self.message_label.setText(message)
    
    def on_cancel_clicked(self):
        """取消按钮点击"""
        self.user_canceled = True
        self.canceled.emit()
        self.reject()
    
    def was_canceled(self):
        """检查是否被取消"""
        return self.user_canceled
    
    def exec_(self):
        """重写exec_方法，在显示前居中"""
        # 在显示前居中，确保布局已完成
        self.adjustSize()
        self._center_on_screen()
        return super().exec_()
    
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


# 为了兼容性，重新导出 CustomMessageDialog
try:
    from ui.dialogs.custom_message_dialog import CustomMessageDialog
except ImportError:
    pass


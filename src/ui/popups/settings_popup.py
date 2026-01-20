"""
设置弹出面板组件

包含地图设置、日志设置和关于信息的弹出面板
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QPushButton, QLabel, QMessageBox,
                             QTabWidget, QTextEdit, QComboBox, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QEvent
from PyQt5.QtGui import QIcon, QKeyEvent, QPainter, QPen, QBrush, QPolygon
from PyQt5.QtCore import QPoint
from services.config.map_config import map_config
from core.logging_setup import clean_logs, open_log_directory, get_log_size, set_log_level
from services.config import about_config
import os


class CustomArrowButton(QPushButton):
    """自定义箭头按钮，绘制更美观的下拉箭头"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(30, 46)
        self.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: #f8f9fa;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
                border-left: 1px solid #e1e5e9;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """)

    def paintEvent(self, event):
        """绘制按钮和箭头"""
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 设置箭头颜色
        if self.isDown():
            color = Qt.black
        elif self.underMouse():
            color = Qt.darkGray
        else:
            color = Qt.gray

        painter.setPen(QPen(color, 2))
        painter.setBrush(QBrush(color))

        # 计算箭头位置（居中）
        center_x = self.width() // 2
        center_y = self.height() // 2

        # 绘制下拉箭头（三角形）
        arrow = QPolygon([
            QPoint(center_x - 5, center_y - 2),  # 左上角
            QPoint(center_x + 5, center_y - 2),  # 右上角
            QPoint(center_x, center_y + 3)       # 底部中心
        ])

        painter.drawPolygon(arrow)


class BaseSettingsPopup(QWidget):
    """设置弹出面板基类"""

    closed = pyqtSignal()  # 关闭信号

    def __init__(self, parent=None):
        super().__init__(parent)

        # 设置窗口标志 - 使用Popup类型，可以自动处理失去焦点时关闭
        # Qt.Popup会在点击外部时自动关闭，并且不抢夺焦点
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)  # 不透明背景

        # 设置样式
        self.setStyleSheet("""
            BaseSettingsPopup {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 2px solid rgba(0, 123, 255, 0.2);
                font-family: 'Microsoft YaHei';
            }
        """)

        # 设置固定宽度
        self.setFixedWidth(500)  # 增加宽度

    def keyPressEvent(self, event: QKeyEvent):
        """处理键盘事件"""
        if event.key() == Qt.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)

    def event(self, event: QEvent):
        """处理所有事件"""
        # 当窗口失去激活状态时自动关闭
        if event.type() == QEvent.WindowDeactivate:
            self.hide()
            return True
        return super().event(event)

    def hideEvent(self, event):
        """窗口隐藏事件 - 确保无论何种方式关闭都发出closed信号"""
        super().hideEvent(event)
        # 发出关闭信号，通知相关组件（如停止按钮动画）
        self.closed.emit()

    def show_popup(self, button_widget):
        """
        显示弹出面板

        Args:
            button_widget: 触发按钮控件（用于定位）
        """
        # 获取按钮的全局位置
        button_rect = button_widget.rect()
        button_global_pos = button_widget.mapToGlobal(button_rect.topRight())

        # 设置面板位置（按钮左侧，向左弹出）
        popup_x = button_global_pos.x() - self.width() - 10  # 10px间距
        popup_y = button_global_pos.y()

        self.move(popup_x, popup_y)
        self.show()
        self.raise_()
        self.setFocus()  # 设置焦点以接收键盘事件


class MapSettingsPopup(BaseSettingsPopup):
    """地图设置弹出面板"""

    config_saved = pyqtSignal()  # 配置保存信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(300, 240)  # 设置宽度为300px
        self._init_ui()
        self.load_current_config()

    def show_popup(self, button_widget):
        """
        显示弹出面板

        Args:
            button_widget: 触发按钮控件（用于定位）
        """
        # 获取按钮的全局位置
        button_rect = button_widget.rect()
        button_global_pos = button_widget.mapToGlobal(button_rect.topLeft())

        # 获取按钮列表容器的位置（假设按钮是right_buttons_container的子元素）
        if hasattr(button_widget.parent(), 'rect'):
            buttons_container = button_widget.parent()
            container_rect = buttons_container.rect()
            container_global_pos = buttons_container.mapToGlobal(container_rect.topLeft())

            # 设置面板位置：与按钮顶部对齐，面板右侧与按钮列表左侧间隔1-2px
            popup_x = container_global_pos.x() - self.width() - 2
            popup_y = button_global_pos.y()
        else:
            #  fallback: 使用默认位置
            popup_x = button_global_pos.x() - self.width() - 10
            popup_y = button_global_pos.y()

        self.move(popup_x, popup_y)
        self.show()
        self.raise_()
        self.setFocus()  # 设置焦点以接收键盘事件

    def _init_ui(self):
        """初始化UI"""
        # 设置面板样式 - 与路线规划面板保持一致
        self.setStyleSheet("""
            MapSettingsPopup {
                background-color: #4A90E2;
                border-radius: 6px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QLabel {
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QPushButton {
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QLineEdit {
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QComboBox {
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
        """)

        # 设置自动填充背景
        self.setAutoFillBackground(True)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(2)

        # 标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel("地图设置")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: bold;
                color: white;
                font-family: 'Microsoft YaHei';
            }
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        # 关闭按钮
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 14px;
                color: white;
                border-radius: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        close_btn.clicked.connect(self.hide)
        title_layout.addWidget(close_btn)

        main_layout.addLayout(title_layout)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: rgba(255, 255, 255, 0.2); margin: 5px 0;")
        main_layout.addWidget(line)

        # 地图数据源选择
        self.map_source_combo = QComboBox()
        self.map_source_combo.addItem("无")
        self.map_source_combo.addItem("OpenStreetMap")
        self.map_source_combo.addItem("高德地图")
        self.map_source_combo.currentIndexChanged.connect(self.on_map_source_changed)
        self.map_source_combo.setFixedHeight(30)  # 直接设置固定高度
        self.map_source_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.map_source_combo.setContentsMargins(0, 0, 0, 0)  # 移除所有内边距

        # 设置下拉框样式
        self.map_source_combo.setStyleSheet("""
            QComboBox {
                padding: 0px 30px 0px 8px; /* 调整padding避免影响高度 */
                border: 0px;
                border-radius: 3px;
                background-color: rgba(255, 255, 255, 0.9);
                font-size: 12px;
                color: #333333;
                min-height: 30px;
                max-height: 30px;
                height: 30px;
                line-height: 30px;
                vertical-align: middle;
            }
            QComboBox:focus {
                background-color: white;
            }
            QComboBox::drop-down {
                border: 0px;
                background-color: transparent;
                width: 30px;
                height: 30px;
                position: absolute;
                right: 0px;
                top: 0px;
            }
            QComboBox::down-arrow {
                image: url(:/icons/arrow-down-white.png);
                width: 10px;
                height: 10px;
                margin: auto;
            }
            QComboBox QAbstractItemView {
                border: 1px solid rgba(0, 0, 0, 0.2);
                border-radius: 3px;
                background-color: white;
                selection-background-color: #4A90E2;
                selection-color: white;
                font-size: 12px;
            }
            QComboBox QLineEdit {
                /* 确保内部编辑器与QComboBox高度一致 */
                border: 0px;
                min-height: 30px;
                max-height: 30px;
                height: 30px;
                padding: 0px;
            }
        """)

        # 创建下拉框容器
        combo_container = QWidget()
        combo_layout = QHBoxLayout(combo_container)
        combo_layout.setContentsMargins(0, 0, 0, 0)
        self.map_source_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 让下拉框自适应宽度
        combo_layout.addWidget(self.map_source_combo)

        # 添加一个占位按钮，使容器宽度与API Key输入框一致
        combo_placeholder_btn = QPushButton()
        combo_placeholder_btn.setFixedSize(30, 30)
        combo_placeholder_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
            }
        """)
        combo_placeholder_btn.setEnabled(False)
        combo_layout.addWidget(combo_placeholder_btn)

        combo_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # 创建输入框和相关控件
        # API Key输入框
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("请输入高德地图API Key")
        self.api_key_edit.setFixedHeight(30)  # 直接设置固定高度
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setAlignment(Qt.AlignLeft)  # 确保文本左对齐
        # 设置较小的字体以显示更多内容
        self.api_key_edit.setStyleSheet("""
            QLineEdit {
                padding: 4px 8px 4px 8px;
                border: none;
                border-radius: 3px;
                background-color: rgba(255, 255, 255, 0.9);
                font-size: 11px;
                color: #333333;
                height: 30px;
            }
            QLineEdit:focus {
                background-color: white;
            }
        """)
        # 设置文本边距，为右侧的眼睛按钮留出空间
        self.api_key_edit.setTextMargins(0, 2, 0, 2)  # 减小上下边距以防止提示语被截断
        # 确保文本始终从左侧开始显示
        self.api_key_edit.textChanged.connect(self.ensure_text_left_aligned)

        self.api_key_eye_btn = QPushButton("👁️")
        self.api_key_eye_btn.setFixedSize(30, 30)
        self.api_key_eye_btn.clicked.connect(self.toggle_api_key_visibility)
        self.api_key_eye_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                font-size: 16px;
                color: white;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)

        # 安全密钥输入框
        self.security_key_edit = QLineEdit()
        self.security_key_edit.setPlaceholderText("可选：安全密钥")
        self.security_key_edit.setFixedHeight(30)  # 直接设置固定高度
        self.security_key_edit.setEchoMode(QLineEdit.Normal)  # 初始为Normal模式显示placeholder
        self.security_key_edit.setAlignment(Qt.AlignLeft)  # 确保文本左对齐
        # 设置较小的字体以显示更多内容
        self.security_key_edit.setStyleSheet("""
            QLineEdit {
                padding: 4px 8px 4px 8px;
                border: none;
                border-radius: 3px;
                background-color: rgba(255, 255, 255, 0.9);
                font-size: 11px;
                color: #333333;
                height: 30px;
            }
            QLineEdit:focus {
                background-color: white;
            }
        """)
        # 设置文本边距，为右侧的眼睛按钮留出空间
        self.security_key_edit.setTextMargins(0, 2, 0, 2)  # 减小上下边距以防止提示语被截断

        self.security_key_eye_btn = QPushButton("👁️")
        self.security_key_eye_btn.setFixedSize(30, 30)
        self.security_key_eye_btn.clicked.connect(self.toggle_security_key_visibility)
        self.security_key_eye_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                font-size: 16px;
                color: white;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)

        # 配置状态标签
        self.status_label = QLabel("未选择")
        self.status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setMinimumHeight(30)
        self.status_label.setMaximumHeight(30)
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 4px 8px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 12px;
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                min-height: 30px;
                max-height: 30px;
                height: 30px;
            }
        """)

        # 创建状态标签容器，模拟API Key输入框的布局
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.addWidget(self.status_label)

        # 添加一个占位按钮，使容器宽度与API Key输入框一致
        status_placeholder_btn = QPushButton()
        status_placeholder_btn.setFixedSize(30, 30)
        status_placeholder_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
            }
        """)
        status_placeholder_btn.setEnabled(False)
        status_layout.addWidget(status_placeholder_btn)

        status_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # 配置表单
        config_layout = QVBoxLayout()
        config_layout.setSpacing(-1)  # 设置为-1表示尽可能小的间距
        config_layout.setContentsMargins(0, 0, 0, 0)  # 清除布局的外边距

        # 地图数据源行
        source_row = QHBoxLayout()
        source_label = QLabel("地图数据源:")
        source_label.setStyleSheet("font-weight: bold; font-size: 12px; color: white; font-family: 'Microsoft YaHei'; margin: 0px; padding: 0px;")
        source_label.setFixedWidth(80)
        source_label.setFixedHeight(30)  # 设置标签固定高度
        source_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        source_row.addWidget(source_label)
        source_row.addSpacing(10)
        source_row.addWidget(combo_container)
        source_row.setContentsMargins(0, 0, 0, 0)  # 清除行布局的边距
        source_row.setSpacing(0)  # 清除行内间距
        source_row.setStretch(0, 0)  # 确保标签不拉伸
        source_row.setStretch(1, 0)  # 确保间距不拉伸
        source_row.setStretch(2, 1)  # 确保容器拉伸
        config_layout.addLayout(source_row)

        # API Key行
        api_key_row = QHBoxLayout()
        api_key_label = QLabel("API Key:")
        api_key_label.setStyleSheet("font-weight: bold; font-size: 12px; color: white; font-family: 'Microsoft YaHei'; margin: 0px; padding: 0px;")
        api_key_label.setFixedWidth(80)
        api_key_label.setFixedHeight(30)  # 设置标签固定高度
        api_key_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        api_key_row.addWidget(api_key_label)
        api_key_row.addSpacing(10)

        # API Key输入框容器
        api_key_container = QWidget()
        api_key_container.setFixedHeight(30)  # 设置容器固定高度
        api_key_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 设置容器宽度策略
        api_key_layout = QHBoxLayout(api_key_container)
        api_key_layout.setContentsMargins(0, 0, 0, 0)
        # 确保输入框占据所有可用空间
        self.api_key_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        api_key_layout.addWidget(self.api_key_edit)
        api_key_layout.addWidget(self.api_key_eye_btn)
        api_key_row.addWidget(api_key_container)
        api_key_row.setContentsMargins(0, 0, 0, 0)  # 清除行布局的边距
        api_key_row.setSpacing(0)  # 清除行内间距
        api_key_row.setStretch(0, 0)  # 确保标签不拉伸
        api_key_row.setStretch(1, 0)  # 确保间距不拉伸
        api_key_row.setStretch(2, 1)  # 确保容器拉伸
        config_layout.addLayout(api_key_row)

        # 安全密钥行
        security_key_row = QHBoxLayout()
        security_key_label = QLabel("安全密钥:")
        security_key_label.setStyleSheet("font-weight: bold; font-size: 12px; color: white; font-family: 'Microsoft YaHei'; margin: 0px; padding: 0px;")
        security_key_label.setFixedWidth(80)
        security_key_label.setFixedHeight(30)  # 设置标签固定高度
        security_key_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        security_key_row.addWidget(security_key_label)
        security_key_row.addSpacing(10)

        # 安全密钥输入框容器
        security_key_container = QWidget()
        security_key_container.setFixedHeight(30)  # 设置容器固定高度
        security_key_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 设置容器宽度策略
        security_key_layout = QHBoxLayout(security_key_container)
        security_key_layout.setContentsMargins(0, 0, 0, 0)
        # 确保输入框占据所有可用空间
        self.security_key_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        security_key_layout.addWidget(self.security_key_edit)
        security_key_layout.addWidget(self.security_key_eye_btn)
        security_key_row.addWidget(security_key_container)
        security_key_row.setContentsMargins(0, 0, 0, 0)  # 清除行布局的边距
        security_key_row.setSpacing(0)  # 清除行内间距
        security_key_row.setStretch(0, 0)  # 确保标签不拉伸
        security_key_row.setStretch(1, 0)  # 确保间距不拉伸
        security_key_row.setStretch(2, 1)  # 确保容器拉伸
        config_layout.addLayout(security_key_row)

        # 配置状态行
        status_row = QHBoxLayout()
        status_label = QLabel("配置状态:")
        status_label.setStyleSheet("font-weight: bold; font-size: 12px; color: white; font-family: 'Microsoft YaHei'; margin: 0px; padding: 0px;")
        status_label.setFixedWidth(80)
        status_label.setFixedHeight(30)  # 设置标签固定高度
        status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        status_row.addWidget(status_label)
        status_row.addSpacing(10)
        status_row.addWidget(status_container)
        status_row.setContentsMargins(0, 0, 0, 0)  # 清除行布局的边距
        status_row.setSpacing(0)  # 清除行内间距
        config_layout.addLayout(status_row)

        main_layout.addLayout(config_layout)

        # 添加分隔线，美化布局并增加与底部按钮的间距
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: rgba(255, 255, 255, 0.2); margin: 20px 0;")  # 进一步增加分隔线的上下边距到20px
        main_layout.addWidget(separator)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch(1)

        self.test_btn = QPushButton("测试连接")
        self.test_btn.clicked.connect(self.test_connection)
        self.test_btn.setMinimumWidth(80)
        self.test_btn.setMinimumHeight(30)
        self.test_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 12px;
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
            QPushButton:disabled {
                background-color: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.6);
            }
        """)
        btn_layout.addWidget(self.test_btn)

        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.save_config)
        self.save_btn.setMinimumWidth(80)
        self.save_btn.setMinimumHeight(30)
        self.save_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 12px;
                background-color: rgba(255, 255, 255, 0.3);
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.4);
            }
        """)
        btn_layout.addWidget(self.save_btn)

        self.clear_btn = QPushButton("清除配置")
        self.clear_btn.clicked.connect(self.clear_config)
        self.clear_btn.setMinimumWidth(80)
        self.clear_btn.setMinimumHeight(30)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 12px;
                background-color: rgba(255, 0, 0, 0.3);
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 0.4);
            }
        """)
        btn_layout.addWidget(self.clear_btn)

        btn_layout.addStretch(1)

        main_layout.addLayout(btn_layout)
        # 删除底部的addStretch()，避免底部空白

    def ensure_text_left_aligned(self, text):
        """确保文本始终从左侧开始显示"""
        self.api_key_edit.home(False)  # 移动光标到文本开头，不选择任何内容

    def on_map_source_changed(self, index):
        """地图数据源选择变化时的处理"""
        if index == 0:  # 无
            self.api_key_edit.setEnabled(False)
            self.api_key_eye_btn.setEnabled(False)
            self.security_key_edit.setEnabled(False)
            self.security_key_eye_btn.setEnabled(False)
            self.test_btn.setEnabled(False)
            self.status_label.setText("未选择")
            self.status_label.setStyleSheet("""
                QLabel {
                    padding: 4px 8px;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 12px;
                    background-color: rgba(255, 255, 255, 0.1);
                    color: white;
                }
            """)
        elif index == 2:  # 高德地图
            self.api_key_edit.setEnabled(True)
            self.api_key_eye_btn.setEnabled(True)
            self.security_key_edit.setEnabled(True)
            self.security_key_eye_btn.setEnabled(True)
            self.test_btn.setEnabled(True)
            if map_config.is_gaode_configured():
                self.status_label.setText("已配置")
                self.status_label.setStyleSheet("""
                    QLabel {
                    padding: 4px 8px;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 12px;
                    background-color: rgba(76, 175, 80, 0.3);
                    color: white;
                }
                """)
            else:
                self.status_label.setText("未配置")
                self.status_label.setStyleSheet("""
                    QLabel {
                    padding: 4px 8px;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 12px;
                    background-color: rgba(255, 87, 34, 0.3);
                    color: white;
                }
                """)
        else:  # OpenStreetMap
            self.api_key_edit.setEnabled(False)
            self.api_key_eye_btn.setEnabled(False)
            self.security_key_edit.setEnabled(False)
            self.security_key_eye_btn.setEnabled(False)
            self.test_btn.setEnabled(False)
            self.status_label.setText("无需配置")
            self.status_label.setStyleSheet("""
                QLabel {
                    padding: 4px 8px;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 12px;
                    background-color: rgba(255, 255, 255, 0.2);
                    color: white;
                }
            """)

    def load_current_config(self):
        """加载当前配置"""
        map_source = map_config.get_map_source()
        if not map_source:
            self.map_source_combo.setCurrentIndex(0)
        elif map_source == "gaode":
            self.map_source_combo.setCurrentIndex(2)
        else:
            self.map_source_combo.setCurrentIndex(1)

        self.api_key_edit.setText(map_config.get_api_key())
        self.security_key_edit.setText(map_config.get_security_key())
        self.on_map_source_changed(self.map_source_combo.currentIndex())

    def test_connection(self):
        """测试连接"""
        api_key = self.api_key_edit.text().strip()
        if not api_key:
            QMessageBox.warning(self, "警告", "请先输入API Key")
            return

        from services.gaode.gaode_geocoding import GaodeGeocodingService
        service = GaodeGeocodingService(api_key=api_key)
        result = service.search_location("北京市")

        if result:
            QMessageBox.information(self, "成功", f"连接测试成功！\n找到 {len(result)} 个结果")
        else:
            QMessageBox.warning(self, "失败", "连接测试失败，请检查API Key是否正确")

    def save_config(self):
        """保存配置"""
        current_index = self.map_source_combo.currentIndex()
        if current_index == 0:
            map_source = ""
        elif current_index == 2:
            map_source = "gaode"
        else:
            map_source = "osm"

        api_key = self.api_key_edit.text().strip()
        security_key = self.security_key_edit.text().strip()

        if map_source == "gaode" and not api_key:
            QMessageBox.warning(self, "警告", "选择高德地图时，API Key不能为空")
            return

        config = {
            "map_source": map_source,
            "api_key": api_key,
            "security_key": security_key
        }

        if map_config.save_config(config):
            self.on_map_source_changed(current_index)
            # 发送配置保存信号，通知主窗口重新加载地图
            self.config_saved.emit()
            QMessageBox.information(self, "成功", "配置已保存，地图将重新加载")
        else:
            QMessageBox.critical(self, "错误", "保存配置失败")

    def clear_config(self):
        """清除配置"""
        reply = QMessageBox.question(self, "确认", "确定要清除配置吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if map_config.clear_config():
                self.api_key_edit.clear()
                self.security_key_edit.clear()
                self.map_source_combo.setCurrentIndex(0)
                self.on_map_source_changed(0)
                QMessageBox.information(self, "成功", "配置已清除")

    def toggle_api_key_visibility(self):
        """切换API Key的可见性"""
        if self.api_key_edit.echoMode() == QLineEdit.Password:
            self.api_key_edit.setEchoMode(QLineEdit.Normal)
            self.api_key_eye_btn.setText("👁️‍🗨️")
        else:
            self.api_key_edit.setEchoMode(QLineEdit.Password)
            self.api_key_eye_btn.setText("👁️")

    def toggle_security_key_visibility(self):
        """切换安全密钥的可见性"""
        if self.security_key_edit.echoMode() == QLineEdit.Normal:
            self.security_key_edit.setEchoMode(QLineEdit.Password)
            self.security_key_eye_btn.setText("👁️")
        else:
            self.security_key_edit.setEchoMode(QLineEdit.Normal)
            self.security_key_eye_btn.setText("👁️‍🗨️")

    def hide(self):
        """隐藏弹出面板并发出关闭信号"""
        super().hide()
        self.closed.emit()



class LogSettingsPopup(BaseSettingsPopup):
    """日志设置弹出面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(300, 240)  # 与地图设置面板保持一致
        self._init_ui()
        self.load_current_config()

    def show_popup(self, button_widget):
        """
        显示弹出面板

        Args:
            button_widget: 触发按钮控件（用于定位）
        """
        # 获取按钮的全局位置
        button_rect = button_widget.rect()
        button_global_pos = button_widget.mapToGlobal(button_rect.topLeft())

        # 获取按钮列表容器的位置（假设按钮是right_buttons_container的子元素）
        if hasattr(button_widget.parent(), 'rect'):
            buttons_container = button_widget.parent()
            container_rect = buttons_container.rect()
            container_global_pos = buttons_container.mapToGlobal(container_rect.topLeft())

            # 设置面板位置：与按钮顶部对齐，面板右侧与按钮列表左侧间隔1-2px
            popup_x = container_global_pos.x() - self.width() - 2
            popup_y = button_global_pos.y()
        else:
            #  fallback: 使用默认位置
            popup_x = button_global_pos.x() - self.width() - 10
            popup_y = button_global_pos.y()

        self.move(popup_x, popup_y)
        self.show()
        self.raise_()
        self.setFocus()  # 设置焦点以接收键盘事件

    def _init_ui(self):
        """初始化UI"""
        # 设置面板样式 - 与地图设置面板保持一致
        self.setStyleSheet("""
            LogSettingsPopup {
                background-color: #4A90E2;
                border-radius: 6px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QLabel {
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QPushButton {
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QComboBox {
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
        """)

        # 设置自动填充背景
        self.setAutoFillBackground(True)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(2)

        # 标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel("日志设置")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: bold;
                color: white;
                font-family: 'Microsoft YaHei';
            }
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        # 关闭按钮
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 14px;
                color: white;
                border-radius: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        close_btn.clicked.connect(self.hide)
        title_layout.addWidget(close_btn)

        main_layout.addLayout(title_layout)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: rgba(255, 255, 255, 0.2); margin: 5px 0;")
        main_layout.addWidget(line)

        # 配置表单
        config_layout = QVBoxLayout()
        config_layout.setSpacing(-1)
        config_layout.setContentsMargins(0, 0, 0, 0)

        # 日志级别设置
        log_level_row = QHBoxLayout()
        log_level_label = QLabel("日志级别:")
        log_level_label.setStyleSheet("font-weight: bold; font-size: 12px; color: white; font-family: 'Microsoft YaHei'; margin: 0px; padding: 0px;")
        log_level_label.setFixedWidth(80)
        log_level_label.setFixedHeight(30)
        log_level_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        log_level_row.addWidget(log_level_label)
        log_level_row.addSpacing(10)

        # 创建下拉框容器
        log_level_container = QWidget()
        log_level_layout = QHBoxLayout(log_level_container)
        log_level_layout.setContentsMargins(0, 0, 0, 0)

        self.log_level_combo = QComboBox()
        self.log_level_combo.addItem("DEBUG", "DEBUG")
        self.log_level_combo.addItem("INFO", "INFO")
        self.log_level_combo.addItem("WARNING", "WARNING")
        self.log_level_combo.addItem("ERROR", "ERROR")
        self.log_level_combo.addItem("CRITICAL", "CRITICAL")
        self.log_level_combo.setFixedHeight(30)
        self.log_level_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.log_level_combo.setStyleSheet("""
            QComboBox {
                padding: 0px 30px 0px 8px;
                border: 0px;
                border-radius: 3px;
                background-color: rgba(255, 255, 255, 0.9);
                font-size: 12px;
                color: #333333;
                min-height: 30px;
                max-height: 30px;
                height: 30px;
            }
            QComboBox:focus {
                background-color: white;
            }
            QComboBox QAbstractItemView {
                border: 1px solid rgba(0, 0, 0, 0.2);
                border-radius: 3px;
                background-color: white;
                selection-background-color: #4A90E2;
                selection-color: white;
                font-size: 12px;
            }
        """)
        # 连接信号实现自动保存
        self.log_level_combo.currentIndexChanged.connect(self.on_log_level_changed)
        log_level_layout.addWidget(self.log_level_combo)
        log_level_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        log_level_row.addWidget(log_level_container)
        log_level_row.setContentsMargins(0, 0, 0, 0)
        log_level_row.setSpacing(0)
        log_level_row.setStretch(0, 0)
        log_level_row.setStretch(1, 0)
        log_level_row.setStretch(2, 1)
        config_layout.addLayout(log_level_row)

        main_layout.addLayout(config_layout)

        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: rgba(255, 255, 255, 0.2); margin: 20px 0;")
        main_layout.addWidget(separator)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch(1)

        self.clean_log_btn = QPushButton("清理日志")
        self.clean_log_btn.clicked.connect(self.on_clean_logs)
        self.clean_log_btn.setMinimumWidth(80)
        self.clean_log_btn.setMinimumHeight(30)
        self.clean_log_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 12px;
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        btn_layout.addWidget(self.clean_log_btn)

        self.open_log_btn = QPushButton("打开日志目录")
        self.open_log_btn.clicked.connect(self.on_open_log_directory)
        self.open_log_btn.setMinimumWidth(80)
        self.open_log_btn.setMinimumHeight(30)
        self.open_log_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 12px;
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        btn_layout.addWidget(self.open_log_btn)

        btn_layout.addStretch(1)
        main_layout.addLayout(btn_layout)

        # 日志大小信息
        log_size = get_log_size()
        self.log_size_label = QLabel(f"当前日志大小: {log_size:.2f} MB")
        self.log_size_label.setAlignment(Qt.AlignCenter)
        self.log_size_label.setStyleSheet("""
            QLabel {
                padding: 2px;
                margin-top: 4px;
                font-weight: bold;
                font-size: 12px;
                color: white;
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 3px;
            }
        """)
        main_layout.addWidget(self.log_size_label)

    def load_current_config(self):
        """加载当前配置"""
        log_level = map_config.get('log_level', 'INFO')
        # 临时断开信号，避免加载时触发保存
        self.log_level_combo.blockSignals(True)
        for i in range(self.log_level_combo.count()):
            if self.log_level_combo.itemData(i) == log_level:
                self.log_level_combo.setCurrentIndex(i)
                break
        self.log_level_combo.blockSignals(False)

    def on_log_level_changed(self, index):
        """日志级别改变时自动保存"""
        selected_level = self.log_level_combo.currentData()
        try:
            set_log_level(selected_level)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存日志级别失败: {str(e)}")

    def on_clean_logs(self):
        """清理日志"""
        reply = QMessageBox.question(self, "确认", "确定要清理所有运行日志吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if clean_logs():
                # 更新日志大小显示
                log_size = get_log_size()
                self.log_size_label.setText(f"当前日志大小: {log_size:.2f} MB")
                QMessageBox.information(self, "成功", "日志已清理")
            else:
                QMessageBox.critical(self, "错误", "清理日志失败")

    def on_open_log_directory(self):
        """打开日志目录"""
        if not open_log_directory():
            QMessageBox.critical(self, "错误", "打开日志目录失败")


class AboutPopup(BaseSettingsPopup):
    """关于弹出面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(400)  # 减少高度，删除底部空白
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # 标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel("关于")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 9pt;
                font-weight: bold;
                color: #333333;
            }
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        # 关闭按钮
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 18px;
                color: #666666;
            }
            QPushButton:hover {
                color: #333333;
                background-color: #f0f0f0;
                border-radius: 12px;
            }
        """)
        close_btn.clicked.connect(self.hide)
        title_layout.addWidget(close_btn)

        main_layout.addLayout(title_layout)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #e0e0e0;")
        main_layout.addWidget(line)

        # 关于内容
        about_label = QLabel()
        about_label.setTextFormat(Qt.RichText)
        about_label.setText(self._get_about_text())
        about_label.setWordWrap(True)
        about_label.setStyleSheet("padding: 10px;")
        main_layout.addWidget(about_label)

        # 删除底部的addStretch()，避免底部空白

    def _get_about_text(self):
        """获取关于内容的HTML"""
        log_size = get_log_size()
        log_warning = ""
        if log_size > 100:
            log_warning = "<div style='color: red; margin-top: 5px;'>⚠️ 运行日志超过100MB，请及时清理</div>"

        # 从配置中获取信息
        app_name = about_config.get_app_name()
        app_version = about_config.get_app_version()
        app_platform = about_config.get_app_platform()
        app_description = about_config.get_app_description()
        license_text = about_config.get_license_text()
        developer_team = about_config.get_developer_team()
        developer_email = about_config.get_developer_email()
        copyright_text = about_config.get_copyright_text()
        map_api_copyright = about_config.get_map_api_copyright()

        html = f"""
        <div style="font-family: 'Microsoft YaHei', Arial, sans-serif; color: #333; line-height: 1.6;">
            <h3 style="color: #4A90E2; text-align: center; margin-bottom: 15px;">{app_name}</h3>

            <div style="text-align: center; margin-bottom: 15px;">
                <div style="font-weight: bold; color: #666;">版本: {app_version} | 平台: {app_platform}</div>
                <div style="margin-top: 5px; color: #555;">{app_description}</div>
            </div>

            <div style="background-color: #e8f5e9; padding: 10px; border-radius: 4px; margin: 10px 0; text-align: center;">
                <div style="color: #2196F3; font-weight: bold;">{license_text}</div>
            </div>

            <div style="background-color: #f5f5f5; padding: 10px; border-radius: 4px; margin: 10px 0; text-align: center;">
                <div>开发者: {developer_team}</div>
                <div>邮箱: {developer_email}</div>
            </div>

            <div style="background-color: #f0f8ff; padding: 10px; border-radius: 4px; margin: 10px 0; text-align: center;">
                <div>运行日志大小: {log_size:.2f} MB</div>
                {log_warning}
            </div>

            <div style="text-align: center; color: #777; font-size: 11px; padding-top: 10px; border-top: 1px solid #e0e0e0; margin-top: 10px;">
                <div>{copyright_text}</div>
                <div>{map_api_copyright}</div>
            </div>
        </div>
        """

        return html


class RouteSettingsPopup(BaseSettingsPopup):
    """路线设置弹出面板"""

    config_saved = pyqtSignal()  # 配置保存信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(300, 240)  # 与地图设置面板保持一致
        self._init_ui()
        self.load_current_config()

    def show_popup(self, button_widget):
        """
        显示弹出面板

        Args:
            button_widget: 触发按钮控件（用于定位）
        """
        # 获取按钮的全局位置
        button_rect = button_widget.rect()
        button_global_pos = button_widget.mapToGlobal(button_rect.topLeft())

        # 获取按钮列表容器的位置（假设按钮是right_buttons_container的子元素）
        if hasattr(button_widget.parent(), 'rect'):
            buttons_container = button_widget.parent()
            container_rect = buttons_container.rect()
            container_global_pos = buttons_container.mapToGlobal(container_rect.topLeft())

            # 设置面板位置：与按钮顶部对齐，面板右侧与按钮列表左侧间隔1-2px
            popup_x = container_global_pos.x() - self.width() - 2
            popup_y = button_global_pos.y()
        else:
            #  fallback: 使用默认位置
            popup_x = button_global_pos.x() - self.width() - 10
            popup_y = button_global_pos.y()

        self.move(popup_x, popup_y)
        self.show()
        self.raise_()
        self.setFocus()  # 设置焦点以接收键盘事件

    def _init_ui(self):
        """初始化UI"""
        # 设置面板样式 - 与地图设置面板保持一致
        self.setStyleSheet("""
            RouteSettingsPopup {
                background-color: #4A90E2;
                border-radius: 6px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QLabel {
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QPushButton {
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QLineEdit {
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QComboBox {
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
        """)

        # 设置自动填充背景
        self.setAutoFillBackground(True)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(2)

        # 标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel("路线设置")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: bold;
                color: white;
                font-family: 'Microsoft YaHei';
            }
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        # 关闭按钮
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 14px;
                color: white;
                border-radius: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        close_btn.clicked.connect(self.hide)
        title_layout.addWidget(close_btn)

        main_layout.addLayout(title_layout)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: rgba(255, 255, 255, 0.2); margin: 5px 0;")
        main_layout.addWidget(line)

        # 配置表单
        config_layout = QVBoxLayout()
        config_layout.setSpacing(-1)  # 设置为-1表示尽可能小的间距
        config_layout.setContentsMargins(0, 0, 0, 0)  # 清除布局的外边距

        # 启用路线优化
        enable_row = QHBoxLayout()
        enable_label = QLabel("启用路线优化:")
        enable_label.setStyleSheet("font-weight: bold; font-size: 12px; color: white; font-family: 'Microsoft YaHei'; margin: 0px; padding: 0px;")
        enable_label.setFixedWidth(80)
        enable_label.setFixedHeight(30)
        enable_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        enable_row.addWidget(enable_label)
        enable_row.addSpacing(10)

        # 创建下拉框容器
        enable_container = QWidget()
        enable_layout = QHBoxLayout(enable_container)
        enable_layout.setContentsMargins(0, 0, 0, 0)

        self.enable_combo = QComboBox()
        self.enable_combo.addItem("启用", True)
        self.enable_combo.addItem("禁用", False)
        self.enable_combo.setFixedHeight(30)
        self.enable_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.enable_combo.setStyleSheet("""
            QComboBox {
                padding: 0px 30px 0px 8px;
                border: 0px;
                border-radius: 3px;
                background-color: rgba(255, 255, 255, 0.9);
                font-size: 12px;
                color: #333333;
                min-height: 30px;
                max-height: 30px;
                height: 30px;
            }
            QComboBox:focus {
                background-color: white;
            }
            QComboBox QAbstractItemView {
                border: 1px solid rgba(0, 0, 0, 0.2);
                border-radius: 3px;
                background-color: white;
                selection-background-color: #4A90E2;
                selection-color: white;
                font-size: 12px;
            }
        """)
        enable_layout.addWidget(self.enable_combo)
        enable_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        enable_row.addWidget(enable_container)
        enable_row.setContentsMargins(0, 0, 0, 0)
        enable_row.setSpacing(0)
        enable_row.setStretch(0, 0)
        enable_row.setStretch(1, 0)
        enable_row.setStretch(2, 1)
        config_layout.addLayout(enable_row)

        # 最大点数设置
        max_points_row = QHBoxLayout()
        max_points_label = QLabel("最大点数限制:")
        max_points_label.setStyleSheet("font-weight: bold; font-size: 12px; color: white; font-family: 'Microsoft YaHei'; margin: 0px; padding: 0px;")
        max_points_label.setFixedWidth(80)
        max_points_label.setFixedHeight(30)
        max_points_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        max_points_row.addWidget(max_points_label)
        max_points_row.addSpacing(10)

        # 创建输入框容器
        max_points_container = QWidget()
        max_points_container.setFixedHeight(30)
        max_points_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        max_points_layout = QHBoxLayout(max_points_container)
        max_points_layout.setContentsMargins(0, 0, 0, 0)

        self.max_points_edit = QLineEdit()
        self.max_points_edit.setPlaceholderText("例如: 500")
        self.max_points_edit.setFixedHeight(30)
        self.max_points_edit.setAlignment(Qt.AlignLeft)
        self.max_points_edit.setStyleSheet("""
            QLineEdit {
                padding: 4px 8px 4px 8px;
                border: none;
                border-radius: 3px;
                background-color: rgba(255, 255, 255, 0.9);
                font-size: 11px;
                color: #333333;
                height: 30px;
            }
            QLineEdit:focus {
                background-color: white;
            }
        """)
        self.max_points_edit.setTextMargins(0, 2, 0, 2)
        self.max_points_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        max_points_layout.addWidget(self.max_points_edit)

        max_points_row.addWidget(max_points_container)
        max_points_row.setContentsMargins(0, 0, 0, 0)
        max_points_row.setSpacing(0)
        max_points_row.setStretch(0, 0)
        max_points_row.setStretch(1, 0)
        max_points_row.setStretch(2, 1)
        config_layout.addLayout(max_points_row)

        # 自动缩放计算
        auto_zoom_row = QHBoxLayout()
        auto_zoom_label = QLabel("自动缩放计算:")
        auto_zoom_label.setStyleSheet("font-weight: bold; font-size: 12px; color: white; font-family: 'Microsoft YaHei'; margin: 0px; padding: 0px;")
        auto_zoom_label.setFixedWidth(80)
        auto_zoom_label.setFixedHeight(30)
        auto_zoom_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        auto_zoom_row.addWidget(auto_zoom_label)
        auto_zoom_row.addSpacing(10)

        # 创建下拉框容器
        auto_zoom_container = QWidget()
        auto_zoom_layout = QHBoxLayout(auto_zoom_container)
        auto_zoom_layout.setContentsMargins(0, 0, 0, 0)

        self.auto_zoom_combo = QComboBox()
        self.auto_zoom_combo.addItem("启用", True)
        self.auto_zoom_combo.addItem("禁用", False)
        self.auto_zoom_combo.setFixedHeight(30)
        self.auto_zoom_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.auto_zoom_combo.setStyleSheet("""
            QComboBox {
                padding: 0px 30px 0px 8px;
                border: 0px;
                border-radius: 3px;
                background-color: rgba(255, 255, 255, 0.9);
                font-size: 12px;
                color: #333333;
                min-height: 30px;
                max-height: 30px;
                height: 30px;
            }
            QComboBox:focus {
                background-color: white;
            }
            QComboBox QAbstractItemView {
                border: 1px solid rgba(0, 0, 0, 0.2);
                border-radius: 3px;
                background-color: white;
                selection-background-color: #4A90E2;
                selection-color: white;
                font-size: 12px;
            }
        """)
        auto_zoom_layout.addWidget(self.auto_zoom_combo)
        auto_zoom_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        auto_zoom_row.addWidget(auto_zoom_container)
        auto_zoom_row.setContentsMargins(0, 0, 0, 0)
        auto_zoom_row.setSpacing(0)
        auto_zoom_row.setStretch(0, 0)
        auto_zoom_row.setStretch(1, 0)
        auto_zoom_row.setStretch(2, 1)
        config_layout.addLayout(auto_zoom_row)

        main_layout.addLayout(config_layout)

        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: rgba(255, 255, 255, 0.2); margin: 20px 0;")
        main_layout.addWidget(separator)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch(1)

        self.reset_btn = QPushButton("重置默认")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        self.reset_btn.setMinimumWidth(80)
        self.reset_btn.setMinimumHeight(30)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 12px;
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        btn_layout.addWidget(self.reset_btn)

        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.save_config)
        self.save_btn.setMinimumWidth(80)
        self.save_btn.setMinimumHeight(30)
        self.save_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 12px;
                background-color: rgba(255, 255, 255, 0.3);
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.4);
            }
        """)
        btn_layout.addWidget(self.save_btn)

        btn_layout.addStretch(1)
        main_layout.addLayout(btn_layout)

    def load_current_config(self):
        """加载当前配置"""
        # 启用状态
        enabled = map_config.is_route_optimization_enabled()
        self.enable_combo.setCurrentIndex(0 if enabled else 1)

        # 最大点数
        max_points = map_config.get_max_points_per_segment()
        self.max_points_edit.setText(str(max_points))

        # 自动缩放计算
        auto_zoom = map_config.is_auto_zoom_calculation_enabled()
        self.auto_zoom_combo.setCurrentIndex(0 if auto_zoom else 1)

    def reset_to_defaults(self):
        """重置为默认值"""
        self.enable_combo.setCurrentIndex(0)  # 启用
        self.max_points_edit.setText("500")   # 默认500点
        self.auto_zoom_combo.setCurrentIndex(0)  # 启用

    def save_config(self):
        """保存配置"""
        try:
            # 获取配置值
            enabled = self.enable_combo.currentData()
            max_points_text = self.max_points_edit.text().strip()
            auto_zoom = self.auto_zoom_combo.currentData()

            # 验证最大点数
            if not max_points_text:
                QMessageBox.warning(self, "警告", "请输入最大点数限制")
                return

            try:
                max_points = int(max_points_text)
                if max_points <= 0:
                    QMessageBox.warning(self, "警告", "最大点数必须大于0")
                    return
            except ValueError:
                QMessageBox.warning(self, "警告", "最大点数必须是有效的数字")
                return

            # 保存配置
            success = True
            success &= map_config.set_route_optimization_enabled(enabled)
            success &= map_config.set_max_points_per_segment(max_points)

            # 保存自动缩放设置（需要添加到map_config中）
            if 'route_optimization' not in map_config._config_data:
                map_config._config_data['route_optimization'] = {}
            map_config._config_data['route_optimization']['auto_zoom_calculation'] = auto_zoom
            success &= map_config.save_config(map_config._config_data)

            if success:
                self.config_saved.emit()
                QMessageBox.information(self, "成功", "路线设置已保存")
                self.hide()
            else:
                QMessageBox.critical(self, "错误", "保存配置失败")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置时发生错误: {str(e)}")

    def hide(self):
        """隐藏弹出面板并发出关闭信号"""
        super().hide()
        self.closed.emit()

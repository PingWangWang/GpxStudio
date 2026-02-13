"""
设置弹出面板组件

包含地图设置、日志设置和关于信息的弹出面板
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QPushButton, QLabel, QMessageBox,
                             QTabWidget, QTextEdit, QComboBox, QFrame, QSizePolicy)

class CustomMessageBox(QWidget):
    """自定义消息提示框"""

    def __init__(self, parent=None, title="", message="", button_text="确定"):
        super().__init__(parent)

        # 设置窗口标志
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        # 设置样式
        self.setStyleSheet("""
            CustomMessageBox {
                background-color: #3b4453;
                border-radius: 8px;
                font-family: 'Microsoft YaHei';
            }
            QLabel {
                color: white;
                font-family: 'Microsoft YaHei';
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.9);
                color: #4A90E2;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
                padding: 8px 20px;
                font-family: 'Microsoft YaHei';
            }
            QPushButton:hover {
                background-color: white;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.8);
            }
        """)

        # 初始化UI
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 标题
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: white;
            }
        """)
        main_layout.addWidget(title_label)

        # 消息内容
        message_label = QLabel(message)
        message_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: rgba(255, 255, 255, 0.9);
                line-height: 1.4;
            }
        """)
        message_label.setWordWrap(True)
        main_layout.addWidget(message_label)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        ok_button = QPushButton(button_text)
        ok_button.clicked.connect(self.close)
        button_layout.addWidget(ok_button)

        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        # 调整大小
        self.adjustSize()

    def show_message(self):
        """显示消息框"""
        # 计算位置（居中显示）
        if self.parent():
            parent_rect = self.parent().rect()
            parent_pos = self.parent().mapToGlobal(parent_rect.topLeft())
            x = parent_pos.x() + (parent_rect.width() - self.width()) // 2
            y = parent_pos.y() + (parent_rect.height() - self.height()) // 2
        else:
            # 屏幕居中
            screen = QApplication.primaryScreen()
            screen_geometry = screen.geometry()
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2

        self.move(x, y)
        self.show()
        self.raise_()

# 导入QApplication（如果还没有导入）
try:
    from PyQt5.QtWidgets import QApplication
except ImportError:
    pass
from PyQt5.QtCore import Qt, pyqtSignal, QEvent
from PyQt5.QtGui import QIcon, QKeyEvent, QPainter, QPen, QBrush, QPolygon
from PyQt5.QtCore import QPoint
from services.config.map_config import map_config
from core.logging_setup import clean_logs, open_log_directory, get_log_size, set_log_level
from services.config import about_config
import os
from app.data_paths import get_geo_info_file, get_route_history_file, get_cache_dir, get_gaode_cache_dir, get_osm_cache_dir


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
                background-color: #3b4453;
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
        self.setFixedSize(300, 250)  # 减少高度
        # 保存用户输入的API Key和安全密钥
        self.saved_api_key = ""
        self.saved_security_key = ""
        # 测试连接状态
        self.connection_tested = False
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
                background-color: #3b4453;
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
                selection-background-color: #3b4453;
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
        # API Key变更时，重置测试连接状态
        self.api_key_edit.textChanged.connect(self._on_api_key_changed)

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



        # 关闭动作选择
        self.close_action_combo = QComboBox()
        self.close_action_combo.addItem("直接退出程序", "exit")
        self.close_action_combo.addItem("最小化到系统托盘", "hide")
        self.close_action_combo.setFixedHeight(30)
        self.close_action_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.close_action_combo.setStyleSheet(self.map_source_combo.styleSheet())
        
        # 创建关闭动作容器（为了保持布局一致性）
        close_action_container = QWidget()
        close_action_layout = QHBoxLayout(close_action_container)
        close_action_layout.setContentsMargins(0, 0, 0, 0)
        close_action_layout.addWidget(self.close_action_combo)
        
        # 添加占位按钮保持对齐
        close_action_placeholder = QPushButton()
        close_action_placeholder.setFixedSize(30, 30)
        close_action_placeholder.setStyleSheet("QPushButton { border: none; background-color: transparent; }")
        close_action_placeholder.setEnabled(False)
        close_action_layout.addWidget(close_action_placeholder)
        close_action_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # 关闭动作行
        close_action_row = QHBoxLayout()
        close_action_label = QLabel("关闭时:")
        close_action_label.setStyleSheet("font-weight: bold; font-size: 12px; color: white; font-family: 'Microsoft YaHei'; margin: 0px; padding: 0px;")
        close_action_label.setFixedWidth(80)
        close_action_label.setFixedHeight(30)
        close_action_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        close_action_row.addWidget(close_action_label)
        close_action_row.addSpacing(10)
        close_action_row.addWidget(close_action_container)
        close_action_row.setContentsMargins(0, 0, 0, 0)
        close_action_row.setSpacing(0)
        close_action_row.setStretch(0, 0)
        close_action_row.setStretch(1, 0)
        close_action_row.setStretch(2, 1)

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

        # 安全密钥行 (当前版本暂不支持，隐藏)
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
        # config_layout.addLayout(security_key_row)



        # 分隔线
        line_close = QFrame()
        line_close.setFrameShape(QFrame.HLine)
        line_close.setStyleSheet("background-color: rgba(255, 255, 255, 0.2); margin: 2px 0;")
        config_layout.addWidget(line_close)
        
        # 添加关闭动作行
        config_layout.addLayout(close_action_row)

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
            QPushButton:disabled {
                background-color: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.5);
            }
        """)
        btn_layout.addWidget(self.save_btn)

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
            self.save_btn.setEnabled(True)  # 无地图时保存按钮可用

        elif index == 2:  # 高德地图
            self.api_key_edit.setEnabled(True)
            self.api_key_eye_btn.setEnabled(True)
            self.security_key_edit.setEnabled(True)
            self.security_key_eye_btn.setEnabled(True)
            self.save_btn.setEnabled(True)  # 切换到高德地图时，保存按钮保持可用
            # 恢复占位符文本
            self.api_key_edit.setPlaceholderText("请输入高德地图API Key")
            self.security_key_edit.setPlaceholderText("可选：安全密钥")
            # 从配置中加载高德地图的API Key和安全密钥
            # 重新加载配置，确保获取最新的高德地图配置
            map_config._load_config()
            # 直接从配置数据中获取高德地图的API Key和安全密钥，不依赖get_api_key方法
            gaode_api_key = map_config._config_data.get('gaode', {}).get('api_key', '')
            gaode_security_key = map_config._config_data.get('gaode', {}).get('security_key', '')
            self.api_key_edit.setText(gaode_api_key)
            self.security_key_edit.setText(gaode_security_key)
            # 保存到实例变量中
            self.saved_api_key = gaode_api_key
            self.saved_security_key = gaode_security_key

        else:  # OpenStreetMap
            # 保存当前的API Key和安全密钥
            self.saved_api_key = self.api_key_edit.text().strip()
            self.saved_security_key = self.security_key_edit.text().strip()
            self.api_key_edit.setEnabled(False)
            self.api_key_eye_btn.setEnabled(False)
            self.security_key_edit.setEnabled(False)
            self.security_key_eye_btn.setEnabled(False)
            self.save_btn.setEnabled(True)  # OpenStreetMap时保存按钮可用
            # 清空编辑框内容
            self.api_key_edit.clear()
            self.security_key_edit.clear()
            # 更新占位符文本
            self.api_key_edit.setPlaceholderText("无需配置API Key")
            self.security_key_edit.setPlaceholderText("无需配置安全密钥")

    def load_current_config(self):
        """加载当前配置"""
        map_source = map_config.get_map_source()
        
        # 加载关闭动作配置
        close_action = map_config.get_close_action()
        index = self.close_action_combo.findData(close_action)
        if index >= 0:
            self.close_action_combo.setCurrentIndex(index)
        else:
            self.close_action_combo.setCurrentIndex(0) # 默认直接退出

        if not map_source:
            self.map_source_combo.setCurrentIndex(0)
        elif map_source == "gaode":
            self.map_source_combo.setCurrentIndex(2)
        else:
            self.map_source_combo.setCurrentIndex(1)

        # 加载并保存API Key和安全密钥
        api_key = map_config.get_api_key()
        security_key = map_config.get_security_key()
        self.api_key_edit.setText(api_key)
        self.security_key_edit.setText(security_key)
        # 保存到实例变量中
        self.saved_api_key = api_key
        self.saved_security_key = security_key
        self.on_map_source_changed(self.map_source_combo.currentIndex())


    def save_config(self):
        """保存配置"""
        current_index = self.map_source_combo.currentIndex()
        if current_index == 0:
            map_source = ""
        elif current_index == 2:
            map_source = "gaode"
        else:
            map_source = "osm"
            
        # 获取关闭动作
        close_action = self.close_action_combo.currentData()
        print(f"[MapSettings] 保存配置 - 关闭动作: {close_action}")

        # 获取API Key和安全密钥
        if map_source == "osm":
            # 对于OSM地图，不需要API Key，使用空字符串
            api_key = ""
            security_key = ""
        else:
            # 对于其他地图源，使用当前编辑框的值
            api_key = self.api_key_edit.text().strip()
            security_key = self.security_key_edit.text().strip()

        if map_source == "gaode" and not api_key:
            # 使用自定义消息提示框
            msg_box = CustomMessageBox(self, "警告", "选择高德地图时，API Key不能为空")
            msg_box.show_message()
            return

        config = {
            "map_source": map_source,
            "close_action": close_action,
            "api_key": api_key,
            "security_key": security_key
        }

        if map_config.save_config(config):
            self.on_map_source_changed(current_index)
            # 发送配置保存信号，通知主窗口重新加载地图
            self.config_saved.emit()
            # 使用自定义消息提示框
            msg_box = CustomMessageBox(self, "成功", "配置已保存，地图将重新加载")
            msg_box.show_message()
        else:
            # 使用自定义消息提示框
            msg_box = CustomMessageBox(self, "错误", "保存配置失败")
            msg_box.show_message()


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

    def _on_api_key_changed(self, text):
        """API Key变更时的处理"""
        pass

    def hide(self):
        """隐藏弹出面板并发出关闭信号"""
        super().hide()
        self.closed.emit()



class LogSettingsPopup(BaseSettingsPopup):
    """日志设置弹出面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(300, 250)
        self._init_ui()
        self.load_current_config()

    def get_file_size(self, file_path):
        """获取文件大小（MB）"""
        if os.path.exists(file_path):
            return os.path.getsize(file_path) / (1024 * 1024)
        return 0.0
    
    def get_directory_size(self, directory):
        """获取目录大小（MB）"""
        total_size = 0
        if os.path.exists(directory):
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        return total_size / (1024 * 1024)

    def show_popup(self, button_widget):
        """
        显示弹出面板

        Args:
            button_widget: 触发按钮控件（用于定位）
        """
        button_rect = button_widget.rect()
        button_global_pos = button_widget.mapToGlobal(button_rect.topLeft())

        if hasattr(button_widget.parent(), 'rect'):
            buttons_container = button_widget.parent()
            container_rect = buttons_container.rect()
            container_global_pos = buttons_container.mapToGlobal(container_rect.topLeft())

            popup_x = container_global_pos.x() - self.width() - 2
            popup_y = button_global_pos.y()
        else:
            popup_x = button_global_pos.x() - self.width() - 10
            popup_y = button_global_pos.y()

        self.move(popup_x, popup_y)
        self.show()
        self.raise_()
        self.setFocus()

    def _init_ui(self):
        """初始化UI"""
        self.setStyleSheet("""
            LogSettingsPopup {
                background-color: #3b4453;
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

        self.setAutoFillBackground(True)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

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

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: rgba(255, 255, 255, 0.2);")
        main_layout.addWidget(line)

        content_layout = QVBoxLayout()
        content_layout.setSpacing(6)
        content_layout.setContentsMargins(0, 0, 0, 0)

        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(6)

        log_size_text = QLineEdit()
        log_size_text.setReadOnly(True)
        log_size_text.setFixedHeight(30)
        log_size_text.setPlaceholderText("日志级别")
        log_size_text.setStyleSheet("""
            QLineEdit {
                padding: 0px 8px;
                border: none;
                border-radius: 3px;
                background-color: rgba(255, 255, 255, 0.9);
                font-size: 12px;
                color: #666666;
                min-height: 30px;
                max-height: 30px;
            }
        """)
        row1_layout.addWidget(log_size_text, 2)

        self.log_level_combo = QComboBox()
        self.log_level_combo.addItem("DEBUG", "DEBUG")
        self.log_level_combo.addItem("INFO", "INFO")
        self.log_level_combo.addItem("WARNING", "WARNING")
        self.log_level_combo.addItem("ERROR", "ERROR")
        self.log_level_combo.addItem("CRITICAL", "CRITICAL")
        self.log_level_combo.setFixedHeight(30)
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
                selection-background-color: #3b4453;
                selection-color: white;
                font-size: 12px;
            }
        """)
        self.log_level_combo.currentIndexChanged.connect(self.on_log_level_changed)
        row1_layout.addWidget(self.log_level_combo, 1)

        self.open_log_btn = QPushButton("打开目录")
        self.open_log_btn.clicked.connect(self.on_open_log_directory)
        self.open_log_btn.setFixedHeight(30)
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
        row1_layout.addWidget(self.open_log_btn, 0)

        content_layout.addLayout(row1_layout)

        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(6)

        log_size = get_log_size()
        self.log_size_text = QLineEdit()
        self.log_size_text.setReadOnly(True)
        self.log_size_text.setFixedHeight(30)
        self.log_size_text.setText(f"日志记录: {log_size:.2f} MB")
        self.log_size_text.setStyleSheet("""
            QLineEdit {
                padding: 0px 8px;
                border: none;
                border-radius: 3px;
                background-color: rgba(255, 255, 255, 0.9);
                font-size: 12px;
                color: #333333;
                min-height: 30px;
                max-height: 30px;
            }
        """)
        row2_layout.addWidget(self.log_size_text, 3)

        self.clean_log_btn = QPushButton("清理日志")
        self.clean_log_btn.clicked.connect(self.on_clean_logs)
        self.clean_log_btn.setFixedHeight(30)
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
        row2_layout.addWidget(self.clean_log_btn, 0)

        content_layout.addLayout(row2_layout)

        row3_layout = QHBoxLayout()
        row3_layout.setSpacing(6)

        geo_info_size = self.get_file_size(get_geo_info_file())
        self.geo_info_text = QLineEdit()
        self.geo_info_text.setReadOnly(True)
        self.geo_info_text.setFixedHeight(30)
        self.geo_info_text.setText(f"地理信息: {geo_info_size:.2f} MB")
        self.geo_info_text.setStyleSheet("""
            QLineEdit {
                padding: 0px 8px;
                border: none;
                border-radius: 3px;
                background-color: rgba(255, 255, 255, 0.9);
                font-size: 12px;
                color: #333333;
                min-height: 30px;
                max-height: 30px;
            }
        """)
        row3_layout.addWidget(self.geo_info_text, 3)

        self.clean_geo_info_btn = QPushButton("清理信息")
        self.clean_geo_info_btn.clicked.connect(self.on_clean_geo_info)
        self.clean_geo_info_btn.setFixedHeight(30)
        self.clean_geo_info_btn.setStyleSheet("""
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
        row3_layout.addWidget(self.clean_geo_info_btn, 0)

        content_layout.addLayout(row3_layout)

        row4_layout = QHBoxLayout()
        row4_layout.setSpacing(6)

        route_history_size = self.get_file_size(get_route_history_file())
        self.route_history_text = QLineEdit()
        self.route_history_text.setReadOnly(True)
        self.route_history_text.setFixedHeight(30)
        self.route_history_text.setText(f"历史路线: {route_history_size:.2f} MB")
        self.route_history_text.setStyleSheet("""
            QLineEdit {
                padding: 0px 8px;
                border: none;
                border-radius: 3px;
                background-color: rgba(255, 255, 255, 0.9);
                font-size: 12px;
                color: #333333;
                min-height: 30px;
                max-height: 30px;
            }
        """)
        row4_layout.addWidget(self.route_history_text, 3)

        self.clean_route_history_btn = QPushButton("清理文件")
        self.clean_route_history_btn.clicked.connect(self.on_clean_route_history)
        self.clean_route_history_btn.setFixedHeight(30)
        self.clean_route_history_btn.setStyleSheet("""
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
        row4_layout.addWidget(self.clean_route_history_btn, 0)

        content_layout.addLayout(row4_layout)

        # 缓存文件大小和清理按钮
        row5_layout = QHBoxLayout()
        row5_layout.setSpacing(6)

        # 只计算Temp目录的大小
        temp_cache_dir = os.path.join(get_cache_dir(), 'Temp')
        cache_size = self.get_directory_size(temp_cache_dir)
        self.cache_size_text = QLineEdit()
        self.cache_size_text.setReadOnly(True)
        self.cache_size_text.setFixedHeight(30)
        self.cache_size_text.setText(f"界面渲染: {cache_size:.2f} MB")
        self.cache_size_text.setStyleSheet("""
            QLineEdit {
                padding: 0px 8px;
                border: none;
                border-radius: 3px;
                background-color: rgba(255, 255, 255, 0.9);
                font-size: 12px;
                color: #333333;
                min-height: 30px;
                max-height: 30px;
            }
        """)
        row5_layout.addWidget(self.cache_size_text, 3)

        self.clean_cache_btn = QPushButton("清理缓存")
        self.clean_cache_btn.clicked.connect(self.on_clean_cache)
        self.clean_cache_btn.setFixedHeight(30)
        self.clean_cache_btn.setStyleSheet("""
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
        row5_layout.addWidget(self.clean_cache_btn, 0)

        content_layout.addLayout(row5_layout)

        # 地图瓦片缓存
        row6_layout = QHBoxLayout()
        row6_layout.setSpacing(6)
        
        gaode_size = self.get_directory_size(get_gaode_cache_dir())
        osm_size = self.get_directory_size(get_osm_cache_dir())
        tiles_size = gaode_size + osm_size
        
        self.tiles_size_text = QLineEdit()
        self.tiles_size_text.setReadOnly(True)
        self.tiles_size_text.setFixedHeight(30)
        self.tiles_size_text.setText(f"地图瓦片: {tiles_size:.2f} MB")
        self.tiles_size_text.setStyleSheet("""
            QLineEdit {
                padding: 0px 8px;
                border: none;
                border-radius: 3px;
                background-color: rgba(255, 255, 255, 0.9);
                font-size: 12px;
                color: #333333;
                min-height: 30px;
                max-height: 30px;
            }
        """)
        row6_layout.addWidget(self.tiles_size_text, 3)

        self.clean_tiles_btn = QPushButton("清理瓦片")
        self.clean_tiles_btn.clicked.connect(self.on_clean_map_tiles)
        self.clean_tiles_btn.setFixedHeight(30)
        self.clean_tiles_btn.setStyleSheet("""
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
        row6_layout.addWidget(self.clean_tiles_btn, 0)
        
        content_layout.addLayout(row6_layout)

        main_layout.addLayout(content_layout)

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

        # 更新文件大小显示
        # 这里不需要更新标签，因为标签是在_init_ui中创建的，
        # 每次显示面板时都会重新初始化

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
                QMessageBox.information(self, "成功", "日志已清理")
                # 重新初始化UI以更新文件大小显示
                self._init_ui()
                self.load_current_config()
            else:
                QMessageBox.critical(self, "错误", "清理日志失败")

    def on_open_log_directory(self):
        """打开日志目录"""
        if not open_log_directory():
            QMessageBox.critical(self, "错误", "打开日志目录失败")

    def on_clean_geo_info(self):
        """清理地理信息文件"""
        reply = QMessageBox.question(self, "确认", "确定要清理地理信息文件吗？\n这将同时清理文件和内存中的地理信息缓存。",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                # 清理文件
                geo_info_file = get_geo_info_file()
                if os.path.exists(geo_info_file):
                    os.remove(geo_info_file)
                
                # 清理内存中的地理信息缓存
                if self.parent() and hasattr(self.parent(), 'search_manager'):
                    search_manager = self.parent().search_manager
                    if hasattr(search_manager, 'geo_storage'):
                        search_manager.geo_storage.clear_history()
                
                QMessageBox.information(self, "成功", "地理信息文件和内存缓存已清理")
                self._init_ui()
                self.load_current_config()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"清理地理信息文件失败: {str(e)}")

    def on_clean_route_history(self):
        """清理路线历史文件"""
        reply = QMessageBox.question(self, "确认", "确定要清理路线历史文件吗？\n这将同时清理文件和内存中的历史记录。",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                # 清理文件
                route_history_file = get_route_history_file()
                if os.path.exists(route_history_file):
                    os.remove(route_history_file)
                
                # 清理内存中的路线历史记录
                if self.parent() and hasattr(self.parent(), 'route_history_storage'):
                    self.parent().route_history_storage.clear_history()
                    
                    # 同时更新路线面板的历史记录列表显示
                    if hasattr(self.parent(), 'route_plan_panel'):
                        if hasattr(self.parent().route_plan_panel, '_last_history_list'):
                            self.parent().route_plan_panel._last_history_list = []
                
                QMessageBox.information(self, "成功", "路线历史文件和内存缓存已清理")
                self._init_ui()
                self.load_current_config()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"清理路线历史文件失败: {str(e)}")
    
    def on_clean_cache(self):
        """清理界面渲染缓存文件"""
        reply = QMessageBox.question(self, "确认", "确定要清理界面渲染缓存文件吗？\n这将同时清理文件和浏览器引擎缓存。",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                import shutil
                # 清理Temp目录
                cache_dir = os.path.join(get_cache_dir(), 'Temp')
                if os.path.exists(cache_dir):
                    # 删除整个Temp目录及其内容
                    shutil.rmtree(cache_dir)
                    # 重新创建空目录
                    os.makedirs(cache_dir, exist_ok=True)
                
                # 清理QWebEngineProfile的缓存
                try:
                    from PyQt5.QtWebEngineWidgets import QWebEngineProfile
                    profile = QWebEngineProfile.defaultProfile()
                    profile.clearHttpCache()
                except Exception as profile_error:
                    print(f"清理浏览器引擎缓存失败: {profile_error}")
                
                QMessageBox.information(self, "成功", "界面渲染缓存已清理")
                self._init_ui()
                self.load_current_config()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"清理缓存文件失败: {str(e)}")

    def on_clean_map_tiles(self):
        """清理地图瓦片缓存"""
        reply = QMessageBox.question(self, "确认", "确定要清理所有地图瓦片缓存吗？\n这会删除已下载的高德和OSM地图瓦片，同时清理内存缓存。",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                import shutil
                
                # 清理高德地图缓存
                gaode_dir = get_gaode_cache_dir()
                if os.path.exists(gaode_dir):
                    shutil.rmtree(gaode_dir)
                    os.makedirs(gaode_dir, exist_ok=True)
                
                # 清理OSM地图缓存
                osm_dir = get_osm_cache_dir()
                if os.path.exists(osm_dir):
                    shutil.rmtree(osm_dir)
                    os.makedirs(osm_dir, exist_ok=True)
                
                # 清理HTTP服务器的内存缓存
                if self.parent() and hasattr(self.parent(), 'map_manager'):
                    map_manager = self.parent().map_manager
                    if hasattr(map_manager, 'http_server'):
                        http_server = map_manager.http_server
                        # 清理视口完整性缓存
                        if hasattr(http_server, 'viewport_completeness_cache'):
                            http_server.viewport_completeness_cache.clear()
                
                QMessageBox.information(self, "成功", "地图瓦片缓存已清理")
                self._init_ui()
                self.load_current_config()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"清理地图瓦片缓存失败: {str(e)}")


class AboutPopup(BaseSettingsPopup):
    """关于弹出面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(300, 240)  # 与地图设置面板保持一致
        self._init_ui()

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
            AboutPopup {
                background-color: #3b4453;
                border-radius: 6px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QLabel {
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QPushButton {
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
        title_label = QLabel("关于")
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

        # 关于内容 - 优化布局和文字样式
        about_label = QLabel()
        about_label.setTextFormat(Qt.RichText)
        about_label.setText(self._get_about_text())
        about_label.setWordWrap(True)
        about_label.setAlignment(Qt.AlignCenter)
        about_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                color: white;
            }
        """)
        main_layout.addWidget(about_label)

    def _get_about_text(self):
        """获取关于内容的HTML"""
        log_size = get_log_size()

        # 从配置中获取信息
        app_name = about_config.get_app_name()
        app_version = about_config.get_app_version()
        app_platform = about_config.get_app_platform()
        license_text = about_config.get_license_text()
        developer_team = about_config.get_developer_team()
        developer_email = about_config.get_developer_email()
        copyright_text = about_config.get_copyright_text()

        html = f"""
        <div style="font-family: 'Microsoft YaHei', Arial, sans-serif; color: white; line-height: 1.5;">
            <h3 style="color: white; text-align: center; margin: 10px 0; font-size: 16px; font-weight: bold;">{app_name}</h3>

            <div style="text-align: center; margin: 8px 0; font-size: 12px;">
                <div>版本: {app_version} | 平台: {app_platform}</div>
            </div>

            <div style="background-color: rgba(255, 255, 255, 0.15); padding: 8px; border-radius: 4px; margin: 8px 16px; text-align: center; font-size: 11px;">
                <div>{license_text}</div>
            </div>

            <div style="background-color: rgba(255, 255, 255, 0.1); padding: 8px; border-radius: 4px; margin: 8px 16px; text-align: center; font-size: 11px;">
                <div>开发者: {developer_team}</div>
                <div>邮箱: {developer_email}</div>
            </div>

            <div style="background-color: rgba(255, 255, 255, 0.1); padding: 6px; border-radius: 4px; margin: 8px 16px; text-align: center; font-size: 10px;">
                <div>运行日志大小: {log_size:.2f} MB</div>
            </div>

            <div style="text-align: center; color: rgba(255, 255, 255, 0.7); font-size: 10px; padding-top: 8px; border-top: 1px solid rgba(255, 255, 255, 0.15); margin: 8px 16px 0;">
                <div>{copyright_text}</div>
            </div>
        </div>
        """

        return html



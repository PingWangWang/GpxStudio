"""
设置弹出面板组件

包含地图设置、日志设置和关于信息的弹出面板
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QPushButton, QLabel, QMessageBox,
                             QTabWidget, QTextEdit, QComboBox, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QKeyEvent
from services.config.map_config import map_config
from core.logging_setup import clean_logs, open_log_directory, get_log_size, set_log_level
from services.config import about_config
import os


class BaseSettingsPopup(QWidget):
    """设置弹出面板基类"""

    closed = pyqtSignal()  # 关闭信号

    def __init__(self, parent=None):
        super().__init__(parent)

        # 设置窗口标志 - 作为工具提示窗口，不抢夺焦点
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)  # 不透明背景

        # 设置样式
        self.setStyleSheet("""
            BaseSettingsPopup {
                background-color: white;
                border-radius: 6px;
                border: 1px solid rgba(0, 0, 0, 0.15);
            }
        """)

        # 设置固定宽度
        self.setFixedWidth(450)

    def keyPressEvent(self, event: QKeyEvent):
        """处理键盘事件"""
        if event.key() == Qt.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)

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
        self.setFixedHeight(500)
        self._init_ui()
        self.load_current_config()

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # 标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel("地图设置")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
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

        # 配置表单
        config_layout = QFormLayout()
        config_layout.setSpacing(12)

        # 地图数据源选择
        self.map_source_combo = QComboBox()
        self.map_source_combo.addItem("无")
        self.map_source_combo.addItem("OpenStreetMap")
        self.map_source_combo.addItem("高德地图")
        self.map_source_combo.currentIndexChanged.connect(self.on_map_source_changed)
        self.map_source_combo.setStyleSheet("""
            QComboBox {
                padding: 6px 12px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                background-color: white;
            }
        """)
        config_layout.addRow("地图数据源:", self.map_source_combo)

        # API Key 输入框和眼睛按钮
        api_key_layout = QHBoxLayout()
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("请输入高德地图Web服务API Key")
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setStyleSheet("""
            QLineEdit {
                padding: 6px 12px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }
        """)
        api_key_layout.addWidget(self.api_key_edit)

        self.api_key_eye_btn = QPushButton("👁️")
        self.api_key_eye_btn.setFixedSize(30, 30)
        self.api_key_eye_btn.setStyleSheet("border: none; background: transparent;")
        self.api_key_eye_btn.clicked.connect(self.toggle_api_key_visibility)
        api_key_layout.addWidget(self.api_key_eye_btn)
        config_layout.addRow("API Key:", api_key_layout)

        # 安全密钥输入框和眼睛按钮
        security_key_layout = QHBoxLayout()
        self.security_key_edit = QLineEdit()
        self.security_key_edit.setPlaceholderText("可选：签名校验密钥")
        self.security_key_edit.setEchoMode(QLineEdit.Password)
        self.security_key_edit.setStyleSheet("""
            QLineEdit {
                padding: 6px 12px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }
        """)
        security_key_layout.addWidget(self.security_key_edit)

        self.security_key_eye_btn = QPushButton("👁️")
        self.security_key_eye_btn.setFixedSize(30, 30)
        self.security_key_eye_btn.setStyleSheet("border: none; background: transparent;")
        self.security_key_eye_btn.clicked.connect(self.toggle_security_key_visibility)
        security_key_layout.addWidget(self.security_key_eye_btn)
        config_layout.addRow("安全密钥:", security_key_layout)

        # 配置状态
        self.status_label = QLabel("未配置")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 6px;
                border-radius: 4px;
                background-color: #f5f5f5;
            }
        """)
        config_layout.addRow("配置状态:", self.status_label)

        main_layout.addLayout(config_layout)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.test_btn = QPushButton("测试连接")
        self.test_btn.clicked.connect(self.test_connection)
        self.test_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        btn_layout.addWidget(self.test_btn)

        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.save_config)
        self.save_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #4A90E2;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3A80D2;
            }
        """)
        btn_layout.addWidget(self.save_btn)

        self.clear_btn = QPushButton("清除配置")
        self.clear_btn.clicked.connect(self.clear_config)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        btn_layout.addWidget(self.clear_btn)

        main_layout.addLayout(btn_layout)
        main_layout.addStretch()

    def on_map_source_changed(self, index):
        """地图数据源选择变化时的处理"""
        if index == 0:  # 无
            self.api_key_edit.setEnabled(False)
            self.api_key_eye_btn.setEnabled(False)
            self.security_key_edit.setEnabled(False)
            self.security_key_eye_btn.setEnabled(False)
            self.test_btn.setEnabled(False)
            self.status_label.setText("未选择")
            self.status_label.setStyleSheet("QLabel { padding: 6px; border-radius: 4px; background-color: #f5f5f5; color: gray; }")
        elif index == 2:  # 高德地图
            self.api_key_edit.setEnabled(True)
            self.api_key_eye_btn.setEnabled(True)
            self.security_key_edit.setEnabled(True)
            self.security_key_eye_btn.setEnabled(True)
            self.test_btn.setEnabled(True)
            if map_config.is_gaode_configured():
                self.status_label.setText("已配置")
                self.status_label.setStyleSheet("QLabel { padding: 6px; border-radius: 4px; background-color: #e8f5e9; color: green; }")
            else:
                self.status_label.setText("未配置")
                self.status_label.setStyleSheet("QLabel { padding: 6px; border-radius: 4px; background-color: #ffebee; color: red; }")
        else:  # OpenStreetMap
            self.api_key_edit.setEnabled(False)
            self.api_key_eye_btn.setEnabled(False)
            self.security_key_edit.setEnabled(False)
            self.security_key_eye_btn.setEnabled(False)
            self.test_btn.setEnabled(False)
            self.status_label.setText("无需配置")
            self.status_label.setStyleSheet("QLabel { padding: 6px; border-radius: 4px; background-color: #e3f2fd; color: blue; }")

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
        if self.security_key_edit.echoMode() == QLineEdit.Password:
            self.security_key_edit.setEchoMode(QLineEdit.Normal)
            self.security_key_eye_btn.setText("👁️‍🗨️")
        else:
            self.security_key_edit.setEchoMode(QLineEdit.Password)
            self.security_key_eye_btn.setText("👁️")



class LogSettingsPopup(BaseSettingsPopup):
    """日志设置弹出面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(400)
        self._init_ui()
        self.load_current_config()

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # 标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel("日志设置")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
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

        # 日志管理说明
        log_info_label = QLabel()
        log_info_label.setTextFormat(Qt.RichText)
        log_info_label.setText("""
        <div style="padding: 10px; background-color: #f0f8ff; border-radius: 5px;">
            <p style="margin: 0; color: #333;">运行日志记录了应用程序的运行情况，有助于排查问题。</p>
            <p style="margin: 5px 0 0 0; color: #666;">当日志文件过大时，可能会影响应用程序性能，建议定期清理。</p>
        </div>
        """)
        log_info_label.setWordWrap(True)
        main_layout.addWidget(log_info_label)

        # 日志级别设置
        log_level_layout = QHBoxLayout()
        log_level_label = QLabel("日志级别:")
        log_level_label.setMinimumWidth(80)
        log_level_layout.addWidget(log_level_label)

        self.log_level_combo = QComboBox()
        self.log_level_combo.addItem("DEBUG", "DEBUG")
        self.log_level_combo.addItem("INFO", "INFO")
        self.log_level_combo.addItem("WARNING", "WARNING")
        self.log_level_combo.addItem("ERROR", "ERROR")
        self.log_level_combo.addItem("CRITICAL", "CRITICAL")
        self.log_level_combo.setStyleSheet("""
            QComboBox {
                padding: 6px 12px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                background-color: white;
            }
        """)
        log_level_layout.addWidget(self.log_level_combo)

        self.save_log_level_btn = QPushButton("保存设置")
        self.save_log_level_btn.clicked.connect(self.on_save_log_level)
        self.save_log_level_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #4A90E2;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3A80D2;
            }
        """)
        log_level_layout.addWidget(self.save_log_level_btn)

        main_layout.addLayout(log_level_layout)

        # 日志管理按钮
        log_btn_layout = QHBoxLayout()
        log_btn_layout.setSpacing(8)

        self.clean_log_btn = QPushButton("清理日志")
        self.clean_log_btn.clicked.connect(self.on_clean_logs)
        self.clean_log_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        log_btn_layout.addWidget(self.clean_log_btn)

        self.open_log_btn = QPushButton("打开日志目录")
        self.open_log_btn.clicked.connect(self.on_open_log_directory)
        self.open_log_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        log_btn_layout.addWidget(self.open_log_btn)

        main_layout.addLayout(log_btn_layout)

        # 日志大小信息
        log_size = get_log_size()
        self.log_size_label = QLabel(f"当前日志大小: {log_size:.2f} MB")
        self.log_size_label.setAlignment(Qt.AlignCenter)
        self.log_size_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                margin-top: 10px;
                font-weight: bold;
                background-color: #f5f5f5;
                border-radius: 4px;
            }
        """)
        main_layout.addWidget(self.log_size_label)

        main_layout.addStretch()

    def load_current_config(self):
        """加载当前配置"""
        log_level = map_config.get('log_level', 'INFO')
        for i in range(self.log_level_combo.count()):
            if self.log_level_combo.itemData(i) == log_level:
                self.log_level_combo.setCurrentIndex(i)
                break

    def on_save_log_level(self):
        """保存日志级别设置"""
        selected_level = self.log_level_combo.currentData()
        try:
            set_log_level(selected_level)
            QMessageBox.information(self, "成功", f"日志级别已设置为: {selected_level}")
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
        self.setFixedHeight(450)
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
                font-size: 16px;
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

        main_layout.addStretch()

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

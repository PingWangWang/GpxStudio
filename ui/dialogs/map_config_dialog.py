"""
地图配置对话框
提供地图数据源配置界面
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                              QLineEdit, QPushButton, QLabel, QMessageBox,
                              QTabWidget, QWidget, QTextEdit, QComboBox)
from PyQt5.QtCore import Qt
from services.config.map_config import map_config

from core.logging_setup import clean_logs, open_log_directory


class MapConfigDialog(QDialog):
    """地图配置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("地图配置")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.resize(550, 450)
        self.init_ui()
        self.load_current_config()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        config_tab = QWidget()
        config_layout = QFormLayout(config_tab)

        # 地图数据源选择
        self.map_source_combo = QComboBox()
        self.map_source_combo.addItem("无")
        self.map_source_combo.addItem("OpenStreetMap")
        self.map_source_combo.addItem("高德地图")
        self.map_source_combo.currentIndexChanged.connect(self.on_map_source_changed)
        self.map_source_combo.setMinimumWidth(300)
        config_layout.addRow("地图数据源:", self.map_source_combo)

        # API Key 输入框和眼睛按钮
        self.api_key_layout = QHBoxLayout()
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("请输入高德地图Web服务API Key")
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setMinimumWidth(300)
        self.api_key_layout.addWidget(self.api_key_edit)
        
        self.api_key_eye_btn = QPushButton("👁️")
        self.api_key_eye_btn.setFixedSize(30, 30)
        self.api_key_eye_btn.setStyleSheet("border: none; background: transparent;")
        self.api_key_eye_btn.clicked.connect(self.toggle_api_key_visibility)
        self.api_key_layout.addWidget(self.api_key_eye_btn)
        self.api_key_row = config_layout.addRow("API Key:", self.api_key_layout)

        # 安全密钥输入框和眼睛按钮
        self.security_key_layout = QHBoxLayout()
        self.security_key_edit = QLineEdit()
        self.security_key_edit.setPlaceholderText("可选：签名校验密钥")
        self.security_key_edit.setEchoMode(QLineEdit.Password)
        self.security_key_edit.setMinimumWidth(300)
        self.security_key_layout.addWidget(self.security_key_edit)
        
        self.security_key_eye_btn = QPushButton("👁️")
        self.security_key_eye_btn.setFixedSize(30, 30)
        self.security_key_eye_btn.setStyleSheet("border: none; background: transparent;")
        self.security_key_eye_btn.clicked.connect(self.toggle_security_key_visibility)
        self.security_key_layout.addWidget(self.security_key_eye_btn)
        self.security_key_row = config_layout.addRow("安全密钥:", self.security_key_layout)

        self.status_label = QLabel("未配置")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_row = config_layout.addRow("配置状态:", self.status_label)

        # 按钮布局 - 按功能分组
        btn_container_layout = QVBoxLayout()
        
        # 第一行：地图配置相关按钮
        config_btn_layout = QHBoxLayout()
        config_btn_layout.addStretch(1)
        
        self.test_btn = QPushButton("测试连接")
        self.test_btn.clicked.connect(self.test_connection)
        self.test_btn.setMinimumWidth(100)
        config_btn_layout.addWidget(self.test_btn)

        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.save_config)
        self.save_btn.setMinimumWidth(100)
        config_btn_layout.addWidget(self.save_btn)

        self.clear_btn = QPushButton("清除配置")
        self.clear_btn.clicked.connect(self.clear_config)
        self.clear_btn.setMinimumWidth(100)
        config_btn_layout.addWidget(self.clear_btn)
        
        config_btn_layout.addStretch(1)
        btn_container_layout.addLayout(config_btn_layout)
        
        self.btn_row = config_layout.addRow("", btn_container_layout)

        tabs.addTab(config_tab, "配置")

        # 日志管理Tab
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        
        # 日志管理说明
        log_info_label = QLabel()
        log_info_label.setTextFormat(Qt.RichText)
        log_info_label.setText("""
        <div style="padding: 10px; margin-bottom: 20px; background-color: #f0f8ff; border-radius: 5px;">
            <h4 style="margin-top: 0; color: #2196F3;">日志管理</h4>
            <p>运行日志记录了应用程序的运行情况，有助于排查问题。</p>
            <p>当日志文件过大时，可能会影响应用程序性能，建议定期清理。</p>
        </div>
        """)
        log_layout.addWidget(log_info_label)
        
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
        self.log_level_combo.setMinimumWidth(200)
        log_level_layout.addWidget(self.log_level_combo)
        
        self.save_log_level_btn = QPushButton("保存设置")
        self.save_log_level_btn.clicked.connect(self.on_save_log_level)
        self.save_log_level_btn.setMinimumWidth(100)
        log_level_layout.addWidget(self.save_log_level_btn)
        
        log_level_layout.addStretch(1)
        log_layout.addLayout(log_level_layout)
        
        # 日志管理按钮
        log_btn_layout = QHBoxLayout()
        log_btn_layout.addStretch(1)
        
        self.clean_log_btn = QPushButton("清理日志")
        self.clean_log_btn.clicked.connect(self.on_clean_logs)
        self.clean_log_btn.setMinimumWidth(120)
        log_btn_layout.addWidget(self.clean_log_btn)

        self.open_log_btn = QPushButton("打开日志目录")
        self.open_log_btn.clicked.connect(self.on_open_log_directory)
        self.open_log_btn.setMinimumWidth(120)
        log_btn_layout.addWidget(self.open_log_btn)
        
        log_btn_layout.addStretch(1)
        log_layout.addLayout(log_btn_layout)
        
        # 日志大小信息
        from core.logging_setup import get_log_size
        log_size = get_log_size()
        log_size_label = QLabel(f"当前日志大小: {log_size:.2f} MB")
        log_size_label.setAlignment(Qt.AlignCenter)
        log_size_label.setStyleSheet("margin-top: 20px; font-weight: bold;")
        log_layout.addWidget(log_size_label)
        
        tabs.addTab(log_tab, "日志管理")

        help_tab = QWidget()
        help_layout = QVBoxLayout(help_tab)

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml("""
        <h3>地图配置说明</h3>
        <p><b>1. 地图数据源选择:</b></p>
        <ul>
            <li><b>OpenStreetMap (OSM):</b> 免费开源地图数据，无需API Key</li>
            <li><b>高德地图:</b> 国内地图数据，需要API Key配置</li>
        </ul>

        <p><b>2. 高德地图API Key配置:</b></p>
        <ol>
            <li>访问 <a href="https://lbs.amap.com/">高德开放平台</a></li>
            <li>注册/登录账号</li>
            <li>创建应用并添加Web服务API</li>
            <li>复制API Key到上方输入框</li>
        </ol>

        <p><b>3. 服务说明:</b></p>
        <ul>
            <li><b>地理编码:</b> 地址搜索、坐标转换</li>
            <li><b>路线规划:</b> 驾车/步行/骑行路线规划</li>
            <li><b>地图显示:</b> 根据选择的数据源显示对应的地图</li>
        </ul>

        <p><b>4. 注意事项:</b></p>
        <ul>
            <li>选择高德地图时，API Key不能为空</li>
            <li>API Key需要开通对应的服务权限</li>
            <li>签名校验密钥为可选，提供更高安全性</li>
            <li>部分服务有每日调用配额限制</li>
        </ul>
        """)
        help_layout.addWidget(help_text)
        tabs.addTab(help_tab, "帮助")

        # 添加间距
        layout.addSpacing(20)
        
        # 关闭按钮布局
        close_btn_layout = QHBoxLayout()
        close_btn_layout.addStretch(1)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        close_btn.setMinimumWidth(100)
        close_btn_layout.addWidget(close_btn)
        
        close_btn_layout.addStretch(1)
        layout.addLayout(close_btn_layout)

    def on_map_source_changed(self, index):
        """地图数据源选择变化时的处理"""
        if index == 0:  # 0 是无
            # 禁用所有API Key相关控件
            self.api_key_edit.setEnabled(False)
            self.api_key_eye_btn.setEnabled(False)
            self.security_key_edit.setEnabled(False)
            self.security_key_eye_btn.setEnabled(False)
            self.test_btn.setEnabled(False)
            
            # 更新状态标签
            self.status_label.setText("未选择")
            self.status_label.setStyleSheet("color: gray;")
        elif index == 2:  # 2 是高德地图
            # 启用API Key相关控件
            self.api_key_edit.setEnabled(True)
            self.api_key_eye_btn.setEnabled(True)
            self.security_key_edit.setEnabled(True)
            self.security_key_eye_btn.setEnabled(True)
            self.test_btn.setEnabled(True)
            
            # 更新状态标签
            if map_config.is_gaode_configured():
                self.status_label.setText("已配置")
                self.status_label.setStyleSheet("color: green;")
            else:
                self.status_label.setText("未配置")
                self.status_label.setStyleSheet("color: red;")
        else:  # 1 是OpenStreetMap
            # 禁用所有API Key相关控件
            self.api_key_edit.setEnabled(False)
            self.api_key_eye_btn.setEnabled(False)
            self.security_key_edit.setEnabled(False)
            self.security_key_eye_btn.setEnabled(False)
            self.test_btn.setEnabled(False)
            
            # 更新状态标签
            self.status_label.setText("无需配置")
            self.status_label.setStyleSheet("color: blue;")

    def load_current_config(self):
        """加载当前配置"""
        # 加载地图数据源
        map_source = map_config.get_map_source()
        if not map_source:
            self.map_source_combo.setCurrentIndex(0)  # 无
        elif map_source == "gaode":
            self.map_source_combo.setCurrentIndex(2)  # 高德地图
        else:
            self.map_source_combo.setCurrentIndex(1)  # OpenStreetMap
        
        # 加载API Key配置
        self.api_key_edit.setText(map_config.get_api_key())
        self.security_key_edit.setText(map_config.get_security_key())
        
        # 加载日志级别配置
        log_level = map_config.get('log_level', 'INFO')
        for i in range(self.log_level_combo.count()):
            if self.log_level_combo.itemData(i) == log_level:
                self.log_level_combo.setCurrentIndex(i)
                break
        
        # 确保所有控件都可见
        self.api_key_edit.setVisible(True)
        self.api_key_eye_btn.setVisible(True)
        self.security_key_edit.setVisible(True)
        self.security_key_eye_btn.setVisible(True)
        self.test_btn.setVisible(True)
        
        # 触发一次数据源变化事件，以更新UI
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
        # 获取地图数据源
        current_index = self.map_source_combo.currentIndex()
        if current_index == 0:
            map_source = ""
        elif current_index == 2:
            map_source = "gaode"
        else:
            map_source = "osm"
        
        # 获取API Key配置
        api_key = self.api_key_edit.text().strip()
        security_key = self.security_key_edit.text().strip()

        # 如果选择高德地图，API Key不能为空
        if map_source == "gaode" and not api_key:
            QMessageBox.warning(self, "警告", "选择高德地图时，API Key不能为空")
            return

        # 保存配置
        config = {
            "map_source": map_source,
            "api_key": api_key,
            "security_key": security_key
        }

        if map_config.save_config(config):
            # 更新状态
            if map_source == "gaode":
                self.status_label.setText("已配置")
                self.status_label.setStyleSheet("color: green;")
            elif map_source == "":
                self.status_label.setText("未选择")
                self.status_label.setStyleSheet("color: gray;")
            else:
                self.status_label.setText("无需配置")
                self.status_label.setStyleSheet("color: blue;")
            QMessageBox.information(self, "成功", "配置已保存")
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
                self.map_source_combo.setCurrentIndex(0)  # 重置为无
                self.on_map_source_changed(0)  # 更新UI
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
    
    def on_clean_logs(self):
        """清理日志"""
        reply = QMessageBox.question(self, "确认", "确定要清理所有运行日志吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if clean_logs():
                QMessageBox.information(self, "成功", "日志已清理")
            else:
                QMessageBox.critical(self, "错误", "清理日志失败")
    
    def on_open_log_directory(self):
        """打开日志目录"""
        if open_log_directory():
            pass  # 目录已打开
        else:
            QMessageBox.critical(self, "错误", "打开日志目录失败")
    
    def on_save_log_level(self):
        """保存日志级别设置"""
        from core.logging_setup import set_log_level
        selected_level = self.log_level_combo.currentData()
        try:
            set_log_level(selected_level)
            QMessageBox.information(self, "成功", f"日志级别已设置为: {selected_level}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存日志级别失败: {str(e)}")

"""
高德地图配置对话框
提供API Key配置界面
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                              QLineEdit, QPushButton, QLabel, QMessageBox,
                              QTabWidget, QWidget, QTextEdit, QComboBox)
from PyQt5.QtCore import Qt
from services.config.gaode_config import gaode_config


class GaodeConfigDialog(QDialog):
    """高德地图配置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("高德地图配置")
        self.setMinimumWidth(400)
        self.init_ui()
        self.load_current_config()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        config_tab = QWidget()
        config_layout = QFormLayout(config_tab)

        # API Key 输入框和眼睛按钮
        api_key_layout = QHBoxLayout()
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("请输入高德地图Web服务API Key")
        self.api_key_edit.setEchoMode(QLineEdit.Password)
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
        security_key_layout.addWidget(self.security_key_edit)
        
        self.security_key_eye_btn = QPushButton("👁️")
        self.security_key_eye_btn.setFixedSize(30, 30)
        self.security_key_eye_btn.setStyleSheet("border: none; background: transparent;")
        self.security_key_eye_btn.clicked.connect(self.toggle_security_key_visibility)
        security_key_layout.addWidget(self.security_key_eye_btn)
        config_layout.addRow("安全密钥:", security_key_layout)

        self.status_label = QLabel("未配置")
        self.status_label.setAlignment(Qt.AlignCenter)
        config_layout.addRow("配置状态:", self.status_label)

        btn_layout = QHBoxLayout()
        self.test_btn = QPushButton("测试连接")
        self.test_btn.clicked.connect(self.test_connection)
        btn_layout.addWidget(self.test_btn)

        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.save_config)
        btn_layout.addWidget(self.save_btn)

        self.clear_btn = QPushButton("清除配置")
        self.clear_btn.clicked.connect(self.clear_config)
        btn_layout.addWidget(self.clear_btn)

        config_layout.addRow("", btn_layout)

        tabs.addTab(config_tab, "API配置")

        help_tab = QWidget()
        help_layout = QVBoxLayout(help_tab)

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml("""
        <h3>高德地图API配置说明</h3>
        <p><b>1. 获取API Key:</b></p>
        <ol>
            <li>访问 <a href="https://lbs.amap.com/">高德开放平台</a></li>
            <li>注册/登录账号</li>
            <li>创建应用并添加Web服务API</li>
            <li>复制API Key到上方输入框</li>
        </ol>

        <p><b>2. 服务说明:</b></p>
        <ul>
            <li><b>地理编码:</b> 地址搜索、坐标转换</li>
            <li><b>路线规划:</b> 驾车/步行/骑行路线规划</li>
            <li><b>地图显示:</b> 高德地图瓦片底图</li>
        </ul>

        <p><b>3. 注意事项:</b></p>
        <ul>
            <li>API Key需要开通对应的服务权限</li>
            <li>签名校验密钥为可选，提供更高安全性</li>
            <li>部分服务有每日调用配额限制</li>
        </ul>
        """)
        help_layout.addWidget(help_text)
        tabs.addTab(help_tab, "帮助")

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def load_current_config(self):
        """加载当前配置"""
        if gaode_config.is_available():
            self.api_key_edit.setText(gaode_config.get_api_key())
            self.security_key_edit.setText(gaode_config.get_security_key())
            self.status_label.setText("已配置")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText("未配置")
            self.status_label.setStyleSheet("color: red;")

    def test_connection(self):
        """测试连接"""
        api_key = self.api_key_edit.text().strip()
        if not api_key:
            QMessageBox.warning(self, "警告", "请先输入API Key")
            return

        from services.gaode_geocoding import GaodeGeocodingService
        service = GaodeGeocodingService(api_key=api_key)
        result = service.search_location("北京市")

        if result:
            QMessageBox.information(self, "成功", f"连接测试成功！\n找到 {len(result)} 个结果")
        else:
            QMessageBox.warning(self, "失败", "连接测试失败，请检查API Key是否正确")

    def save_config(self):
        """保存配置"""
        api_key = self.api_key_edit.text().strip()
        security_key = self.security_key_edit.text().strip()

        if not api_key:
            QMessageBox.warning(self, "警告", "API Key不能为空")
            return

        if gaode_config.save_config({"api_key": api_key, "security_key": security_key}):
            self.status_label.setText("已配置")
            self.status_label.setStyleSheet("color: green;")
            QMessageBox.information(self, "成功", "配置已保存")
        else:
            QMessageBox.critical(self, "错误", "保存配置失败")

    def clear_config(self):
        """清除配置"""
        reply = QMessageBox.question(self, "确认", "确定要清除配置吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if gaode_config.clear_config():
                self.api_key_edit.clear()
                self.security_key_edit.clear()
                self.status_label.setText("未配置")
                self.status_label.setStyleSheet("color: red;")
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

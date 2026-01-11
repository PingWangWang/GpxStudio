from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt

from core.logging_setup import get_log_size
from services.config import about_config


class AboutDialog(QDialog):
    """
    关于对话框类
    显示应用程序的关于信息
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于 GPX Studio")
        self.setFixedSize(600, 300)  # 设置固定大小为600*300
        self._init_ui()

    def _init_ui(self):
        """初始化用户界面"""
        # 创建布局
        layout = QVBoxLayout(self)

        # 创建标签用于显示HTML内容
        label = QLabel()
        label.setTextFormat(Qt.RichText)
        label.setText(self._get_about_text())
        label.setWordWrap(True)
        label.setStyleSheet("padding: 20px;")

        # 创建关闭按钮
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.close)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 6px;
                font-size: 9pt;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #388e3c;
            }
        """)

        # 添加到布局
        layout.addWidget(label)

        # 创建按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        button_layout.addStretch()
        button_layout.setContentsMargins(0, 0, 0, 20)
        layout.addLayout(button_layout)

    def _get_about_text(self):
        """获取关于对话框的HTML内容"""
        log_size = get_log_size()
        log_warning = ""
        if log_size > 100:
            log_warning = "<div style='color: red;'>⚠️ 运行日志超过100MB，请及时清理</div>"
        
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
        
        # 使用普通字符串拼接，避免format方法解析CSS中的大括号
        html = ""
        html += "<style>"
        html += "body {"
        html += "font-family: 'Microsoft YaHei', Arial, sans-serif;"
        html += "color: #333;"
        html += "line-height: 1.5;"
        html += "background-color: #f9f9f9;"
        html += "padding: 10px;"
        html += "border-radius: 5px;"
        html += "font-size: 9pt;"
        html += "}"
        html += "h3 {"
        html += "color: #4CAF50;"
        html += "margin-top: 0;"
        html += "margin-bottom: 15px;"
        html += "font-size: 9pt;"
        html += "font-weight: bold;"
        html += "text-align: center;"
        html += "padding-bottom: 8px;"
        html += "border-bottom: 1px solid #e0e0e0;"
        html += "}"
        html += ".container {"
        html += "max-width: 520px;"
        html += "margin: 0 auto;"
        html += "}"
        html += ".section {"
        html += "margin-bottom: 15px;"
        html += "padding: 8px;"
        html += "}"
        html += ".version-info {"
        html += "font-size: 9pt;"
        html += "color: #666;"
        html += "text-align: center;"
        html += "font-weight: bold;"
        html += "}"
        html += ".description {"
        html += "font-size: 9pt;"
        html += "color: #555;"
        html += "text-align: center;"
        html += "margin-bottom: 10px;"
        html += "}"
        html += ".open-source {"
        html += "color: #2196F3;"
        html += "font-size: 9pt;"
        html += "text-align: center;"
        html += "font-weight: bold;"
        html += "padding: 10px;"
        html += "background-color: #e8f5e9;"
        html += "border-radius: 3px;"
        html += "margin: 10px 0;"
        html += "}"
        html += ".developer-info {"
        html += "font-size: 9pt;"
        html += "text-align: center;"
        html += "background-color: #f5f5f5;"
        html += "padding: 10px;"
        html += "border-radius: 3px;"
        html += "}"
        html += ".log-info {"
        html += "font-size: 9pt;"
        html += "text-align: center;"
        html += "background-color: #f0f8ff;"
        html += "padding: 10px;"
        html += "border-radius: 3px;"
        html += "margin: 10px 0;"
        html += "}"
        html += ".copyright {"
        html += "font-size: 9pt;"
        html += "color: #777;"
        html += "text-align: center;"
        html += "padding: 8px;"
        html += "border-top: 1px solid #e0e0e0;"
        html += "margin-top: 10px;"
        html += "}"
        html += "</style>"
        html += "<div class='container'>"
        html += "<h3>" + app_name + "</h3>"
        html += "<div class='section'>"
        html += "<div class='version-info'>"
        html += "版本: " + app_version + " | 平台: " + app_platform
        html += "</div>"
        html += "<div class='description'>"
        html += app_description
        html += "</div>"
        html += "</div>"
        html += "<div class='section'>"
        html += "<div class='open-source'>"
        html += license_text
        html += "</div>"
        html += "</div>"
        html += "<div class='section'>"
        html += "<div class='developer-info'>"
        html += "开发者: " + developer_team + "<br>邮箱: " + developer_email
        html += "</div>"
        html += "</div>"
        html += "<div class='section'>"
        html += "<div class='log-info'>"
        html += "运行日志大小: " + "{:.2f}".format(log_size) + " MB"
        if log_warning:
            html += "<br>" + log_warning
        html += "</div>"
        html += "</div>"
        html += "<div class='section'>"
        html += "<div class='copyright'>"
        html += copyright_text + "<br>" + map_api_copyright
        html += "</div>"
        html += "</div>"
        html += "</div>"
        
        return html

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt


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
                font-size: 14px;
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
        return """
        <style>
            body {
                font-family: 'Microsoft YaHei', Arial, sans-serif;
                color: #333;
                line-height: 1.5;
                background-color: #f9f9f9;
                padding: 10px;
                border-radius: 5px;
            }
            h3 {
                color: #4CAF50;
                margin-top: 0;
                margin-bottom: 15px;
                font-size: 20px;
                text-align: center;
                padding-bottom: 8px;
                border-bottom: 1px solid #e0e0e0;
            }
            .container {
                max-width: 520px;
                margin: 0 auto;
            }
            .section {
                margin-bottom: 15px;
                padding: 8px;
            }
            .version-info {
                font-size: 13px;
                color: #666;
                text-align: center;
                font-weight: bold;
            }
            .description {
                font-size: 13px;
                color: #555;
                text-align: center;
                margin-bottom: 10px;
            }
            .open-source {
                color: #2196F3;
                font-size: 14px;
                text-align: center;
                font-weight: bold;
                padding: 10px;
                background-color: #e8f5e9;
                border-radius: 3px;
                margin: 10px 0;
            }
            .developer-info {
                font-size: 13px;
                text-align: center;
                background-color: #f5f5f5;
                padding: 10px;
                border-radius: 3px;
            }
            .copyright {
                font-size: 11px;
                color: #777;
                text-align: center;
                padding: 8px;
                border-top: 1px solid #e0e0e0;
                margin-top: 10px;
            }
        </style>

        <div class="container">
            <h3>GPX Studio</h3>
            <div class="section">
                <div class="version-info">
                    版本: 1.0.1 | 平台: Windows
                </div>
                <div class="description">
                    路线规划工具，支持多种交通方式，可导出GPX格式文件
                </div>
            </div>
            <div class="section">
                <div class="open-source">
                    开源软件 - 本软件采用 MIT 许可证开源
                </div>
            </div>
            <div class="section">
                <div class="developer-info">
                    开发者: GPX Studio 团队<br>
                    邮箱: contact@gpxstudio.com
                </div>
            </div>
            <div class="section">
                <div class="copyright">
                    © 2024-2025 GPX Studio 团队<br>
                    使用高德地图API，© 2025 AutoNavi
                </div>
            </div>
        </div>
        """
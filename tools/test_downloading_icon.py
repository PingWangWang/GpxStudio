#!/usr/bin/env python3
"""
测试Downloading图标的显示和垂直居中效果
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from core.resource_path import resource_path


class TestDownloadingIcon(QMainWindow):
    """测试Downloading图标的窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Downloading图标测试")
        self.setGeometry(100, 100, 600, 400)
        
        # 创建中央控件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 测试不同大小的Downloading图标
        self.create_test_buttons(layout)
        
    def create_test_buttons(self, layout):
        """创建测试按钮"""
        
        # 标题
        title_label = QLabel("Downloading图标测试")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)
        
        # 测试不同版本的图标
        versions = [
            ("普通版本", "res/Downloading.png"),
            ("白色版本", "res/Downloading_white.png")
        ]
        
        for version_name, icon_path in versions:
            # 版本标题
            version_label = QLabel(f"{version_name}:")
            version_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 20px;")
            layout.addWidget(version_label)
            
            # 创建水平布局测试不同大小
            size_layout = QHBoxLayout()
            
            sizes = [16, 18, 20, 24, 32]
            for size in sizes:
                # 创建容器模拟路线列表项
                container = QWidget()
                container.setFixedHeight(60)
                container.setStyleSheet("""
                    QWidget {
                        background-color: #4A90E2;
                        border-radius: 4px;
                        margin: 2px;
                    }
                """)
                
                container_layout = QHBoxLayout(container)
                container_layout.setContentsMargins(8, 8, 8, 8)
                
                # 模拟路线信息
                info_label = QLabel(f"路线信息\n{size}px图标")
                info_label.setStyleSheet("color: white; font-size: 12px;")
                container_layout.addWidget(info_label)
                
                container_layout.addStretch()
                
                # 导出按钮
                export_button = QPushButton()
                export_button.setFixedSize(size + 4, size + 4)  # 按钮比图标稍大
                
                # 加载图标
                full_path = resource_path(icon_path)
                if os.path.exists(full_path):
                    export_button.setIcon(QIcon(full_path))
                    export_button.setIconSize(QSize(size, size))
                
                export_button.setToolTip(f'导出GPX文件 ({size}px)')
                export_button.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(255, 255, 255, 0.1);
                        border: 1px solid rgba(255, 255, 255, 0.3);
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: rgba(255, 255, 255, 0.2);
                        border: 1px solid rgba(255, 255, 255, 0.5);
                    }
                    QPushButton:pressed {
                        background-color: rgba(255, 255, 255, 0.3);
                        border: 1px solid rgba(255, 255, 255, 0.7);
                    }
                """)
                
                # 垂直居中对齐
                container_layout.addWidget(export_button, 0, Qt.AlignVCenter)
                
                size_layout.addWidget(container)
            
            layout.addLayout(size_layout)
        
        # 添加弹簧
        layout.addStretch()
        
        # 说明文字
        info_label = QLabel("""
        测试说明：
        1. 上方显示普通版本的Downloading图标（黑色）
        2. 下方显示白色版本的Downloading图标（适用于蓝色背景）
        3. 每个图标都在模拟的路线列表项中垂直居中显示
        4. 不同大小的图标用于测试最佳显示效果
        """)
        info_label.setStyleSheet("color: #666; font-size: 12px; margin: 10px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    window = TestDownloadingIcon()
    window.show()
    
    print("Downloading图标测试程序已启动")
    print("检查图标是否正确显示并垂直居中")
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
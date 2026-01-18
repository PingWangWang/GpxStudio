#!/usr/bin/env python3
"""
测试Loading图标显示效果的工具
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer
from ui.widgets.transform_animated_button import TransformAnimatedButton


class LoadingIconTestWindow(QMainWindow):
    """Loading图标测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Loading图标测试")
        self.setGeometry(100, 100, 400, 300)
        
        # 创建中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignCenter)
        
        # 添加说明标签
        label = QLabel("Loading图标测试")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        # 创建Loading按钮
        self.loading_button = TransformAnimatedButton('Loading')
        self.loading_button.setFixedSize(100, 100)  # 放大显示
        layout.addWidget(self.loading_button)
        
        # 添加控制说明
        control_label = QLabel("鼠标悬停查看动画效果\n点击开始/停止持续动画")
        control_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(control_label)
        
        # 连接点击事件
        self.loading_button.clicked.connect(self.toggle_animation)
        
        # 动画状态
        self.is_animating = False
    
    def toggle_animation(self):
        """切换动画状态"""
        if self.is_animating:
            self.loading_button.stop_animation()
            self.is_animating = False
            print("停止Loading动画")
        else:
            self.loading_button.start_animation()
            self.is_animating = True
            print("开始Loading动画")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    window = LoadingIconTestWindow()
    window.show()
    
    print("Loading图标测试启动")
    print("- 鼠标悬停查看动画效果")
    print("- 点击按钮开始/停止持续动画")
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
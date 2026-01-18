#!/usr/bin/env python3
"""
测试自定义日期时间选择器
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt5.QtCore import Qt, QDateTime
from ui.widgets.custom_datetime_edit import CustomDateTimeEdit
from ui.widgets.custom_datetime_picker import CustomDateTimePicker


class TestWindow(QMainWindow):
    """测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("自定义日期时间选择器测试")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(20)
        
        # 说明标签
        info_label = QLabel("测试自定义日期时间选择器")
        info_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(info_label)
        
        # 测试1：自定义日期时间编辑控件
        edit_label = QLabel("1. 自定义日期时间编辑控件（点击显示选择器）:")
        edit_label.setStyleSheet("font-size: 14px; color: #666;")
        layout.addWidget(edit_label)
        
        self.datetime_edit = CustomDateTimeEdit()
        self.datetime_edit.dateTimeChanged.connect(self.on_datetime_changed)
        layout.addWidget(self.datetime_edit)
        
        # 测试2：直接显示选择器
        picker_label = QLabel("2. 直接显示的日期时间选择器:")
        picker_label.setStyleSheet("font-size: 14px; color: #666;")
        layout.addWidget(picker_label)
        
        self.datetime_picker = CustomDateTimePicker()
        self.datetime_picker.dateTimeChanged.connect(self.on_picker_changed)
        layout.addWidget(self.datetime_picker)
        
        # 结果显示
        self.result_label = QLabel("选择结果将显示在这里")
        self.result_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 10px;
                font-size: 13px;
                color: #333;
            }
        """)
        layout.addWidget(self.result_label)
        
        # 测试说明
        instruction_label = QLabel("""
测试说明:
• 日历：双击日期确认选择，单击无响应
• 时间列表：双击时间确认选择，单击无响应
• 时间间隔：30分钟一个时间点
• 点击下拉箭头或输入框显示选择器
        """)
        instruction_label.setStyleSheet("font-size: 12px; color: #888; margin-top: 10px;")
        layout.addWidget(instruction_label)
    
    def on_datetime_changed(self, datetime):
        """日期时间编辑控件改变"""
        self.result_label.setText(f"编辑控件选择: {datetime.toString('yyyy-MM-dd hh:mm dddd')}")
        print(f"编辑控件选择: {datetime.toString('yyyy-MM-dd hh:mm dddd')}")
    
    def on_picker_changed(self, datetime):
        """日期时间选择器改变"""
        self.result_label.setText(f"选择器选择: {datetime.toString('yyyy-MM-dd hh:mm dddd')}")
        print(f"选择器选择: {datetime.toString('yyyy-MM-dd hh:mm dddd')}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    window = TestWindow()
    window.show()
    
    print("自定义日期时间选择器测试启动")
    print("测试功能:")
    print("1. 左侧日历双击选择日期")
    print("2. 右侧时间列表双击选择时间（30分钟间隔）")
    print("3. 单击无响应，只有双击才确认")
    print("4. 下拉编辑控件点击显示选择器")
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
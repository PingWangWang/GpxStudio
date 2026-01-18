#!/usr/bin/env python3
"""
测试路线规划面板ESC键关闭功能
"""

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QPushButton, QLabel)
from PyQt5.QtCore import Qt, pyqtSignal


class MockRoutePlanPanel(QWidget):
    """模拟路线规划面板"""
    
    cancel_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 设置窗口标志
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        # 设置焦点策略以接收键盘事件
        self.setFocusPolicy(Qt.StrongFocus)
        
        self._init_ui()
    
    def _init_ui(self):
        self.setStyleSheet("""
            MockRoutePlanPanel {
                background-color: #4A90E2;
                border-radius: 8px;
                border: 1px solid rgba(0, 0, 0, 0.15);
            }
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.9);
                color: #4A90E2;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 标题
        title_label = QLabel("路线规划面板")
        layout.addWidget(title_label)
        
        # 说明
        info_label = QLabel("按ESC键应该关闭此面板")
        info_label.setStyleSheet("QLabel { font-size: 12px; font-weight: normal; }")
        layout.addWidget(info_label)
        
        # 焦点状态显示
        self.focus_label = QLabel("焦点状态: 未知")
        self.focus_label.setStyleSheet("QLabel { font-size: 11px; font-weight: normal; color: rgba(255, 255, 255, 0.8); }")
        layout.addWidget(self.focus_label)
        
        # 关闭按钮
        close_button = QPushButton("关闭面板")
        close_button.clicked.connect(self._on_close_clicked)
        layout.addWidget(close_button)
        
        self.setFixedSize(300, 200)
        
        # 定时器更新焦点状态
        from PyQt5.QtCore import QTimer
        self.focus_timer = QTimer()
        self.focus_timer.timeout.connect(self._update_focus_status)
        self.focus_timer.start(100)  # 每100ms更新一次
    
    def _update_focus_status(self):
        """更新焦点状态显示"""
        if self.hasFocus():
            self.focus_label.setText("焦点状态: ✅ 有焦点")
        else:
            focused_widget = QApplication.focusWidget()
            if focused_widget:
                widget_name = focused_widget.__class__.__name__
                self.focus_label.setText(f"焦点状态: ❌ 无焦点 (当前: {widget_name})")
            else:
                self.focus_label.setText("焦点状态: ❌ 无焦点 (当前: None)")
    
    def _on_close_clicked(self):
        """关闭按钮点击"""
        self.hide()
        self.cancel_clicked.emit()
    
    def keyPressEvent(self, event):
        """键盘事件处理"""
        print(f"[面板] 接收到键盘事件: {event.key()}")
        if event.key() == Qt.Key_Escape:
            print("[面板] ESC键关闭面板")
            self.hide()
            self.cancel_clicked.emit()
            event.accept()
        else:
            super().keyPressEvent(event)
    
    def show_and_focus(self):
        """显示面板并设置焦点"""
        self.show()
        self.raise_()
        self.setFocus()
        print("[面板] 显示面板并设置焦点")
    
    def focusInEvent(self, event):
        """获得焦点事件"""
        print("[面板] 获得焦点")
        super().focusInEvent(event)
    
    def focusOutEvent(self, event):
        """失去焦点事件"""
        print("[面板] 失去焦点")
        super().focusOutEvent(event)


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("路线规划面板ESC键测试")
        self.setGeometry(100, 100, 600, 400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 说明
        info_label = QLabel("""
路线规划面板ESC键关闭功能测试：

问题：点击路线规划按钮弹出路线规划面板后，按下ESC按键，无法直接关闭该面板

解决方案：
1. 在路线规划面板初始化时设置焦点策略：setFocusPolicy(Qt.StrongFocus)
2. 在显示面板时调用setFocus()设置焦点
3. 确保keyPressEvent能正确处理ESC键

测试步骤：
1. 点击"显示路线规划面板"按钮
2. 观察面板的焦点状态
3. 按ESC键测试是否能关闭面板
        """)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 10px;
                font-size: 12px;
            }
        """)
        layout.addWidget(info_label)
        
        # 控制按钮
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        
        show_btn = QPushButton("显示路线规划面板")
        show_btn.clicked.connect(self.show_route_panel)
        button_layout.addWidget(show_btn)
        
        hide_btn = QPushButton("隐藏面板")
        hide_btn.clicked.connect(self.hide_route_panel)
        button_layout.addWidget(hide_btn)
        
        focus_btn = QPushButton("设置面板焦点")
        focus_btn.clicked.connect(self.set_panel_focus)
        button_layout.addWidget(focus_btn)
        
        layout.addWidget(button_container)
        
        # 状态标签
        self.status_label = QLabel("状态: 准备就绪")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #e8f5e8;
                border: 1px solid #4CAF50;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.status_label)
        
        # 创建路线规划面板
        self.route_panel = MockRoutePlanPanel(self)
        self.route_panel.cancel_clicked.connect(self.on_panel_closed)
        self.route_panel.hide()
    
    def show_route_panel(self):
        """显示路线规划面板"""
        self.status_label.setText("状态: 显示路线规划面板")
        
        # 设置面板位置（在主窗口中央）
        center_pos = self.geometry().center()
        panel_pos = center_pos - self.route_panel.rect().center()
        self.route_panel.move(panel_pos)
        
        # 显示并设置焦点
        self.route_panel.show_and_focus()
        
        print("[测试] 路线规划面板已显示")
    
    def hide_route_panel(self):
        """隐藏路线规划面板"""
        self.status_label.setText("状态: 隐藏面板")
        self.route_panel.hide()
        print("[测试] 路线规划面板已隐藏")
    
    def set_panel_focus(self):
        """设置面板焦点"""
        if self.route_panel.isVisible():
            self.route_panel.setFocus()
            self.status_label.setText("状态: 已设置面板焦点")
            print("[测试] 已设置面板焦点")
        else:
            self.status_label.setText("状态: 面板未显示，无法设置焦点")
            print("[测试] 面板未显示，无法设置焦点")
    
    def on_panel_closed(self):
        """面板关闭"""
        self.status_label.setText("状态: 面板已关闭")
        print("[测试] 面板已关闭")
    
    def keyPressEvent(self, event):
        """主窗口键盘事件"""
        print(f"[主窗口] 接收到键盘事件: {event.key()}")
        if event.key() == Qt.Key_Escape:
            self.status_label.setText("状态: 主窗口接收到ESC键")
            print("[主窗口] 接收到ESC键")
        super().keyPressEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = TestWindow()
    window.show()
    
    print("=== 路线规划面板ESC键测试 ===")
    print("1. 点击'显示路线规划面板'按钮")
    print("2. 观察面板的焦点状态")
    print("3. 按ESC键测试是否能关闭面板")
    print("4. 观察控制台输出")
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
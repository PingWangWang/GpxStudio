"""
滑块动画按钮组件
专门用于路线设置按钮的滑块移动动画
"""

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtSvg import QSvgRenderer
import os
from core.resource_path import resource_path
from ui.theme import theme


class SliderAnimatedButton(QPushButton):
    """支持滑块移动动画的按钮"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 动画属性
        self._animation_progress = 0.0  # 0.0 = normal, 1.0 = animate
        self._is_animating = False
        
        # 设置按钮属性
        self.setFixedSize(36, 36)
        theme.set_theme_stylesheet(self, """
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 6px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: __HOVER__;
            }
            QPushButton:pressed {
                background-color: __HOVER_STRONG__;
            }
        """)
        
        # 确保按钮可以接收鼠标事件
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_Hover, True)
        
        # 创建动画
        self._init_animations()
    
    def _init_animations(self):
        """初始化动画"""
        # 持续滑块动画
        self.slider_animation = QPropertyAnimation(self, b"animationProgress")
        self.slider_animation.setDuration(2000)  # 2秒完成一个周期
        self.slider_animation.setStartValue(0.0)
        self.slider_animation.setEndValue(1.0)
        self.slider_animation.setEasingCurve(QEasingCurve.InOutSine)
        self.slider_animation.setLoopCount(-1)  # 无限循环
        
        # 悬停/点击动画 - 使用更明显的缓动效果
        self.hover_animation = QPropertyAnimation(self, b"animationProgress")
        self.hover_animation.setDuration(600)
        self.hover_animation.setEasingCurve(QEasingCurve.OutBack)  # 更有弹性的动画效果
    
    @pyqtProperty(float)
    def animationProgress(self):
        """获取动画进度"""
        return self._animation_progress
    
    @animationProgress.setter
    def animationProgress(self, value):
        """设置动画进度"""
        old_value = self._animation_progress
        self._animation_progress = max(0.0, min(1.0, value))
        if abs(old_value - self._animation_progress) > 0.01:  # 只在有明显变化时打印
            print(f"[滑块按钮] 动画进度更新: {old_value:.2f} -> {self._animation_progress:.2f}")
        self.update()  # 触发重绘
    
    def start_animation(self):
        """开始持续滑块动画"""
        if not self._is_animating:
            self._is_animating = True
            self.slider_animation.start()
            print("[滑块按钮] 开始动画")
    
    def stop_animation(self):
        """停止持续滑块动画"""
        if self._is_animating:
            self._is_animating = False
            self.slider_animation.stop()
            
            # 平滑回到初始状态
            self.hover_animation.setStartValue(self._animation_progress)
            self.hover_animation.setEndValue(0.0)
            self.hover_animation.setDuration(500)
            self.hover_animation.start()
            print("[滑块按钮] 停止动画")
    
    def is_animating(self):
        """检查是否正在动画"""
        return self._is_animating
    
    def enterEvent(self, event):
        """鼠标进入事件 - 触发滑块动画但保持颜色不变"""
        super().enterEvent(event)
        if not self._is_animating:
            # 悬停时滑块移动到更明显的位置，但颜色保持深色
            self.hover_animation.stop()
            self.hover_animation.setStartValue(self._animation_progress)
            self.hover_animation.setEndValue(0.7)  # 更明显的移动
            self.hover_animation.setDuration(300)  # 更快的响应
            self.hover_animation.start()
            print(f"[滑块按钮] 鼠标进入，动画进度: {self._animation_progress} -> 0.7")
    
    def leaveEvent(self, event):
        """鼠标离开事件 - 滑块回到初始位置但保持颜色不变"""
        super().leaveEvent(event)
        if not self._is_animating:
            # 鼠标离开时回到初始位置，但颜色保持深色
            self.hover_animation.stop()
            self.hover_animation.setStartValue(self._animation_progress)
            self.hover_animation.setEndValue(0.0)
            self.hover_animation.setDuration(250)  # 稍快的回归
            self.hover_animation.start()
            print(f"[滑块按钮] 鼠标离开，动画进度: {self._animation_progress} -> 0.0")
    
    def mousePressEvent(self, event):
        """鼠标按下事件 - 滑块移动到终点但保持颜色不变"""
        super().mousePressEvent(event)
        if not self._is_animating:
            # 点击时快速移动滑块到终点，但颜色保持深色
            self.hover_animation.stop()
            self.hover_animation.setStartValue(self._animation_progress)
            self.hover_animation.setEndValue(1.0)
            self.hover_animation.setDuration(150)  # 更快的点击响应
            self.hover_animation.start()
            print(f"[滑块按钮] 鼠标按下，动画进度: {self._animation_progress} -> 1.0")
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件 - 如果鼠标仍在按钮上，回到悬停状态"""
        super().mouseReleaseEvent(event)
        if not self._is_animating and self.underMouse():
            # 如果鼠标仍在按钮上，回到悬停状态
            self.hover_animation.stop()
            self.hover_animation.setStartValue(self._animation_progress)
            self.hover_animation.setEndValue(0.7)
            self.hover_animation.setDuration(200)
            self.hover_animation.start()
            print(f"[滑块按钮] 鼠标释放，回到悬停状态: {self._animation_progress} -> 0.7")
    
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制按钮背景
        rect = self.rect()
        
        if self.isDown():
            painter.fillRect(rect, QColor(0, 0, 0, 25))
        elif self.underMouse():
            painter.fillRect(rect, QColor(0, 0, 0, 13))
        
        # 绘制滑块图标
        self._draw_sliders(painter, rect)
    
    def _draw_sliders(self, painter, rect):
        """绘制滑块图标"""
        # 设置绘制参数
        margin = 6
        icon_rect = rect.adjusted(margin, margin, -margin, -margin)
        
        # 缩放到图标区域
        scale_x = icon_rect.width() / 24.0
        scale_y = icon_rect.height() / 24.0
        
        painter.save()
        painter.translate(icon_rect.left(), icon_rect.top())
        painter.scale(scale_x, scale_y)
        
        # 设置画笔颜色，始终保持深色，与地图设置按钮一致
        # 不使用蓝色交互效果，保持视觉一致性
        color = QColor(32, 32, 32)  # 始终使用深色，不变化
        
        # 根据动画进度稍微调整线条粗细，让动画更明显
        line_width = 2.0 + (self._animation_progress * 0.5)  # 2.0 -> 2.5
        
        pen = QPen(color, line_width)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        
        # 根据动画进度计算滑块位置
        progress = self._animation_progress
        
        # 第一行滑块 (y=4)
        # normal: x2=14, x1=10  animate: x2=10, x1=5
        x2_1 = 14 - (14 - 10) * progress  # 14 -> 10
        x1_1 = 10 - (10 - 5) * progress   # 10 -> 5
        slider1_x = (x1_1 + x2_1) / 2     # 滑块中心位置
        
        # 绘制第一行
        painter.drawLine(21, 4, int(x2_1), 4)  # 右侧线段
        painter.drawLine(int(x1_1), 4, 3, 4)   # 左侧线段
        painter.drawLine(int(slider1_x), 2, int(slider1_x), 6)  # 滑块手柄
        
        # 第二行滑块 (y=12)
        # normal: x2=12, x1=8  animate: x2=18, x1=13
        x2_2 = 12 + (18 - 12) * progress  # 12 -> 18
        x1_2 = 8 + (13 - 8) * progress    # 8 -> 13
        slider2_x = (x1_2 + x2_2) / 2     # 滑块中心位置
        
        # 绘制第二行
        painter.drawLine(21, 12, int(x2_2), 12)  # 右侧线段
        painter.drawLine(int(x1_2), 12, 3, 12)   # 左侧线段
        painter.drawLine(int(slider2_x), 10, int(slider2_x), 14)  # 滑块手柄
        
        # 第三行滑块 (y=20)
        # normal: x2=12, x1=16  animate: x2=4, x1=8
        x2_3 = 12 - (12 - 4) * progress   # 12 -> 4
        x1_3 = 16 - (16 - 8) * progress   # 16 -> 8
        slider3_x = (x1_3 + x2_3) / 2     # 滑块中心位置
        
        # 绘制第三行
        painter.drawLine(int(x1_3), 20, 21, 20)  # 右侧线段
        painter.drawLine(3, 20, int(x2_3), 20)   # 左侧线段
        painter.drawLine(int(slider3_x), 18, int(slider3_x), 22)  # 滑块手柄
        
        painter.restore()


def create_slider_button(tooltip=None, parent=None):
    """
    创建滑块动画按钮的工厂函数
    
    Args:
        tooltip: 工具提示文本
        parent: 父组件
    
    Returns:
        SliderAnimatedButton: 配置好的按钮实例
    """
    button = SliderAnimatedButton(parent)
    
    if tooltip:
        button.setToolTip(tooltip)
    
    return button
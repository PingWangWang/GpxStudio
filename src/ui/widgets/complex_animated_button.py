"""
复杂动画按钮组件
用于复杂的多元素动画效果，如History等图标
"""

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QPainter, QColor, QPen, QPainterPath
from PyQt5.QtSvg import QSvgRenderer
import os
import math
from core.resource_path import resource_path


class ComplexAnimatedButton(QPushButton):
    """支持复杂动画的按钮"""
    
    def __init__(self, icon_name, parent=None):
        super().__init__(parent)
        
        self.icon_name = icon_name
        self._animation_progress = 0.0  # 0.0 = 初始状态, 1.0 = 动画状态
        self._is_animating = False
        
        # 设置按钮属性
        self.setFixedSize(36, 36)
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 6px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.05);
            }
            QPushButton:pressed {
                background-color: rgba(0, 0, 0, 0.1);
            }
        """)
        
        # 确保按钮可以接收鼠标事件
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_Hover, True)
        
        # 创建动画
        self._init_animations()
    
    def _init_animations(self):
        """初始化动画"""
        # 持续复杂动画
        self.complex_animation = QPropertyAnimation(self, b"animationProgress")
        self.complex_animation.setDuration(3000)  # 更长的动画周期
        self.complex_animation.setStartValue(0.0)
        self.complex_animation.setEndValue(1.0)
        self.complex_animation.setEasingCurve(QEasingCurve.InOutSine)
        self.complex_animation.setLoopCount(-1)
        
        # 悬停/点击动画
        self.hover_animation = QPropertyAnimation(self, b"animationProgress")
        self.hover_animation.setDuration(600)
        self.hover_animation.setEasingCurve(QEasingCurve.OutBack)
    
    @pyqtProperty(float)
    def animationProgress(self):
        """获取动画进度"""
        return self._animation_progress
    
    @animationProgress.setter
    def animationProgress(self, value):
        """设置动画进度"""
        self._animation_progress = max(0.0, min(1.0, value))
        self.update()
    
    def start_animation(self):
        """开始持续复杂动画"""
        if not self._is_animating:
            self._is_animating = True
            self.complex_animation.start()
    
    def stop_animation(self):
        """停止持续复杂动画"""
        if self._is_animating:
            self._is_animating = False
            self.complex_animation.stop()
            
            # 平滑回到初始状态
            self.hover_animation.setStartValue(self._animation_progress)
            self.hover_animation.setEndValue(0.0)
            self.hover_animation.setDuration(400)
            self.hover_animation.start()
    
    def is_animating(self):
        """检查是否正在动画"""
        return self._is_animating
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        super().enterEvent(event)
        if not self._is_animating:
            # 悬停时触发复杂动画
            self.hover_animation.stop()
            self.hover_animation.setStartValue(self._animation_progress)
            self.hover_animation.setEndValue(0.7)
            self.hover_animation.setDuration(400)
            self.hover_animation.start()
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        super().leaveEvent(event)
        if not self._is_animating:
            # 鼠标离开时回到初始状态
            self.hover_animation.stop()
            self.hover_animation.setStartValue(self._animation_progress)
            self.hover_animation.setEndValue(0.0)
            self.hover_animation.setDuration(300)
            self.hover_animation.start()
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        super().mousePressEvent(event)
        if not self._is_animating:
            # 点击时快速动画
            self.hover_animation.stop()
            self.hover_animation.setStartValue(self._animation_progress)
            self.hover_animation.setEndValue(1.0)
            self.hover_animation.setDuration(200)
            self.hover_animation.start()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        super().mouseReleaseEvent(event)
        if not self._is_animating and self.underMouse():
            # 如果鼠标仍在按钮上，回到悬停状态
            self.hover_animation.stop()
            self.hover_animation.setStartValue(self._animation_progress)
            self.hover_animation.setEndValue(0.7)
            self.hover_animation.setDuration(250)
            self.hover_animation.start()
    
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
        
        # 绘制图标
        self._draw_icon(painter, rect)
    
    def _draw_icon(self, painter, rect):
        """绘制图标"""
        # 设置绘制参数
        margin = 6
        icon_rect = rect.adjusted(margin, margin, -margin, -margin)
        
        # 缩放到图标区域
        scale_x = icon_rect.width() / 24.0
        scale_y = icon_rect.height() / 24.0
        
        painter.save()
        painter.translate(icon_rect.left(), icon_rect.top())
        painter.scale(scale_x, scale_y)
        
        # 设置画笔颜色，始终保持深色
        color = QColor(32, 32, 32)
        pen = QPen(color, 2)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        
        # 根据图标类型绘制不同的图标
        if self.icon_name == 'History':
            self._draw_history_icon(painter)
        
        painter.restore()
    
    def _draw_history_icon(self, painter):
        """绘制历史图标"""
        progress = self._animation_progress
        
        # 绘制圆形和箭头（带旋转动画）
        painter.save()
        
        # 箭头旋转动画
        arrow_rotation = -50 * progress
        painter.translate(12, 12)
        painter.rotate(arrow_rotation)
        painter.translate(-12, -12)
        
        # 绘制圆弧和箭头
        # M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8
        painter.drawArc(3, 3, 18, 18, 0, 270 * 16)  # 3/4圆弧
        
        # 绘制箭头
        painter.drawLine(3, 3, 3, 8)   # 垂直线
        painter.drawLine(3, 8, 8, 8)   # 水平线
        
        painter.restore()
        
        # 绘制时钟指针（带旋转动画）
        painter.save()
        painter.translate(12, 12)
        
        # 时针旋转动画（完整圆周）
        hour_rotation = -360 * progress
        painter.rotate(hour_rotation)
        painter.drawLine(0, 0, 0, -5)  # 时针
        
        painter.restore()
        
        # 分针旋转动画（较小角度）
        painter.save()
        painter.translate(12, 12)
        
        minute_rotation = -45 * progress
        painter.rotate(minute_rotation)
        painter.drawLine(0, 0, 4, 2)   # 分针
        
        painter.restore()


def create_complex_button(icon_name, tooltip=None, parent=None):
    """
    创建复杂动画按钮的工厂函数
    
    Args:
        icon_name: 图标名称 ('History')
        tooltip: 工具提示文本
        parent: 父组件
    
    Returns:
        ComplexAnimatedButton: 配置好的按钮实例
    """
    button = ComplexAnimatedButton(icon_name, parent)
    
    if tooltip:
        button.setToolTip(tooltip)
    
    return button
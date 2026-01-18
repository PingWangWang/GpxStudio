"""
位置动画按钮组件
专门用于Location图标的Y轴跳跃动画 + SVG渲染
"""

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtSvg import QSvgRenderer
import os
from core.resource_path import resource_path


class LocationAnimatedButton(QPushButton):
    """支持Y轴跳跃动画的Location按钮"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 动画属性
        self._animation_progress = 0.0  # 0.0 = 初始状态, 1.0 = 动画状态
        self._is_animating = False
        
        # 加载SVG渲染器
        self.svg_renderer = None
        self._load_svg()
        
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
    
    def _load_svg(self):
        """加载Location SVG文件"""
        svg_path = resource_path('res/icons/Location.svg')
        if os.path.exists(svg_path):
            self.svg_renderer = QSvgRenderer(svg_path)
            print(f"[Location按钮] 成功加载SVG: {svg_path}")
        else:
            print(f"[Location按钮] SVG文件不存在: {svg_path}")
    
    def _init_animations(self):
        """初始化动画"""
        # 持续跳跃动画
        self.jump_animation = QPropertyAnimation(self, b"animationProgress")
        self.jump_animation.setDuration(2000)  # 2秒完成一个周期
        self.jump_animation.setStartValue(0.0)
        self.jump_animation.setEndValue(1.0)
        self.jump_animation.setEasingCurve(QEasingCurve.InOutSine)
        self.jump_animation.setLoopCount(-1)  # 无限循环
        
        # 悬停/点击动画
        self.hover_animation = QPropertyAnimation(self, b"animationProgress")
        self.hover_animation.setDuration(500)
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
        """开始持续跳跃动画"""
        if not self._is_animating:
            self._is_animating = True
            self.jump_animation.start()
    
    def stop_animation(self):
        """停止持续跳跃动画"""
        if self._is_animating:
            self._is_animating = False
            self.jump_animation.stop()
            
            # 平滑回到初始状态
            self.hover_animation.setStartValue(self._animation_progress)
            self.hover_animation.setEndValue(0.0)
            self.hover_animation.setDuration(300)
            self.hover_animation.start()
    
    def is_animating(self):
        """检查是否正在动画"""
        return self._is_animating
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        super().enterEvent(event)
        if not self._is_animating:
            # 悬停时触发跳跃动画
            self.hover_animation.stop()
            self.hover_animation.setStartValue(self._animation_progress)
            self.hover_animation.setEndValue(0.7)
            self.hover_animation.setDuration(300)
            self.hover_animation.start()
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        super().leaveEvent(event)
        if not self._is_animating:
            # 鼠标离开时回到初始状态
            self.hover_animation.stop()
            self.hover_animation.setStartValue(self._animation_progress)
            self.hover_animation.setEndValue(0.0)
            self.hover_animation.setDuration(250)
            self.hover_animation.start()
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        super().mousePressEvent(event)
        if not self._is_animating:
            # 点击时快速跳跃
            self.hover_animation.stop()
            self.hover_animation.setStartValue(self._animation_progress)
            self.hover_animation.setEndValue(1.0)
            self.hover_animation.setDuration(150)
            self.hover_animation.start()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        super().mouseReleaseEvent(event)
        if not self._is_animating and self.underMouse():
            # 如果鼠标仍在按钮上，回到悬停状态
            self.hover_animation.stop()
            self.hover_animation.setStartValue(self._animation_progress)
            self.hover_animation.setEndValue(0.7)
            self.hover_animation.setDuration(200)
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
        
        # 绘制SVG图标（带跳跃动画）
        if self.svg_renderer and self.svg_renderer.isValid():
            self._draw_animated_svg(painter, rect)
    
    def _draw_animated_svg(self, painter, rect):
        """绘制带动画的SVG图标"""
        progress = self._animation_progress
        
        # 计算Y轴跳跃偏移
        # 基于TSX动画: y: [0, -5, -3], times: [0, 0.6, 1]
        if progress <= 0.6:
            # 0 -> -5 (前60%时间)
            y_offset = -5 * (progress / 0.6)
        else:
            # -5 -> -3 (后40%时间)
            y_offset = -5 + 2 * ((progress - 0.6) / 0.4)
        
        # 设置绘制参数 - Location图标需要更小的边距以显示更大
        margin = 3  # 减小边距，从6改为3
        icon_rect = rect.adjusted(margin, margin, -margin, -margin)
        
        # 应用Y轴偏移
        painter.save()
        painter.translate(0, y_offset)
        
        # 渲染SVG
        self.svg_renderer.render(painter, QRectF(icon_rect))
        
        painter.restore()


def create_location_button(tooltip=None, parent=None):
    """
    创建Location动画按钮的工厂函数
    
    Args:
        tooltip: 工具提示文本
        parent: 父组件
    
    Returns:
        LocationAnimatedButton: 配置好的按钮实例
    """
    button = LocationAnimatedButton(parent)
    
    if tooltip:
        button.setToolTip(tooltip)
    
    return button
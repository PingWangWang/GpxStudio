"""
SVG动画按钮组件
支持加载SVG图标并应用旋转动画，兼容Lucide风格图标
"""

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
from PyQt5.QtSvg import QSvgRenderer
import os
from core.resource_path import resource_path
from ui.theme import theme


class SvgAnimatedButton(QPushButton):
    """支持SVG图标的动画按钮"""
    
    def __init__(self, svg_path=None, parent=None):
        super().__init__(parent)
        
        # 动画属性
        self._rotation = 0
        self._is_animating = False
        self._svg_renderer = None
        self._svg_path = svg_path
        
        # 设置按钮属性
        self.setFixedSize(36, 36)
        theme.set_theme_stylesheet(self, """
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: __HOVER__;
            }
            QPushButton:pressed {
                background-color: __HOVER_STRONG__;
            }
        """)
        
        # 初始化SVG渲染器
        self._init_svg_renderer()
        
        # 创建旋转动画
        self._init_animations()
    
    def _init_svg_renderer(self):
        """初始化SVG渲染器"""
        if self._svg_path and os.path.exists(self._svg_path):
            self._svg_renderer = QSvgRenderer(self._svg_path)
            print(f"[SVG按钮] 加载SVG图标: {self._svg_path}")
        else:
            print(f"[SVG按钮] SVG文件不存在: {self._svg_path}")
    
    def _init_animations(self):
        """初始化动画"""
        # 持续旋转动画
        self.rotation_animation = QPropertyAnimation(self, b"rotation")
        self.rotation_animation.setDuration(2000)  # 2秒完成一圈
        self.rotation_animation.setStartValue(0)
        self.rotation_animation.setEndValue(360)
        self.rotation_animation.setEasingCurve(QEasingCurve.Linear)
        self.rotation_animation.setLoopCount(-1)  # 无限循环
        
        # 悬停/点击动画
        self.hover_animation = QPropertyAnimation(self, b"rotation")
        self.hover_animation.setDuration(600)
        self.hover_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    @pyqtProperty(float)
    def rotation(self):
        """获取旋转角度"""
        return self._rotation
    
    @rotation.setter
    def rotation(self, value):
        """设置旋转角度"""
        self._rotation = value % 360
        self.update()  # 触发重绘
    
    def set_svg_path(self, svg_path):
        """设置SVG文件路径"""
        self._svg_path = svg_path
        self._init_svg_renderer()
        self.update()
    
    def start_animation(self):
        """开始持续旋转动画"""
        if not self._is_animating:
            self._is_animating = True
            self.rotation_animation.start()
            print("[SVG按钮] 开始动画")
    
    def stop_animation(self):
        """停止持续旋转动画"""
        if self._is_animating:
            self._is_animating = False
            self.rotation_animation.stop()
            
            # 平滑回到0度
            self.hover_animation.setStartValue(self._rotation)
            self.hover_animation.setEndValue(0)
            self.hover_animation.setDuration(500)
            self.hover_animation.start()
            print("[SVG按钮] 停止动画")
    
    def is_animating(self):
        """检查是否正在动画"""
        return self._is_animating
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        super().enterEvent(event)
        if not self._is_animating:
            # 悬停时旋转180度（模拟TSX中的效果）
            start_rotation = self._rotation
            end_rotation = start_rotation + 180
            
            self.hover_animation.stop()
            self.hover_animation.setStartValue(start_rotation)
            self.hover_animation.setEndValue(end_rotation)
            self.hover_animation.setDuration(600)  # 与TSX中的spring动画类似
            self.hover_animation.start()
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        super().leaveEvent(event)
        if not self._is_animating:
            # 鼠标离开时回到原位
            start_rotation = self._rotation
            end_rotation = 0
            
            self.hover_animation.stop()
            self.hover_animation.setStartValue(start_rotation)
            self.hover_animation.setEndValue(end_rotation)
            self.hover_animation.setDuration(400)
            self.hover_animation.start()
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        super().mousePressEvent(event)
        if not self._is_animating:
            # 点击时快速旋转
            start_rotation = self._rotation
            end_rotation = start_rotation + 90
            
            self.hover_animation.stop()
            self.hover_animation.setStartValue(start_rotation)
            self.hover_animation.setEndValue(end_rotation)
            self.hover_animation.setDuration(200)
            self.hover_animation.start()
    
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制按钮背景
        rect = self.rect()
        
        if self.isDown():
            painter.fillRect(rect, QColor(224, 224, 224))
        elif self.underMouse():
            painter.fillRect(rect, QColor(240, 240, 240))
        else:
            painter.fillRect(rect, QColor(255, 255, 255, 0))  # 透明
        
        # 绘制SVG图标
        if self._svg_renderer and self._svg_renderer.isValid():
            # 计算SVG绘制区域，确保居中
            margin = 6
            size = min(rect.width(), rect.height()) - 2 * margin
            
            # 计算居中位置
            center_x = rect.center().x()
            center_y = rect.center().y()
            
            svg_rect = rect.__class__(
                center_x - size // 2,
                center_y - size // 2,
                size,
                size
            )
            
            # 如果有旋转，应用变换
            if self._rotation != 0:
                painter.save()
                painter.translate(center_x, center_y)
                painter.rotate(self._rotation)
                painter.translate(-center_x, -center_y)
            
            # 渲染SVG
            from PyQt5.QtCore import QRectF
            svg_rectf = QRectF(svg_rect)
            self._svg_renderer.render(painter, svg_rectf)
            
            # 恢复变换状态
            if self._rotation != 0:
                painter.restore()
        else:
            # 备用：绘制Unicode齿轮字符
            center = rect.center()
            
            # 如果有旋转，应用变换
            if self._rotation != 0:
                painter.save()
                painter.translate(center.x(), center.y())
                painter.rotate(self._rotation)
                painter.translate(-center.x(), -center.y())
            
            # 设置文字颜色
            color = QColor(102, 102, 102)
            if self.isDown():
                color = QColor(46, 91, 186)
            elif self.underMouse():
                color = QColor(74, 144, 226)
            
            painter.setPen(color)
            
            # 绘制备用图标
            font = self.font()
            font.setPixelSize(16)
            painter.setFont(font)
            
            text_rect = rect.adjusted(0, -1, 0, -1)
            painter.drawText(text_rect, Qt.AlignCenter, "⚙")
            
            # 恢复变换状态
            if self._rotation != 0:
                painter.restore()


class LucideSvgButton(SvgAnimatedButton):
    """专门用于Lucide风格图标的按钮"""
    
    def __init__(self, icon_name, parent=None):
        """
        初始化Lucide风格按钮
        
        Args:
            icon_name: 图标名称，如 'cog', 'settings', 'user' 等
            parent: 父组件
        """
        self.icon_name = icon_name
        svg_path = resource_path(f'res/icons/{icon_name}.svg')
        super().__init__(svg_path, parent)
        
        # Lucide风格的颜色配置
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
    
    def paintEvent(self, event):
        """重写绘制事件以支持Lucide风格"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制按钮背景（圆角）
        rect = self.rect()
        
        if self.isDown():
            painter.fillRect(rect, QColor(0, 0, 0, 25))  # 10% 黑色
        elif self.underMouse():
            painter.fillRect(rect, QColor(0, 0, 0, 13))  # 5% 黑色
        
        # 绘制SVG图标
        if self._svg_renderer and self._svg_renderer.isValid():
            # 计算SVG绘制区域，确保居中
            margin = 6
            size = min(rect.width(), rect.height()) - 2 * margin
            
            # 计算居中位置
            center_x = rect.center().x()
            center_y = rect.center().y()
            
            svg_rect = rect.__class__(
                center_x - size // 2,
                center_y - size // 2,
                size,
                size
            )
            
            # 如果有旋转，应用变换
            if self._rotation != 0:
                painter.save()
                painter.translate(center_x, center_y)
                painter.rotate(self._rotation)
                painter.translate(-center_x, -center_y)
            
            # 渲染SVG
            from PyQt5.QtCore import QRectF
            svg_rectf = QRectF(svg_rect)
            self._svg_renderer.render(painter, svg_rectf)
            
            # 恢复变换状态
            if self._rotation != 0:
                painter.restore()
        else:
            # 备用方案
            super().paintEvent(event)


def create_icon_button(svg_path=None, tooltip=None, size=36, parent=None):
    """
    创建SVG图标按钮的工厂函数
    
    Args:
        svg_path: SVG文件路径
        tooltip: 工具提示文本
        size: 按钮大小
        parent: 父组件
    
    Returns:
        SvgAnimatedButton: 配置好的按钮实例
    """
    button = SvgAnimatedButton(svg_path, parent)
    button.setFixedSize(size, size)
    
    if tooltip:
        button.setToolTip(tooltip)
    
    return button


def create_lucide_button(icon_name, tooltip=None, parent=None):
    """
    创建Lucide风格按钮的工厂函数
    
    Args:
        icon_name: 图标名称
        tooltip: 工具提示文本
        parent: 父组件
    
    Returns:
        LucideSvgButton: 配置好的按钮实例
    """
    button = LucideSvgButton(icon_name, parent)
    
    if tooltip:
        button.setToolTip(tooltip)
    
    return button
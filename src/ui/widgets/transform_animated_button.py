"""
变换动画按钮组件
用于旋转、缩放、位移等变换动画效果，如Search、Location、ZoomBig、Loading等图标
"""

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QPainter, QColor, QPen, QTransform
from PyQt5.QtSvg import QSvgRenderer
import os
import math
from core.resource_path import resource_path
from ui.theme import theme


class TransformAnimatedButton(QPushButton):
    """支持变换动画的按钮"""

    def __init__(self, icon_name, parent=None):
        super().__init__(parent)

        self.icon_name = icon_name
        self._animation_progress = 0.0  # 0.0 = 初始状态, 1.0 = 动画状态
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
        # 持续变换动画
        self.transform_animation = QPropertyAnimation(self, b"animationProgress")
        self.transform_animation.setDuration(2000)
        self.transform_animation.setStartValue(0.0)
        self.transform_animation.setEndValue(1.0)
        self.transform_animation.setEasingCurve(QEasingCurve.InOutSine)
        self.transform_animation.setLoopCount(-1)

        # 悬停/点击动画
        self.hover_animation = QPropertyAnimation(self, b"animationProgress")
        self.hover_animation.setDuration(400)
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
        """开始持续变换动画"""
        if not self._is_animating:
            self._is_animating = True
            self.transform_animation.start()

    def stop_animation(self):
        """停止持续变换动画"""
        if self._is_animating:
            self._is_animating = False
            self.transform_animation.stop()

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
            # 悬停时触发变换动画
            self.hover_animation.stop()
            self.hover_animation.setStartValue(self._animation_progress)
            self.hover_animation.setEndValue(0.6)
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
            # 点击时快速变换
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
            self.hover_animation.setEndValue(0.6)
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

        # 绘制图标
        self._draw_icon(painter, rect)

    def _draw_icon(self, painter, rect):
        """绘制图标"""
        # 设置绘制参数 - ZoomBig和ZoomSmall图标需要更小的边距
        margin = 3 if self.icon_name in ['ZoomBig', 'ZoomSmall'] else 6
        icon_rect = rect.adjusted(margin, margin, -margin, -margin)

        # 计算中心点
        center_x = icon_rect.center().x()
        center_y = icon_rect.center().y()

        # 缩放到图标区域
        scale_x = icon_rect.width() / 24.0
        scale_y = icon_rect.height() / 24.0

        painter.save()

        # 应用变换
        self._apply_transform(painter, center_x, center_y, scale_x, scale_y)

        # 设置画笔颜色，始终保持深色
        color = QColor(32, 32, 32)
        pen = QPen(color, 2)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)

        # 根据图标类型绘制不同的图标
        if self.icon_name == 'Search':
            self._draw_search_icon(painter)
        elif self.icon_name == 'ZoomBig':
            self._draw_zoom_big_icon(painter)
        elif self.icon_name == 'ZoomSmall':
            self._draw_zoom_small_icon(painter)
        elif self.icon_name == 'Loading':
            self._draw_loading_icon(painter)

        painter.restore()

    def _apply_transform(self, painter, center_x, center_y, scale_x, scale_y):
        """应用变换"""
        progress = self._animation_progress

        # 移动到中心点
        painter.translate(center_x, center_y)

        # 应用缩放
        painter.scale(scale_x, scale_y)

        # 根据图标类型应用不同的变换
        if self.icon_name == 'Search':
            # 搜索图标：轻微的位移动画
            offset_x = progress * -3
            offset_y = progress * -4 * math.sin(progress * math.pi)
            painter.translate(offset_x, offset_y)

        elif self.icon_name == 'ZoomBig':
            # 放大图标：旋转动画
            rotation = progress * 180
            painter.rotate(rotation)

        elif self.icon_name == 'ZoomSmall':
            # 缩小图标：旋转动画（与ZoomBig一致）
            rotation = progress * 180
            painter.rotate(rotation)

        elif self.icon_name == 'Loading':
            # 加载图标：旋转动画 (TSX中是50度旋转)
            rotation = progress * 50
            painter.rotate(rotation)

        # 移动到绘制原点
        painter.translate(-12, -12)

    def _draw_search_icon(self, painter):
        """绘制搜索图标"""
        # 绘制圆形
        painter.drawEllipse(3, 3, 16, 16)  # cx=11, cy=11, r=8 -> 3,3,16,16

        # 绘制搜索柄
        painter.drawLine(17, 17, 21, 21)  # m21 21-4.3-4.3 -> 16.7,16.7 to 21,21

    def _draw_zoom_big_icon(self, painter):
        """绘制放大图标"""
        # 绘制加号
        painter.drawLine(5, 12, 19, 12)  # 水平线
        painter.drawLine(12, 5, 12, 19)  # 垂直线

    def _draw_zoom_small_icon(self, painter):
        """绘制缩小图标"""
        # 绘制减号
        painter.drawLine(5, 12, 19, 12)  # 水平线

    def _draw_loading_icon(self, painter):
        """绘制加载图标"""
        # 根据SVG路径绘制Loading图标
        # 第一个路径: M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8
        # 这是一个从右侧开始的圆弧，逆时针到上方

        # 绘制主圆弧 (从0度开始，逆时针270度)
        # 圆心在(12,12)，半径9
        # Qt的角度：0度=3点钟方向，正值=逆时针
        painter.drawArc(3, 3, 18, 18, 0 * 16, -270 * 16)

        # 第二个路径: M21 3v5h-5 (箭头)
        # 从(21,3)开始，垂直向下5个单位到(21,8)，然后水平向左5个单位到(16,8)
        painter.drawLine(21, 3, 21, 8)   # 垂直线
        painter.drawLine(16, 8, 21, 8)   # 水平线


def create_transform_button(icon_name, tooltip=None, parent=None):
    """
    创建变换动画按钮的工厂函数

    Args:
        icon_name: 图标名称 ('Search', 'Location', 'ZoomBig', 'Loading')
        tooltip: 工具提示文本
        parent: 父组件

    Returns:
        TransformAnimatedButton: 配置好的按钮实例
    """
    button = TransformAnimatedButton(icon_name, parent)

    if tooltip:
        button.setToolTip(tooltip)

    return button
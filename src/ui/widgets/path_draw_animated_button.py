"""
路径绘制动画按钮组件
用于路径逐步绘制的动画效果，如Cancel、Yes、Route等图标
"""

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QPainter, QColor, QPen, QPainterPath
from PyQt5.QtSvg import QSvgRenderer
import os
from core.resource_path import resource_path
from ui.theme import theme


class PathDrawAnimatedButton(QPushButton):
    """支持路径绘制动画的按钮"""

    def __init__(self, icon_name, parent=None):
        super().__init__(parent)

        self.icon_name = icon_name
        self._animation_progress = 1.0  # 1.0 = 完全绘制, 0.0 = 未绘制
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
        # 路径绘制动画（一次性，与TypeScript保持一致）
        self.path_animation = QPropertyAnimation(self, b"animationProgress")
        self.path_animation.setDuration(800)  # 与TypeScript的delay时间匹配
        self.path_animation.setStartValue(0.0)
        self.path_animation.setEndValue(1.0)
        self.path_animation.setEasingCurve(QEasingCurve.OutCubic)

        # 悬停/点击动画
        self.hover_animation = QPropertyAnimation(self, b"animationProgress")
        self.hover_animation.setDuration(400)
        self.hover_animation.setEasingCurve(QEasingCurve.OutCubic)

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
        """开始持续路径绘制动画"""
        if not self._is_animating:
            self._is_animating = True
            self.path_animation.start()

    def stop_animation(self):
        """停止持续路径绘制动画"""
        if self._is_animating:
            self._is_animating = False
            self.path_animation.stop()

            # 平滑回到完全绘制状态
            self.hover_animation.setStartValue(self._animation_progress)
            self.hover_animation.setEndValue(1.0)
            self.hover_animation.setDuration(300)
            self.hover_animation.start()

    def is_animating(self):
        """检查是否正在动画"""
        return self._is_animating

    def enterEvent(self, event):
        """鼠标进入事件"""
        super().enterEvent(event)
        if not self._is_animating:
            # 悬停时触发路径绘制动画（与TypeScript的animate状态一致）
            self.path_animation.stop()
            self.path_animation.setStartValue(0.0)
            self.path_animation.setEndValue(1.0)
            self.path_animation.start()

    def leaveEvent(self, event):
        """鼠标离开事件"""
        super().leaveEvent(event)
        if not self._is_animating:
            # 鼠标离开时回到normal状态（完全绘制）
            self.path_animation.stop()
            self.hover_animation.stop()
            self.hover_animation.setStartValue(self._animation_progress)
            self.hover_animation.setEndValue(1.0)
            self.hover_animation.setDuration(300)
            self.hover_animation.start()

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        super().mousePressEvent(event)
        # 按下时不做特殊处理，保持当前动画状态

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        super().mouseReleaseEvent(event)
        # 释放时不做特殊处理，保持当前动画状态

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

        # 根据图标类型绘制不同的路径
        if self.icon_name == 'Cancel':
            self._draw_cancel_paths(painter)
        elif self.icon_name == 'Yes':
            self._draw_yes_paths(painter)
        elif self.icon_name == 'Route':
            self._draw_route_paths(painter)

        painter.restore()

    def _draw_cancel_paths(self, painter):
        """绘制取消图标的路径"""
        progress = self._animation_progress

        # 第一条路径: M18 6 L6 18
        if progress > 0:
            path1_progress = min(1.0, progress * 2)  # 前半段动画
            x1, y1 = 18, 6
            x2, y2 = 6, 18
            end_x = x1 + (x2 - x1) * path1_progress
            end_y = y1 + (y2 - y1) * path1_progress
            painter.drawLine(x1, y1, int(end_x), int(end_y))

        # 第二条路径: M6 6 L18 18 (延迟绘制)
        if progress > 0.5:
            path2_progress = min(1.0, (progress - 0.5) * 2)  # 后半段动画
            x1, y1 = 6, 6
            x2, y2 = 18, 18
            end_x = x1 + (x2 - x1) * path2_progress
            end_y = y1 + (y2 - y1) * path2_progress
            painter.drawLine(x1, y1, int(end_x), int(end_y))

    def _draw_yes_paths(self, painter):
        """绘制确认图标的路径"""
        progress = self._animation_progress

        # 勾选路径: M4 12 L9 17 L20 6
        if progress > 0:
            # 第一段: M4 12 L9 17
            if progress <= 0.5:
                segment_progress = progress * 2
                x1, y1 = 4, 12
                x2, y2 = 9, 17
                end_x = x1 + (x2 - x1) * segment_progress
                end_y = y1 + (y2 - y1) * segment_progress
                painter.drawLine(x1, y1, int(end_x), int(end_y))
            else:
                # 绘制完整的第一段
                painter.drawLine(4, 12, 9, 17)

                # 第二段: L9 17 L20 6
                segment_progress = (progress - 0.5) * 2
                x1, y1 = 9, 17
                x2, y2 = 20, 6
                end_x = x1 + (x2 - x1) * segment_progress
                end_y = y1 + (y2 - y1) * segment_progress
                painter.drawLine(x1, y1, int(end_x), int(end_y))

    def _draw_route_paths(self, painter):
        """绘制路线图标的路径"""
        progress = self._animation_progress

        # Route图标使用路径长度动画，每个元素有不同的延迟
        # 圆形元素 (custom=0, 无延迟)
        circles = [
            (12, 4.5, 2.5),    # 顶部圆点
            (4.5, 12, 2.5),    # 左侧圆点
            (19.5, 12, 2.5),   # 右侧圆点
            (12, 19.5, 2.5),   # 底部圆点
        ]

        # 路径元素 (custom=1,2,3, 有延迟)
        paths = [
            (10.2, 6.3, 6.3, 10.2, 1),    # 左上连线 (custom=1, delay=0.15)
            (7, 12, 17, 12, 2),            # 水平连线 (custom=2, delay=0.30)
            (13.8, 17.7, 17.7, 13.8, 3),  # 右下连线 (custom=3, delay=0.45)
        ]

        # 设置基础画笔
        base_color = QColor(32, 32, 32)

        # 绘制圆形 (custom=0, 无延迟)
        # 透明度动画：opacity: [0, 1], delay: 0.1 * 0 = 0
        circle_alpha = int(255 * min(1.0, progress))
        if circle_alpha > 0:
            pen = QPen(QColor(32, 32, 32, circle_alpha), 2)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)

            for cx, cy, r in circles:
                painter.drawEllipse(int(cx - r), int(cy - r), int(r * 2), int(r * 2))

        # 绘制路径 (custom=1,2,3, 有延迟)
        for x1, y1, x2, y2, custom in paths:
            # 计算延迟
            path_delay = 0.15 * custom
            opacity_delay = 0.1 * custom

            # 路径长度动画
            if progress > path_delay:
                path_progress = min(1.0, (progress - path_delay) / (1.0 - path_delay))
                end_x = x1 + (x2 - x1) * path_progress
                end_y = y1 + (y2 - y1) * path_progress

                # 透明度动画
                if progress > opacity_delay:
                    alpha_progress = min(1.0, (progress - opacity_delay) / (1.0 - opacity_delay))
                    alpha = int(255 * alpha_progress)

                    if alpha > 0:
                        pen = QPen(QColor(32, 32, 32, alpha), 2)
                        pen.setCapStyle(Qt.RoundCap)
                        pen.setJoinStyle(Qt.RoundJoin)
                        painter.setPen(pen)
                        painter.drawLine(int(x1), int(y1), int(end_x), int(end_y))


def create_path_draw_button(icon_name, tooltip=None, parent=None):
    """
    创建路径绘制动画按钮的工厂函数

    Args:
        icon_name: 图标名称 ('Cancel', 'Yes', 'Route')
        tooltip: 工具提示文本
        parent: 父组件

    Returns:
        PathDrawAnimatedButton: 配置好的按钮实例
    """
    button = PathDrawAnimatedButton(icon_name, parent)

    if tooltip:
        button.setToolTip(tooltip)

    return button
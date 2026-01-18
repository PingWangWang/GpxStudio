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


class PathDrawAnimatedButton(QPushButton):
    """支持路径绘制动画的按钮"""
    
    def __init__(self, icon_name, parent=None):
        super().__init__(parent)
        
        self.icon_name = icon_name
        self._animation_progress = 1.0  # 1.0 = 完全绘制, 0.0 = 未绘制
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
        # 持续路径绘制动画
        self.path_animation = QPropertyAnimation(self, b"animationProgress")
        self.path_animation.setDuration(2000)
        self.path_animation.setStartValue(0.0)
        self.path_animation.setEndValue(1.0)
        self.path_animation.setEasingCurve(QEasingCurve.InOutSine)
        self.path_animation.setLoopCount(-1)
        
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
            # 悬停时触发路径绘制动画
            self.hover_animation.stop()
            self.hover_animation.setStartValue(self._animation_progress)
            self.hover_animation.setEndValue(0.3)  # 部分擦除
            self.hover_animation.setDuration(200)
            self.hover_animation.start()
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        super().leaveEvent(event)
        if not self._is_animating:
            # 鼠标离开时回到完全绘制状态
            self.hover_animation.stop()
            self.hover_animation.setStartValue(self._animation_progress)
            self.hover_animation.setEndValue(1.0)
            self.hover_animation.setDuration(300)
            self.hover_animation.start()
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        super().mousePressEvent(event)
        if not self._is_animating:
            # 点击时快速绘制
            self.hover_animation.stop()
            self.hover_animation.setStartValue(self._animation_progress)
            self.hover_animation.setEndValue(0.0)  # 完全擦除
            self.hover_animation.setDuration(100)
            self.hover_animation.start()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        super().mouseReleaseEvent(event)
        if not self._is_animating and self.underMouse():
            # 如果鼠标仍在按钮上，回到悬停状态
            self.hover_animation.stop()
            self.hover_animation.setStartValue(self._animation_progress)
            self.hover_animation.setEndValue(0.3)
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
        
        # 绘制圆点和连接线，按顺序出现
        elements = [
            ('circle', 12, 4.5, 2.5),      # 顶部圆点
            ('line', 10.2, 6.3, 6.3, 10.2), # 左上连线
            ('circle', 4.5, 12, 2.5),      # 左侧圆点
            ('line', 7, 12, 17, 12),       # 水平连线
            ('circle', 19.5, 12, 2.5),     # 右侧圆点
            ('line', 13.8, 17.7, 17.7, 13.8), # 右下连线
            ('circle', 12, 19.5, 2.5),     # 底部圆点
        ]
        
        elements_per_step = len(elements)
        for i, element in enumerate(elements):
            element_progress = max(0, min(1, (progress * elements_per_step) - i))
            
            if element_progress > 0:
                if element[0] == 'circle':
                    # 绘制圆形
                    _, cx, cy, r = element
                    painter.drawEllipse(int(cx - r), int(cy - r), int(r * 2), int(r * 2))
                elif element[0] == 'line':
                    # 绘制线段
                    _, x1, y1, x2, y2 = element
                    end_x = x1 + (x2 - x1) * element_progress
                    end_y = y1 + (y2 - y1) * element_progress
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
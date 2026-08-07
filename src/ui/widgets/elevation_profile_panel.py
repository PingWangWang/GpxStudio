"""
海拔剖面图面板组件

主界面底部显示当前路线的海拔剖面：
- 左侧详情区：距离、上升/下降（同一行）、时速、总耗时
- 右侧剖面图：横轴为距离（km），纵轴为海拔（m），QPainter 自绘
  （零第三方依赖，主题色适配），支持鼠标悬停取值（十字线 + 值提示）

使用方式
--------
在主线布局底部实例化（初始隐藏）：

    panel = ElevationProfilePanel()
    main_layout.addWidget(panel)   # 渲染到主界面最底部

路线海拔数据就绪后调用 show_route() 更新并显示：
    panel.show_route(name, distances_km, elevations_m, duration_seconds)
"""

import math

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel,
                             QFrame)
from PyQt5.QtCore import Qt, pyqtSignal, QRectF, QPointF
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QFontMetrics
from ui.theme import theme


class ElevationChart(QWidget):
    """海拔剖面图（QPainter 自绘）

    横轴为距离（km），纵轴为海拔（m）。纵轴底部不固定为 0，
    而是按路线最低海拔向下留出缓冲区间（需求：最低点区间合理）。
    支持鼠标悬停：显示十字线与当前点距离/海拔提示，并发射 hovered 信号。
    """

    # 悬停取值信号（供外部联动，如地图路线定位圆点）：
    # (剖面索引, 距离 km, 海拔 m)——索引与显示剖面时的有效路线点序列一一对应
    hovered = pyqtSignal(int, float, float)
    # 鼠标离开图表信号（外部据此隐藏地图路线上的定位圆点）
    hover_ended = pyqtSignal()

    # 绘图边距（像素）：左侧留 Y 轴刻度、底部留 X 轴刻度
    _MARGIN_LEFT = 52
    _MARGIN_RIGHT = 14
    _MARGIN_TOP = 14
    _MARGIN_BOTTOM = 30

    def __init__(self, parent=None):
        super().__init__(parent)
        self._distances = []   # 累计距离（km）
        self._elevations = []  # 海拔（m）
        self._hover_index = None  # 悬停最近数据点索引
        # 统计缓存（数据不变时避免每次重绘全量扫描 min/max/total，万级点提速明显）
        self._cached_min_el = None
        self._cached_max_el = None
        self._cached_total = None
        self.setMouseTracking(True)  # 无按键移动也触发 mouseMoveEvent
        self.setMinimumHeight(150)
        # QWidget 子类的 QSS 背景需 WA_StyledBackground 才会绘制（透明样式尊重后不绘制，
        # 显示父级面板的 __PANEL_BG__ 主题背景，避免透出浅色父容器）
        self.setAttribute(Qt.WA_StyledBackground, True)
        theme.apply_to_sub(self, "ElevationChart { background-color: transparent; }")

    def _reset_cache(self):
        """重置统计缓存（数据变更时调用）"""
        self._cached_min_el = None
        self._cached_max_el = None
        self._cached_total = None

    def set_data(self, distances, elevations):
        """设置剖面数据并重绘

        Args:
            distances: 累计距离列表（km，从 0 起）
            elevations: 对应海拔列表（m）
        """
        self._distances = list(distances)
        self._elevations = list(elevations)
        self._hover_index = None
        self._reset_cache()
        self.update()

    def clear(self):
        """清空数据"""
        self._distances = []
        self._elevations = []
        self._hover_index = None
        self._reset_cache()
        self.update()

    # ── 数据 ↔ 像素变换 ────────────────────────────────────────────────

    def _value_range(self):
        """计算纵轴范围：底部 = 最低海拔 - 缓冲，顶部 = 最高海拔 + 缓冲

        缓冲取跨度 10% 与 20m 的较大值，保证曲线不贴边且底部非零。
        使用缓存避免每次重绘全量扫描（数据不变时 O(1)）。
        """
        if not self._elevations:
            return 0.0, 100.0
        if self._cached_min_el is None:
            self._cached_min_el = min(self._elevations)
            self._cached_max_el = max(self._elevations)
        min_el, max_el = self._cached_min_el, self._cached_max_el
        span = max(max_el - min_el, 1.0)
        pad = max(span * 0.1, 20.0)
        return min_el - pad, max_el + pad

    def _plot_rect(self):
        """图表绘制区域（扣除刻度边距）"""
        return QRectF(self._MARGIN_LEFT, self._MARGIN_TOP,
                      max(self.width() - self._MARGIN_LEFT - self._MARGIN_RIGHT, 1),
                      max(self.height() - self._MARGIN_TOP - self._MARGIN_BOTTOM, 1))

    def _to_pixel(self, dist_km, elev_m):
        """数据坐标 → 像素坐标"""
        rect = self._plot_rect()
        bottom, top = self._value_range()
        x = rect.left() + rect.width() * dist_km / max(self._total_distance(), 0.001)
        y = rect.top() + rect.height() * (top - elev_m) / max(top - bottom, 0.001)
        return QPointF(x, y)

    def _total_distance(self):
        """路线总距离（km，缓存复用）"""
        if self._cached_total is None and self._distances:
            self._cached_total = self._distances[-1]
        return self._cached_total or 0.0

    def _index_at_x(self, x):
        """像素 x → 最近数据点索引（二分查找，无数据返回 None）

        distances 为单调递增的累计距离，二分 O(log n) 替代线性扫描——
        万级海拔点下鼠标移动不再逐点全量比较（卡顿根因之一）。
        """
        if not self._distances:
            return None
        total = self._total_distance()
        if total <= 0:
            return None
        rect = self._plot_rect()
        ratio = (x - rect.left()) / rect.width()
        target = max(0.0, min(1.0, ratio)) * total
        # 二分定位 target 的插入位置，取两侧中更近的点
        import bisect
        i = bisect.bisect_left(self._distances, target)
        if i >= len(self._distances):
            return len(self._distances) - 1
        if i == 0:
            return 0
        if (self._distances[i] - target) < (target - self._distances[i - 1]):
            return i
        return i - 1

    # ── 主题取色 ────────────────────────────────────────────────────────

    @staticmethod
    def _theme_color(placeholder, alpha=255):
        """从主题取色并设置透明度（QPainter 自绘随浅色/深色模式自动切换）"""
        color = QColor(theme.apply(placeholder))
        color.setAlpha(alpha)
        return color

    # ── 事件：悬停取值 ─────────────────────────────────────────────────

    def mouseMoveEvent(self, event):
        idx = self._index_at_x(event.pos().x())
        if idx != self._hover_index:
            self._hover_index = idx
            self.update()
        if idx is not None:
            self.hovered.emit(idx, self._distances[idx], self._elevations[idx])
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self._hover_index = None
        self.update()
        self.hover_ended.emit()
        super().leaveEvent(event)

    # ── 绘制 ───────────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if not self._distances or not self._elevations:
            self._paint_empty(painter)
            return

        rect = self._plot_rect()
        bottom, top = self._value_range()
        total = self._total_distance()

        # 主题取色（浅色/深色模式自适应）
        accent = self._theme_color('__ACCENT__')
        text_secondary = self._theme_color('__TEXT_SECONDARY__')
        panel_bg = self._theme_color('__PANEL_BG__')

        # 轴线与网格
        grid_pen = QPen(self._theme_color('__TEXT_SECONDARY__', 60), 1)
        grid_pen.setStyle(Qt.DashLine)
        label_pen = QPen(text_secondary, 1)
        font = QFont("Microsoft YaHei", 8)
        painter.setFont(font)

        # Y 轴刻度（4 等分）
        for i in range(5):
            ratio = i / 4.0
            el = top - (top - bottom) * ratio
            y = rect.top() + rect.height() * ratio
            painter.setPen(grid_pen)
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            painter.setPen(label_pen)
            painter.drawText(
                QRectF(0, y - 8, self._MARGIN_LEFT - 6, 16),
                Qt.AlignRight | Qt.AlignVCenter, f"{el:.0f}")

        # X 轴刻度（5 等分）
        for i in range(6):
            ratio = i / 5.0
            dist = total * ratio
            x = rect.left() + rect.width() * ratio
            painter.setPen(grid_pen)
            painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
            painter.setPen(label_pen)
            painter.drawText(
                QRectF(x - 30, rect.bottom() + 4, 60, 16),
                Qt.AlignHCenter | Qt.AlignTop, f"{dist:.0f}")

        # 轴标签
        painter.drawText(
            QRectF(rect.left(), self.height() - 16, rect.width(), 14),
            Qt.AlignCenter, "距离 (km)")
        painter.save()
        painter.translate(10, rect.center().y())
        painter.rotate(-90)
        painter.drawText(QRectF(-60, -8, 120, 16), Qt.AlignCenter, "海拔 (m)")
        painter.restore()

        # 海拔折线：按像素宽抽稀（每像素 ≤1 段），万级点下绘制量 O(图宽)，
        # 亚像素细节在图中不可见，视觉无损且重绘提速数十倍（卡顿根因之一）
        plot_w = max(int(rect.width()), 1)
        step = max(1, (len(self._distances) + plot_w - 1) // plot_w)
        indices = list(range(0, len(self._distances), step))
        if indices[-1] != len(self._distances) - 1:
            indices.append(len(self._distances) - 1)  # 保证终点纳入
        line_pen = QPen(accent, 2)  # 主题强调色
        painter.setPen(line_pen)
        prev = None
        for i in indices:
            p = self._to_pixel(self._distances[i], self._elevations[i])
            if prev is not None:
                painter.drawLine(prev, p)
            prev = p

        # 悬停十字线 + 值提示（悬停点单点计算像素，不依赖抽稀列表）
        if self._hover_index is not None:
            hover_p = self._to_pixel(self._distances[self._hover_index],
                                     self._elevations[self._hover_index])
            hx, hy = hover_p.x(), hover_p.y()
            cross_pen = QPen(self._theme_color('__ACCENT__', 160), 1)
            cross_pen.setStyle(Qt.DashLine)
            painter.setPen(cross_pen)
            painter.drawLine(QPointF(hx, rect.top()), QPointF(hx, rect.bottom()))
            painter.drawLine(QPointF(rect.left(), hy), QPointF(rect.right(), hy))

            # 值提示框（跟随鼠标点，背景取面板色随主题切换）
            tip_text = (f"{self._distances[self._hover_index]:.1f} km · "
                        f"{self._elevations[self._hover_index]:.0f} m")
            fm = QFontMetrics(font)
            tip_w = fm.horizontalAdvance(tip_text) + 12
            tip_x = hx + 10
            if tip_x + tip_w > self.width() - 2:
                tip_x = hx - 10 - tip_w
            tip_rect = QRectF(tip_x, hy - 22, tip_w, 20)
            painter.setPen(QPen(accent, 1))
            painter.setBrush(self._theme_color('__PANEL_BG__', 230))
            painter.drawRoundedRect(tip_rect, 4, 4)
            painter.setPen(accent)
            painter.drawText(tip_rect, Qt.AlignCenter, tip_text)

        painter.end()

    def _paint_empty(self, painter):
        """无数据占位提示（颜色随主题切换）"""
        painter.setPen(self._theme_color('__TEXT_SECONDARY__'))
        painter.setFont(QFont("Microsoft YaHei", 9))
        painter.drawText(self.rect(), Qt.AlignCenter, "暂无海拔数据")

    def sizeHint(self):
        return self.minimumSize()


class ElevationProfilePanel(QWidget):
    """海拔剖面图面板（左侧详情 + 右侧剖面图）

    主界面底部渲染当前路线的海拔剖面。海拔数据就绪后调用 show_route()。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # QWidget 子类的 QSS 背景需 WA_StyledBackground 才会绘制：
        # 面板 __PANEL_BG__ 背景真正生效（深色=深灰蓝、浅色=白），
        # 与详情区 QFrame 背景一致，图表区（透明）随面板背景
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._build_ui()
        self.hide()  # 初始隐藏（开关开启且有路线时显示）

    def _build_ui(self):
        # 面板背景与详情区同色（__PANEL_BG__）：深浅模式下图表区与详情区背景统一，
        # 剖面图（透明背景）随面板背景自适应
        theme.apply_to_sub(self, """
            ElevationProfilePanel { background-color: __PANEL_BG__; }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(10)

        # 左侧详情区（固定宽度）：距离 / 上升·下降（同一行）/ 时速 / 总耗时
        detail_frame = QFrame()
        theme.apply_to_sub(detail_frame, """
            QFrame { background-color: __PANEL_BG__; border: 1px solid __BORDER__;
                     border-radius: 6px; }
        """)
        detail_layout = QVBoxLayout(detail_frame)
        detail_layout.setContentsMargins(10, 8, 10, 8)
        detail_layout.setSpacing(8)

        self._detail_labels = {}

        def _make_title_label(text, tooltip=''):
            label = QLabel(text)
            theme.apply_to_sub(label, """
                QLabel { color: __TEXT_SECONDARY__; font-size: 12px; }""")
            label.setFixedWidth(60)
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if tooltip:
                label.setToolTip(tooltip)
            return label

        def _make_value_label():
            label = QLabel("-")
            theme.apply_to_sub(label, """
                QLabel { color: __TEXT__; font-size: 13px; font-weight: bold; }""")
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            return label

        def _add_detail_row(title, key, tooltip=''):
            row = QHBoxLayout()
            row.setSpacing(8)
            row.addWidget(_make_title_label(title, tooltip))
            value = _make_value_label()
            row.addWidget(value, 1)
            detail_layout.addLayout(row)
            self._detail_labels[key] = value

        # 距离
        _add_detail_row("距离", "distance", "路线总长度（公里）")
        # 上升 / 下降（同一行两列，等宽对齐）
        ascent_row = QHBoxLayout()
        ascent_row.setSpacing(8)
        # tooltip 格外说明：上升/下降为全程逐段的累计值，而非起终点海拔差
        ascent_row.addWidget(_make_title_label(
            "上升/下降",
            "累计上升 / 累计下降——全程逐段海拔升高（上升）与降低（下降）的总和，"
            "而非起点与最高点的差值"))
        self._detail_labels["ascent"] = _make_value_label()
        self._detail_labels["descent"] = _make_value_label()
        ascent_row.addWidget(self._detail_labels["ascent"], 1)
        ascent_row.addWidget(self._detail_labels["descent"], 1)
        detail_layout.addLayout(ascent_row)
        # 时速 / 总耗时
        _add_detail_row("时速", "speed", "全程平均时速（公里/小时）")
        _add_detail_row("总耗时", "duration", "路线总耗时（按规划时长估算）")

        layout.addWidget(detail_frame, 0)

        # 右侧剖面图
        self.chart = ElevationChart()
        layout.addWidget(self.chart, 1)

    # ── 数据接口 ───────────────────────────────────────────────────────

    def show_route(self, route_name, distances_km, elevations_m, duration_seconds):
        """更新并显示当前路线的海拔剖面

        Args:
            route_name: 路线名称（起点 → 终点，面板详情不显示路线名称）
            distances_km: 累计距离列表（km）
            elevations_m: 对应海拔列表（m）
            duration_seconds: 路线总耗时（秒）
        """
        if not distances_km or not elevations_m:
            return

        # 统计指标
        total_km = distances_km[-1]
        ascent = sum(max(elevations_m[i] - elevations_m[i - 1], 0)
                     for i in range(1, len(elevations_m)))
        descent = sum(max(elevations_m[i - 1] - elevations_m[i], 0)
                      for i in range(1, len(elevations_m)))
        hours = duration_seconds / 3600.0 if duration_seconds > 0 else 0.0
        speed = total_km / hours if hours > 0 else 0.0

        self._detail_labels["distance"].setText(f"{total_km:.2f} 公里")
        self._detail_labels["ascent"].setText(f"↑ {ascent:.0f} m")
        self._detail_labels["descent"].setText(f"↓ {descent:.0f} m")
        self._detail_labels["speed"].setText(f"{speed:.1f} km/h")
        self._detail_labels["duration"].setText(self._format_duration(duration_seconds))

        self.chart.set_data(distances_km, elevations_m)
        self.show()

    def show_empty(self):
        """显示空数据占位（面板保持可见，图表显示"暂无海拔数据"）"""
        self.chart.clear()
        for label in self._detail_labels.values():
            label.setText("-")
        self.show()

    def clear_route(self):
        """清除剖面数据并隐藏面板（设置开关关闭时调用）"""
        self.chart.clear()
        for label in self._detail_labels.values():
            label.setText("-")
        self.hide()

    @staticmethod
    def _format_duration(seconds):
        """秒 → "x 小时 x 分钟" 文本"""
        seconds = int(seconds)
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        if h > 0:
            return f"{h} 小时 {m} 分钟" if m else f"{h} 小时"
        if m > 0:
            return f"{m} 分钟" if s == 0 else f"{m} 分 {s} 秒"
        return f"{s} 秒"

    @staticmethod
    def compute_profile(route_points):
        """从路线点计算剖面数据（Haversine 距离 + 海拔序列）

        Args:
            route_points: [(lat, lon, elevation), ...]（海拔缺失的点按 None 跳过）

        Returns:
            (distances_km, elevations_m) 或 (None, None)（数据不足）
        """
        valid = [(p[0], p[1], p[2]) for p in route_points
                 if p is not None and len(p) >= 3 and p[2] is not None]
        if len(valid) < 2:
            return None, None

        distances = [0.0]
        elevations = [valid[0][2]]
        for i in range(1, len(valid)):
            lat1, lon1 = valid[i - 1][0], valid[i - 1][1]
            lat2, lon2 = valid[i][0], valid[i][1]
            distances.append(distances[-1] + ElevationProfilePanel._haversine_km(lat1, lon1, lat2, lon2))
            elevations.append(valid[i][2])
        return distances, elevations

    @staticmethod
    def _haversine_km(lat1, lon1, lat2, lon2):
        """两点间球面距离（km，Haversine 公式）"""
        r = 6371.0
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dp = math.radians(lat2 - lat1)
        dl = math.radians(lon2 - lon1)
        a = (math.sin(dp / 2) ** 2
             + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2)
        return 2 * r * math.asin(math.sqrt(a))

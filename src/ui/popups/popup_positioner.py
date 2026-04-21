"""
弹出面板位置计算工具

封装三类位置计算逻辑（均为静态方法，无 Qt 父类）：

1. ``update_popup_positions``  — 跟随主窗口移动时平移所有弹出面板
2. ``update_button_positions`` — 在地图容器 resize 时重新定位工具栏控件
3. ``update_route_panel_position`` — 路线规划面板 / GPX 导出弹出面板的位置计算
"""

from PyQt5.QtCore import QPoint, QRect
from PyQt5.QtWidgets import QApplication


class PopupPositioner:
    """弹出面板位置计算工具（纯静态工具类）。"""

    # ──────────────────────────────────────────────────────────────────
    # 1. 跟随主窗口移动
    # ──────────────────────────────────────────────────────────────────

    @staticmethod
    def update_popup_positions(active_popups: list, current_geometry, last_geometry) -> object:
        """根据主窗口位移量平移所有可见弹出面板。

        参数:
            active_popups: 已注册的弹出面板列表
            current_geometry: 当前窗口 geometry()
            last_geometry: 上次记录的 geometry()（可为 None）

        返回:
            current_geometry（调用方应将其保存为新的 last_geometry）
        """
        if last_geometry is not None:
            dx = current_geometry.x() - last_geometry.x()
            dy = current_geometry.y() - last_geometry.y()
            for popup in active_popups:
                if popup and popup.isVisible():
                    popup.move(popup.pos() + QPoint(dx, dy))
        return current_geometry

    # ──────────────────────────────────────────────────────────────────
    # 2. 工具栏控件位置（地图容器 resize 触发）
    # ──────────────────────────────────────────────────────────────────

    @staticmethod
    def update_button_positions(container, toolbar) -> None:
        """在地图容器大小变化后重新定位工具栏中的浮动控件。

        参数:
            container: map_container QWidget
            toolbar: MapToolbar 实例
        """
        width = container.width()
        height = container.height()
        margin_right = 20
        margin_left = 20
        margin_top = 20
        margin_bottom = 20

        # 右侧按钮组 — 垂直居中
        toolbar.right_buttons_container.adjustSize()
        bw = toolbar.right_buttons_container.width()
        bh = toolbar.right_buttons_container.height()
        toolbar.right_buttons_container.move(width - bw - margin_right, (height - bh) // 2)
        toolbar.right_buttons_container.raise_()

        # 比例尺标签 — 左下角
        toolbar.scale_info_label.adjustSize()
        toolbar.scale_info_label.move(
            margin_left,
            height - toolbar.scale_info_label.height() - margin_bottom,
        )
        toolbar.scale_info_label.raise_()

        # 搜索容器 — 左上角
        toolbar.search_container.adjustSize()
        toolbar.search_container.move(margin_left, margin_top)
        toolbar.search_container.raise_()

    # ──────────────────────────────────────────────────────────────────
    # 3. 路线规划面板 / GPX 导出弹出面板
    # ──────────────────────────────────────────────────────────────────

    @staticmethod
    def update_route_panel_position(route_plan_panel, search_container,
                                    gpx_export_popup=None, logger=None) -> None:
        """更新路线规划面板及 GPX 导出弹出面板的位置。

        参数:
            route_plan_panel: RoutePlanPanel 实例（可为 None）
            search_container: 搜索容器 QWidget
            gpx_export_popup: GpxExportPopup 实例（可为 None）
            logger: 日志对象（可为 None）
        """
        try:
            # 路线规划面板
            if (route_plan_panel is not None and search_container is not None
                    and route_plan_panel.isVisible()):
                pos = search_container.mapToGlobal(search_container.rect().topLeft())
                route_plan_panel.move(pos.x(), pos.y())
                if logger:
                    logger.debug(f"[面板位置] 路线面板: ({pos.x()}, {pos.y()})")

            # GPX 导出弹出面板
            if (gpx_export_popup is not None and route_plan_panel is not None
                    and gpx_export_popup.isVisible() and route_plan_panel.isVisible()):
                panel_pos = route_plan_panel.mapToGlobal(route_plan_panel.rect().topLeft())
                panel_rect = route_plan_panel.rect()
                screen = QApplication.primaryScreen().geometry()

                popup_x = panel_pos.x() + panel_rect.width() + 10
                popup_y = panel_pos.y() + 50

                if popup_x + gpx_export_popup.width() > screen.right():
                    popup_x = panel_pos.x() - gpx_export_popup.width() - 10
                if popup_y + 200 > screen.bottom():
                    popup_y = screen.bottom() - 250

                gpx_export_popup.move(popup_x, popup_y)
                if logger:
                    logger.debug(f"[面板位置] GPX弹出: ({popup_x}, {popup_y})")

        except Exception as e:
            msg = f"[面板位置] 更新位置时出错: {e}"
            if logger:
                logger.error(msg)
            else:
                print(msg)

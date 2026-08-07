"""
UICallbacks — 类型化 UI 回调容器

替代之前无类型的 ``ui_updater`` 字典，提供 IDE 自动补全和静态类型检查支持。
管理器（RouteManager、SearchManager 等）接受此对象而非 dict，
通过 ``self.ui_callbacks.show_warning(...)`` 代替 ``self.ui_updater['show_warning'](...)``.

所有字段均为可调用对象（Callable），在 ``app/mixins/init_mixin.py`` 的
``_build_ui_callbacks()`` 中完成绑定。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


def _noop(*_args, **_kwargs):
    """占位空操作，防止未绑定字段调用时引发 TypeError。"""
    return None


@dataclass
class UICallbacks:
    """类型化 UI 回调容器（替代 ui_updater 字典）。

    字段按功能分组：
    - 弹窗 / 通知
    - 进度条
    - 结果列表
    - 搜索
    - 位置 / 地图
    - 时间面板
    - 路线
    - 杂项
    """

    # ── 弹窗 / 通知 ───────────────────────────────────────────────────────
    show_warning:               Callable = field(default=_noop)
    show_info:                  Callable = field(default=_noop)

    # ── 进度条 ────────────────────────────────────────────────────────────
    set_progress_indeterminate: Callable = field(default=_noop)
    set_progress_complete:      Callable = field(default=_noop)
    set_progress:               Callable = field(default=_noop)

    # ── 结果列表 ──────────────────────────────────────────────────────────
    clear_results:              Callable = field(default=_noop)
    clear_results_list:         Callable = field(default=_noop)
    add_result:                 Callable = field(default=_noop)
    set_results_title:          Callable = field(default=_noop)

    # ── 搜索 ──────────────────────────────────────────────────────────────
    show_search_results:            Callable = field(default=_noop)
    show_search_results_on_map:     Callable = field(default=_noop)
    show_search_results_dropdown:   Callable = field(default=_noop)

    # ── 位置 / 预览 ───────────────────────────────────────────────────────
    update_location_display:    Callable = field(default=_noop)
    update_start_from_search:   Callable = field(default=_noop)
    update_end_from_search:     Callable = field(default=_noop)
    add_waypoint_to_list:       Callable = field(default=_noop)
    update_map_preview:         Callable = field(default=_noop)
    preview_search_result:      Callable = field(default=_noop)
    show_location_on_map:       Callable = field(default=_noop)
    show_elevation_profile:     Callable = field(default=_noop)  # 海拔数据就绪后更新剖面图
    elevation_fetch_completed:  Callable = field(default=_noop)  # 海拔获取完成（手动链路，回写历史）

    # ── 地图操作 ──────────────────────────────────────────────────────────
    show_route_on_map:          Callable = field(default=_noop)
    load_map_url:               Callable = field(default=_noop)
    trigger_browser_location:   Callable = field(default=_noop)

    # ── 时间面板 ──────────────────────────────────────────────────────────
    get_start_time:             Callable = field(default=_noop)
    set_start_time:             Callable = field(default=_noop)
    get_end_time:               Callable = field(default=_noop)
    set_end_time:               Callable = field(default=_noop)
    get_duration:               Callable = field(default=_noop)
    set_duration:               Callable = field(default=_noop)
    get_transport_mode:         Callable = field(default=_noop)
    hide_time_panel:            Callable = field(default=_noop)
    hide_date_panel:            Callable = field(default=_noop)
    show_date_panel:            Callable = field(default=_noop)
    show_time_panel:            Callable = field(default=_noop)
    setup_date_panel_callback:  Callable = field(default=_noop)
    setup_time_panel_callback:  Callable = field(default=_noop)

    # ── 路线 ──────────────────────────────────────────────────────────────
    add_route_time_info:        Callable = field(default=_noop)
    show_route_alternatives:    Callable = field(default=_noop)
    save_route_history:         Callable = field(default=_noop)

    # ── 杂项 ──────────────────────────────────────────────────────────────
    main_window:                Any = field(default=None)

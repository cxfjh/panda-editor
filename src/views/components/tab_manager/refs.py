from __future__ import annotations
from collections.abc import Callable
from typing import TYPE_CHECKING
from PySide6.QtCore import SignalInstance


if TYPE_CHECKING:
    from PySide6.QtWidgets import QTabWidget
    from src.views.components.tab_manager.models import TabData


class TabsRefs:
    """标签页共享成员的声明"""
    tab_widget: QTabWidget
    tab_data_map: dict[int, TabData]
    tab_changed: SignalInstance
    tab_count_changed: SignalInstance
    file_saved_as: SignalInstance
    _dark_mode: bool
    _syntax_highlight: bool
    _get_tab_name: Callable[..., str]
    _remap_tab_data: Callable[..., None]
    _update_tab_title: Callable[..., None]
    close_tab: Callable[..., bool]
    create_new_tab: Callable[..., int]
    index_of_path: Callable[..., int]
    save_tab: Callable[..., bool]

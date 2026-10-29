from __future__ import annotations
from collections.abc import Callable
from typing import TYPE_CHECKING

from PySide6.QtCore import SignalInstance
from PySide6.QtWidgets import QWidget


if TYPE_CHECKING:
    from PySide6.QtWidgets import QComboBox, QLabel, QLineEdit, QPushButton
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from src.utils.blockly.bridge import BlocklyBridge


class PanelRefs(QWidget):
    """积木面板共享成员的声明"""
    view: QWebEngineView
    bridge: BlocklyBridge
    status_label: QLabel
    target_edit: QLineEdit
    mode_combo: QComboBox
    palette_btn: QPushButton
    code_written: SignalInstance
    _buttons: list[QPushButton]
    _confirmed_paths: set[str]
    _dark_mode: bool
    _page_ready: bool
    _palette_pinned: bool
    _target_path: str
    _workspace_file: str
    _pending_save_mode: str
    _status_hold_until: float
    _load_target_path: Callable[..., str]
    _load_append_mode: Callable[..., bool]
    _load_workspace_file: Callable[..., str]
    _setup_web_view: Callable[..., None]
    _set_ready: Callable[..., None]
    _sync_palette_button: Callable[..., None]
    _set_status: Callable[..., None]
    _set_status_result: Callable[..., None]
    _restore_workspace: Callable[..., None]
    _request_workspace_autosave: Callable[..., None]
    _on_code_submitted: Callable[..., None]
    _on_generate_clicked: Callable[..., None]
    _on_mode_changed: Callable[..., None]
    _on_palette_pin_toggled: Callable[..., None]
    _on_page_notice: Callable[..., None]
    _on_workspace_submitted: Callable[..., None]
    choose_target: Callable[..., bool]
    clear_workspace: Callable[..., None]
    load_workspace: Callable[..., None]
    save_workspace: Callable[..., None]

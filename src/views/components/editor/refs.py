from __future__ import annotations
from collections.abc import Callable
from PySide6.QtCore import SignalInstance
from pyside6_scintilla import ScintillaEdit


class EditorRefs(ScintillaEdit):
    """编辑器共享成员的声明"""
    _dark_mode: bool
    _show_line_numbers: bool
    fontChanged: SignalInstance
    _apply_theme: Callable[..., None]
    _handle_english_bracket_completion: Callable[..., bool]
    _pair_cn_bracket_after_commit: Callable[..., None]
    _skip_closing_bracket: Callable[..., bool]
    _toggle_comment: Callable[..., None]
    _update_line_margin_width: Callable[..., None]

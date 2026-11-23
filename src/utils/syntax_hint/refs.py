from __future__ import annotations
from collections.abc import Callable
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from PySide6.QtCore import QTimer
    from src.utils.completion_index import DocumentIndex
    from src.views.components.editor import CodeEditor


class HintRefs:
    """提示管理器共享成员的声明"""
    _editor: CodeEditor
    _current_file: str | None
    _lib_ops: dict[str, dict]
    _ime_composing: bool
    _debounce_timer: QTimer
    _document_index: Callable[..., DocumentIndex]
    _mark_index_dirty: Callable[..., None]
    _on_char_added: Callable[..., None]
    _request_completion: Callable[..., None]
    _should_complete: Callable[..., bool]
    _show_call_tip: Callable[..., None]
    _index: DocumentIndex
    _index_built_at: float | int
    _last_shown: tuple[int, tuple[str, ...]]

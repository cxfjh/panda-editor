from __future__ import annotations
from collections.abc import Callable
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from PySide6.QtWidgets import QTreeWidget
    from src.views.file_tree.view import FileTreeSignals


class TreeRefs:
    """文件树共享成员的声明"""
    tree: QTreeWidget
    signals: FileTreeSignals
    _new_file: Callable[..., None]
    _new_folder: Callable[..., None]
    _rename_item: Callable[..., None]
    _delete_item: Callable[..., None]
    _open_in_explorer: Callable[..., None]
    _refresh_parent: Callable[..., None]
    _show_message: Callable[..., None]
    _ask_question: Callable[..., bool]
    _dark_mode: bool

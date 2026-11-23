from __future__ import annotations
from collections.abc import Callable
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from PySide6.QtCore import QProcess
    from PySide6.QtWidgets import QPlainTextEdit, QPushButton
    from src.views.terminal.input_box import TerminalLineEdit


class TerminalRefs:
    """终端共享成员的声明"""
    _process: QProcess
    _output: QPlainTextEdit
    _input: TerminalLineEdit
    _stop_btn: QPushButton
    _dark_mode: bool
    _process_running: bool
    _command_history: list[str]
    _get_code_callback: Callable[[], str] | None
    _get_file_path_callback: Callable[[], str | None] | None
    _current_dir: str
    _append_output: Callable[..., None]
    _is_busy: Callable[..., bool]
    _set_running: Callable[..., None]
    _report_run_error: Callable[..., None]
    _run_pip: Callable[..., None]
    _on_submit: Callable[..., None]
    _setup_process: Callable[..., None]
    _stop_process: Callable[..., None]
    run_python_script: Callable[..., None]
    _error_report_path: str | None
    _history_index: int

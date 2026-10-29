from __future__ import annotations
from collections.abc import Callable
from typing import TYPE_CHECKING
from PySide6.QtGui import QAction


if TYPE_CHECKING:
    from PySide6.QtWidgets import QMainWindow, QMenuBar
    from src.views.blockly import BlocklyPanel
    from src.views.components.custom_title_bar import CustomTitleBar
    from src.views.components.handlers import MainWindowHandlers
    from src.views.components.tab_manager import TabManager
    from src.views.file_tree import FileTreeView
    from src.views.terminal import TerminalWidget


class UiRefs:
    """主窗口共享部件的声明"""
    main_window: QMainWindow
    handlers: MainWindowHandlers
    tab_manager: TabManager
    file_tree: FileTreeView
    terminal: TerminalWidget
    blockly_panel: BlocklyPanel
    custom_title_bar: CustomTitleBar
    menu_bar: QMenuBar
    _setup_main_window: Callable[[QMainWindow], None]
    _setup_icon: Callable[[QMainWindow], None]
    _setup_central_widget: Callable[[QMainWindow], None]
    _setup_style: Callable[[QMainWindow], None]
    _setup_close_event: Callable[[QMainWindow], None]
    _setup_global_shortcuts: Callable[[QMainWindow], None]
    _init_file_tree: Callable[[], None]
    _init_menu_states: Callable[[], None]
    _setup_signals_and_slots: Callable[[], None]
    _setup_auto_save: Callable[[], None]
    _fix_menu_bar_width: Callable[[], None]
    _on_toggle_maximize: Callable[[], None]
    _sync_maximize_button: Callable[[], None]
    _ensure_source_directory: Callable[[], None]
    _handle_launch_path: Callable[[], bool]
    open_action: QAction
    save_action: QAction
    save_as_action: QAction
    find_action: QAction
    run_action: QAction
    compile_action: QAction
    compile_ui_action: QAction
    website_action: QAction
    github_action: QAction
    author_github_action: QAction
    email_action: QAction
    uninstall_action: QAction
    reset_action: QAction
    dark_mode_action: QAction
    syntax_highlight_action: QAction
    window_top_action: QAction
    update_action: QAction
    tutorial_action: QAction
    toggle_file_tree_action: QAction
    toggle_terminal_action: QAction
    toggle_blockly_action: QAction
    toggle_line_numbers_action: QAction
    fold_all_action: QAction
    unfold_all_action: QAction
    gui_designer_action: QAction
    pip_taobao_action: QAction
    independent_run_action: QAction
    hide_window_action: QAction
    admin_privilege_action: QAction
    single_file_action: QAction
    add_data_action: QAction
    compile_default_icon_action: QAction
    compile_icon_action: QAction
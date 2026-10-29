from PySide6 import QtCore
from PySide6.QtGui import QKeySequence, QShortcut
from src.utils.code_proc import signals as code_signals
from src.utils.set_page import reset_program, uninstall_program
from src.views.components.event_filters import WindowFocusFilter
from src.views.components.handlers import URL_AUTHOR, URL_EMAIL, URL_REPO, URL_TUTORIAL, URL_WEBSITE
from src.views.main_win.refs import UiRefs


# 全局快捷键与实际处理方法的对应关系
_SHORTCUT_TABLE = (
    ("Ctrl+O", "on_open_directory"),
    ("Ctrl+S", "on_save_file"),
    ("Ctrl+Shift+S", "on_save_as_file"),
    ("Ctrl+F", "on_find_replace"),
    ("F3", "on_find_next"),
    ("Shift+F3", "on_find_previous"),
    ("Ctrl+R", "on_run_code"),
    ("Ctrl+B", "on_compile_code"),
    ("Ctrl+W", "on_close_tab"),
    ("Ctrl+Tab", "on_next_tab"),
    ("Ctrl+Shift+Tab", "on_previous_tab"),
    ("Shift+Esc", "toggle_file_tree_shortcut"),
    ("Ctrl+`", "toggle_terminal_shortcut"),
    ("Ctrl+Shift+B", "toggle_blockly_shortcut"),
    ("Ctrl+Shift+[", "on_fold_all"),
    ("Ctrl+Shift+]", "on_unfold_all"),
)


class BindingMixin(UiRefs):
    """菜单信号 快捷键与窗口事件的绑定"""

    def _init_menu_states(self):
        """
        初始化菜单项的选中状态

        Args:
            self: 当前 UI 实例
        """
        self.handlers.init_menu_states()

    def _setup_signals_and_slots(self):
        """
        设置信号与槽连接

        Args:
            self: 当前 UI 实例
        """

        # 文件菜单
        self.open_action.triggered.connect(self.handlers.on_open_directory)
        self.save_action.triggered.connect(self.handlers.on_save_file)
        self.save_as_action.triggered.connect(self.handlers.on_save_as_file)
        self.find_action.triggered.connect(self.handlers.on_find_replace)
        self.run_action.triggered.connect(self.handlers.on_run_code)
        self.compile_action.triggered.connect(self.handlers.on_compile_code)
        self.compile_ui_action.triggered.connect(self.handlers.on_compile_ui)

        # 帮助与外部链接
        self.website_action.triggered.connect(lambda: self.handlers.open_url(URL_WEBSITE))
        self.github_action.triggered.connect(lambda: self.handlers.open_url(URL_REPO))
        self.author_github_action.triggered.connect(lambda: self.handlers.open_url(URL_AUTHOR))
        self.email_action.triggered.connect(lambda: self.handlers.open_url(URL_EMAIL))

        # 程序维护
        self.uninstall_action.triggered.connect(uninstall_program)
        self.reset_action.triggered.connect(reset_program)

        # 外观与窗口
        self.dark_mode_action.triggered.connect(self.handlers.on_dark_mode_changed)
        self.syntax_highlight_action.triggered.connect(self.handlers.on_syntax_highlight_changed)
        self.window_top_action.triggered.connect(self.handlers.on_window_top_changed)
        self.update_action.triggered.connect(lambda: self.handlers.open_url(URL_WEBSITE))
        self.tutorial_action.triggered.connect(lambda: self.handlers.open_url(URL_TUTORIAL))

        # 面板与编辑器显示
        self.toggle_file_tree_action.toggled.connect(self.handlers.toggle_file_tree)
        self.toggle_terminal_action.toggled.connect(self.handlers.toggle_terminal)
        self.toggle_blockly_action.toggled.connect(self.handlers.toggle_blockly)
        self.toggle_line_numbers_action.toggled.connect(self.handlers.toggle_line_numbers)
        self.fold_all_action.triggered.connect(self.handlers.on_fold_all)
        self.unfold_all_action.triggered.connect(self.handlers.on_unfold_all)
        self.gui_designer_action.triggered.connect(self.handlers.on_open_gui_designer)

        # 编译设置
        self.pip_taobao_action.triggered.connect(self.handlers.on_pip_mirror_changed)
        self.independent_run_action.triggered.connect(self.handlers.on_independent_run_changed)
        self.hide_window_action.triggered.connect(self.handlers.on_hide_window_changed)
        self.admin_privilege_action.triggered.connect(self.handlers.on_admin_privilege_changed)
        self.single_file_action.triggered.connect(self.handlers.on_single_file_changed)
        self.add_data_action.triggered.connect(self.handlers.on_add_data_changed)
        self.compile_default_icon_action.triggered.connect(self.handlers.on_compile_default_icon_changed)
        self.compile_icon_action.triggered.connect(self.handlers.on_compile_icon_changed)

        # 文件树与编译线程的信号
        self.file_tree.signals.file_selected.connect(self.handlers.on_file_tree_selected)
        self.file_tree.signals.file_renamed.connect(self.tab_manager.rename_file_path)
        self.file_tree.signals.file_deleted.connect(self.tab_manager.handle_file_deleted)
        code_signals.compile_log.connect(self.handlers.on_compile_log)
        code_signals.compile_finished.connect(self.handlers.on_compile_finished)

    def _setup_global_shortcuts(self, main_window):
        """
        使用 QShortcut 设置全局快捷键

        Args:
            self: 当前 UI 实例
            main_window: 主窗口对象
        """
        self._shortcuts = []
        for key_seq, method_name in _SHORTCUT_TABLE:
            shortcut = QShortcut(QKeySequence(key_seq), main_window)
            shortcut.activated.connect(getattr(self.handlers, method_name))
            self._shortcuts.append(shortcut)

    def _setup_auto_save(self):
        """
        设置自动保存功能

        Args:
            self: 当前 UI 实例
        """
        if self.main_window:
            self._window_focus_filter = WindowFocusFilter(self.handlers.auto_save)
            self.main_window.installEventFilter(self._window_focus_filter)

    def _setup_close_event(self, main_window):
        """
        设置窗口关闭事件, 保存标签页状态

        Args:
            self: 当前 UI 实例
            main_window: 主窗口对象
        """
        original_close = main_window.closeEvent

        def new_close_event(event):
            """
            关闭事件回调, 保存标签页状态后调用原关闭逻辑

            Args:
                event: 关闭事件对象
            """
            self.tab_manager.save_tabs_state()
            self.handlers.auto_save()
            original_close(event)

        main_window.closeEvent = new_close_event

        # 监听窗口状态变化 同步最大化按钮图标
        original_change = main_window.changeEvent

        def new_change_event(event):
            """
            状态变化回调, 窗口状态变化时同步最大化按钮图标

            Args:
                event: 状态变化事件对象
            """
            original_change(event)
            if event.type() == QtCore.QEvent.Type.WindowStateChange:
                self._sync_maximize_button()

        main_window.changeEvent = new_change_event

    def on_cursor_position_changed(self):
        """
        光标位置变化时的回调

        Args:
            self: 当前 UI 实例
        """
        self.handlers.on_cursor_position_changed()

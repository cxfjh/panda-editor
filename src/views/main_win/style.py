from PySide6 import QtCore
from src.utils.config_service import get_config_service
from src.utils.dialog_utils import DialogUtils
from src.utils.exceptions import safe_log
from src.views.main_win.refs import UiRefs


class StyleMixin(UiRefs):
    """主题 字号 语法高亮应用与启动流程编排"""

    def _setup_style(self, main_window):
        """
        设置编辑器样式

        Args:
            self: 当前 UI 实例
            main_window: 主窗口对象
        """

        def init_style(font_sizes=25, dark_mode=True, syntax_highlight=True, window_top=False):
            """
            应用字号 主题 语法高亮与置顶等样式

            Args:
                font_sizes: 字号, 默认 25
                dark_mode: 是否深色模式, 默认 True
                syntax_highlight: 是否启用语法高亮, 默认 True
                window_top: 是否窗口置顶, 默认 False
            """
            self.tab_manager.apply_font_size(font_sizes)

            self.tab_manager.apply_theme(dark_mode)

            # 语法高亮由各标签页的高亮器统一管理 这里仅做开关切换
            self.tab_manager.toggle_syntax_highlight(syntax_highlight)

            self.file_tree.apply_theme(dark_mode)
            self.terminal.apply_theme(dark_mode)
            self.blockly_panel.apply_theme(dark_mode)
            main_window.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint, window_top)
            main_window.show()

        try:
            settings = get_config_service().get_personal_config() or { }

            # 字号缺省或越界时回落到默认值, 避免样式初始化整体失败
            try:
                font_size = int(settings.get('fontSize', 25))
            except (TypeError, ValueError) as e:
                safe_log(f"字号配置非法, 回落默认值: {e}")
                font_size = 25
            init_style(
                max(6, min(90, font_size)),
                bool(settings.get('darkMode', True)),
                bool(settings.get('highlightSyntax', True)),
                bool(settings.get('windowTop', False)),
            )
        except Exception as e:
            DialogUtils.show_error(main_window, "样式配置", f"配置样式文件读取失败：\n{e}")

        # 恢复上次打开的标签页, 其中的空标签在恢复时已被跳过
        self.tab_manager.restore_tabs_state()

        # 处理启动时拖拽的文件/文件夹路径, 带了路径就不再管源码目录
        if not self._handle_launch_path():
            # 延到事件循环第一轮, 等主窗口真正显示后再弹目录选择, 避免窗口被对话框压到后面
            QtCore.QTimer.singleShot(0, self._ensure_source_directory)

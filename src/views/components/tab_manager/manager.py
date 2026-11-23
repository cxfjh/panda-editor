import os
from PySide6 import QtCore, QtWidgets
from PySide6.QtGui import QFont
from src.utils import theme
from src.utils.app_dialog import MessageDialog
from src.utils.dialog_utils import DialogUtils
from src.utils.syntax_high import CnHighlighter
from src.utils.syntax_hint import SyntaxHintManager
from src.views.components.editor import CodeEditor
from src.views.components.event_filters import FontSizeFilter
from src.views.components.find_replace import FindReplaceDialog
from src.views.components.tab_manager.file_ops import FileTabMixin
from src.views.components.tab_manager.models import TabData
from src.views.components.tab_manager.session import SessionMixin
from src.views.components.tab_manager.styles import build_tab_style


class TabManager(FileTabMixin, SessionMixin, QtCore.QObject):
    """标签页管理器"""

    # 信号定义
    tab_changed = QtCore.Signal()  # 标签页切换或光标位置变化时触发
    tab_count_changed = QtCore.Signal(int)  # 标签页数量变化时触发
    file_saved_as = QtCore.Signal(str)  # 未命名标签另存为后发出, 参数为新路径

    def __init__(self, tab_widget: QtWidgets.QTabWidget, parent=None):
        """
        初始化标签页管理器

        Args:
            self: 类实例自身
            tab_widget: QTabWidget 实例, UI 标签页组件
            parent: 父对象
        """
        super().__init__(parent)
        self.tab_widget = tab_widget
        self.tab_data_map: dict[int, TabData] = { }  # 标签索引
        self._dark_mode = True  # 默认深色主题
        self._font_size = 25  # 默认字体大小
        self._syntax_highlight = True  # 默认启用语法高亮
        self._max_tabs = 12  # 最大标签页数量限制

        self._setup_tab_style()

        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self.tab_widget.tabCloseRequested.connect(self._on_tab_close_requested)

    @property
    def dark_mode(self) -> bool:
        """
        获取当前是否为深色模式

        Returns:
            当前为深色模式返回 True, 否则返回 False
        """
        return self._dark_mode

    def _setup_tab_style(self):
        """
        设置标签页样式, 默认按深色初始化

        Args:
            self: 类实例自身
        """
        self._apply_tab_style(theme.colors(True))

    def _apply_tab_style(self, c: dict[str, str]):
        """
        应用标签页配色

        Args:
            self: 类实例自身
            c: 主题色板
        """
        self.tab_widget.setStyleSheet(build_tab_style(c))
        self.tab_widget.setTabsClosable(True)  # 显示关闭按钮
        self.tab_widget.setMovable(True)  # 允许拖拽排序

    def create_new_tab(self, file_path: str | None = None, content: str = "", encoding: str = "utf-8") -> int:
        """
        创建新标签页

        Args:
            self: 类实例自身
            file_path: 文件路径
            content: 初始内容
            encoding: 文件原始编码

        Returns:
            新标签页的索引
        """

        # 检查文件是否已经打开
        if file_path:
            for index, tab_data in self.tab_data_map.items():
                if tab_data.file_path == file_path:
                    self.tab_widget.setCurrentIndex(index)  # 切换到已打开的标签页
                    return index

        # 标签页数量达到上限时不再自动关闭已有标签, 交给用户处理
        if self.tab_widget.count() >= self._max_tabs:
            DialogUtils.show_warning(self.tab_widget, "标签页已达上限", f"最多同时打开 {self._max_tabs} 个标签页, 请先关闭部分标签页")
            return self.tab_widget.currentIndex()

        editor = CodeEditor(parent=self.tab_widget, dark_mode=self._dark_mode)
        editor.set_editor_font(QFont("Sarasa Mono SC", self._font_size))  # 更纱黑体
        editor.set_text(content)

        tab_data = TabData(file_path)
        tab_data.encoding = encoding
        tab_data.editor = editor

        font_filter = FontSizeFilter(editor, self._on_editor_font_size_changed)
        editor.installEventFilter(font_filter)
        tab_data.font_filter = font_filter

        # 编辑器先建好并设置字体, 高亮器构造时会按当前字号整篇着色
        is_cn_file = file_path and file_path.endswith('.cn')
        if self._syntax_highlight and is_cn_file:
            tab_data.highlighter = CnHighlighter(editor, self._dark_mode)

        tab_data.find_replace_dialog = FindReplaceDialog(editor, parent=self.tab_widget, dark_mode=self._dark_mode)

        # 为每个标签页创建语法补全管理器, 未命名文件同样可用, 非 .cn 文件内部自动禁用
        tab_data.syntax_hint = SyntaxHintManager(editor, dark_mode=self._dark_mode)
        tab_data.syntax_hint.set_current_file(file_path)

        tab_name = self._get_tab_name(file_path)
        tab_index = self.tab_widget.addTab(editor, tab_name)
        self.tab_data_map[tab_index] = tab_data

        self.tab_widget.setCurrentIndex(tab_index)

        # 首个标签页在 addTab 时就已成当前页, 那时数据还没入表, 这里补发一次
        self.tab_changed.emit()

        editor.updateUi.connect(self._on_cursor_position_changed)  # 光标移动 选区变化
        editor.notifyChange.connect(self._on_text_changed)  # 文本修改

        self.tab_count_changed.emit(self.tab_widget.count())
        return tab_index

    def get_current_tab_data(self) -> TabData | None:
        """
        获取当前标签页数据

        Returns:
            当前标签页数据, 无当前标签页时返回 None
        """
        current_index = self.tab_widget.currentIndex()
        if current_index < 0:
            return None
        return self.tab_data_map.get(current_index)

    def get_current_editor(self) -> CodeEditor | None:
        """
        获取当前标签页的编辑器

        Returns:
            当前标签页的编辑器, 无可用编辑器时返回 None
        """
        tab_data = self.get_current_tab_data()
        if tab_data:
            return tab_data.editor
        return None

    def get_current_file_path(self) -> str | None:
        """
        获取当前标签页的文件路径

        Returns:
            当前标签页的文件路径, 无可用路径时返回 None
        """
        tab_data = self.get_current_tab_data()
        if tab_data:
            return tab_data.file_path
        return None

    def index_of_path(self, file_path: str) -> int:
        """
        查找文件对应的标签页索引

        Args:
            self: 类实例自身
            file_path: 文件路径

        Returns:
            标签页索引, 文件未打开时返回 -1
        """
        if not file_path:
            return -1
        target = os.path.normcase(os.path.normpath(os.path.abspath(file_path)))
        for index, tab_data in self.tab_data_map.items():
            if not tab_data.file_path:
                continue
            current = os.path.normcase(os.path.normpath(os.path.abspath(tab_data.file_path)))
            if current == target:
                return index
        return -1

    def mark_tab_modified(self, index: int, modified: bool = True):
        """
        标记指定标签页的修改状态并刷新标题

        Args:
            self: 类实例自身
            index: 标签页索引
            modified: 是否有未保存的修改
        """
        tab_data = self.tab_data_map.get(index)
        if tab_data:
            tab_data.has_unsaved_changes = modified
            self._update_tab_title(index)

    def mark_current_tab_modified(self, modified: bool = True):
        """
        标记当前标签页为已修改

        Args:
            self: 类实例自身
            modified: 是否有未保存的修改
        """
        self.mark_tab_modified(self.tab_widget.currentIndex(), modified)

    def close_tab(self, index: int) -> bool:
        """
        关闭指定标签页

        Args:
            self: 类实例自身
            index: 标签页索引

        Returns:
            是否成功关闭
        """
        if index < 0 or index >= self.tab_widget.count():
            return False

        tab_data = self.tab_data_map.get(index)
        if tab_data and tab_data.has_unsaved_changes:
            save_dialog = MessageDialog(
                self.tab_widget, "保存文件",
                f"文件 '{self._get_tab_name(tab_data.file_path)}' 尚未保存, 是否保存？",
                "question", ("保存", "不保存", "取消"), True,
            )
            save_dialog.exec_centered()

            if save_dialog.clicked_button == "保存":
                if not self.save_tab(index):  # 保存失败则取消关闭
                    return False
            elif save_dialog.clicked_button == "取消":
                return False  # 用户取消操作

        # 清理标签页资源
        if tab_data:
            if tab_data.syntax_hint:
                tab_data.syntax_hint = None  # 父对象为编辑器, 随编辑器一并释放
            if tab_data.highlighter:
                tab_data.highlighter = None  # 父对象为编辑器, 随编辑器一并释放
            if tab_data.find_replace_dialog:
                tab_data.find_replace_dialog.close()
                tab_data.find_replace_dialog.deleteLater()
                tab_data.find_replace_dialog = None

        self.tab_widget.removeTab(index)
        if tab_data and tab_data.editor:
            tab_data.editor.deleteLater()
        if index in self.tab_data_map:
            del self.tab_data_map[index]

        self._remap_tab_data()

        self.tab_count_changed.emit(self.tab_widget.count())
        return True

    def close_all_tabs(self, force: bool = False):
        """
        关闭所有标签页

        Args:
            self: 类实例自身
            force: True 表示未保存的标签也一并关闭, 关闭前先静默存盘
        """
        for index in range(self.tab_widget.count() - 1, -1, -1):
            tab_data = self.tab_data_map.get(index)
            if tab_data and tab_data.has_unsaved_changes:
                if not force:
                    continue

                # 切目录前先静默存盘, 未命名的存不上就只能放弃
                self.save_tab(index, interactive=False)
                tab_data.has_unsaved_changes = False
            self.close_tab(index)

    def apply_theme(self, dark_mode: bool):
        """
        应用主题到所有标签页

        Args:
            self: 类实例自身
            dark_mode: True 表示深色主题, False 表示浅色主题
        """
        self._dark_mode = dark_mode
        self._apply_tab_style(theme.colors(dark_mode))
        for tab_data in self.tab_data_map.values():
            if tab_data.editor:
                tab_data.editor.set_dark_mode(dark_mode)

            if tab_data.highlighter:
                tab_data.highlighter.update_theme(dark_mode)
            if tab_data.syntax_hint:
                tab_data.syntax_hint.update_theme(dark_mode)
            if tab_data.find_replace_dialog:
                tab_data.find_replace_dialog.update_theme(dark_mode)

    def apply_font_size(self, font_size: int):
        """
        应用字体大小到所有标签页, 语法高亮由 fontChanged 信号自动重新上色

        Args:
            self: 类实例自身
            font_size: 字体大小
        """
        self._font_size = font_size
        for tab_data in self.tab_data_map.values():
            if tab_data.editor:
                tab_data.editor.set_editor_font(QFont("Sarasa Mono SC", font_size))

    def toggle_syntax_highlight(self, enable: bool):
        """
        切换语法高亮

        Args:
            self: 类实例自身
            enable: True 表示启用, False 表示禁用
        """
        self._syntax_highlight = enable
        for tab_data in self.tab_data_map.values():
            if tab_data.editor and tab_data.file_path and tab_data.file_path.endswith('.cn'):
                if enable and not tab_data.highlighter:
                    tab_data.highlighter = CnHighlighter(tab_data.editor, self._dark_mode)
                elif not enable and tab_data.highlighter:
                    tab_data.highlighter.remove()
                    tab_data.highlighter.deleteLater()
                    tab_data.highlighter = None

    def toggle_line_numbers(self, show: bool):
        """
        切换行号显示

        Args:
            self: 类实例自身
            show: True 表示显示行号, False 表示隐藏
        """
        for tab_data in self.tab_data_map.values():
            if tab_data.editor:
                tab_data.editor.set_show_line_numbers(show)

    def fold_all(self, expand: bool):
        """
        折叠或展开当前标签页的全部代码

        Args:
            self: 类实例自身
            expand: True 表示展开全部, False 表示折叠全部
        """
        editor = self.get_current_editor()
        if editor:
            editor.fold_all(expand)

    def _on_editor_font_size_changed(self, size: int):
        """
        编辑器通过 Ctrl 加滚轮改变字号时同步管理器状态

        Args:
            self: 类实例自身
            size: 新的字体大小
        """
        self._font_size = size

    def _on_tab_changed(self):
        """
        标签页切换时的回调

        Args:
            self: 类实例自身
        """
        self.tab_changed.emit()

    def _on_tab_close_requested(self, index: int):
        """
        关闭标签页请求

        Args:
            self: 类实例自身
            index: 要关闭的标签页索引
        """
        self.close_tab(index)

    def _on_cursor_position_changed(self):
        """
        光标位置变化时发出信号

        Args:
            self: 类实例自身
        """
        self.tab_changed.emit()

    def _on_text_changed(self):
        """
        文本内容变化时标记为已修改

        Args:
            self: 类实例自身
        """
        self.mark_current_tab_modified(True)

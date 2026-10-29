import os
from src.utils.dialog_utils import DialogUtils
from src.utils.exceptions import safe_log
from src.utils.file_ops import save_as_file
from src.utils.syntax_high import CnHighlighter
from src.utils.text_io import read_text_file_with_encoding
from src.views.components.tab_manager.paths import is_within
from src.views.components.tab_manager.refs import TabsRefs


class FileTabMixin(TabsRefs):
    """标签页文件读写相关方法, 由标签管理器混入使用"""

    def reload_tab(self, file_path: str, confirm_discard: bool = True) -> bool:
        """
        用磁盘上的内容重新载入已打开的文件

        Args:
            self: 类实例自身
            file_path: 文件路径
            confirm_discard: 编辑器里有未保存修改时是否先询问

        Returns:
            是否重新载入, 文件未打开或读取失败时返回 False
        """
        index = self.index_of_path(file_path)
        if index < 0:
            return False

        tab_data = self.tab_data_map.get(index)
        if not tab_data or not tab_data.editor:
            return False

        if tab_data.has_unsaved_changes and confirm_discard:
            message = f"「{os.path.basename(file_path)}」有未保存的修改, 重新载入会丢弃这些修改, 是否继续？"
            if not DialogUtils.ask_question(self.tab_widget, "重新载入文件", message):
                return False

        try:
            content, encoding = read_text_file_with_encoding(file_path)
        except Exception as e:
            DialogUtils.show_error(self.tab_widget, "重新载入失败", f"无法读取文件：\n{e}")
            return False

        tab_data.encoding = encoding
        tab_data.editor.set_text(content)  # set_text 会清空撤销栈并重置保存点
        tab_data.has_unsaved_changes = False
        self._update_tab_title(index)
        return True

    def rename_file_path(self, old_path: str, new_path: str):
        """
        文件被重命名后同步更新相关标签页, 重命名目录时同步其下的文件

        Args:
            self: 类实例自身
            old_path: 旧文件路径
            new_path: 新文件路径
        """
        for index, tab_data in self.tab_data_map.items():
            current_path: str = tab_data.file_path  # type: ignore
            if not current_path:
                continue
            if current_path == old_path:
                updated_path = new_path
            elif is_within(current_path, old_path):
                # 目录被重命名, 保留其下文件的相对路径
                updated_path = os.path.join(new_path, os.path.relpath(current_path, old_path))
            else:
                continue

            tab_data.file_path = updated_path
            if tab_data.syntax_hint:
                tab_data.syntax_hint.set_current_file(updated_path)
            self._update_tab_title(index)

    def handle_file_deleted(self, path: str):
        """
        文件被删除后关闭对应标签页, 删除目录时其下文件一并关闭

        Args:
            self: 类实例自身
            path: 被删除的路径
        """
        for index in range(self.tab_widget.count() - 1, -1, -1):
            tab_data = self.tab_data_map.get(index)
            if not tab_data or not tab_data.file_path:
                continue
            if not (tab_data.file_path == path or is_within(tab_data.file_path, path)):  # type: ignore
                continue
            if tab_data.has_unsaved_changes:
                # 有未保存修改时保留标签页, 内存内容可能是唯一副本
                continue
            self.close_tab(index)

    def save_tab(self, index: int, interactive: bool = True) -> bool:
        """
        保存指定标签页到文件

        Args:
            self: 类实例自身
            index: 标签页索引
            interactive: False 表示静默保存, 未命名标签直接放弃而不是弹另存为

        Returns:
            是否保存成功
        """
        tab_data = self.tab_data_map.get(index)
        if not tab_data or not tab_data.editor:
            return False

        content = tab_data.editor.text_all()

        # 未命名的标签页走另存为, 否则用户选了保存却什么也不会发生
        if not tab_data.file_path:
            if not interactive:
                return False
            return self.save_tab_as(index)

        try:
            with open(tab_data.file_path, 'w', encoding=tab_data.encoding) as f:
                f.write(content)
            tab_data.has_unsaved_changes = False
            self._update_tab_title(index)
            return True
        except Exception as e:
            if interactive:
                DialogUtils.show_error(self.tab_widget, "保存失败", f"保存文件出错：\n{e}")
            else:
                safe_log(f"静默保存 {tab_data.file_path} 失败: {e}")
            return False

    def save_tab_as(self, index: int) -> bool:
        """
        另存为, 始终弹出路径选择对话框, 写成 UTF-8 并同步补全与高亮与标题

        Args:
            self: 类实例自身
            index: 标签页索引

        Returns:
            是否保存成功
        """
        tab_data = self.tab_data_map.get(index)
        if not tab_data or not tab_data.editor:
            return False

        file_path = save_as_file(tab_data.editor.text_all())
        if not file_path:
            return False

        tab_data.file_path = file_path
        tab_data.encoding = "utf-8"  # 另存为统一写成 UTF-8
        if tab_data.syntax_hint:
            tab_data.syntax_hint.set_current_file(file_path)
        if self._syntax_highlight and file_path.endswith('.cn') and not tab_data.highlighter:
            tab_data.highlighter = CnHighlighter(tab_data.editor, self._dark_mode)
        tab_data.has_unsaved_changes = False
        self._update_tab_title(index)
        self.file_saved_as.emit(file_path)  # 主窗口据此同步文件树与终端目录
        return True

    def _update_tab_title(self, index: int):
        """
        更新标签页标题

        Args:
            self: 类实例自身
            index: 标签页索引
        """
        tab_data = self.tab_data_map.get(index)
        if tab_data:
            tab_name = self._get_tab_name(tab_data.file_path)
            if tab_data.has_unsaved_changes:
                tab_name += " *"  # 未保存文件添加 * 标记

            # 每敲一个字符都会走到这里, 标题没变就不必重设
            if self.tab_widget.tabText(index) != tab_name:
                self.tab_widget.setTabText(index, tab_name)

    @staticmethod
    def _get_tab_name(file_path: str | None) -> str:
        """
        获取标签页名称

        Args:
            file_path: 文件路径

        Returns:
            文件名或未命名
        """
        if not file_path:
            return "未命名"
        return os.path.basename(file_path)

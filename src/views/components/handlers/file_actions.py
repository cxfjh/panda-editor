import os
from src import __version__
from src.utils.dialog_utils import DialogUtils
from src.utils.file_ops import open_directory
from src.utils.text_io import read_text_file_with_encoding
from src.views.components.handlers.base import HandlerBase


class FileActions(HandlerBase):
    """文件与标签页动作"""

    def on_open_directory(self):
        """
        处理打开目录操作

        Args:
            self: 类实例自身
        """
        try:
            dir_path = open_directory()
            if dir_path:
                # 统一交给主窗口完成配置更新, 文件树与终端目录同步
                self.ui.open_directory(dir_path)  # type: ignore
        except Exception as e:
            DialogUtils.show_error(self.ui.main_window, "打开失败", f"无法打开目录:\n{e}")

    def on_save_file(self):
        """
        处理保存文件操作

        Args:
            self: 类实例自身
        """
        index = self.ui.tab_manager.tab_widget.currentIndex()
        self.ui.tab_manager.save_tab(index)

    def on_save_as_file(self):
        """
        处理另存为文件操作

        Args:
            self: 类实例自身
        """
        self.ui.tab_manager.save_tab_as(self.ui.tab_manager.tab_widget.currentIndex())

    def on_close_tab(self):
        """
        关闭当前标签页, 对应 Ctrl+W

        Args:
            self: 类实例自身
        """
        self.ui.tab_manager.close_tab(self.ui.tab_manager.tab_widget.currentIndex())

    def on_next_tab(self):
        """
        切换到下一个标签页, 对应 Ctrl+Tab

        Args:
            self: 类实例自身
        """
        self._switch_tab(1)

    def on_previous_tab(self):
        """
        切换到上一个标签页, 对应 Ctrl+Shift+Tab

        Args:
            self: 类实例自身
        """
        self._switch_tab(-1)

    def _switch_tab(self, step: int):
        """
        在当前标签页之间循环切换

        Args:
            self: 类实例自身
            step: 1 表示下一个, -1 表示上一个
        """
        tabs = self.ui.tab_manager.tab_widget
        count = tabs.count()
        if count > 1:
            tabs.setCurrentIndex((tabs.currentIndex() + step) % count)

    def on_file_tree_selected(self, file_path: str):
        """
        处理文件树双击事件, 打开选中的文件

        Args:
            self: 类实例自身
            file_path: 双击选中的文件完整路径
        """
        self.auto_save()  # 先保存当前文件

        try:
            # 直接从磁盘读取文件内容, 自动兼容 UTF-8 与 GBK
            content, encoding = read_text_file_with_encoding(file_path)

            # 拆解文件路径信息
            file_dir, file_name = os.path.split(file_path)
            base_name, _ = os.path.splitext(file_name)

            # 检查文件是否已经在标签页中打开
            already_open = False
            for index in range(self.ui.tab_manager.tab_widget.count()):
                tab_data = self.ui.tab_manager.tab_data_map.get(index)
                if tab_data and tab_data.file_path == file_path:
                    already_open = True

                    # 文件已打开切换到该标签页并重新加载最新内容
                    self.ui.tab_manager.tab_widget.setCurrentIndex(index)
                    if tab_data.editor:
                        tab_data.editor.set_text(content)
                        tab_data.encoding = encoding

                        # 清除修改标记并刷新标题
                        self.ui.tab_manager.mark_current_tab_modified(False)
                    break

            if not already_open:
                # 文件未打开创建新标签页
                self.ui.tab_manager.create_new_tab(file_path=file_path, content=content, encoding=encoding)

                # 更新语法补全的当前文件
                tab_data = self.ui.tab_manager.get_current_tab_data()
                if tab_data and tab_data.syntax_hint:
                    tab_data.syntax_hint.set_current_file(file_path)

                # 更新终端工作目录
                self.ui.terminal.set_working_directory(file_dir)

                # 更新状态栏
                self.on_cursor_position_changed()

            # 当前文件信息由 TabManager 持有, 无需再写入配置
        except Exception as e:
            DialogUtils.show_error(self.ui.main_window, "打开失败", f"无法打开文件:\n{e}")

    def on_cursor_position_changed(self):
        """
        光标位置变化时, 更新状态栏的行号和文件信息

        Args:
            self: 类实例自身
        """
        current_editor = self.ui.tab_manager.get_current_editor()
        if not current_editor:
            return

        # 计算当前光标所在行号
        cursor_line_number = current_editor.lineFromPosition(current_editor.currentPos()) + 1  # 行号从 1 开始
        file_path = self.ui.tab_manager.get_current_file_path() or "未命名"

        # 更新状态栏显示
        spaces = ' ' * 10
        self.ui.status_label.setText(f"行号: {cursor_line_number}{spaces}文件: {file_path}{spaces}版本: v{__version__}")

    def auto_save(self):
        """
        自动保存所有有未保存修改的标签页, 失败静默记录

        Args:
            self: 类实例自身
        """
        tab_manager = self.ui.tab_manager
        for index in range(tab_manager.tab_widget.count()):
            tab_data = tab_manager.tab_data_map.get(index)
            if not tab_data or not tab_data.file_path or not tab_data.has_unsaved_changes:
                continue
            tab_manager.save_tab(index, interactive=False)

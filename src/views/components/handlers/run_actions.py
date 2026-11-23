import os
from src.utils.code_proc import compile_code, parse_to_python_code_path
from src.utils.dialog_utils import DialogUtils
from src.views.components.handlers.base import HandlerBase, is_cn_path


class RunActions(HandlerBase):
    """运行与编译动作"""

    def on_run_code(self):
        """
        处理运行代码操作

        Args:
            self: 类实例自身
        """

        # 以当前标签页为准判断文件类型, 不再依赖配置里的陈旧状态
        if not is_cn_path(self.ui.tab_manager.get_current_file_path()):
            DialogUtils.show_error(self.ui.main_window, "运行失败", "只能运行已保存的 .cn 格式中文代码文件")
            return

        if not self._save_current_file():
            return

        current_editor = self.ui.tab_manager.get_current_editor()
        if current_editor:
            # 解析中文代码为 Python, 获取转换后的 .py 路径
            py_path = parse_to_python_code_path(current_editor.text_all(), self.ui.tab_manager.get_current_file_path())
            if py_path:
                self.ui.terminal.run_python_script(py_path, os.path.dirname(py_path))

    def on_compile_code(self):
        """
        处理编译代码操作

        Args:
            self: 类实例自身
        """
        if not is_cn_path(self.ui.tab_manager.get_current_file_path()):
            DialogUtils.show_error(self.ui.main_window, "编译失败", "只能编译已保存的 .cn 格式中文代码文件")
            return

        if not self._save_current_file():
            return

        current_editor = self.ui.tab_manager.get_current_editor()
        if current_editor:
            # 直接传递文件路径, 不修改全局配置
            compile_code(current_editor.text_all(), self.ui.tab_manager.get_current_file_path())

    def _save_current_file(self) -> bool:
        """
        保存当前文件, 成功返回 True, 失败返回 False

        Args:
            self: 类实例自身

        Returns:
            保存成功返回 True, 否则返回 False
        """
        index = self.ui.tab_manager.tab_widget.currentIndex()
        return self.ui.tab_manager.save_tab(index, interactive=False)

    def on_compile_log(self, log: str):
        """
        处理编译日志输出

        Args:
            self: 类实例自身
            log: 编译日志文本
        """
        self.ui.terminal.append_output(log)

    def on_compile_finished(self, success: bool, msg: str):
        """
        处理编译完成事件

        Args:
            self: 类实例自身
            success: 编译是否成功
            msg: 失败原因
        """
        if success:
            self.ui.terminal.append_output("\n> 编译成功，已打开输出目录\n")
        else:
            self.ui.terminal.append_output(f"\n> 编译失败：{msg}\n")

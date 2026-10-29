import os
from src.utils.blockly.file_output import CN_FILE_FILTER, ensure_cn_extension, read_code_file, write_generated_code
from src.utils.blockly.workspace_io import default_directory
from src.utils.config_service import get_config_service
from src.utils.dialog_utils import DialogUtils
from src.views.blockly.panel import constants
from src.views.blockly.panel.refs import PanelRefs


class CodegenMixin(PanelRefs):
    """目标文件选择与代码写入相关方法, 由积木面板混入使用"""

    @staticmethod
    def _load_append_mode() -> bool:
        """
        从配置读取上次使用的写入方式

        Returns:
            True 为追加, False 为覆盖
        """
        return bool(get_config_service().get_app_config(constants.CONFIG_WRITE_APPEND))

    def choose_target(self) -> bool:
        """
        选择生成的代码要写入的 .cn 文件

        Args:
            self: 当前面板实例

        Returns:
            True 表示已选定文件
        """
        start_dir = self._target_path or default_directory()
        file_path = DialogUtils.save_file_dialog(self.window(), "选择代码输出文件", CN_FILE_FILTER, start_dir)
        if not file_path:
            return False

        # 另存对话框本身已让用户确认过覆盖, 这里不再重复询问
        self.set_target_path(ensure_cn_extension(file_path), confirmed=True)
        return True

    def set_target_path(self, file_path: str, confirmed: bool = False):
        """
        设置输出文件并写入配置

        Args:
            self: 当前面板实例
            file_path: 目标文件路径
            confirmed: True 表示用户刚刚通过对话框选定, 覆盖时无需再次确认
        """
        self._target_path = file_path
        if confirmed:
            self._confirmed_paths.add(file_path)
        self.target_edit.setText(file_path)
        self.target_edit.setToolTip(file_path)
        get_config_service().update_app_config(constants.CONFIG_TARGET_FILE, file_path)
        self._set_status(f"输出文件: {os.path.basename(file_path)}")

    @staticmethod
    def _on_mode_changed(index: int):
        """
        记录写入方式

        Args:
            index: 0 为覆盖, 1 为追加
        """
        get_config_service().update_app_config(constants.CONFIG_WRITE_APPEND, index == 1)

    def _on_generate_clicked(self):
        """
        工具栏生成代码按钮

        Args:
            self: 当前面板实例
        """
        self.generate_code()

    def generate_code(self):
        """
        请求页面生成 CnLang 代码

        Args:
            self: 当前面板实例
        """
        if not self._page_ready:
            self._set_status("积木编辑器尚未就绪, 请稍候")
            return
        if not self._target_path and not self.choose_target():
            self._set_status("未指定输出文件, 已取消生成")
            return
        self.bridge.generate_requested.emit()

    def _on_code_submitted(self, code: str):
        """
        接收页面回传的代码并写入目标文件

        Args:
            self: 当前面板实例
            code: 生成的 CnLang 代码
        """
        if not code.strip():
            DialogUtils.show_warning(self.window(), "没有可生成的积木", "积木工作区还是空的, 请先拼出积木再点击「生成代码」")
            self._set_status("工作区为空")
            return

        # 目标文件可能在生成期间被清空配置, 这里再兜底一次
        if not self._target_path and not self.choose_target():
            self._set_status("未指定输出文件, 已取消写入")
            return

        path = self._target_path
        append = self.mode_combo.currentIndex() == 1

        # 覆盖一个已有内容的文件时先确认一次, 同一文件在本次会话中不再重复询问
        if not append and path not in self._confirmed_paths and read_code_file(path).strip():
            if not DialogUtils.ask_question(self.window(), "覆盖文件", f"「{os.path.basename(path)}」已有内容, 确定用生成的代码替换它吗？"):
                self._set_status("已取消写入")
                return

        try:
            lines = write_generated_code(path, code, append)
        except OSError as e:
            DialogUtils.show_error(self.window(), "写入失败", f"无法写入文件：\n{path}\n\n{e}")
            self._set_status("写入失败")
            return

        self._confirmed_paths.add(path)
        action = "追加" if append else "写入"
        self._set_status_result(f"已{action} {lines} 行到 {os.path.basename(path)}")
        self.code_written.emit(path)
        self._request_workspace_autosave()

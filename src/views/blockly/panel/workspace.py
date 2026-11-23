import os
from src.utils.blockly.workspace_io import default_directory, load_workspace_xml, read_workspace_file, save_workspace_xml, workspace_path_for, write_workspace_silently
from src.utils.config_service import get_config_service
from src.utils.dialog_utils import DialogUtils
from src.utils.exceptions import safe_log
from src.views.blockly.panel import constants
from src.views.blockly.panel.refs import PanelRefs


class WorkspaceMixin(PanelRefs):
    """工作区 XML 读写相关方法, 由积木面板混入使用"""

    @staticmethod
    def _load_workspace_file() -> str:
        """
        从配置读取上次生成代码时自动保存的积木文件

        Returns:
            积木文件路径, 未配置时返回空字符串
        """
        value = get_config_service().get_app_config(constants.CONFIG_WORKSPACE_FILE)
        return value if isinstance(value, str) else ""

    def _restore_workspace(self):
        """
        面板打开后自动加载上次生成代码时保存的积木

        Args:
            self: 当前面板实例
        """
        for path in (self._workspace_file, workspace_path_for(self._target_path)):
            xml = read_workspace_file(path)
            if not xml:
                continue
            self._workspace_file = path
            self.bridge.load_workspace_requested.emit(xml)
            return

    def _request_workspace_autosave(self):
        """
        生成代码后请求页面回传工作区, 以便保存到代码文件同名的 xml

        Args:
            self: 当前面板实例
        """
        if not self._target_path or self._pending_save_mode:
            return
        self._pending_save_mode = "auto"
        self.bridge.workspace_requested.emit()

    def save_workspace(self):
        """
        请求页面回传工作区并保存为 XML 文件

        Args:
            self: 当前面板实例
        """
        if not self._page_ready:
            self._set_status("积木编辑器尚未就绪, 请稍候")
            return
        self._pending_save_mode = "dialog"
        self.bridge.workspace_requested.emit()

    def _on_workspace_submitted(self, xml: str):
        """
        接收页面回传的工作区 XML, 按等待中的动作落盘

        Args:
            self: 当前面板实例
            xml: Blockly 原生 XML 文本
        """
        mode = self._pending_save_mode
        self._pending_save_mode = ""
        if mode == "dialog":
            file_path = save_workspace_xml(self.window(), xml, default_directory())
            if file_path:
                self._set_status(f"积木已保存: {os.path.basename(file_path)}")
            return
        if mode == "auto" and self._target_path:
            self._save_workspace_beside_code(xml)

    def _save_workspace_beside_code(self, xml: str):
        """
        把工作区静默保存到代码文件同名的 xml, 并记录到配置

        Args:
            self: 当前面板实例
            xml: Blockly 原生 XML 文本
        """
        file_path = workspace_path_for(self._target_path)
        if not write_workspace_silently(file_path, xml):
            return
        self._workspace_file = file_path
        get_config_service().update_app_config(constants.CONFIG_WORKSPACE_FILE, file_path)

    def load_workspace(self):
        """
        从 XML 文件加载工作区

        Args:
            self: 当前面板实例
        """
        if not self._page_ready:
            self._set_status("积木编辑器尚未就绪, 请稍候")
            return
        xml = load_workspace_xml(self.window(), default_directory())
        if not xml:
            return
        self.bridge.load_workspace_requested.emit(xml)
        self._set_status_result("已加载积木工作区")

    def clear_workspace(self):
        """
        确认后清空工作区

        Args:
            self: 当前面板实例
        """
        if not self._page_ready:
            self._set_status("积木编辑器尚未就绪, 请稍候")
            return
        if not DialogUtils.ask_question(self.window(), "清空积木", "确定要清空当前积木工作区吗？此操作无法撤销"):
            return
        self.bridge.clear_workspace_requested.emit()
        self._discard_workspace_snapshot()
        self._set_status_result("工作区已清空")

    def _discard_workspace_snapshot(self):
        """
        删除生成代码时自动保存的积木快照, 免得清空后下次打开又被恢复

        Args:
            self: 当前面板实例
        """
        path = self._workspace_file or workspace_path_for(self._target_path)
        if path and os.path.isfile(path):
            try:
                os.remove(path)
            except OSError as e:
                safe_log(f"删除积木快照失败: {e}")
        self._workspace_file = ""
        get_config_service().update_app_config(constants.CONFIG_WORKSPACE_FILE, "")

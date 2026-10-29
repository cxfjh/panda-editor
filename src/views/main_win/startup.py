import os
from src.utils.config_service import get_config_service
from src.utils.dialog_utils import DialogUtils
from src.utils.exceptions import safe_log
from src.utils.file_ops import open_directory as choose_directory
from src.utils.file_ops import split_file_path
from src.utils.text_io import read_text_file_with_encoding
from src.views.main_win.refs import UiRefs


# 新建 code.cn 时写入的示例代码, 让用户打开就能直接运行看到效果
_NEW_FILE_CONTENT = '输出*（“你好，世界”）\n'


class StartupMixin(UiRefs):
    """源码目录 拖拽入口与文件打开相关方法"""

    def _init_file_tree(self):
        """
        初始化文件树根目录和工作目录

        Args:
            self: 当前 UI 实例
        """
        source_code_path = get_config_service().get_file_config("source_code_path")
        if source_code_path and os.path.isdir(source_code_path):
            self.file_tree.set_root_path(source_code_path)
            self.terminal.set_working_directory(source_code_path)

    def _ensure_source_directory(self):
        """
        启动时处理源码目录

        Args:
            self: 当前 UI 实例
        """
        source_path = get_config_service().get_file_config("source_code_path") or ""
        if source_path and os.path.isdir(source_path):
            self._open_workspace_file(source_path)
            return

        # 先把主窗口拉到前台, 再让对话框挂到它上面, 关闭后焦点才会回到主窗口
        self.main_window.raise_()
        self.main_window.activateWindow()
        chosen = choose_directory() or ""
        self.main_window.raise_()
        self.main_window.activateWindow()

        if not chosen:
            self.tab_manager.close_all_tabs(force=True)
            return

        # 用户刚选的目录算切换目录, 交给 open_directory 清空旧标签再打开 code.cn
        self.open_directory(chosen)

    def _open_workspace_file(self, dir_path: str):
        """
        有目录却没有任何标签时, 打开该目录的 code.cn

        Args:
            self: 当前 UI 实例
            dir_path: 源码目录
        """
        if self.tab_manager.tab_widget.count() > 0:
            return

        file_path = self._ensure_code_file(dir_path)
        if not file_path:
            return

        split_file_path(file_path)
        try:
            content, encoding = read_text_file_with_encoding(file_path)
        except Exception as e:
            safe_log(f"读取 {file_path} 失败: {e}")
            return

        self.tab_manager.create_new_tab(file_path=file_path, content=content, encoding=encoding)
        self.handlers.on_cursor_position_changed()

    @staticmethod
    def _ensure_code_file(dir_path: str) -> str:
        """
        确保目录下存在 code.cn, 缺失时带示例代码创建一个

        Args:
            dir_path: 目录路径

        Returns:
            code.cn 的完整路径, 创建失败时返回空字符串
        """
        file_path = os.path.join(dir_path, "code.cn")
        if os.path.isfile(file_path):
            return file_path
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(_NEW_FILE_CONTENT)
        except OSError as e:
            safe_log(f"创建 code.cn 失败: {e}")
            return ""
        return file_path

    def _handle_launch_path(self) -> bool:
        """
        处理启动时通过拖拽或命令行传入的文件或文件夹路径

        Args:
            self: 当前 UI 实例

        Returns:
            True 表示已按传入路径打开, 不需要再补默认的 code.cn
        """
        launch_path = self.main_window.property("launch_path")
        if not launch_path:
            return False

        launch_path = launch_path.strip().strip('"').strip("'")

        if not os.path.exists(launch_path):
            DialogUtils.show_warning(self.main_window, "路径无效", f"找不到指定的路径：\n{launch_path}")
            return False

        # 先判断是否为目录
        if os.path.isdir(launch_path):
            self.open_directory(launch_path)
            return True
        if os.path.isfile(launch_path):
            self._open_file(launch_path)
            return True

        DialogUtils.show_warning(self.main_window, "路径类型未知", f"无法识别的路径类型：\n{launch_path}")
        return False

    def open_directory(self, dir_path: str):
        """
        打开指定目录作为项目根目录, 清掉旧标签并打开目录里的 code.cn

        Args:
            self: 当前 UI 实例
            dir_path: 目录路径
        """
        normalized_path = os.path.normpath(dir_path)

        # 换目录后旧标签已不属于当前项目, 全部关掉, 未保存的先静默存盘
        self.tab_manager.close_all_tabs(force=True)
        get_config_service().update_file_config("source_code_path", normalized_path)
        self.file_tree.set_root_path(normalized_path)
        self.terminal.set_working_directory(normalized_path)

        # 目录里没有 code.cn 就建一个, 打开后可以直接写代码
        file_path = self._ensure_code_file(normalized_path)
        if file_path:
            split_file_path(file_path)
            try:
                content, encoding = read_text_file_with_encoding(file_path)
            except Exception as e:
                safe_log(f"读取 {file_path} 失败: {e}")
            else:
                self.tab_manager.create_new_tab(file_path=file_path, content=content, encoding=encoding)

        self.handlers.on_cursor_position_changed()

    def open_file(self, file_path: str):
        """
        打开文件到标签页, 供菜单动作等外部调用

        Args:
            self: 当前 UI 实例
            file_path: 文件路径
        """
        self._open_file(file_path)

    def _open_file(self, file_path: str):
        """
        打开指定文件

        Args:
            self: 当前 UI 实例
            file_path: 文件路径
        """
        normalized_path = os.path.normpath(file_path)

        # 更新文件树的根目录为文件所在目录
        file_dir = os.path.dirname(normalized_path)
        get_config_service().update_file_config("source_code_path", file_dir)
        self.file_tree.set_root_path(file_dir)
        self.terminal.set_working_directory(file_dir)

        # 读取文件内容并创建标签页, 自动兼容 UTF-8 与 GBK
        try:
            content, encoding = read_text_file_with_encoding(normalized_path)
            self.tab_manager.create_new_tab(file_path=normalized_path, content=content, encoding=encoding)
            self.handlers.on_cursor_position_changed()
        except Exception as e:
            DialogUtils.show_error(self.main_window, "打开失败", f"无法打开文件：\n{normalized_path}\n错误：{e}", )

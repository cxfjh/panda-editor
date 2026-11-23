import os
import subprocess
from src.utils.app_dialog import ask_question, get_text, show_message
from src.utils.exceptions import safe_log
from src.utils.recycle_bin import move_to_recycle_bin
from src.views.file_tree.items import PATH_ROLE, set_item_appearance
from src.views.file_tree.refs import TreeRefs


class FileOperations(TreeRefs):
    """文件树节点操作集合, 由视图类混入使用"""

    def _show_input_dialog(self, title, label, default_text=""):
        """
        显示输入对话框

        Args:
            self: 当前视图实例
            title: 对话框标题
            label: 提示文本
            default_text: 默认输入值

        Returns:
            用户输入的文本, 取消时返回 None
        """
        value = get_text(self, title, label, default_text, self._dark_mode)
        return value.strip() if value else None

    def _show_message(self, icon, title, text):
        """
        显示提示弹窗

        Args:
            self: 当前视图实例
            icon: 图标类型, info / warning / error
            title: 弹窗标题
            text: 正文内容
        """
        show_message(self, title, text, icon, self._dark_mode)

    def _ask_question(self, title, text):
        """
        显示确认弹窗

        Args:
            self: 当前视图实例
            title: 弹窗标题
            text: 正文内容

        Returns:
            True 表示用户点了"是"
        """
        return ask_question(self, title, text, self._dark_mode)

    def _new_file(self, dir_path: str):
        """
        新建文件

        Args:
            self: 当前视图实例
            dir_path: 文件所在目录路径
        """
        name = self._show_input_dialog("新建文件", "请输入文件名:")
        if not name:
            return
        if not os.path.splitext(name)[1]:
            name += ".cn"
        file_path = os.path.join(dir_path, name)
        if os.path.exists(file_path):
            self._show_message("warning", "警告", f"文件已存在:\n{file_path}")
            return
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('')  # 创建空文件
            self._refresh_parent(dir_path)
        except Exception as e:
            safe_log(f"创建文件失败: {e}")
            self._show_message("error", "错误", f"创建文件失败:\n{e}")

    def _new_folder(self, dir_path: str):
        """
        新建文件夹

        Args:
            self: 当前视图实例
            dir_path: 文件夹所在目录路径
        """
        name = self._show_input_dialog("新建文件夹", "请输入文件夹名:")
        if not name:
            return
        folder_path = os.path.join(dir_path, name)
        if os.path.exists(folder_path):
            self._show_message("warning", "警告", f"文件夹已存在:\n{folder_path}")
            return
        try:
            os.makedirs(folder_path, exist_ok=True)
            self._refresh_parent(dir_path)
        except Exception as e:
            safe_log(f"创建文件夹失败: {e}")
            self._show_message("error", "错误", f"创建文件夹失败:\n{e}")

    def _rename_item(self, item, old_path: str):
        """
        重命名文件或文件夹

        Args:
            self: 当前视图实例
            item: 被重命名的树节点
            old_path: 旧的完整路径
        """
        old_name = os.path.basename(old_path)
        new_name = self._show_input_dialog("重命名", "请输入新名称:", old_name)
        if not new_name or new_name == old_name:
            return
        new_path = os.path.join(os.path.dirname(old_path), new_name)  # type: ignore
        if os.path.exists(new_path):
            self._show_message("warning", "警告", f"已存在同名文件/文件夹:\n{new_path}")
            return
        try:
            os.rename(old_path, new_path)

            # 更新节点显示与图标
            set_item_appearance(item, new_name, new_path)  # type: ignore
            item.setData(0, PATH_ROLE, new_path)
            self.signals.file_renamed.emit(old_path, new_path)
        except Exception as e:
            safe_log(f"重命名失败: {e}")
            self._show_message("error", "错误", f"重命名失败:\n{e}")

    def _delete_item(self, item, path: str):
        """
        删除文件或文件夹

        Args:
            self: 当前视图实例
            item: 树节点对象
            path: 要删除的文件或文件夹路径
        """
        name = os.path.basename(path)
        kind = "文件夹" if os.path.isdir(path) else "文件"
        if not self._ask_question("确认删除", f"确定要删除 {kind} 吗?\n{name}"):
            return
        try:
            # 删除内容, 优先进回收站, 避免误删后无法恢复
            if not move_to_recycle_bin(path):
                raise OSError("无法移入回收站")

            # 从树控件中移除节点
            parent = item.parent()
            if parent:
                parent.removeChild(item)
            else:
                self.tree.invisibleRootItem().removeChild(item)

            self.signals.file_deleted.emit(path)
        except Exception as e:
            safe_log(f"删除失败: {e}")
            self._show_message("error", "错误", f"删除失败:\n{e}")

    def _open_in_explorer(self, path: str):
        """
        在资源管理器中打开文件或文件夹

        Args:
            self: 当前视图实例
            path: 文件或文件夹路径
        """
        try:
            if os.path.isfile(path):
                # 打开文件所在目录并选中文件, 用参数列表避免路径中的引号被 shell 解析
                subprocess.Popen(["explorer", f"/select,{path}"])
            else:
                os.startfile(path)
        except Exception as e:
            safe_log(f"打开资源管理器失败: {e}")
            self._show_message("error", "错误", f"打开资源管理器失败:\n{e}")

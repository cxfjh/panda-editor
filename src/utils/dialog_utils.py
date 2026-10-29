from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget
from src.utils.app_dialog import ask_question, show_message
from src.utils.config_service import get_config_service


class DialogUtils:
    """对话框工具类"""

    # 全局父窗口引用
    _parent_widget: QWidget | None = None

    @staticmethod
    def set_parent_widget(widget: QWidget | None) -> None:
        """
        设置全局父窗口引用

        Args:
            widget: 父窗口, 用于给后续弹窗提供父对象
        """
        DialogUtils._parent_widget = widget

    @staticmethod
    def parent_widget() -> QWidget | None:
        """
        取全局父窗口引用

        Returns:
            已设置的父窗口, 未设置时返回 None
        """
        return DialogUtils._parent_widget

    @staticmethod
    def _dark_mode() -> bool:
        """
        取当前主题是否为深色, 弹窗背景要跟着主界面走

        Returns:
            True 表示深色主题
        """
        settings = get_config_service().get_personal_config() or {}
        return bool(settings.get("darkMode", True))

    @staticmethod
    def _icon_name(icon: QMessageBox.Icon) -> str:
        """
        把消息框图标换成自绘弹窗的图标名

        Args:
            icon: 消息框图标

        Returns:
            图标名, 取 info / warning / error / question 之一
        """
        mapping = {
            QMessageBox.Icon.Critical: "error",
            QMessageBox.Icon.Warning: "warning",
            QMessageBox.Icon.Question: "question",
        }
        return mapping.get(icon, "info")

    @staticmethod
    def _show_message_box(parent: QWidget | None, icon: QMessageBox.Icon, title: str, message: str, detail: str = "") -> None:
        """
        展示消息对话框

        Args:
            parent: 父窗口
            icon: 消息图标
            title: 对话框标题
            message: 消息内容
            detail: 详细信息
        """
        text = message if not detail else f"{message}\n\n{detail}"
        show_message(parent, title, text, DialogUtils._icon_name(icon), DialogUtils._dark_mode())

    @staticmethod
    def show_error(parent: QWidget | None, title: str, message: str, detail: str = "") -> None:
        """
        展示错误对话框

        Args:
            parent: 父窗口
            title: 对话框标题
            message: 错误信息
            detail: 详细信息
        """
        DialogUtils._show_message_box(parent, QMessageBox.Icon.Critical, title, message, detail)

    @staticmethod
    def show_warning(parent: QWidget | None, title: str, message: str) -> None:
        """
        展示警告对话框

        Args:
            parent: 父窗口
            title: 对话框标题
            message: 警告信息
        """
        DialogUtils._show_message_box(parent, QMessageBox.Icon.Warning, title, message)

    @staticmethod
    def show_info(parent: QWidget | None, title: str, message: str) -> None:
        """
        展示信息对话框

        Args:
            parent: 父窗口
            title: 对话框标题
            message: 提示信息
        """
        DialogUtils._show_message_box(parent, QMessageBox.Icon.Information, title, message)

    @staticmethod
    def ask_question(parent: QWidget | None, title: str, message: str) -> bool:
        """
        展示确认对话框

        Args:
            parent: 父窗口
            title: 对话框标题
            message: 确认信息

        Returns:
            bool, 用户确认返回 True, 取消返回 False
        """
        return ask_question(parent, title, message, DialogUtils._dark_mode())

    @staticmethod
    def _file_dialog(parent: QWidget | None, title: str, file_filter: str, directory: str, save: bool) -> str:
        """
        文件选择对话框

        Args:
            parent: 父窗口
            title: 对话框标题
            file_filter: 文件过滤器
            directory: 默认目录
            save: True 为保存对话框, False 为打开对话框

        Returns:
            str, 选中的文件路径, 取消返回空字符串
        """
        if save:
            file_path, _ = QFileDialog.getSaveFileName(parent, title, directory, file_filter)
        else:
            file_path, _ = QFileDialog.getOpenFileName(parent, title, directory, file_filter)
        return file_path or ""

    @staticmethod
    def save_file_dialog(parent: QWidget | None, title: str, file_filter: str, directory: str = "") -> str:
        """
        保存文件对话框

        Args:
            parent: 父窗口
            title: 对话框标题
            file_filter: 文件过滤器
            directory: 默认目录

        Returns:
            str, 保存路径, 取消返回空字符串
        """
        return DialogUtils._file_dialog(parent, title, file_filter, directory, save=True)

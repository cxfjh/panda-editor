import os
from PySide6.QtWidgets import QFileDialog
from src.utils.config_service import get_config_service
from src.utils.dialog_utils import DialogUtils
from src.utils.exceptions import safe_log
from src.utils.text_io import read_text_file_with_encoding


def _get_current_file_path() -> str | None:
    """
    获取当前配置中的文件路径

    Returns:
        规范化的文件完整路径若配置不完整则返回 None
    """
    source_dir = get_config_service().get_file_config("source_code_path")
    code_name = get_config_service().get_file_config("code_name")
    file_ext = get_config_service().get_file_config("file_ext") or ".cn"
    if not all([source_dir, code_name]): return None  # 配置不完整, 返回 None
    return os.path.normpath(os.path.join(source_dir, f"{code_name}{file_ext}"))


def split_file_path(file_path: str | None) -> None:
    """
    解析文件路径更新目录文件名和扩展名配置

    Args:
        file_path: 文件完整路径为 None 时不执行任何操作
    """
    if not file_path: return
    file_dir, file_name = os.path.split(file_path)
    base_name, file_ext = os.path.splitext(file_name)
    get_config_service().update_file_config("code_name", base_name)
    get_config_service().update_file_config("source_code_path", os.path.normpath(file_dir))
    get_config_service().update_file_config("file_ext", file_ext)


def open_directory() -> str | None:
    """
    打开目录选择对话框, 仅负责选择, 打开逻辑由调用方完成

    Returns:
        选中的目录路径, 用户取消或发生错误则返回 None
    """
    try:
        dir_path = QFileDialog.getExistingDirectory(DialogUtils.parent_widget(), "打开目录")
        if dir_path:
            return os.path.normpath(dir_path)
    except Exception as e:
        safe_log(f"打开目录失败: {e}")
        DialogUtils.show_error(DialogUtils.parent_widget(), "打开失败", f"无法打开目录：\n{e}")
    return None


def write_text_file(file_path: str, content: str, encoding: str = "utf-8") -> bool:
    """
    低层文本写入供所有保存操作复用

    Args:
        file_path: 目标文件完整路径
        content: 要写入的内容
        encoding: 写入编码, 打开的文件沿用其原始编码

    Returns:
        写入成功返回 True, 失败返回 False
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        safe_log(f"写入文件失败: {e}")
        DialogUtils.show_error(DialogUtils.parent_widget(), "写入失败", f"写入文件出错：\n{e}")
        return False


def save_as_file(content: str) -> str | None:
    """
    另存为新文件并更新配置

    Args:
        content: 要保存的文件内容

    Returns:
        保存的文件路径若用户取消则返回 None
    """
    try:
        # 弹出另存为对话框
        file_path = DialogUtils.save_file_dialog(DialogUtils.parent_widget(), "另存为 CN 文件", "CN 文件 (*.cn)")
        if not file_path:
            return None

        normalized_path = os.path.normpath(file_path)

        # 仅当用户完全没有输入扩展名时才自动补 .cn,
        if not os.path.splitext(normalized_path)[1]:
            normalized_path += '.cn'

        if not write_text_file(normalized_path, content):
            raise OSError("写入文件失败")

        # 更新配置
        split_file_path(normalized_path)
        return normalized_path
    except Exception as e:
        safe_log(f"另存为失败: {e}")
        DialogUtils.show_error(DialogUtils.parent_widget(), "另存失败", f"无法保存文件：\n{e}")
        return None


def read_file_content_with_encoding() -> tuple[str | None, str]:
    """
    读取当前配置文件内容并返回其编码

    Returns:
        文件内容, 编码, 读取失败时内容为 None
    """
    try:
        # 从配置获取当前文件路径
        file_path = _get_current_file_path()

        # 文件不存在清空相关配置
        if not file_path or not os.path.isfile(file_path):
            get_config_service().update_file_config("source_code_path", "")
            get_config_service().update_file_config("code_name", "")
            return None, "utf-8"

        # 读取文件内容, 自动兼容 UTF-8 与 GBK
        return read_text_file_with_encoding(file_path)
    except Exception as e:
        safe_log(f"读取文件失败: {e}")
        DialogUtils.show_error(DialogUtils.parent_widget(), "读取失败", f"无法读取文件内容：\n{e}")
        return None, "utf-8"

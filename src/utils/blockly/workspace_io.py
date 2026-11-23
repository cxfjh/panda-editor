import os
from PySide6.QtWidgets import QFileDialog, QWidget
from src.utils.config_service import get_config_service
from src.utils.dialog_utils import DialogUtils
from src.utils.exceptions import safe_log
from src.utils.file_ops import write_text_file
from src.utils.text_io import read_text_file_with_encoding


# 积木工作区文件过滤器, 内容为 Blockly 原生 XML
BLOCKLY_FILE_FILTER = "积木工作区 (*.xml)"


def default_directory() -> str:
    """
    取积木文件的默认所在目录

    Returns:
        源码目录, 未配置或目录不存在时返回空字符串
    """
    source_path = get_config_service().get_file_config("source_code_path") or ""
    return source_path if os.path.isdir(source_path) else ""


def is_workspace_xml(text: str) -> bool:
    """
    判断文本是否为 Blockly 工作区 XML

    Args:
        text: 待判断的文本

    Returns:
        bool, True 表示是合法的积木工作区 XML
    """
    content = (text or "").strip()
    if not content:
        return False
    if content.startswith("<?xml"):
        content = content[content.find("?>") + 2:].strip()
    return content.startswith("<xml")


def workspace_path_for(target_path: str) -> str:
    """
    按生成的代码文件推导同名积木文件路径

    Args:
        target_path: 代码文件路径, 例如 demo.cn

    Returns:
        同目录同名的 .xml 路径, 传入空串时返回空字符串
    """
    if not target_path:
        return ""
    stem, _ = os.path.splitext(target_path)
    return stem + ".xml"


def write_workspace_silently(file_path: str, xml: str) -> bool:
    """
    把工作区 XML 写入指定文件, 全程不弹对话框

    Args:
        file_path: 目标文件路径
        xml: Blockly 原生 XML 文本

    Returns:
        True 表示写入成功
    """
    if not file_path or not is_workspace_xml(xml):
        return False
    return write_text_file(file_path, xml)


def read_workspace_file(file_path: str) -> str | None:
    """
    读取工作区 XML 文件, 全程不弹对话框

    Args:
        file_path: 文件路径

    Returns:
        工作区 XML 文本, 文件不存在或内容无效时返回 None
    """
    if not file_path or not os.path.isfile(file_path):
        return None
    try:
        content, _ = read_text_file_with_encoding(os.path.normpath(file_path))
    except Exception as e:
        safe_log(f"读取积木文件时发生错误: {e}")
        return None
    return content if is_workspace_xml(content) else None


def save_workspace_xml(parent: QWidget | None, xml: str, directory: str = "") -> str | None:
    """
    把工作区 XML 保存到文件

    Args:
        parent: 父窗口
        xml: Blockly 原生 XML 文本
        directory: 对话框默认目录

    Returns:
        实际保存的文件路径, 用户取消或保存失败时返回 None
    """
    if not is_workspace_xml(xml):
        DialogUtils.show_warning(parent, "无法保存", "积木工作区还是空的, 请先拼出积木再保存")
        return None

    file_path = DialogUtils.save_file_dialog(parent, "保存积木工作区", BLOCKLY_FILE_FILTER, directory)
    if not file_path:
        return None

    normalized_path = os.path.normpath(file_path)
    if not os.path.splitext(normalized_path)[1]:
        normalized_path += ".xml"

    if not write_text_file(normalized_path, xml):
        return None
    return normalized_path


def load_workspace_xml(parent: QWidget | None, directory: str = "") -> str | None:
    """
    从文件读取工作区 XML

    Args:
        parent: 父窗口
        directory: 对话框默认目录

    Returns:
        工作区 XML 文本, 用户取消或读取失败时返回 None
    """
    file_path, _ = QFileDialog.getOpenFileName(parent, "加载积木工作区", directory, BLOCKLY_FILE_FILTER)
    if not file_path:
        return None

    try:
        content, _ = read_text_file_with_encoding(os.path.normpath(file_path))
    except Exception as e:
        safe_log(f"读取积木工作区失败: {e}")
        DialogUtils.show_error(parent, "加载失败", f"无法读取积木文件：\n{e}")
        return None

    if not is_workspace_xml(content):
        DialogUtils.show_warning(parent, "文件无效", "所选文件不是 Blockly 积木工作区文件")
        return None
    return content

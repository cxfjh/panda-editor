import os
from src.utils.exceptions import safe_log


# 生成的代码写入的文件过滤器
CN_FILE_FILTER = "CnLang 代码 (*.cn)"


def ensure_cn_extension(file_path: str) -> str:
    """
    确保路径带 .cn 扩展名

    Args:
        file_path: 用户选择的文件路径

    Returns:
        规范化后的路径, 缺少扩展名时补上 .cn
    """
    path = os.path.normpath(file_path)
    if not os.path.splitext(path)[1]:
        path += ".cn"
    return path


def read_code_file(file_path: str) -> str:
    """
    读取目标文件现有内容, 用于覆盖前的提示

    Args:
        file_path: 文件路径

    Returns:
        文件文本, 文件不存在或读取失败时返回空字符串
    """
    if not file_path or not os.path.isfile(file_path):
        return ""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError as e:
        safe_log(f"读取目标文件失败: {e}")
        return ""


def write_generated_code(file_path: str, code: str, append: bool = False) -> int:
    """
    把积木生成的代码写入 .cn 文件

    Args:
        file_path: 目标文件路径
        code: CnLang 代码
        append: True=追加到文件末尾 False=覆盖整个文件

    Returns:
        写入的代码行数, 代码为空时返回 0

    Raises:
        OSError, 目录或文件无法写入时抛出
    """
    text = (code or "").replace("\r\n", "\n").replace("\r", "\n")

    # 全是空白的代码视为空, 但不做 lstrip, 否则会破坏代码缩进
    if not text.strip():
        return 0
    text = text.rstrip("\n") + "\n"

    directory = os.path.dirname(os.path.abspath(file_path))
    os.makedirs(directory, exist_ok=True)

    if append:
        existing = read_code_file(file_path)
        if existing.strip():
            # 与已有代码之间留一个空行, 避免两段积木代码贴在一起
            if existing.endswith("\n\n"):
                pass
            elif existing.endswith("\n"):
                text = "\n" + text
            else:
                text = "\n\n" + text

    mode = "a" if append else "w"
    with open(file_path, mode, encoding="utf-8", newline="\n") as f:
        f.write(text)
    return len(text.strip("\n").split("\n"))

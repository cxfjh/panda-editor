import os
from src.utils.text_io import read_text_file_with_encoding


def _read_lines(path: str) -> list[str] | None:
    """
    按项目统一的编码规则读取文本文件

    Args:
        path: 文件路径

    Returns:
        按行拆分的文本, 读取失败时返回 None
    """
    if not path or not os.path.isfile(path):
        return None
    try:
        content, _encoding = read_text_file_with_encoding(path)
    except (OSError, ValueError):
        return None
    return content.splitlines()


def _source_path(py_path: str) -> str:
    """
    由转译后的 .py 路径推出源文件路径

    Args:
        py_path: 转译生成的 .py 文件路径

    Returns:
        同名的 .cn 文件路径
    """
    base, _separator = os.path.splitext(py_path)
    return base + ".cn"


def _line_no_usable(py_path: str, source_lines: list[str]) -> bool:
    """
    判断转译前后行号是否一一对应

    Args:
        py_path: 转译生成的 .py 文件路径
        source_lines: 源文件的行列表

    Returns:
        行数一致返回 True, 此时可以直接用转译后的行号
    """
    py_lines = _read_lines(py_path)
    return py_lines is not None and len(py_lines) == len(source_lines)

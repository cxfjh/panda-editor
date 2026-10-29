from src.utils.error_message.models import ErrorReport
from src.utils.error_message.parser import parse_tail
from src.utils.error_message.source import _line_no_usable, _read_lines, _source_path
from src.utils.error_message.translate import exception_name, translate_message


def build_report(tail: list[str], py_path: str, source_text: str | None = None) -> ErrorReport | None:
    """
    生成追加到终端的错误说明

    Args:
        tail: 终端最后若干行输出
        py_path: 本次运行的 .py 文件路径
        source_text: 编辑器里的源码文本, 传 None 时回退到磁盘上的 .cn

    Returns:
        说明行与需要标红的片段, 不是崩溃或无法识别时返回 None
    """
    error = parse_tail(tail)
    if error is None:
        return None

    # 源码优先用编辑器里的内容, 它和刚才转译的文本完全一致
    source_lines = source_text.splitlines() if source_text else _read_lines(_source_path(py_path))
    if source_lines is None:
        source_lines = []

    # 用了会展开源码的库指令时行数会对不上, 这时只翻译错误不给行号
    show_line = bool(source_lines) and _line_no_usable(py_path, source_lines)
    name = exception_name(error.type_name)
    mark = "【%s】" % name
    header = "> 运行出错: " + mark
    if show_line:
        header = "> 第 %d 行出错: %s" % (error.line_no, mark)
    if error.func_name and error.func_name != "<module>":
        header += ", 出错位置在函数 %s 里" % error.func_name

    lines = ["", header]
    if not show_line and source_lines:
        lines.append("> 源码里用了库指令, 展开后行号对不上, 这里不显示行号")
    if show_line and 0 < error.line_no <= len(source_lines):
        text = source_lines[error.line_no - 1].strip()
        if text:
            # 出错代码单独成段, 上下各留一个空行
            lines.append("")
            lines.append(">     " + text)
            lines.append("")

    # 提示那一行整行标红, 记下它的下标交给视图处理
    hint_index = len(lines)
    lines.append("> 【温馨提示】" + translate_message(error.type_name, error.message))
    return ErrorReport(lines, mark, hint_index)

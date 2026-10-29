import re
from src.utils.error_message.models import CodeError
from src.utils.error_message.names import EXCEPTION_NAMES


_LAST_LINE = re.compile(r"^(?P<type>[^\W\d][\w.]*)(?::\s?(?P<msg>.*))?$")
_FRAME_LINE = re.compile(r'^\s+File "(?P<path>[^"]+)", line (?P<line>\d+)(?:, in (?P<func>.+))?$')
_QUIET_TYPES = { "SystemExit", "KeyboardInterrupt", "GeneratorExit" }


def _match_exception_line(line: str) -> re.Match[str] | None:
    """
    判断末行是不是异常提示行

    Args:
        line: 末行文本

    Returns:
        匹配结果, 不是异常行时返回 None
    """
    found = _LAST_LINE.match(line)
    if not found:
        return None
    short = found.group("type").rsplit(".", 1)[-1]
    if short in EXCEPTION_NAMES:
        return found
    if short.endswith(("Error", "Exception", "Interrupt", "Warning", "Group")):
        return found
    if short.endswith(("错误", "异常", "中断")):
        return found
    return None


def parse_tail(lines: list[str]) -> CodeError | None:
    """
    从终端尾部输出里解析出崩溃信息

    Args:
        lines: 终端最后若干行输出, 顺序与显示一致

    Returns:
        解析出的错误信息, 不是崩溃或无法识别时返回 None
    """
    cleaned = [line.rstrip() for line in lines]
    while cleaned and not cleaned[-1]:
        cleaned.pop()
    if not cleaned:
        return None

    found = _match_exception_line(cleaned[-1])
    if found is None:
        return None
    type_name = found.group("type").rsplit(".", 1)[-1]
    if type_name in _QUIET_TYPES:
        return None

    # 从尾部往前找最内层调用帧, 语法错误的帧没有函数名
    line_no = 0
    func_name = ""
    for index in range(len(cleaned) - 1, -1, -1):
        frame = _FRAME_LINE.match(cleaned[index])
        if frame:
            line_no = int(frame.group("line"))
            func_name = (frame.group("func") or "").strip()
            break

    # 没有调用帧说明只是一段形似异常的文本, 不当作崩溃
    if not line_no:
        return None
    return CodeError(type_name, found.group("msg") or "", line_no, func_name)

import hashlib
import os
import re
from collections import OrderedDict
from src.module.grammar import grammar, symbols
from src.utils.cn_tokens import DOUBLE_QUOTE_FAMILY, SINGLE_QUOTE_FAMILY, TOKEN_CODE, tokenize_line
from src.utils.code_proc.config import apply_file_path, get_config
from src.utils.dialog_utils import DialogUtils


# 解析结果缓存
_PARSE_CACHE: "OrderedDict[str, str]" = OrderedDict()
_CACHE_MAX_SIZE = 100  # 最大缓存条目数

# 预编译正则表达式
_GRAMMAR_KEYS_SORTED = sorted(grammar.keys(), key=len, reverse=True)
GRAMMAR_PATTERN = re.compile(fr'(?<![\w\u4e00-\u9fff])({"|".join(map(re.escape, _GRAMMAR_KEYS_SORTED))})(?![\w\u4e00-\u9fff])')
SYMBOLS_PATTERN = re.compile('|'.join(map(re.escape, symbols.keys())))

# 预编译注释检查
_COMMENT_PREFIX = '#'


def _transform_code_segment(segment: str) -> str:
    """
    对代码段应用语法与符号替换

    Args:
        segment: 待替换的代码段文本

    Returns:
        替换语法与符号后的代码段
    """
    parsed = GRAMMAR_PATTERN.sub(lambda m: grammar[m.group(0)], segment)
    return SYMBOLS_PATTERN.sub(lambda m: symbols[m.group(0)], parsed)


def _convert_segment_quotes(segment: str) -> str:
    """
    将受保护字符串两端的引号统一转为英文引号

    Args:
        segment: 受保护的字符串段

    Returns:
        转换后的字符串段
    """
    if len(segment) >= 2:
        if segment[0] in DOUBLE_QUOTE_FAMILY and segment[-1] in DOUBLE_QUOTE_FAMILY:
            return '"' + segment[1:-1] + '"'
        if segment[0] in SINGLE_QUOTE_FAMILY and segment[-1] in SINGLE_QUOTE_FAMILY:
            return "'" + segment[1:-1] + "'"
    return segment


def _process_line_fast(line: str) -> str:
    """
    快速处理单行代码

    Args:
        line: 单行代码

    Returns:
        处理后的代码行
    """

    # 空行或纯空白行直接返回
    if not line or line.isspace():
        return line

    # 注释行直接返回
    stripped = line.lstrip()
    if stripped.startswith(_COMMENT_PREFIX):
        return line

    # 按 token 处理, 代码段做替换, 字符串 注释保持内容不变
    parsed_parts = []
    for token_type, text in tokenize_line(line):
        if token_type == TOKEN_CODE:
            parsed_parts.append(_transform_code_segment(text))
        else:
            parsed_parts.append(_convert_segment_quotes(text))
    return ''.join(parsed_parts)


def _get_code_hash(code: str) -> str:
    """
    生成代码内容的哈希值

    Args:
        code: 代码内容字符串

    Returns:
        MD5 哈希值字符串
    """
    return hashlib.md5(code.encode('utf-8')).hexdigest()


def _write_parsed(code_path: str, parsed_str: str) -> None:
    """
    将转换结果写入 .py 文件

    Args:
        code_path: 目标 .py 文件路径
        parsed_str: 转换后的 Python 代码内容
    """
    try:
        with open(code_path, "r", encoding="utf-8") as f:
            if f.read() == parsed_str:
                return  # 磁盘内容已是最新, 无需重写
    except (OSError, UnicodeDecodeError):
        pass  # 读取失败时直接按新内容写入

    with open(code_path, "w", encoding="utf-8") as f:
        f.write(parsed_str)


def parse_code(code_str: str, file_path: str | None = None) -> bool:
    """
    中文代码到 Python 代码的解析转换

    Args:
        code_str: 中文代码字符串
        file_path: 当前 .cn 文件路径

    Returns:
        转换是否成功
    """
    try:
        config = get_config()
        if not config:
            DialogUtils.show_error(DialogUtils.parent_widget(), "配置错误", "请先正确配置文件路径！")
            return False

        config = apply_file_path(config, file_path)
        os.makedirs(os.path.dirname(config["code_path"]), exist_ok=True)  # type: ignore

        # 反复运行同一份代码时直接命中缓存, 省掉整篇转译
        code_hash = _get_code_hash(code_str)
        if code_hash and code_hash in _PARSE_CACHE:
            parsed_str = _PARSE_CACHE[code_hash]
            _PARSE_CACHE.move_to_end(code_hash)
            _write_parsed(config["code_path"], parsed_str)  # type: ignore
            return True

        processed_lines = [_process_line_fast(line) for line in code_str.split('\n')]
        parsed_str = '\n'.join(processed_lines)

        if code_hash:
            if len(_PARSE_CACHE) >= _CACHE_MAX_SIZE:
                _PARSE_CACHE.popitem(last=False)
            _PARSE_CACHE[code_hash] = parsed_str

        _write_parsed(config["code_path"], parsed_str)  # type: ignore
        return True
    except Exception as e:
        DialogUtils.show_error(DialogUtils.parent_widget(), "代码解析失败", f"解析异常：\n{e!s}")
        return False


def parse_to_python_code_path(text_code: str, file_path: str | None = None) -> str | None:
    """
    解析中文代码并返回转换后的 .py 文件路径

    Args:
        text_code: 中文代码文本
        file_path: 当前 .cn 文件路径

    Returns:
        转换后的 .py 文件路径, 解析失败时返回 None
    """
    if not parse_code(text_code, file_path):
        return None
    if file_path:
        base_name = os.path.splitext(file_path)[0]
        return f"{base_name}.py"
    config = get_config()
    if config:
        return os.path.join(config["source_code_path"], f"{config['code_name']}.py")  # type: ignore
    return None

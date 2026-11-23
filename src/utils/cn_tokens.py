"""引号族定义"""

DOUBLE_QUOTE_FAMILY = frozenset({ '"', '\u201c', '\u201d' })  # 半角双引号 左双引号 右双引号
SINGLE_QUOTE_FAMILY = frozenset({ "'", '\u2018', '\u2019' })  # 半角单引号 左单引号 右单引号

# Token 类型
TOKEN_CODE = 'code'  # 代码段
TOKEN_STRING = 'string'  # 字符串字面量
TOKEN_COMMENT = 'comment'  # 注释

# 注释前缀
_COMMENT_PREFIX = '#'


def quote_family(char: str):
    """
    返回字符所属的引号族

    Args:
        char: 单个字符

    Returns:
        frozenset, 所属引号族, 不是引号时返回 None
    """
    if char in DOUBLE_QUOTE_FAMILY:
        return DOUBLE_QUOTE_FAMILY
    if char in SINGLE_QUOTE_FAMILY:
        return SINGLE_QUOTE_FAMILY
    return None


def find_any_quote(line: str, start: int, family: frozenset) -> int:
    """
    在 start 之后查找 family 中任意引号最早出现的位置

    Args:
        line: 行文本
        start: 起始查找下标
        family: 引号族集合

    Returns:
        int, 最早出现的下标, 未找到返回 -1
    """
    best = -1
    for q in family:
        pos = line.find(q, start)
        if pos != -1 and (best == -1 or pos < best):
            best = pos
    return best


def tokenize_line(line: str) -> list[tuple[str, str]]:
    """
    单遍扫描将一行代码切分为类型与文本组成的 token 序列

    Args:
        line: 单行代码

    Returns:
        List[Tuple[str, str]]: token 序列, 每项为类型与文本, 类型为 TOKEN_CODE / TOKEN_STRING / TOKEN_COMMENT
    """
    tokens: list[tuple[str, str]] = []
    i, n = 0, len(line)
    start = 0

    while i < n:
        ch = line[i]

        # 注释, 从 # 到行尾
        if ch == _COMMENT_PREFIX:
            if i > start:
                tokens.append((TOKEN_CODE, line[start:i]))
            tokens.append((TOKEN_COMMENT, line[i:]))
            return tokens

        # 字符串, 同族任意引号均可作为结束
        family = quote_family(ch)
        if family is not None:
            if i > start:
                tokens.append((TOKEN_CODE, line[start:i]))
            j = find_any_quote(line, i + 1, family)
            end = j if j != -1 else n - 1  # 未闭合则延伸到行尾
            tokens.append((TOKEN_STRING, line[i:end + 1]))
            i = end + 1
            start = i
            continue
        i += 1

    if start < n:
        tokens.append((TOKEN_CODE, line[start:n]))
    return tokens

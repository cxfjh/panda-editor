from __future__ import annotations
import re
from collections.abc import Sequence
from src.utils.cn_tokens import TOKEN_COMMENT, find_any_quote, quote_family, tokenize_line
from src.utils.completion_index.model import DocumentIndex
from src.utils.completion_index.patterns import ASCII_ALPHA, ASSIGN, CATCH, CLASS_CALL, CLASS_HEAD, FOR_EACH, FROM_NAMES, FUNC_HEAD, IMPORT_HEAD, NUMBER_START, SELF_MEMBER, TUPLE_ASSIGN
from src.utils.completion_index.types import TYPE_CLASS_PREFIX, TYPE_DICT, TYPE_HINTS, TYPE_LIST, TYPE_NUM, TYPE_SET, TYPE_STR, TYPE_TUPLE, TYPE_UNKNOWN
from src.utils.pinyin_index import initials_of, is_subsequence, starts_with_initials


def filter_items(items: Sequence[str], prefix: str) -> list[str]:
    """
    按已输入前缀筛选候选词, 支持中文名的拼音首字母

    Args:
        items: 候选词列表
        prefix: 已输入的前缀

    Returns:
        筛选后的候选词列表, 保持原顺序
    """
    if not prefix:
        return list(items)
    lowered = prefix.lower()
    starts = [item for item in items if item.lower().startswith(lowered)]
    if not ASCII_ALPHA.fullmatch(lowered):
        return starts or [item for item in items if lowered in item.lower()]

    # 纯字母输入才做拼音匹配, 已在前缀结果里的候选不再重复
    matched = set(starts)
    main_first: list[str] = []
    heteronym_first: list[str] = []
    initials_inner: list[str] = []
    for item in items:
        if item in matched:
            continue
        initials = initials_of(item)
        if not initials:
            continue  # 不含汉字, 原文前缀已覆盖
        if initials.startswith(lowered):
            main_first.append(item)
        elif starts_with_initials(item, lowered):
            heteronym_first.append(item)
        elif lowered != item.lower() and is_subsequence(lowered, initials):
            initials_inner.append(item)

    if starts:
        return starts + main_first
    pinyin_hits = main_first + heteronym_first + initials_inner
    if pinyin_hits:
        return pinyin_hits
    return [item for item in items if lowered in item.lower()]


def _indent_width(line: str) -> int:
    """
    计算行首缩进宽度, 制表符按 4 空格计

    Args:
        line: 行文本

    Returns:
        缩进宽度
    """
    width = 0
    for ch in line:
        if ch == ' ':
            width += 1
        elif ch == '\t':
            width += 4
        else:
            break
    return width


def _strip_comment(line: str) -> str:
    """
    去掉行尾注释, 保留字符串中的 #

    Args:
        line: 行文本

    Returns:
        去除注释后的文本
    """
    cursor = 0
    for token_type, seg in tokenize_line(line):
        if token_type == TOKEN_COMMENT:
            return line[:cursor]
        cursor += len(seg)
    return line


def _extract_bracket_text(text: str, start: int) -> str | None:
    """
    从 start 起查找第一个左括号并取出括号内文本, 支持嵌套与字符串

    Args:
        text: 文本
        start: 起始下标

    Returns:
        括号内文本, 没有左括号时返回 None
    """
    i, n = start, len(text)
    while i < n and text[i] not in '（(':
        i += 1
    if i >= n:
        return None
    depth = 0
    j = i
    while j < n:
        ch = text[j]
        family = quote_family(ch)
        if family is not None:
            close = find_any_quote(text, j + 1, family)
            j = (close + 1) if close != -1 else n
            continue
        if ch in '（(':
            depth += 1
        elif ch in '）)':
            depth -= 1
            if depth == 0:
                return text[i + 1:j]
        j += 1
    return text[i + 1:]


def split_params(params_text: str | None) -> tuple[str, ...]:
    """
    按顶层逗号切分参数文本

    Args:
        params_text: 括号内的参数文本

    Returns:
        参数展示文本元组
    """
    if not params_text:
        return ()
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    i, n = 0, len(params_text)
    while i < n:
        ch = params_text[i]

        # 字符串整体跳过, 里面的逗号不参与切分
        family = quote_family(ch)
        if family is not None:
            close = find_any_quote(params_text, i + 1, family)
            end = close if close != -1 else n - 1
            current.append(params_text[i:end + 1])
            i = end + 1
            continue

        # 只有顶层逗号才分隔参数, 默认值里的括号逗号要忽略
        if ch in '（([【{｛':
            depth += 1
        elif ch in '）)]】}｝':
            depth -= 1
        if ch in '，,' and depth == 0:
            parts.append(''.join(current).strip())
            current = []
        else:
            current.append(ch)
        i += 1
    tail = ''.join(current).strip()
    if tail:
        parts.append(tail)
    return tuple(p for p in parts if p)


def infer_type(rhs: str, classes: Sequence[str] = ()) -> str:
    """
    根据赋值右侧文本推断变量类型

    Args:
        rhs: 赋值号右侧文本
        classes: 文档中已定义的类名

    Returns:
        类型标签
    """
    text = rhs.strip()
    if not text:
        return TYPE_UNKNOWN

    # 先按字面量的首字符判断, 再看是否为已知的内置调用, 最后才尝试类实例
    head = text[0]
    if head in '【[':
        return TYPE_LIST
    if head in '｛{':
        return TYPE_DICT if (':' in text or '：' in text) else TYPE_SET
    if head in '（(':
        return TYPE_TUPLE
    if quote_family(head) is not None:
        return TYPE_STR
    if NUMBER_START.match(text):
        return TYPE_NUM
    for prefix, tag in TYPE_HINTS:
        if text.startswith(prefix):
            return tag
    match = CLASS_CALL.match(text)
    if match and match.group(1) in classes:
        return TYPE_CLASS_PREFIX + match.group(1)
    return TYPE_UNKNOWN


def build_index(text: str) -> DocumentIndex:
    """
    扫描文档构建符号索引

    Args:
        text: 文档全文

    Returns:
        DocumentIndex 实例
    """
    index = DocumentIndex()
    seen_globals: set = set()
    seen_members: set = set()
    class_stack: list[tuple[int, str, int]] = []  # 缩进, 类名, 起始行

    def add_symbol(names: str | None) -> None:
        """
        登记一个全局标识符

        Args:
            names: 待登记的标识符
        """
        if not names or names in seen_globals:
            return
        seen_globals.add(names)
        index.symbols.append(names)

    for line_no, raw in enumerate(text.split('\n')):
        code = _strip_comment(raw).rstrip()
        if not code.strip():
            continue  # 空行不结束类作用域
        indent = _indent_width(code)

        # CnLang 用缩进表示类体, 缩进回退到类声明列即代表类结束
        while class_stack and indent <= class_stack[-1][0]:
            _, cls, start = class_stack.pop()
            index.class_ranges.append((start, line_no - 1, cls))

        current_class = class_stack[-1][1] if class_stack else None

        class_match = CLASS_HEAD.match(code)
        if class_match:
            name = class_match.group(1)
            index.classes.setdefault(name, { })
            class_stack.append((indent, name, line_no))
            add_symbol(name)
            continue

        # 类体里的定义算方法, 顶层的定义算普通函数, 两者的提示来源不同
        func_match = FUNC_HEAD.match(code)
        if func_match:
            name = func_match.group(1)
            params = split_params(_extract_bracket_text(code, func_match.end()))
            if current_class:
                index.classes.setdefault(current_class, { })[name] = (params, line_no)
            else:
                index.functions[name] = (params, line_no)
                add_symbol(name)
            continue

        for member in SELF_MEMBER.finditer(code):
            name = member.group(1)
            if name not in seen_members:
                seen_members.add(name)
                index.self_members.append(name)

        import_match = IMPORT_HEAD.match(code)
        if import_match:
            module, alias = import_match.group(1), import_match.group(2)
            index.aliases[alias or module] = module
            add_symbol(alias or module)
            names_match = FROM_NAMES.search(code)
            if code.lstrip().startswith('来自') and names_match:
                for part in split_params(names_match.group(1)):
                    add_symbol(part.strip())
            continue

        for_each = FOR_EACH.search(code)
        if for_each:
            for group in for_each.groups():
                if group:
                    index.variables.setdefault(group, TYPE_UNKNOWN)
                    add_symbol(group)

        catch = CATCH.search(code)
        if catch:
            index.variables.setdefault(catch.group(1), TYPE_UNKNOWN)
            add_symbol(catch.group(1))

        assign = ASSIGN.match(code)
        if assign:
            name, rhs = assign.group(1), assign.group(2)
            index.variables[name] = infer_type(rhs, tuple(index.classes))
            add_symbol(name)
        else:
            tuple_assign = TUPLE_ASSIGN.match(code)
            if tuple_assign:
                tag = infer_type(tuple_assign.group(2), tuple(index.classes))
                for name in re.split(r'[ \t]*[,，][ \t]*', tuple_assign.group(1)):
                    if name:
                        index.variables[name] = tag
                        add_symbol(name)

    # 收尾, 未闭合的类作用域延伸到文件末尾
    total_lines = text.count('\n')
    while class_stack:
        _, cls, start = class_stack.pop()
        index.class_ranges.append((start, total_lines, cls))

    return index

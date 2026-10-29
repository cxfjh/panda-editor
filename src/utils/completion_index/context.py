from __future__ import annotations
import re
from collections.abc import Sequence
from src.utils.cn_tokens import find_any_quote, quote_family
from src.utils.completion_index.model import NONE_CONTEXT, CallContext, CompletionContext, ScanState
from src.utils.completion_index.patterns import IMPORT_CTX, MEMBER_CTX, NUMBER_TAIL, RECEIVER, TAIL_WORD
from src.utils.completion_index.types import NAME


def scan_prefix(prefix: str) -> ScanState:
    """
    扫描光标前的行文本, 得到字符串 注释状态与未闭合括号栈

    Args:
        prefix: 光标前的行文本

    Returns:
        ScanState 实例
    """
    state = ScanState()
    i, n = 0, len(prefix)
    while i < n:
        ch = prefix[i]

        # 注释之后的内容不再参与判定
        if ch == '#':
            state.in_comment = True
            break
        family = quote_family(ch)
        if family is not None:
            close = find_any_quote(prefix, i + 1, family)

            # 没有闭合引号说明光标还在字符串里, 直接返回字符串起点
            if close == -1:
                state.in_string = True
                state.string_start = i
                break
            i = close + 1
            continue

        # 括号栈用于判断当前处在第几个实参, 逗号只累加最内层括号的计数
        if ch in '（(' or ch in '【[｛{':
            state.brackets.append([ch, i, 0])
        elif ch in '，,':
            if state.brackets:
                state.brackets[-1][2] += 1

        # 右括号逐层弹出, 直到遇到同类左括号为止, 兼容混用中英文括号
        elif ch in '）)]】}｝':
            while state.brackets:
                opener = state.brackets.pop()
                if opener[0] in '（(【[｛{' and _bracket_pairs(opener[0]) == ch:
                    break
        i += 1
    return state


def _bracket_pairs(opener: str) -> str:
    """
    获取左括号对应的右括号

    Args:
        opener: 左括号字符

    Returns:
        右括号字符
    """
    return { '（': '）', '(': ')', '【': '】', '[': ']', '｛': '｝', '{': '}' }.get(opener, '')


def _call_from_state(prefix: str, state: ScanState) -> CallContext | None:
    """
    从括号栈中取出最内层函数调用

    Args:
        prefix: 光标前的行文本
        state: 扫描结果

    Returns:
        CallContext, 不在调用实参中时返回 None
    """
    for bracket, index, arg_index in reversed(state.brackets):
        if bracket not in '（(':
            continue
        head = prefix[:index]
        match = re.search(rf'(?:({NAME})[ \t]*[.。][ \t]*)?({NAME}\*?)[ \t]*$', head)
        if not match:
            return None
        return CallContext(
            name=match.group(2),
            arg_index=arg_index,
            paren_index=index,
            args_text=prefix[index + 1:],
            receiver=match.group(1),
        )
    return None


def enclosing_call(prefix: str) -> CallContext | None:
    """
    判定光标是否位于某个函数调用的实参位置

    Args:
        prefix: 光标前的行文本

    Returns:
        CallContext, 不在实参中时返回 None
    """
    state = scan_prefix(prefix)
    if state.in_comment:
        return None
    return _call_from_state(prefix, state)


def detect_context(prefix: str, lib_names: Sequence[str] = ()) -> CompletionContext:
    """
    判定补全上下文

    Args:
        prefix: 光标前的行文本
        lib_names: 扩展库函数名集合, 如 自动化*

    Returns:
        CompletionContext 实例
    """
    state = scan_prefix(prefix)
    if state.in_comment:
        return NONE_CONTEXT

    if state.in_string:
        call = _call_from_state(prefix, state)
        if call and call.arg_index == 0 and call.name in lib_names:
            return CompletionContext(
                kind='library',
                prefix=prefix[state.string_start + 1:],
                lib_name=call.name,
                in_string=True,
            )
        return CompletionContext(kind='none', in_string=True)

    import_match = IMPORT_CTX.search(prefix)
    if import_match:
        return CompletionContext(kind='import', prefix=import_match.group(1) or '')

    member_match = MEMBER_CTX.search(prefix)
    if member_match:
        word = member_match.group(1) or ''
        head = prefix[:member_match.start()]
        receiver_match = RECEIVER.search(head)
        receiver = receiver_match.group(1) if receiver_match else None
        if (receiver and receiver.isdigit()) or (receiver is None and head[-1:].isdigit()):  # type: ignore
            return NONE_CONTEXT  # 数字字面量的小数点, 如 3.14
        return CompletionContext(kind='member', prefix=word, receiver=receiver)

    if prefix.endswith('简称'):
        return NONE_CONTEXT

    # 数字字面量 3 / 3.14 / 3. 后面不弹补全
    if NUMBER_TAIL.search(prefix):
        return NONE_CONTEXT

    tail = TAIL_WORD.search(prefix)
    return CompletionContext(kind='global', prefix=tail.group(1) if tail else '')


def first_string_arg(call: CallContext) -> str | None:
    """
    取出调用第一个实参的字符串内容

    Args:
        call: 调用上下文

    Returns:
        字符串内容, 首参不是字符串时返回 None
    """
    text = call.args_text.lstrip()
    if not text:
        return None
    family = quote_family(text[0])
    if family is None:
        return None
    close = find_any_quote(text, 1, family)
    return text[1:close] if close != -1 else text[1:]

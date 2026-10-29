from collections.abc import Sequence
from src.module.builtin_map import builtin
from src.module.lib_map import lib
from src.module.method_map import method
from src.module.stdlib_map import stdlib
from src.utils.completion_index import TYPE_CLASS_PREFIX, CallContext, enclosing_call, first_string_arg
from src.utils.syntax_signature import signature_params, to_byte_spans
from src.utils.syntax_hint.refs import HintRefs


def compose_tip(name: str, params: Sequence[str], note: str, arg_index: int):
    """
    拼装提示文本并计算各参数的字节区间

    Args:
        name: 函数名
        params: 参数展示文本
        note: 附加说明, 第二行
        arg_index: 当前参数序号

    Returns:
        提示文本, 参数字节区间列表, 当前参数序号
    """
    head = name + '（'
    parts: list[str] = [head]
    spans: list[tuple[int, int]] = []
    cursor = len(head)

    # 拼接的同时记录每个参数在提示文本中的字符区间, 用于高亮当前参数
    for index, param in enumerate(params):
        if index:
            parts.append('，')
            cursor += 1
        spans.append((cursor, cursor + len(param)))
        parts.append(param)
        cursor += len(param)
    parts.append('）')
    if note:
        parts.append('\n' + note)
    text = ''.join(parts)

    # Scintilla 的高亮接口按字节计, 中文参数需要换算
    byte_spans = to_byte_spans(text, spans)
    if not byte_spans:
        return text, byte_spans, -1

    # 实参序号超出参数个数时固定高亮最后一个, 例如传了多余实参
    return text, byte_spans, min(max(arg_index, 0), len(byte_spans) - 1)


def lookup_py_name(cn_name: str) -> str | None:
    """
    在各类词表中查找中文名对应的 Python 目标

    Args:
        cn_name: 中文函数名

    Returns:
        Python 目标名; 未找到时返回 None
    """
    for mapping in (builtin, stdlib, method, lib):
        value = mapping.get(cn_name)
        if isinstance(value, str) and len(value) <= 60 and '\n' not in value:
            return value
    return None


class TipMixin(HintRefs):
    """参数提示相关方法, 由提示管理器混入使用"""

    def _show_call_tip(self):
        """
        在函数调用的实参位置显示参数提示

        Args:
            self: 当前管理器实例
        """
        editor = self._editor
        pos = editor.currentPos()
        if pos < 0:
            return
        line = editor.lineFromPosition(pos)
        prefix = editor.line_text(line)[:editor.column_of_position(pos)]
        call = enclosing_call(prefix)
        if call is None:
            return
        tip = self._build_tip(call)
        if tip is None:
            return
        text, spans, highlight = tip
        editor.callTipShow(pos, text)
        if 0 <= highlight < len(spans):
            start, end = spans[highlight]
            editor.callTipSetHlt(start, end)

    def _build_tip(self, call: CallContext) -> tuple[str, list[tuple[int, int]], int] | None:
        """
        构建参数提示文本

        Args:
            self: 当前管理器实例
            call: 调用上下文

        Returns:
            提示文本, 各参数的字节区间, 当前参数序号; 无信息时返回 None
        """
        name = call.name

        # 扩展库分派函数, 按第一个字符串实参给出具体操作的签名
        ops = self._lib_ops.get(name)
        if ops:
            op = ops.get(first_string_arg(call) or '')
            if op is not None:
                params = (repr(op.name),) + op.params  # type: ignore
                return compose_tip(name, params, op.doc or '扩展库操作', call.arg_index)  # type: ignore
            summary = '、'.join(list(ops)[:6])
            more = f" 等共 {len(ops)} 项" if len(ops) > 6 else ''
            return compose_tip(name, ('操作名', '…'), f"可用操作：{summary}{more}", call.arg_index)

        index = self._document_index()

        # 文档中自定义的函数
        params = index.params_of(name)
        if params is not None:
            return compose_tip(name, params, '文档中自定义的函数', call.arg_index)

        # 文档中自定义类的实例方法
        if call.receiver:
            tag = index.variables.get(call.receiver, '')
            if tag.startswith(TYPE_CLASS_PREFIX):
                methods = index.classes.get(tag[len(TYPE_CLASS_PREFIX):], { })
                if name in methods:
                    params = methods[name][0]

                    # 隐藏方法定义里的 自身 参数
                    if params and params[0] in ('自身', 'self'):
                        params = params[1:]
                    return compose_tip(name, params, f"{call.receiver} 的方法", call.arg_index)

        # 内置与标准库词表
        py_name = lookup_py_name(name)
        if py_name:
            signature = signature_params(py_name)
            if signature is not None:
                return compose_tip(name, signature, f"Python: {py_name}", call.arg_index)
        return None

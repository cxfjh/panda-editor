import builtins
import datetime
import inspect
import math
import os
import pathlib
import random
import time
import types
import turtle as _turtle_module
from collections.abc import Sequence
from src.module.lib_map import lib
from src.module.stdlib_map import stdlib
from src.utils.exceptions import safe_log
from src.utils.library_docs import DEFAULT_TEXT


# Python 目标模块表, 用于解析词表值并 introspect 签名
_PY_MODULES: dict[str, types.ModuleType] = {
    'math': math,
    'random': random,
    'os': os,
    'path': os.path,
    'pathlib': pathlib,
    'time': time,
    'datetime': datetime,
}

if _turtle_module is not None:
    _PY_MODULES['turtle'] = _turtle_module

# 裸函数名在多个模块重名时, 指定参数提示解析到哪个模块
_BARE_NAME_MODULE: dict[str, str] = {
    'write': 'turtle',
}

# 模块上不直接暴露, 需要到类里找的成员
_MODULE_CLASSES: dict[str, tuple[str, ...]] = {
    'pathlib': ('Path',),
}

# 单个签名最多展示的参数个数
_MAX_TIP_PARAMS = 8

# 签名缓存, 避免重复 inspect
_SIGNATURE_CACHE: dict[str, tuple[str, ...] | None] = { }


def dedupe(items: Sequence[str]) -> list[str]:
    """
    去重并保持顺序, 同时剔除空串与含空格的项

    Args:
        items: 原始词条序列

    Returns:
        去重后的词条列表
    """
    result: list[str] = []
    seen = set()
    for item in items:
        text = str(item).strip()
        if not text or ' ' in text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _resolve_py_target(py_name: str):
    """
    解析词表值对应的 Python 对象, 用于签名内省

    Args:
        py_name: 词表中的 Python 目标名, 如 print / sqrt / path.join

    Returns:
        Python 对象; 无法解析时返回 None
    """
    parts = py_name.split('.')
    if parts[0] in _PY_MODULES:
        obj = _PY_MODULES[parts[0]]
        for attr in parts[1:]:
            obj = getattr(obj, attr, None)
            if obj is None:
                return None
        return obj
    obj = getattr(builtins, parts[0], None)
    if obj is not None:
        for attr in parts[1:]:
            obj = getattr(obj, attr, None)
            if obj is None:
                return None
        return obj

    # 重名函数优先走指定模块, 避免解析到签名不符的同名函数
    preferred = _BARE_NAME_MODULE.get(parts[0])
    if preferred:
        module = _PY_MODULES.get(preferred)
        if module is None:
            return None
        return _resolve_module_attr(module, py_name)

    # 未指明模块的标准库函数, 逐模块尝试
    for module in _PY_MODULES.values():
        obj = getattr(module, parts[0], None)
        if obj is None:
            continue
        for attr in parts[1:]:
            obj = getattr(obj, attr, None)
            if obj is None:
                break
        if obj is not None:
            return obj
    return None


def _resolve_module_attr(module: types.ModuleType, py_name: str):
    """
    按点号路径取模块属性

    Args:
        module: 模块对象
        py_name: 点号分隔的属性路径

    Returns:
        属性值; 不存在时返回 None
    """
    obj = module
    for attr in py_name.split('.'):
        obj = getattr(obj, attr, None)
        if obj is None:
            return None
    return obj


def build_module_members() -> dict[str, list[str]]:
    """
    构建"中文库名 映射到 该模块可用的中文词条"映射

    Returns:
        形如 {'数学库': ['圆周率', '平方根', ...], ...}
    """
    ordered: list[tuple[str, types.ModuleType]] = []
    for cn_name, target in lib.items():
        if not isinstance(target, str) or not target.isidentifier():
            continue
        module = _PY_MODULES.get(target)
        if module is not None:
            ordered.append((cn_name, module))

    result: dict[str, list[str]] = { }
    pending: list[tuple[str, str]] = []

    # 模块自身的属性
    for cn_name, py_name in stdlib.items():
        matched = False
        preferred = _BARE_NAME_MODULE.get(py_name)
        for lib_name, module in ordered:
            # 重名函数只归到指定模块, 避免被更靠前的库先抢走
            if preferred and module.__name__ != preferred:
                continue
            if _resolve_module_attr(module, py_name) is not None:
                result.setdefault(lib_name, []).append(cn_name)
                matched = True
                break
        if not matched:
            pending.append((cn_name, py_name))

    # 模块内类的成员
    for cn_name, py_name in pending:
        for lib_name, module in ordered:
            classes = _MODULE_CLASSES.get(module.__name__)
            if not classes:
                continue
            if any(hasattr(getattr(module, cls, None), py_name) for cls in classes if cls in vars(module)):
                result.setdefault(lib_name, []).append(cn_name)
                break

    return { name: dedupe(items) for name, items in result.items() }


def signature_params(py_name: str) -> tuple[str, ...] | None:
    """
    内省 Python 目标的可调用参数并格式化为展示文本

    Args:
        py_name: 词表中的 Python 目标名

    Returns:
        参数展示文本元组; 无法内省时返回 None
    """
    if py_name in _SIGNATURE_CACHE:
        return _SIGNATURE_CACHE[py_name]

    target = _resolve_py_target(py_name)
    if target is None or not callable(target):
        _SIGNATURE_CACHE[py_name] = None
        return None
    try:
        signature = inspect.signature(target)
    except (TypeError, ValueError) as e:
        safe_log(f"解析函数签名失败: {e}", "debug")
        _SIGNATURE_CACHE[py_name] = None
        return None

    params: list[str] = []
    for parameter in signature.parameters.values():
        text = parameter.name

        # 可变参数保留星号, 让使用者一眼看出能传任意个实参
        if parameter.kind is inspect.Parameter.VAR_POSITIONAL:
            text = '*' + text
        elif parameter.kind is inspect.Parameter.VAR_KEYWORD:
            text = '**' + text
        if parameter.default is not inspect.Parameter.empty:
            default_text = DEFAULT_TEXT.get(repr(parameter.default), repr(parameter.default))
            text += '=' + (default_text if len(default_text) <= 16 else default_text[:13] + '...')
        params.append(text)

        # 参数过多时截断, 否则提示框会宽到超出屏幕
        if len(params) >= _MAX_TIP_PARAMS:
            params.append('…')
            break

    result = tuple(params)
    _SIGNATURE_CACHE[py_name] = result
    return result


def to_byte_spans(text: str, spans: Sequence[tuple[int, int]]) -> list[tuple[int, int]]:
    """
    将字符下标区间转换为字节下标区间, Scintilla 高亮使用字节偏移

    Args:
        text: 完整文本
        spans: 字符下标区间列表

    Returns:
        字节下标区间列表
    """
    if text.isascii():
        return list(spans)
    offsets: list[int] = [0] * (len(text) + 1)
    total = 0
    for index, char in enumerate(text):
        offsets[index] = total
        total += len(char.encode('utf-8'))
    offsets[len(text)] = total
    return [(offsets[start], offsets[end]) for start, end in spans]

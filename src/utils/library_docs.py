from __future__ import annotations
import ast
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from src.utils.exceptions import safe_log


# 默认值展示时的中文替换, 供签名内省等模块复用
DEFAULT_TEXT = { 'None': '空', 'True': '真', 'False': '假' }

_LIB_OPS_CACHE: LibraryOps | None = None
_SOURCE_CACHE: dict[str, dict[str, LibraryOp]] = { }


@dataclass(frozen=True)
class LibraryOp:
    """扩展库中的一个操作"""
    name: str  # 中文操作名, 调用时作为第一个字符串实参
    func: str  # 库内部的 Python 函数名
    params: tuple[str, ...]  # 参数展示文本
    doc: str  # 摘要, 文档字符串首行
    returns: bool  # 是否有返回值, True=椭圆取值积木, False=方块执行积木


def _default_text(value) -> str:
    """
    将参数默认值转为展示文本

    Args:
        value: Python 默认值

    Returns:
        展示文本
    """
    text = repr(value)
    text = DEFAULT_TEXT.get(text, text)
    return text if len(text) <= 20 else text[:17] + '...'


def _module_constants(module: ast.Module) -> dict[str, object]:
    """
    收集模块级字面量常量, 压缩后的库源码会用 _A/_B/_C 等代表 True/False/None

    Args:
        module: 模块 AST

    Returns:
        常量名到取值的映射
    """
    consts: dict[str, object] = { }
    for node in module.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        try:
            consts[target.id] = ast.literal_eval(node.value)
        except (ValueError, SyntaxError):
            continue
    return consts


def _format_params(node: ast.AST, consts: dict[str, object] | None = None) -> tuple[str, ...]:
    """
    将函数定义参数格式化为展示文本

    Args:
        node: 函数定义节点
        consts: 模块级常量表, 用于还原压缩后的默认值

    Returns:
        参数展示文本元组
    """
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return ()
    consts = consts or { }
    args = node.args
    positional = list(args.posonlyargs) + list(args.args)
    defaults: list[ast.expr | None] = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)

    def render(default_value: ast.expr | None) -> str:
        """
        渲染单个默认值

        Args:
            default_value: 默认值表达式节点, None 表示该参数无默认值

        Returns:
            渲染后的默认值展示文本, 无默认值时返回空字符串
        """
        if default_value is None:
            return ''
        if isinstance(default_value, ast.Name) and default_value.id in consts:  # type: ignore
            return '=' + _default_text(consts[default_value.id])  # type: ignore
        try:
            return '=' + _default_text(ast.literal_eval(default_value))
        except (ValueError, SyntaxError):
            return '=…'  # type: ignore

    result: list[str] = []
    for arg, default in zip(positional, defaults):
        result.append(arg.arg + render(default))  # type: ignore
    if args.vararg is not None:  # type: ignore
        result.append('*' + args.vararg.arg)
    for arg, default in zip(args.kwonlyargs, args.kw_defaults):
        result.append(arg.arg + render(default))
    if args.kwarg is not None:
        result.append('**' + args.kwarg.arg)
    return tuple(result)


def _summary(node: ast.AST) -> str:
    """
    取出文档字符串首行作为摘要

    Args:
        node: 函数定义节点

    Returns:
        摘要文本, 可能为空
    """
    doc = ast.get_docstring(node) or ''  # type: ignore
    for line in doc.splitlines():
        line = line.strip()
        if line:
            return line
    return ''


def _has_return_value(node: ast.AST) -> bool:
    """
    静态判断函数是否返回非 None 的值

    Args:
        node: 函数定义节点

    Returns:
        True 表示有返回值, 生成椭圆取值积木, False 表示无返回值, 生成方块执行积木
    """
    for child in ast.walk(node):
        if not isinstance(child, ast.Return):
            continue
        value = child.value
        if value is None:
            continue
        if isinstance(value, ast.Constant) and value.value is None:
            continue
        return True
    return False


def parse_library_source(source: str) -> dict[str, LibraryOp]:
    """
    解析单个扩展库源码, 提取中文操作名到操作信息的映射

    Args:
        source: 扩展库的 Python 源码

    Returns:
        操作名到操作信息的映射, 无分发表时为空
    """
    cached = _SOURCE_CACHE.get(source)
    if cached is not None:
        return cached
    result: dict[str, LibraryOp] = { }
    try:
        module = ast.parse(source)
    except (SyntaxError, ValueError) as e:
        safe_log(f"解析库源码失败, 该库操作将全部缺失: {e}", "error")
        _SOURCE_CACHE[source] = result
        return result

    funcs = {
        node.name: node
        for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    consts = _module_constants(module)

    dispatch: dict[str, str] = { }
    for node in ast.walk(module):
        if not isinstance(node, ast.Dict):
            continue
        mapping = { }
        for key, value in zip(node.keys, node.values):
            if (
                    isinstance(key, ast.Constant)
                    and isinstance(key.value, str)
                    and isinstance(value, ast.Name)
                    and value.id in funcs
            ):
                mapping[key.value] = value.id
        if len(mapping) > len(dispatch):
            dispatch = mapping

    for op_name, func_name in dispatch.items():
        target = funcs[func_name]
        result[op_name] = LibraryOp(
            name=op_name,
            func=func_name,
            params=_format_params(target, consts),
            doc=_summary(target),
            returns=_has_return_value(target),
        )
    _SOURCE_CACHE[source] = result
    return result


def get_library_ops() -> LibraryOps:
    """
    获取内置扩展库的操作表, 首次使用时按库解析源码

    Returns:
        库函数名到操作表的映射, 懒加载
    """
    global _LIB_OPS_CACHE
    if _LIB_OPS_CACHE is None:
        from src.module import lib_map
        from src.module.builtin_map import builtin

        sources = {
            name: value
            for name, value in vars(lib_map).items()
            if isinstance(value, str) and 'def ' in value
        }
        _LIB_OPS_CACHE = LibraryOps(builtin, sources)
    return _LIB_OPS_CACHE  # type: ignore


class LibraryOps(Mapping[str, dict[str, LibraryOp]]):
    """扩展库操作表的懒加载映射, 只解析真正用到的库, 避免启动卡顿"""

    def __init__(self, builtin_map: dict[str, str], sources: dict[str, str]):
        """
        初始化

        Args:
            builtin_map: 内置函数映射, 如 自动化* 对应 automation_library
            sources: 扩展库源码映射, 如 automation_library 对应源码
        """
        self._sources: dict[str, str] = { }
        for cn_name, target in builtin_map.items():
            if isinstance(target, str) and sources.get(target):
                self._sources[cn_name] = sources[target]
        self._cache: dict[str, dict[str, LibraryOp]] = { }

    def __getitem__(self, key: str) -> dict[str, LibraryOp]:
        """
        按库函数名取操作表, 首次访问时触发解析

        Args:
            key: 库函数名

        Returns:
            该库的操作表
        """
        if key not in self._cache:
            self._cache[key] = parse_library_source(self._sources[key])
        return self._cache[key]

    def __iter__(self) -> Iterator[str]:
        """
        迭代库函数名

        Returns:
            库函数名迭代器
        """
        return iter(self._sources)

    def __len__(self) -> int:
        """
        返回库的数量

        Returns:
            库函数名数量
        """
        return len(self._sources)

    def get(self, key, default=None):
        """
        获取操作表, 不存在时返回默认值, 不触发解析

        Args:
            key: 库函数名
            default: 默认值

        Returns:
            操作表或默认值
        """
        if key not in self._sources:
            return default
        return self[key]

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class DocumentIndex:
    """当前文档的符号索引"""
    symbols: list[str] = field(default_factory=list)  # 全局标识符, 文档顺序
    variables: dict[str, str] = field(default_factory=dict)  # 变量名对应类型标签
    functions: dict[str, tuple[tuple[str, ...], int]] = field(default_factory=dict)  # 函数名对应参数与行号
    classes: dict[str, dict[str, tuple[tuple[str, ...], int]]] = field(default_factory=dict)  # 类对应方法
    class_ranges: list[tuple[int, int, str]] = field(default_factory=list)  # 起始行, 结束行, 类名
    self_members: list[str] = field(default_factory=list)  # 自身.xxx 出现过的成员
    aliases: dict[str, str] = field(default_factory=dict)  # 模块别名对应模块标识, 即 import 后的名字

    def class_at(self, line: int) -> str | None:
        """
        获取指定行所在的类

        Args:
            self: 索引实例
            line: 行号, 0 起

        Returns:
            类名, 不在任何类体内时返回 None
        """
        for start, end, name in self.class_ranges:
            if start <= line <= end:
                return name
        return None

    def methods_of(self, class_name: str) -> list[str]:
        """
        获取类的方法名列表

        Args:
            self: 索引实例
            class_name: 类名

        Returns:
            方法名列表, 文档顺序
        """
        return list(self.classes.get(class_name, { }))

    def params_of(self, name: str) -> tuple[str, ...] | None:
        """
        获取文档内自定义函数的参数列表

        Args:
            self: 索引实例
            name: 函数名

        Returns:
            参数展示文本元组, 未定义时返回 None
        """
        item = self.functions.get(name)
        return item[0] if item else None


@dataclass
class CompletionContext:
    """补全上下文"""
    kind: str = 'none'  # none / global / member / library / import
    prefix: str = ''  # 已输入, 需要被替换的前缀
    receiver: str | None = None  # 成员补全时的接收者
    lib_name: str | None = None  # 扩展库函数名, 如 自动化*
    in_string: bool = False  # 是否位于字符串内部


NONE_CONTEXT = CompletionContext(kind='none')


@dataclass
class CallContext:
    """函数调用上下文, 用于参数提示"""
    name: str  # 被调用的函数名
    arg_index: int  # 当前实参序号, 0 起
    paren_index: int  # 左括号在行前缀中的下标
    args_text: str  # 左括号之后, 光标之前的文本
    receiver: str | None = None  # 方法调用的接收者, 如 对象.方法 中的 对象


@dataclass
class ScanState:
    """单行扫描结果"""
    in_string: bool = False
    string_start: int = -1
    in_comment: bool = False
    brackets: list[list] = field(default_factory=list)  # 括号字符, 下标, 实参序号

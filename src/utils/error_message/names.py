import re
from src.module.builtin_map import builtin


_EXTRA_EXCEPTION_NAMES = {
    "SyntaxError": "语法错误",
    "IndentationError": "缩进错误",
    "TabError": "缩进混用错误",
    "UnboundLocalError": "局部变量未赋值",
    "ModuleNotFoundError": "模块未找到",
    "ImportError": "导入错误",
    "OverflowError": "数值溢出",
    "MemoryError": "内存不足",
    "ArithmeticError": "算术错误",
    "LookupError": "查找错误",
    "UnicodeDecodeError": "编码解码错误",
    "UnicodeEncodeError": "编码转换错误",
    "PermissionError": "权限错误",
    "OSError": "系统错误",
    "EOFError": "输入提前结束",
    "StopAsyncIteration": "异步迭代结束",
    "ExceptionGroup": "异常组",
    "BaseExceptionGroup": "异常组",
}

EXCEPTION_NAMES: dict[str, str] = {
    english: chinese
    for chinese, english in builtin.items()
    if english.endswith(("Error", "Exception", "Interrupt", "Iteration"))
}
EXCEPTION_NAMES.update(_EXTRA_EXCEPTION_NAMES)

TYPE_NAMES = {
    "int": "整数",
    "float": "小数",
    "str": "文本",
    "string": "文本",
    "bool": "布尔值",
    "list": "列表",
    "dict": "字典",
    "tuple": "元组",
    "set": "集合",
    "frozenset": "不可变集合",
    "NoneType": "空值",
    "bytes": "字节",
    "bytearray": "字节数组",
    "range": "范围",
    "complex": "复数",
    "object": "对象",
    "type": "类型",
    "module": "模块",
    "function": "函数",
    "method": "方法",
    "generator": "生成器",
    "slice": "切片",
}

_PHRASE_NAMES = {
    "None or str": "空值或文本",
    "str or a tuple of str": "文本或元组",
    "str or an os.PathLike object": "文本或路径对象",
    "bytes-like object or ASCII string": "字节或文本",
    "string or bytes-like object": "文本或字节",
    "string or compiled pattern": "文本或已编译的正则",
}

_WIN_ERRORS = {
    2: "找不到文件或路径",
    3: "找不到路径",
    5: "拒绝访问, 可能需要管理员身份",
    32: "文件正被其它程序占用",
    183: "文件或目录已经存在",
}

_WIN_ERROR_LINE = re.compile(r"^\[WinError (?P<code>\d+)] .*?[:：] '(?P<path>.+)'$")

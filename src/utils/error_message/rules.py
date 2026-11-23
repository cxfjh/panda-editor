import re


_MESSAGE_RULES: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"^name '(?P<name>.+)' is not defined\. Did you mean: '(?P<fix>.+)'\?$"),
        "名称 {name} 没有定义, 是想写 {fix} 吗",
    ),
    (
        re.compile(r"^name '(?P<name>.+)' is not defined$"),
        "名称 {name} 没有定义, 检查是否拼错, 或者忘了先赋值",
    ),
    (
        re.compile(r"^unsupported operand type\(s\) for (?P<op>.+): '(?P<t1>.+)' and '(?P<t2>.+)'$"),
        "运算符 {op} 两边的类型对不上, 不能把 {t1} 和 {t2} 一起运算",
    ),
    (
        re.compile(r"^can only concatenate (?P<t1>.+) \(not \"(?P<t2>.+)\"\) to (?P<t3>.+)$"),
        "拼接时两边类型要一致, 不能把 {t2} 拼到 {t3} 后面",
    ),
    (
        re.compile(r"^'(?P<t1>.+)' object is not subscriptable$"),
        "{t1} 不能用方括号取下标",
    ),
    (
        re.compile(r"^'(?P<t1>.+)' object is not callable$"),
        "{t1} 不是函数, 不能在后面加括号调用",
    ),
    (
        re.compile(r"^'(?P<t1>.+)' object is not iterable$"),
        "{t1} 不能遍历, 需要换成列表或元组这类能遍历的类型",
    ),
    (
        re.compile(r"^'(?P<t1>.+)' object has no attribute '(?P<attr>.+)'$"),
        "{t1} 没有 {attr} 这个属性或方法, 检查名字是否拼错",
    ),
    (
        re.compile(r"^object of type '(?P<t1>.+)' has no len\(\)$"),
        "{t1} 没有长度, 不能用 长度 去取",
    ),
    (
        re.compile(r"^list assignment index out of range$"),
        "给列表赋值时下标越界",
    ),
    (
        re.compile(r"^list index out of range$"),
        "列表下标越界, 检查下标是否超过了列表长度",
    ),
    (
        re.compile(r"^(?P<t1>.+) index out of range$"),
        "{t1} 的下标越界",
    ),
    (
        re.compile(r"^list\.remove\(x\): x not in list$"),
        "要删除的元素不在列表里",
    ),
    (
        re.compile(r"^pop from empty list$"),
        "列表是空的, 取不出元素",
    ),
    (
        re.compile(r"^pop from empty (?:dict|set)$"),
        "字典或集合是空的, 取不出元素",
    ),
    (
        re.compile(r"^'(?P<op>.+)' not supported between instances of '(?P<t1>.+)' and '(?P<t2>.+)'$"),
        "不能用 {op} 比较 {t1} 和 {t2}, 两边的类型要一致",
    ),
    (
        re.compile(r"^(?:(?:integer|float) )?(?:division(?: or modulo)?|modulo) by zero$"),
        "除数不能是 0",
    ),
    (
        re.compile(r"^invalid literal for int\(\) with base 10: '(?P<text>.*)'$"),
        "'{text}' 不能转成整数, 里面可能有非数字字符",
    ),
    (
        re.compile(r"^could not convert string to float: '(?P<text>.*)'$"),
        "'{text}' 不能转成小数",
    ),
    (
        re.compile(r"^(?P<name>[\w.]+)\(\) takes exactly one argument \((?P<got>\d+) given\)$"),
        "函数 {name} 只能有 1 个参数, 实际给了 {got} 个",
    ),
    (
        re.compile(r"^(?P<name>[\w.]+)\(\) takes (?P<need>\d+) positional arguments? but (?P<got>\d+) were given$"),
        "函数 {name} 需要 {need} 个参数, 实际给了 {got} 个",
    ),
    (
        re.compile(r"^(?P<name>[\w.]+)\(\) missing (?P<need>\d+) required positional arguments?: (?P<names>.+)$"),
        "函数 {name} 少了 {need} 个必填参数: {names}",
    ),
    (
        re.compile(r"^(?P<name>\w+) expected at least (?P<need>\d+) arguments?, got (?P<got>\d+)$"),
        "函数 {name} 至少要 {need} 个参数, 实际只给了 {got} 个",
    ),
    (
        re.compile(r"^(?P<name>\w+) expected at most (?P<need>\d+) arguments?, got (?P<got>\d+)$"),
        "函数 {name} 最多只能有 {need} 个参数, 实际给了 {got} 个",
    ),
    (
        re.compile(r"^(?P<name>[\w.]+)\(\) takes no arguments \((?P<got>\d+) given\)$"),
        "函数 {name} 不接受参数, 实际给了 {got} 个",
    ),
    (
        re.compile(r"^(?P<name>[\w.]+)\(\) takes exactly (?P<need>\d+) arguments? \((?P<got>\d+) given\)$"),
        "函数 {name} 需要 {need} 个参数, 实际给了 {got} 个",
    ),
    (
        re.compile(r"^(?P<name>\w+) expected (?P<need>\d+) arguments?, got (?P<got>\d+)$"),
        "函数 {name} 需要 {need} 个参数, 实际只给了 {got} 个",
    ),
    (
        re.compile(r"^takes (?P<need>\d+) positional arguments? but (?P<got>\d+) were given$"),
        "参数个数不对, 需要 {need} 个, 实际给了 {got} 个",
    ),
    (
        re.compile(r"^missing (?P<need>\d+) required positional arguments?: (?P<names>.+)$"),
        "{names} 这几项没有传, 是必填参数",
    ),
    (
        re.compile(r"^got an unexpected keyword argument '(?P<name>.+)'$"),
        "多传了一个用不到的参数 {name}",
    ),
    (
        re.compile(r"^maximum recursion depth exceeded.*$"),
        "递归太深了, 检查函数有没有写结束条件",
    ),
    (
        re.compile(r"^(?:max|min)\(\) (?:iterable argument is empty|arg is an empty sequence)$"),
        "不能在空序列上求最大值或最小值",
    ),
    (
        re.compile(r"^'(?P<t1>.+)' object does not support item assignment$"),
        "{t1} 不支持按位置赋值, 它是不可变的, 先转成列表再改",
    ),
    (
        re.compile(r"^cannot unpack non-iterable (?P<t1>.+) object$"),
        "{t1} 不能解包, 只有列表或元组这类能遍历的值可以拆开赋值",
    ),
    (
        re.compile(r"^can't multiply sequence by non-int of type '(?P<t1>.+)'$"),
        "序列只能乘整数, 不能乘 {t1}",
    ),
    (
        re.compile(r"^range\(\) arg 3 must not be zero$"),
        "range 的步长不能是 0",
    ),
    (
        re.compile(r"^Replacement index (?P<index>\d+) out of range for positional args tuple$"),
        "格式化时第 {index} 个占位符没有对应的参数",
    ),
    (
        re.compile(r"^(?P<name>[\w.]+)\(\) takes at most (?P<need>\d+) arguments? \((?P<got>\d+) given\)$"),
        "函数 {name} 最多只能有 {need} 个参数, 实际给了 {got} 个",
    ),
    (
        re.compile(r"^(?P<name>[\w.]+)\(\) takes at least (?P<need>\d+) arguments? \((?P<got>\d+) given\)$"),
        "函数 {name} 至少要 {need} 个参数, 实际只给了 {got} 个",
    ),
    (
        re.compile(r"^(?P<name>[\w.]+)\(\) missing required argument '(?P<arg>.+)' \(pos (?P<pos>\d+)\)$"),
        "函数 {name} 少了必填参数 {arg}",
    ),
    (
        re.compile(r"^(?P<name>[\w.]+)\(\) takes (?P<need>\d+) or (?P<other>\d+) arguments$"),
        "函数 {name} 只能接受 {need} 个或 {other} 个参数",
    ),
    (
        re.compile(r"^(?P<name>[\w.]+)\(\) must have at least two arguments\.$"),
        "函数 {name} 至少要两个参数",
    ),
    (
        re.compile(r"^(?P<name>[\w.]+) first arg must be (?P<expect>.+), not (?P<t1>.+)$"),
        "函数 {name} 的第一个参数应该是 {expect}, 不能是 {t1}",
    ),
    (
        re.compile(r"^(?P<name>[\w.]+)\(\) argument '(?P<arg>.+)' must be (?P<expect>.+), not (?P<t1>.+)$"),
        "函数 {name} 的参数 {arg} 应该是 {expect}, 不能是 {t1}",
    ),
    (
        re.compile(r"^(?P<name>[\w.]+)\(\) expected a character, but string of length (?P<length>\d+) found$"),
        "函数 {name} 只接受单个字符, 这里给了 {length} 个",
    ),
    (
        re.compile(r"^(?P<name>[\w.]+) arg must be (?P<expect>.+)$"),
        "函数 {name} 的参数应该是 {expect}",
    ),
    (
        re.compile(r"^expected (?P<expect>.+), got '(?P<t1>.+)'$"),
        "这里应该是 {expect}, 实际给的是 {t1}",
    ),
    (
        re.compile(r"^argument should be a (?P<expect>.+?)(?: where __fspath__ returns a str)?, not '(?P<t1>.+)'$"),
        "这个参数应该是 {expect}, 不能是 {t1}",
    ),
    (
        re.compile(r"^bad operand type for (?P<op>.+)\(\): '(?P<t1>.+)'$"),
        "{t1} 不能用在 {op} 上",
    ),
    (
        re.compile(r"^type (?P<t1>.+) doesn't define __(?P<method>\w+)__ method$"),
        "{t1} 不支持这个操作, 缺少 __{method}__ 方法",
    ),
    (
        re.compile(r"^must be real number, not (?P<t1>.+)$"),
        "这里需要数字, 不能是 {t1}",
    ),
    (
        re.compile(r"^'(?P<t1>.+)' object cannot be interpreted as an integer$"),
        "{t1} 不能当作整数用",
    ),
    (
        re.compile(r"^first argument must be string or compiled pattern$"),
        "第一个参数应该是文本或已编译的正则",
    ),
    (
        re.compile(r"^math domain error$"),
        "数学函数的值超出允许范围, 例如对负数开平方",
    ),
    (
        re.compile(r"^math range error$"),
        "数学计算的结果太大, 超出允许范围",
    ),
    (
        re.compile(r"^(?P<name>[\w.]+)\(\) not defined for negative values$"),
        "函数 {name} 不接受负数",
    ),
    (
        re.compile(r"^(?P<name>[\w.]+)\(\) arg is a malformed string$"),
        "函数 {name} 的参数不是合法的数字文本",
    ),
    (
        re.compile(r"^(?P<name>[\w.]+)\(\) arg not in range\((?P<limit>.+)\)$"),
        "函数 {name} 的参数超出允许范围",
    ),
    (
        re.compile(r"^(?P<value>.+) is not in list$"),
        "列表里没有 {value}",
    ),
    (
        re.compile(r"^Tuple or struct_time argument required$"),
        "这里需要传入时间元组, 不能直接给文本",
    ),
    (
        re.compile(r"^'(?P<t1>.+)' object is not an iterator$"),
        "{t1} 不是迭代器, 不能直接取下一项",
    ),
    (
        re.compile(r"^'(?P<t1>.+)' object is not reversible$"),
        "{t1} 不能反转",
    ),
    (
        re.compile(r"^Object of type (?P<t1>.+) is not JSON serializable$"),
        "{t1} 不能转成 json, 只支持数字 文本 列表 字典 布尔值 和 空值",
    ),
    (
        re.compile(r"^(?P<detail>.+), unterminated subpattern at position (?P<pos>\d+)$"),
        "正则里的括号没有闭合",
    ),
    (
        re.compile(r"^not enough values to unpack \(expected (?P<need>\d+), got (?P<got>\d+)\)$"),
        "解包时数量不够, 需要 {need} 个值, 实际只有 {got} 个",
    ),
    (
        re.compile(r"^too many values to unpack \(expected (?P<need>\d+)\)$"),
        "解包时数量太多, 只需要 {need} 个值",
    ),
    (
        re.compile(r"^'.+' codec can't encode characters? .*$"),
        "文本里有当前编码存不下的字符, 换成 utf-8 再试",
    ),
    (
        re.compile(r"^'.+' codec can't decode bytes? .*$"),
        "这段字节不是当前编码的, 换个编码试试, 例如 gb18030",
    ),
    (
        re.compile(r"^Expecting property name enclosed in double quotes: line (?P<line>\d+) column (?P<col>\d+).*$"),
        "json 第 {line} 行的键名要用双引号包起来",
    ),
    (
        re.compile(r"^Expecting value: line (?P<line>\d+) column (?P<col>\d+) .*$"),
        "json 第 {line} 行不是合法的值, 检查括号和引号",
    ),
    (
        re.compile(r"^time data '(?P<data>.+)' does not match format '(?P<fmt>.+)'$"),
        "时间文本 {data} 和格式 {fmt} 对不上, 检查两边的写法",
    ),
    (
        re.compile(r"^unterminated character set at position (?P<pos>\d+)$"),
        "正则里的方括号没有闭合",
    ),
    (
        re.compile(r"^No module named '(?P<name>.+)'$"),
        "找不到模块 {name}, 检查名字是否拼错, 或者先安装这个库",
    ),
    (
        re.compile(r"^can only join an iterable$"),
        "只能拼接可遍历的对象, 检查括号里是不是列表或元组",
    ),
    (
        re.compile(r"^(?P<name>[\w.]+)\(\) argument must be a string, a bytes-like object or a real number, not '(?P<t1>.+)'$"),
        "{t1} 不能直接转成数字, 先把这个值的类型换对",
    ),
    (
        re.compile(r"^(?P<what>[\w.]+) indices must be integers(?: or slices)?, not '?(?P<t1>\w+)'?$"),
        "{what} 的下标必须是整数, 不能用 {t1}",
    ),
    (
        re.compile(r"^unhashable type: '(?P<t1>.+)'$"),
        "{t1} 不能当字典的键",
    ),
    (
        re.compile(r"^\[Errno 2] No such file or directory: '(?P<path>.+)'$"),
        "找不到文件 {path}, 检查路径是否正确",
    ),
    (
        re.compile(r"^\[Errno 13] Permission denied: '(?P<path>.+)'$"),
        "没有权限访问 {path}, 换个目录或试试管理员身份运行",
    ),
    (
        re.compile(r"^(?P<text>.+) was never closed$"),
        "括号或引号没有闭合",
    ),
    (
        re.compile(r"^invalid character .*$"),
        "出现了不认识的符号, 检查是否用了全角括号或其它特殊字符",
    ),
    (
        re.compile(r"^invalid decimal literal$"),
        "数字后面直接跟了其它字符, 检查变量名是否以数字开头",
    ),
    (
        re.compile(r"^unexpected character after line continuation character$"),
        "换行写法有误, 检查反斜杠后面是否多了空格",
    ),
    (
        re.compile(r"^invalid syntax$"),
        "语法错误, 检查这一行是否漏写了符号",
    ),
    (
        re.compile(r"^expected ':'$"),
        "这一行的末尾少了冒号",
    ),
    (
        re.compile(r"^unexpected EOF while parsing$"),
        "代码还没写完, 检查括号是否配对",
    ),
    (
        re.compile(r"^unindent does not match any outer indentation level$"),
        "缩进对不齐, 同一层的代码缩进空格数要一致",
    ),
    (
        re.compile(r"^expected an indented block.*$"),
        "这里应该有一段缩进的代码",
    ),
    (
        re.compile(r"^cannot assign to .+$"),
        "等号左边不能这么写, 只能给变量或列表元素赋值",
    ),
]

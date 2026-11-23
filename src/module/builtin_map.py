"""内置函数映射表"""

builtin = { }

builtin.update(
    {
        "输出*": "print",
        "输入*": "input",
        "区间*": "range",
        "长度*": "len",
        "最大*": "max",
        "最小*": "min",
        "求和*": "sum",
        "绝对值*": "abs",
        "取整*": "round",
        "次方*": "pow",
        "商余*": "divmod",
        "复数*": "complex",
        "转整数*": "int",
        "转小数*": "float",
        "转文本*": "str",
        "转布尔*": "bool",
        "列表*": "list",
        "元组*": "tuple",
        "字典*": "dict",
        "集合*": "set",
        "字符*": "chr",
        "编码*": "ord",
        "序遍历*": "enumerate",
        "配对*": "zip",
        "排序*": "sorted",
        "反转*": "reversed",
        "映射*": "map",
        "筛选*": "filter",
        "迭代器*": "iter",
        "下一项*": "next",
        "全成立*": "all",
        "任一真*": "any",
        "类型*": "type",
        "属类型*": "isinstance",
        "哈希*": "hash",
        "打开*": "open",
        "执行码*": "exec",
    },
)

builtin.update(
    {
        "异常": "Exception",
        "值错误": "ValueError",
        "类型错误": "TypeError",
        "名称错误": "NameError",
        "索引错误": "IndexError",
        "键错误": "KeyError",
        "除零错误": "ZeroDivisionError",
        "文件未找到": "FileNotFoundError",
        "运行时错误": "RuntimeError",
        "停止迭代": "StopIteration",
        "属性错误": "AttributeError",
        "断言错误": "AssertionError",
        "未实现错误": "NotImplementedError",
        "递归错误": "RecursionError",
        "超时错误": "TimeoutError",
        "中断": "KeyboardInterrupt",
    },
)

builtin.update(
    {
        "自动化*": "automation_library",
        "文件*": "document_library",
        "界面*": "interface_library",
        "网络*": "network_library",
        "系统*": "system_library",
        "并发*": "concurrent_libraries",
        "随机*": "random_library",
    },
)

# 内置库方法
from src.utils.extend import extract_fun


builtin_funcs = { }

# 常用库方法
builtin_funcs.update(
    {
        "输出*": "print",
        "输入*": "input",
        "执行*": "exec",
        "退出*": "exit",
        "范围*": "range",
        "数字*": "int",
        "字符串*": "str",
        "布尔值*": "bool",
        "类型*": "type",
        "异常*": "Exception",
        "长度*": "len",
    },
)

# 内置库方法
builtin_funcs.update(
    {
        "自动化*": "AutomationLibrary",
        "文件*": "DocumentLibrary",
        "界面*": "InterfaceLibrary",
        "网络*": "NetworkLibrary",
        "系统*": "SystemLibrary",
        "并发*": "ConcurrentLibraries",
        "随机*": "RandomLibrary",
        "错误器*": "@_catch",
        "线程器*": "@_thread",
        "计时器*": "@_timeout",
        "间隔器*": "@_interval",
        "循环器*": "@_loop",
    },
)

# 扩展库方法
extract_fun(builtin_funcs)

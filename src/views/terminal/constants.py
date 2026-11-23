"""终端显示相关的常量"""

# 终端输出最大行数限制
MAX_OUTPUT_LINES = 5000

# 崩溃时从终端尾部回看的行数, 足够覆盖最内层调用帧与异常提示行
TAIL_LINES = 40

# 内部命令映射
COMMAND_HANDLERS = {
    "帮助": "_show_help",
    "清屏": "_clear_screen",
    "显示": "_show_pwd",
    "运行": "_run_code",
    "列出": "_list_all_packages",
}

# 带参数的命令前缀, 中文前缀不强制空格
PREFIX_COMMANDS = (
    ("切换", "_change_directory"),
    ("安装", "_install_package"),
    ("卸载", "_uninstall_package"),
)

# 帮助列表, 命令与说明
HELP_ROWS = (
    ("清屏", "清空终端内容"),
    ("显示", "显示当前目录"),
    ("帮助", "显示帮助信息"),
    ("列出", "列出安装的库"),
    ("运行", "运行当前编辑器里的代码"),
    ("安装 <库名>", "安装 Python 库, 例如 安装 requests"),
    ("卸载 <库名>", "卸载 Python 库, 例如 卸载 requests"),
    ("切换 <路径>", "切换目录, 例如 切换 C:\\Windows\\System32"),
)

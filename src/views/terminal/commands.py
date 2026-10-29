import os
from wcwidth import wcswidth
from src.utils.code_proc import parse_to_python_code_path
from src.utils.config_service import get_config_service
from src.views.terminal import constants
from src.views.terminal.refs import TerminalRefs


class CommandMixin(TerminalRefs):
    """内置命令相关方法, 由终端组件混入使用"""

    def _on_submit(self):
        """
        处理用户提交命令

        Args:
            self: 当前终端实例
        """
        command = self._input.text()
        self._input.clear()
        if self._process_running:
            self._process.write(command.encode("utf-8") + b"\n")  # 发送输入和换行符
            if command:
                self._append_output(command)  # 回显用户输入
            return

        # 命令模式下空输入直接返回
        if not command.strip():
            return

        self._append_output(f"> {command.strip()}")

        self._command_history.append(command.strip())
        self._history_index = len(self._command_history)  # 索引指向最新位置
        self._execute_command(command.strip())

    def _execute_command(self, command: str):
        """
        执行命令

        Args:
            self: 当前终端实例
            command: 用户输入的命令字符串
        """

        # 中文输入法容易带出全角空格, 统一成半角再解析
        command = command.replace("\u3000", " ").strip()
        cmd_lower = command.lower()

        # 精确匹配内部命令
        if cmd_lower in constants.COMMAND_HANDLERS:
            getattr(self, constants.COMMAND_HANDLERS[cmd_lower])()
            return

        # 前缀匹配带参数的命令
        for prefix, handler in constants.PREFIX_COMMANDS:
            if cmd_lower.startswith(prefix):
                getattr(self, handler)(command[len(prefix):].strip())
                return

        # 外部命令
        if self._is_busy():
            self._append_output("错误: 当前有进程正在运行 请等待其结束")
            return
        self._set_running(True)
        self._error_report_path = None  # 外部命令不是用户代码, 不做错误翻译
        self._process.start("cmd.exe", ["/c", command])  # /c 表示执行后关闭

    def _clear_screen(self):
        """
        清空终端

        Args:
            self: 当前终端实例
        """
        self._output.clear()

    def _show_pwd(self):
        """
        显示当前目录

        Args:
            self: 当前终端实例
        """
        self._append_output(self._current_dir)

    def _show_help(self):
        """
        显示帮助信息

        Args:
            self: 当前终端实例
        """

        # 命令列按显示宽度对齐, 中文占两格才不会错位
        width = max(wcswidth(row[0]) for row in constants.HELP_ROWS)
        lines = ["", "内部命令"]
        for command, description in constants.HELP_ROWS:
            padding = " " * (width - wcswidth(command) + 4)
            lines.append(f"  {command}{padding}{description}")
        lines.append("")
        lines.append("外部命令")
        lines.append("  直接输入系统命令即可, 例如 dir, echo, pause")
        lines.append("")
        self._append_output("\n".join(lines))

    def _change_directory(self, path: str):
        """
        切换工作目录

        Args:
            self: 当前终端实例
            path: 目标目录路径
        """
        if not path:
            self._append_output(self._current_dir)  # 无参数时显示当前目录
            return

        # 处理路径, 绝对路径直接使用 相对路径基于当前目录拼接
        new_dir = os.path.normpath(path if os.path.isabs(path) else os.path.join(self._current_dir, path))
        if os.path.isdir(new_dir):
            self._current_dir = new_dir
            self._process.setWorkingDirectory(new_dir)
            self._append_output(f"已切换到: {new_dir}")
        else:
            self._append_output(f"目录不存在: {path}")

    def _install_package(self, package_name: str):
        """
        安装 Python 库

        Args:
            self: 当前终端实例
            package_name: 要安装的库名称
        """
        if not package_name:
            self._append_output("错误: 请指定要安装的库名称")
            return
        pip_args = ["-m", "pip", "install", package_name]

        # 检查是否配置了高速镜像源
        if get_config_service().get_personal_config("pipMirror") == "taobao":
            pip_args.extend(["-i", "https://mirrors.aliyun.com/pypi/simple/"])
        self._run_pip(pip_args, f"正在安装 {package_name}...")

    def _uninstall_package(self, package_name: str):
        """
        卸载 Python 库

        Args:
            self: 当前终端实例
            package_name: 要卸载的库名称
        """
        if not package_name:
            self._append_output("错误: 请指定要卸载的库名称")
            return
        self._run_pip(["-m", "pip", "uninstall", "-y", package_name], f"正在卸载 {package_name}...")

    def _list_all_packages(self):
        """
        列出所有已安装的 Python 库

        Args:
            self: 当前终端实例
        """
        self._run_pip(["-m", "pip", "list"], "正在获取已安装的库列表...")

    def _run_code(self):
        """
        终端运行命令, 运行当前编辑器代码

        Args:
            self: 当前终端实例
        """
        if not self._get_code_callback:
            self._append_output("错误: 未设置代码回调 无法运行！")
            return

        # 以当前标签页的文件路径为准判断类型, 不依赖配置里的陈旧状态
        file_path = self._get_file_path_callback() if self._get_file_path_callback else None
        if not file_path or not file_path.endswith('.cn'):
            self._append_output("错误: 只能运行已保存的 .cn 格式中文代码文件！")
            return

        assert callable(self._get_code_callback)
        code_text = self._get_code_callback()
        if not code_text:
            self._append_output("错误: 代码为空！")
            return

        # 解析中文代码并获取转换后的 .py 路径, 显式传入当前文件路径
        py_path = parse_to_python_code_path(code_text, file_path)
        if not py_path:
            self._append_output("错误: 代码解析失败！")
            return

        self.run_python_script(py_path, os.path.dirname(py_path))

import os
import subprocess
from PySide6.QtCore import QProcess
from src.utils.config_service import get_config_service
from src.utils.exceptions import safe_log
from src.views.terminal.refs import TerminalRefs


class ProcessMixin(TerminalRefs):
    """子进程运行相关方法, 由终端组件混入使用"""

    def _setup_process(self):
        """
        初始化子进程配置

        Args:
            self: 当前终端实例
        """
        self._process.setWorkingDirectory(self._current_dir)
        self._process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)  # 合并标准输出和标准错误
        self._process.readyReadStandardOutput.connect(self._on_ready_read)
        self._process.readyReadStandardError.connect(self._on_ready_read)
        self._process.finished.connect(self._on_process_finished)
        self._process.errorOccurred.connect(self._on_process_error)

    def _set_running(self, running: bool):
        """
        更新子进程运行状态与停止按钮

        Args:
            self: 当前终端实例
            running: True 表示有子进程在运行
        """
        self._process_running = running
        self._stop_btn.setEnabled(running)

    def _is_busy(self) -> bool:
        """
        检查子进程是否正在运行

        Args:
            self: 当前终端实例

        Returns:
            True 表示有子进程在运行, False 表示空闲
        """
        return self._process.state() != QProcess.ProcessState.NotRunning

    def _stop_process(self):
        """
        终止正在运行的子进程

        Args:
            self: 当前终端实例
        """
        if not self._is_busy():
            self._set_running(False)
            return
        self._stopping = True
        self._process.kill()
        self._append_output("\n> 已终止当前进程\n")

    def _get_python_dir(self):
        """
        获取 Python 目录, 未配置时输出错误信息

        Args:
            self: 当前终端实例

        Returns:
            Python 可执行文件路径, 未配置时返回 None
        """
        python_dir = get_config_service().get_app_config("python_path")
        if not python_dir:
            self._append_output("错误: 未配置Python路径")
        return python_dir

    def run_python_script(self, py_path: str, working_dir: str | None = None) -> None:
        """
        通过终端 QProcess 或独立窗口运行指定 Python 脚本

        Args:
            self: 当前终端实例
            py_path: 待运行的 .py 文件绝对路径
            working_dir: 子进程工作目录
        """
        python_dir = get_config_service().get_app_config("python_path")
        if not python_dir:
            self._append_output("错误: 未配置Python路径")
            return
        if not os.path.isfile(py_path):
            self._append_output(f"错误: 代码文件不存在：\n{py_path}")
            return

        # 先清空标记, 只有真正交给终端运行的代码才会重新打上
        self._error_report_path = None

        independent_run = get_config_service().get_personal_config("independentRun")
        if independent_run:
            try:
                subprocess.Popen([python_dir, "-u", py_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                self._append_output(f"\n> 已在独立窗口运行: {py_path}\n")
            except Exception as e:
                safe_log(f"启动独立窗口运行失败: {e}")
                self._append_output(f"\n> 启动独立窗口失败: {e}\n")
            return

        if self._is_busy():
            self._append_output("错误: 当前有进程正在运行 请等待其结束")
            return
        if working_dir and os.path.isdir(working_dir):
            # 同步终端显示的当前目录与子进程工作目录
            self._current_dir = working_dir
            self._process.setWorkingDirectory(working_dir)
        self._set_running(True)
        self._append_output(f"正在运行: {py_path}\n")

        # 标记本次是用户代码运行, 崩溃时据此补充中文说明
        self._error_report_path = py_path
        self._process.start(python_dir, ["-u", py_path])

    def _run_pip(self, pip_args: list, start_msg: str) -> None:
        """
        经统一通道运行 pip 子命令, 复用进程占用与 Python 路径检查

        Args:
            self: 当前终端实例
            pip_args: 传给 python -m pip 的参数列表
            start_msg: 启动时输出的提示文本
        """
        python_dir = self._get_python_dir()
        if not python_dir:
            return
        if self._is_busy():
            self._append_output("错误: 当前有进程正在运行 请等待其结束")
            return
        self._append_output(start_msg)
        self._set_running(True)
        self._error_report_path = None  # pip 不是用户代码, 不做错误翻译
        self._process.start(python_dir, pip_args)

    @staticmethod
    def _decode_process_data(raw_data) -> str:
        """
        解码进程输出数据

        Args:
            raw_data: QProcess 输出的原始字节数据

        Returns:
            解码后的字符串
        """
        data = bytes(raw_data.data())
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            return data.decode("gbk", errors="ignore")  # 忽略无法解码的字符

    def _on_ready_read(self):
        """
        进程输出就绪时调用

        Args:
            self: 当前终端实例
        """
        raw_data = self._process.readAllStandardOutput()
        if raw_data.isEmpty():
            return

        self._output_buffer += self._decode_process_data(raw_data)

        # 仅输出完整行, 不完整的尾部留在缓冲区等待后续数据
        while '\n' in self._output_buffer:
            line, self._output_buffer = self._output_buffer.split('\n', 1)
            self._append_output(line.rstrip('\r'))

        # 当进程在运行时, 立即输出缓冲区中的提示文本
        if self._process_running and self._output_buffer:
            self._append_output(self._output_buffer.rstrip('\r'))
            self._output_buffer = ""

    def _on_process_finished(self, exit_code: int):
        """
        进程结束时调用

        Args:
            self: 当前终端实例
            exit_code: 进程退出码, 0 为成功, 非 0 为失败
        """
        self._set_running(False)

        # 冲刷缓冲区中剩余的不完整输出
        if self._output_buffer:
            self._append_output(self._output_buffer.rstrip('\r\n'))
            self._output_buffer = ""

        # 主动终止的进程不再重复报告退出状态
        if self._stopping:
            self._stopping = False
            return

        if exit_code != 0:
            # 崩溃时先补中文说明, 再报退出码, 读尾巴时最后一行才是异常提示
            self._report_run_error()
            self._append_output(f"\n> 进程退出 退出码: {exit_code}\n")
        else:
            self._append_output("\n> 执行完毕\n")

    def _on_process_error(self, error):
        """
        进程发生错误时调用

        Args:
            self: 当前终端实例
            error: QProcess.Error 枚举值
        """
        self._set_running(False)
        if self._stopping:
            return  # 主动终止会触发 Crashed, 不必再提示
        self._append_output(f"\n进程错误: {error}")

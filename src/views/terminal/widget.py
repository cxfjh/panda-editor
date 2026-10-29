import os
from collections.abc import Callable
from PySide6.QtCore import QProcess
from PySide6.QtGui import QFont, QTextCharFormat
from PySide6.QtWidgets import QHBoxLayout, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget
from src.utils import theme
from src.views.terminal import styles
from src.views.terminal.commands import CommandMixin
from src.views.terminal.constants import MAX_OUTPUT_LINES
from src.views.terminal.error_hint import ErrorHintMixin
from src.views.terminal.history import HistoryMixin
from src.views.terminal.input_box import TerminalLineEdit
from src.views.terminal.runner import ProcessMixin


class TerminalWidget(CommandMixin, ProcessMixin, ErrorHintMixin, HistoryMixin, QWidget):
    """终端组件"""

    def __init__(self, parent=None):
        """
        初始化终端组件

        Args:
            self: 当前终端实例
            parent: 父窗口部件
        """
        super().__init__(parent)
        self.setObjectName("TerminalWidget")

        self._process = QProcess(self)  # 子进程管理器
        self._current_dir = os.getcwd()  # 当前工作目录
        self._command_history: list[str] = []  # 命令历史记录列表
        self._history_index: int = -1  # 当前浏览的历史记录索引
        self._process_running = False  # 是否有子进程在跑, 期间输入转发给子进程
        self._stopping = False  # 是否由停止按钮主动终止
        self._output_buffer = ""  # 未构成完整行的输出缓冲区
        self._dark_mode = True  # 当前主题, 首次按深色初始化
        self._error_report_path: str | None = None  # 正在运行的 .py 路径, 非用户代码运行为 None
        self._get_code_callback: Callable[[], str] | None = None  # 回调函数用于从编辑器获取当前代码
        self._get_file_path_callback: Callable[[], str | None] | None = None  # 回调用于取当前标签页路径

        self._setup_ui()
        self._setup_process()

    def _setup_ui(self):
        """
        初始化终端 UI 布局

        Args:
            self: 当前终端实例
        """
        c = theme.colors(True)  # 首次按深色初始化
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)  # 极窄边距
        layout.setSpacing(0)  # 无间距

        self._output = QPlainTextEdit(self)
        self._output.setReadOnly(True)  # 只读不允许用户直接编辑输出
        self._output.setFont(QFont("Cascadia Code", 10))
        self._output.setStyleSheet(styles.output_style(c))
        self._output.setUndoRedoEnabled(False)  # 禁用撤销 重做
        self._output.setMaximumBlockCount(MAX_OUTPUT_LINES)  # 限制最大行数防止内存溢出

        input_container = QWidget(self)
        input_container.setStyleSheet(styles.container_style(c))
        input_container.setFixedHeight(30)
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(4, 2, 4, 2)
        input_layout.setSpacing(4)

        self._input = TerminalLineEdit(self)
        self._input.setFont(QFont("Cascadia Code", 10))
        self._input.setStyleSheet(styles.input_style(c))
        self._input.setPlaceholderText("输入命令后按 Enter 执行...")
        self._input.returnPressed.connect(self._on_submit)

        # 停止按钮, 只在有子进程运行时可用
        self._stop_btn = QPushButton("停止", self)
        self._stop_btn.setFixedWidth(52)
        self._stop_btn.setEnabled(False)
        self._stop_btn.setStyleSheet(styles.stop_button_style(c['fg'], c['border'], c['danger_hover']))
        self._stop_btn.clicked.connect(self._stop_process)

        input_layout.addWidget(self._input, 1)
        input_layout.addWidget(self._stop_btn)
        layout.addWidget(self._output)
        layout.addWidget(input_container)

        self._append_output("> 熊猫编辑器终端")
        self._append_output("> 输入 帮助 查看可用命令\n")

    def apply_theme(self, dark_mode: bool):
        """
        应用主题样式

        Args:
            self: 当前终端实例
            dark_mode: True 为深色主题, False 为浅色主题
        """
        c = theme.colors(dark_mode)
        self._dark_mode = dark_mode  # 记录主题, 错误提示按深浅色取不同的红
        self.setStyleSheet(styles.panel_style(c))
        self._output.setStyleSheet(styles.output_style(c))
        self._input.setStyleSheet(styles.input_style(c))
        self._stop_btn.setStyleSheet(styles.stop_button_style(c['fg'], c['border'], c['danger_hover']))

    def _append_output(self, text: str):
        """
        追加输出文本

        Args:
            self: 当前终端实例
            text: 要追加的文本
        """

        # 上一行可能被标红过, 追加前先复位, 否则这一行会跟着变红
        self._output.setCurrentCharFormat(QTextCharFormat())
        self._output.appendPlainText(text)

    def append_output(self, text: str):
        """
        追加输出文本

        Args:
            self: 当前终端实例
            text: 要追加的文本
        """
        self._append_output(text)

    def set_get_code_callback(self, callback):
        """
        设置获取代码的回调函数

        Args:
            self: 当前终端实例
            callback: 回调函数, 返回当前编辑器代码
        """
        self._get_code_callback = callback

    def set_get_file_path_callback(self, callback):
        """
        设置获取当前标签页文件路径的回调函数

        Args:
            self: 当前终端实例
            callback: 回调函数, 返回当前标签页文件路径
        """
        self._get_file_path_callback = callback

    def set_working_directory(self, path: str):
        """
        设置工作目录

        Args:
            self: 当前终端实例
            path: 工作目录路径
        """
        if os.path.isdir(path):
            self._current_dir = path
            self._process.setWorkingDirectory(path)

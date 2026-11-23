import os
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from src.utils import theme
from src.utils.error_message import build_report
from src.utils.exceptions import safe_log
from src.views.terminal.constants import TAIL_LINES
from src.views.terminal.refs import TerminalRefs


class ErrorHintMixin(TerminalRefs):
    """错误说明与标红相关方法, 由终端组件混入使用"""

    def _tail_output_lines(self, count: int) -> list[str]:
        """
        取终端最后若干行输出

        Args:
            self: 当前终端实例
            count: 取多少行

        Returns:
            按显示顺序排列的行文本
        """
        document = self._output.document()
        total = document.blockCount()
        start = max(0, total - count)
        return [document.findBlockByNumber(index).text() for index in range(start, total)]

    def _report_run_error(self):
        """
        崩溃退出时在终端补充中文错误说明

        Args:
            self: 当前终端实例
        """
        py_path = self._error_report_path
        self._error_report_path = None
        if not py_path:
            return

        # 只有编辑器还停在同一份文件上时才用编辑器文本, 否则回退到磁盘上的 .cn
        source_text = None
        current_path = self._get_file_path_callback() if self._get_file_path_callback else None
        if current_path and os.path.splitext(current_path)[0] == os.path.splitext(py_path)[0]:  # type: ignore
            source_text = self._get_code_callback() if self._get_code_callback else None
        try:
            report = build_report(self._tail_output_lines(TAIL_LINES), py_path, source_text)
        except Exception as e:
            safe_log(f"生成错误报告失败: {e}")
            return  # 说明生成失败时保持终端原样, 绝不干扰正常输出
        if report is None:
            return

        # 异常类型那一段单独标红, 提示行整行标红, 其余保持终端常规颜色
        color = theme.colors(self._dark_mode)["brace_bad"]
        for index, line in enumerate(report.lines):
            self._append_output(line)
            if index == report.hint_index:
                self._mark_whole_line(color)
            elif report.mark and report.mark in line:
                self._mark_span(report.mark, color)

    def _mark_whole_line(self, color: str):
        """
        把刚追加的那一行整行改成指定字体颜色

        Args:
            self: 当前终端实例
            color: 字体颜色
        """
        cursor = QTextCursor(self._output.document().lastBlock())
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        char_format = QTextCharFormat()
        char_format.setForeground(QColor(color))
        cursor.mergeCharFormat(char_format)

    def _mark_span(self, mark: str, color: str):
        """
        给刚追加的那一行里的指定片段改字体颜色

        Args:
            self: 当前终端实例
            mark: 需要上色的片段, 必须是该行的一部分
            color: 字体颜色
        """
        block = self._output.document().lastBlock()
        start = block.text().find(mark)
        if start < 0 or not mark:
            return

        # 只改这一段文字的字符格式, 不影响后续追加的输出
        cursor = QTextCursor(block)
        cursor.setPosition(block.position() + start)
        cursor.setPosition(block.position() + start + len(mark), QTextCursor.MoveMode.KeepAnchor)
        char_format = QTextCharFormat()
        char_format.setForeground(QColor(color))
        cursor.mergeCharFormat(char_format)

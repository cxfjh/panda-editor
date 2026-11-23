from src.views.terminal.refs import TerminalRefs


class HistoryMixin(TerminalRefs):
    """命令历史相关方法, 由终端组件混入使用"""

    def get_history_prev(self) -> str | None:
        """
        获取上一条历史命令

        Args:
            self: 当前终端实例

        Returns:
            上一条命令文本, 没有更多历史时返回 None
        """
        if not self._command_history:
            return None
        if self._history_index > 0:
            self._history_index -= 1
        return self._command_history[self._history_index]

    def get_history_next(self) -> str | None:
        """
        获取下一条历史命令

        Args:
            self: 当前终端实例

        Returns:
            下一条命令文本, 已是最新位置时返回空字符串
        """
        if not self._command_history:
            return None
        if self._history_index < len(self._command_history) - 1:
            self._history_index += 1
            return self._command_history[self._history_index]
        self._history_index = len(self._command_history)
        return ""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit


class TerminalLineEdit(QLineEdit):
    """终端输入框"""

    def __init__(self, terminal):
        """
        初始化终端输入框

        Args:
            self: 当前输入框实例
            terminal: 关联的终端组件实例
        """
        super().__init__()
        self._terminal = terminal

    def keyPressEvent(self, event):
        """
        拦截键盘事件, 处理上下键浏览历史

        Args:
            self: 当前输入框实例
            event: 键盘事件对象
        """
        key = event.key()

        # 上箭头键获取上一条历史命令
        if key == Qt.Key.Key_Up:
            history = self._terminal.get_history_prev()
            if history is not None:
                self.setText(history)
            return

        # 下箭头键获取下一条历史命令
        if key == Qt.Key.Key_Down:
            history = self._terminal.get_history_next()
            if history is not None:
                self.setText(history)
            return

        super().keyPressEvent(event)

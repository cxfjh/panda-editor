from src.views.components.handlers.base import HandlerBase


class FindActions(HandlerBase):
    """查找与替换动作"""

    def on_find_replace(self):
        """
        处理查找和替换操作

        Args:
            self: 类实例自身
        """
        tab_data = self.ui.tab_manager.get_current_tab_data()
        if tab_data and tab_data.find_replace_dialog:
            tab_data.find_replace_dialog.show()
            tab_data.find_replace_dialog.raise_()
            tab_data.find_replace_dialog.activateWindow()

    def on_find_next(self):
        """
        查找下一个, 对应 F3

        Args:
            self: 类实例自身
        """
        self._repeat_find(forward=True)

    def on_find_previous(self):
        """
        查找上一个, 对应 Shift+F3

        Args:
            self: 类实例自身
        """
        self._repeat_find(forward=False)

    def _repeat_find(self, forward: bool):
        """
        复用上次的查找词继续查找

        Args:
            self: 类实例自身
            forward: True 向后查找, False 向前查找
        """
        tab_data = self.ui.tab_manager.get_current_tab_data()
        if not tab_data or not tab_data.find_replace_dialog:
            return

        dialog = tab_data.find_replace_dialog
        if not dialog.find_input.text():
            # 还没有查找词, 先打开对话框让用户输入
            self.on_find_replace()
            return

        if forward:
            dialog.find_next()
        else:
            dialog.find_previous()

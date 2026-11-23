from PySide6 import QtCore
from src.views.components.editor.refs import EditorRefs


# 中文输入法开括号对应闭括号
CN_BRACKET_MAP = { '（': '）', '【': '】', '《': '》', '“': '”', '‘': '’' }

# 英文开括号对应闭括号
OPEN_BRACKET_MAP = {
    QtCore.Qt.Key.Key_ParenLeft: ('(', ')'),
    QtCore.Qt.Key.Key_BraceLeft: ('{', '}'),
    QtCore.Qt.Key.Key_BracketLeft: ('[', ']'),
    QtCore.Qt.Key.Key_QuoteDbl: ('"', '"'),
    QtCore.Qt.Key.Key_Apostrophe: ("'", "'"),
}

# 闭括号与闭引号按键对应字符
CLOSE_KEY_MAP = {
    QtCore.Qt.Key.Key_ParenRight: ')',
    QtCore.Qt.Key.Key_BraceRight: '}',
    QtCore.Qt.Key.Key_BracketRight: ']',
    QtCore.Qt.Key.Key_QuoteDbl: '"',
    QtCore.Qt.Key.Key_Apostrophe: "'",
}


class BracketMixin(EditorRefs):
    """括号配对相关方法, 由编辑器混入使用"""

    def _pair_cn_bracket_after_commit(self, open_char: str, close_char: str):
        """
        输入法提交开括号后补插闭括号并将光标置于括号中间

        Args:
            self: 类实例自身
            open_char: 已提交的开括号字符
            close_char: 对应的闭括号字符
        """
        pos = self.currentPos()
        if pos <= 0:
            return

        # 确认光标前确实是刚提交的开括号, 且光标后不是已有的闭括号
        before = bytes(self.get_text_range(self.positionRelative(pos, -1), pos)).decode('utf-8', errors='ignore')  # type: ignore
        if before != open_char:
            return
        after = bytes(self.get_text_range(pos, self.positionRelative(pos, 1))).decode('utf-8', errors='ignore')  # type: ignore
        if after == close_char:
            return
        self.replaceSel(close_char)
        new_pos = self.positionRelative(self.currentPos(), -1)
        self.setSel(new_pos, new_pos)

    def _insert_bracket_pair(self, open_char: str, close_char: str):
        """
        插入成对括号并将光标置于括号中间

        Args:
            self: 类实例自身
            open_char: 开括号字符
            close_char: 闭括号字符
        """
        self.replaceSel(open_char + close_char)
        pos = self.positionRelative(self.currentPos(), -1)
        self.setSel(pos, pos)

    def _skip_closing_bracket(self, event) -> bool:
        """
        输入闭括号或闭引号时, 若光标后紧邻相同字符则越过该字符

        Args:
            self: 类实例自身
            event: QKeyEvent 实例

        Returns:
            已处理返回 True, 否则返回 False
        """
        char = CLOSE_KEY_MAP.get(event.key())
        if not char:
            return False
        if self.selectionEmpty() and self.charAt(self.currentPos()) == ord(char):
            pos = self.positionRelative(self.currentPos(), 1)
            self.setSel(pos, pos)
            return True
        return False

    def _handle_english_bracket_completion(self, event) -> bool:
        """
        处理英文键盘括号补全

        Args:
            self: 类实例自身
            event: QKeyEvent 实例

        Returns:
            已处理括号补全返回 True, 否则返回 False
        """
        brackets = OPEN_BRACKET_MAP.get(event.key())
        if not brackets:
            return False
        self._insert_bracket_pair(brackets[0], brackets[1])
        return True

from src.views.components.editor import constants
from src.views.components.editor.refs import EditorRefs


class EditingMixin(EditorRefs):
    """文本操作相关方法, 由编辑器混入使用"""

    def text_all(self) -> str:
        """
        获取整个文档文本

        Args:
            self: 类实例自身

        Returns:
            整个文档的文本
        """
        return bytes(self.get_text_range(0, self.textLength())).decode('utf-8')  # type: ignore

    def line_text(self, line: int) -> str:
        """
        获取指定行文本, 不含换行符

        Args:
            self: 类实例自身
            line: 行号

        Returns:
            该行文本, 不含换行符
        """
        text = bytes(self.getLine(line)).decode('utf-8', errors='replace')  # type: ignore

        # 该绑定的 getLine 会带回换行符, 统一去除
        text = text.removesuffix('\n')
        text = text.removesuffix('\r')
        return text

    def set_text(self, text: str):
        """
        设置文档文本, 统一换行符并刷新行号宽度

        Args:
            self: 类实例自身
            text: 文档文本
        """
        self.setText(text.replace('\r\n', '\n').replace('\r', '\n'))

        # 载入新内容后清空撤销栈, 否则 Ctrl+Z 会退回到上一个文件的内容
        self.emptyUndoBuffer()
        self.setSavePoint()
        self._update_line_margin_width()

    def column_of_position(self, pos: int) -> int:
        """
        将字节位置换算为所在行的字符列号

        Args:
            self: 类实例自身
            pos: 文档字节位置

        Returns:
            行内字符列号
        """
        line = self.lineFromPosition(pos)
        prefix = bytes(self.get_text_range(self.positionFromLine(line), pos))  # type: ignore
        return len(prefix.decode('utf-8', errors='ignore'))

    def fold_all(self, expand: bool):
        """
        折叠或展开全部代码

        Args:
            self: 类实例自身
            expand: True 表示展开全部, False 表示折叠全部
        """
        action = constants.SC.FoldAction.Expand if expand else constants.SC.FoldAction.Contract
        self.foldAll(action)

    def _toggle_comment(self):
        """
        切换注释或取消注释, 对应 Ctrl 加 / 快捷键

        Args:
            self: 类实例自身
        """
        if self.selectionEmpty():
            first = last = self.lineFromPosition(self.currentPos())
        else:
            first = self.lineFromPosition(self.selectionStart())
            last = self.lineFromPosition(self.selectionEnd())

            # 选区终点恰好在行首时不包含该行
            if last > first and self.selectionEnd() == self.positionFromLine(last):
                last -= 1

        lines = [self.line_text(line) for line in range(first, last + 1)]

        # 判断是否所有非空行都已注释
        all_commented = all(line.lstrip().startswith('#') for line in lines if line.strip())

        new_lines = []
        if all_commented:
            # 取消注释删除第一个 # 及其后的一个空格
            for line in lines:
                if line.lstrip().startswith('#'):
                    idx = line.index('#')
                    tail = line[idx + 1:]
                    tail = tail.removeprefix(' ')
                    new_lines.append(line[:idx] + tail)
                else:
                    new_lines.append(line)
        else:
            # 添加注释在缩进后插入 # 加一个空格
            for line in lines:
                if line.strip():
                    stripped = line.lstrip()
                    indent = len(line) - len(stripped)
                    new_lines.append(line[:indent] + '# ' + line[indent:])
                else:
                    new_lines.append(line)  # 空行保持不变

        # 批量替换文本
        self.beginUndoAction()
        for offset, (old, new) in enumerate(zip(lines, new_lines)):
            if old == new:
                continue
            line = first + offset
            start = self.positionFromLine(line)
            self.setSel(start, start + len(old.encode('utf-8')))
            self.replaceSel(new)
        self.endUndoAction()

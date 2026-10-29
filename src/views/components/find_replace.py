import re
from PySide6 import QtWidgets
from pyside6_scintilla import Scintilla
from src.utils import theme


SC = Scintilla


class FindReplaceDialog(QtWidgets.QDialog):
    """查找和替换对话框"""

    def __init__(self, editor, parent=None, dark_mode=True):
        """
        初始化查找替换对话框

        Args:
            editor: 代码编辑器实例
            parent: 父组件
            dark_mode: 是否使用深色主题
        """
        super().__init__(parent)
        self._editor = editor
        self._dark_mode = dark_mode
        self._setup_ui()

    def _setup_ui(self):
        """
        设置对话框界面

        Args:
            self: 类实例自身
        """
        self.setWindowTitle("查找和替换")
        self.setModal(False)  # 非模态对话框
        self.resize(400, 150)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(8)

        # 查找行布局
        find_layout = QtWidgets.QHBoxLayout()
        self.find_label = QtWidgets.QLabel("查找:")
        self.find_input = QtWidgets.QLineEdit()
        self.find_input.returnPressed.connect(self.find_next)  # 回车键查找下一个
        find_layout.addWidget(self.find_label)
        find_layout.addWidget(self.find_input, 1)

        self.find_prev_btn = QtWidgets.QPushButton("上一个")
        self.find_prev_btn.clicked.connect(self.find_previous)
        find_layout.addWidget(self.find_prev_btn)

        self.find_next_btn = QtWidgets.QPushButton("下一个")
        self.find_next_btn.clicked.connect(self.find_next)
        find_layout.addWidget(self.find_next_btn)

        layout.addLayout(find_layout)

        # 替换行布局
        replace_layout = QtWidgets.QHBoxLayout()
        self.replace_label = QtWidgets.QLabel("替换:")
        self.replace_input = QtWidgets.QLineEdit()
        self.replace_input.returnPressed.connect(self._replace)  # 回车键替换
        replace_layout.addWidget(self.replace_label)
        replace_layout.addWidget(self.replace_input, 1)

        self.replace_btn = QtWidgets.QPushButton("替换")
        self.replace_btn.clicked.connect(self._replace)
        replace_layout.addWidget(self.replace_btn)

        self.replace_all_btn = QtWidgets.QPushButton("全部替换")
        self.replace_all_btn.clicked.connect(self._replace_all)
        replace_layout.addWidget(self.replace_all_btn)

        layout.addLayout(replace_layout)

        # 选项行布局
        options_layout = QtWidgets.QHBoxLayout()
        self.case_sensitive = QtWidgets.QCheckBox("区分大小写")
        options_layout.addWidget(self.case_sensitive)

        self.use_regex = QtWidgets.QCheckBox("正则表达式")
        options_layout.addWidget(self.use_regex)

        options_layout.addStretch()  # 弹性空间, 将关闭按钮推到右侧

        self.close_btn = QtWidgets.QPushButton("关闭")
        self.close_btn.clicked.connect(self.close)
        options_layout.addWidget(self.close_btn)

        layout.addLayout(options_layout)

        # 状态标签, 显示查找/替换结果
        self.status_label = QtWidgets.QLabel("")
        layout.addWidget(self.status_label)

        # 设置主题样式
        self._apply_theme()

    def _apply_theme(self):
        """
        根据当前主题应用样式

        Args:
            self: 类实例自身
        """
        c = theme.colors(self._dark_mode)
        self.setStyleSheet(
            f"""
            QDialog {{ background-color: {c['bg']}; color: {c['fg']}; }}
            QLabel {{ color: {c['fg']}; }}
            QComboBox, QLineEdit {{ background-color: {c['input_bg']}; color: {c['fg']}; border: 1px solid {c['border']}; padding: 3px; }}
            QPushButton {{ background-color: #0E639C; color: white; border: none; padding: 5px 10px; }}
            QPushButton:hover {{ background-color: #1177BB; }}
            QCheckBox {{ color: {c['fg']}; }}
        """,
        )

    def update_theme(self, dark_mode: bool):
        """
        更新对话框主题

        Args:
            dark_mode: True=深色主题, False=浅色主题
        """
        self._dark_mode = dark_mode
        self._apply_theme()

    def showEvent(self, event):
        """
        对话框显示时把编辑器选中文本带入查找框

        Args:
            event: QShowEvent 实例
        """
        super().showEvent(event)
        editor = self._editor
        if not editor.selectionEmpty():
            selected = bytes(editor.get_text_range(editor.selectionStart(), editor.selectionEnd())).decode('utf-8')
            self.find_input.setText(selected)  # 使用选中文本作为查找内容
        self.find_input.selectAll()  # 全选输入框文本, 方便用户修改
        self.find_input.setFocus()

    def _search_flags(self) -> int:
        """
        根据选项组装 Scintilla 查找标志

        Returns:
            int, 查找标志位组合
        """
        flags = 0
        if self.case_sensitive.isChecked():
            flags |= SC.FindOption.MatchCase
        if self.use_regex.isChecked():
            # 旧引擎不支持 | 交替等常用写法, 统一使用 C++11 正则
            flags |= SC.FindOption.RegExp | SC.FindOption.Cxx11RegEx
        return flags

    def _search_range(self, start: int, end: int, flags: int, find_text: str) -> bool:
        """
        在指定范围内查找, 命中后选中并滚动到可视区域

        Args:
            start: 扫描起点
            end: 扫描终点, 小于起点时 Scintilla 自动反向扫描
            flags: 查找标志
            find_text: 查找文本

        Returns:
            bool, 是否命中
        """
        editor = self._editor
        length = max(1, len(find_text.encode('utf-8')))
        editor.setTargetStart(start)
        editor.setTargetEnd(end)
        editor.setSearchFlags(flags)
        found = editor.searchInTarget(length, find_text)
        if found == SC.InvalidPosition:
            return False

        # searchInTarget 会把 target 收窄成命中范围, 直接据此选中即可
        editor.setSel(found, editor.targetEnd())
        editor.scrollCaret()  # 命中项可能在视口之外, 不滚动就看不出变化
        return True

    def find_next(self):
        """
        查找下一个匹配项

        Args:
            self: 类实例自身
        """
        self._find(forward=True)

    def find_previous(self):
        """
        查找上一个匹配项

        Args:
            self: 类实例自身
        """
        self._find(forward=False)

    def _find(self, forward=True):
        """
        执行查找, 未找到时自动环绕到文档开头/结尾继续

        Args:
            forward: True=向后查找, False=向前查找
        """
        find_text = self.find_input.text()
        if not find_text:
            self.status_label.setText("请输入查找内容")
            return

        editor = self._editor
        flags = self._search_flags()
        doc_length = editor.textLength()

        # 起点取选区的边缘而不是光标, searchAnchor 会把选区折叠到起点,
        if editor.selectionEmpty():
            start = editor.currentPos()
        else:
            start = editor.selectionEnd() if forward else editor.selectionStart()

        if self._search_range(start, doc_length if forward else 0, flags, find_text):
            self.status_label.setText("已找到")
            return

        # 未找到, 环绕到另一端继续
        wrap_start = 0 if forward else doc_length
        if self._search_range(wrap_start, start, flags, find_text):
            self.status_label.setText("已找到, 从文档另一端继续")
            return

        self.status_label.setText("未找到")

    def _replace(self):
        """
        替换当前匹配项

        Args:
            self: 类实例自身
        """
        find_text = self.find_input.text()
        replace_text = self.replace_input.text()

        if not find_text:
            self.status_label.setText("请输入查找内容")
            return

        editor = self._editor
        if editor.selectionEmpty():
            self.status_label.setText("当前选中的不是查找内容，请先查找")
            return

        selected = bytes(editor.get_text_range(editor.selectionStart(), editor.selectionEnd())).decode('utf-8')

        if self.use_regex.isChecked():
            try:
                flags = 0 if self.case_sensitive.isChecked() else re.IGNORECASE
                regex = re.compile(find_text, flags)
            except re.error as e:
                self.status_label.setText(f"正则表达式错误: {e}")
                return
            if not regex.fullmatch(selected):
                self.status_label.setText("当前选中的不是查找内容，请先查找")
                return

            # 用 Python 的 re 生成替换结果, 避免与 Scintilla 正则引擎的语义差异
            new_text = regex.sub(replace_text, selected)
            editor.setTargetRange(editor.selectionStart(), editor.selectionEnd())
            editor.replaceTarget(len(new_text.encode('utf-8')), new_text)
        else:
            if self.case_sensitive.isChecked():
                matched = selected == find_text
            else:
                matched = selected.lower() == find_text.lower()
            if not matched:
                self.status_label.setText("当前选中的不是查找内容，请先查找")
                return
            editor.setTargetRange(editor.selectionStart(), editor.selectionEnd())
            editor.replaceTarget(len(replace_text.encode('utf-8')), replace_text)

        # 替换后自动跳到下一处, 状态以替换结果为准
        self.find_next()
        if self.status_label.text() == "未找到":
            self.status_label.setText("已替换, 这是最后一处")
        else:
            self.status_label.setText("已替换")

    def _replace_all(self):
        """
        全部替换

        Args:
            self: 类实例自身
        """
        find_text = self.find_input.text()
        replace_text = self.replace_input.text()

        if not find_text:
            self.status_label.setText("请输入查找内容")
            return

        editor = self._editor
        full_text = editor.text_all()

        # 执行替换
        flags = 0
        if not self.case_sensitive.isChecked():
            flags = re.IGNORECASE

        try:
            if self.use_regex.isChecked():
                # 正则模式按用户输入的正则表达式替换, 支持 \1 等反向引用
                regex = re.compile(find_text, flags)
                new_text, count = regex.subn(replace_text, full_text)
            else:
                # 普通模式转义查找文本中的正则特殊字符
                escaped_find = re.escape(find_text)
                regex = re.compile(escaped_find, flags)
                new_text, count = regex.subn(lambda m: replace_text, full_text)
        except re.error as e:
            self.status_label.setText(f"正则表达式错误: {e}")
            return

        if count == 0:
            self.status_label.setText("未找到匹配项")
            return

        # 通过目标范围整体替换, 保留撤销历史
        encoded = new_text.encode('utf-8')
        editor.targetWholeDocument()
        editor.replaceTarget(len(encoded), new_text)

        self.status_label.setText(f"已替换 {count} 处")

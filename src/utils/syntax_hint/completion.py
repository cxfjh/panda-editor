import time
from src.utils.completion_index import CompletionContext, DocumentIndex, build_index, detect_context, filter_items
from src.utils.exceptions import safe_log
from src.utils.syntax_hint import vocabulary
from src.utils.syntax_signature import dedupe
from src.utils.syntax_hint.refs import HintRefs


class CompletionMixin(HintRefs):
    """补全列表相关方法, 由提示管理器混入使用"""

    def _should_complete(self) -> bool:
        """
        检查是否应该启用补全

        Args:
            self: 当前管理器实例

        Returns:
            True 表示启用补全 False 表示禁用
        """
        if not self._current_file:
            return True  # 无文件路径时默认启用
        return self._current_file.endswith('.cn')  # 仅 .cn 文件启用

    def _mark_index_dirty(self):
        """
        文档发生变化, 索引需要重建

        Args:
            self: 当前管理器实例
        """
        self._index_dirty = True

    def _document_index(self) -> DocumentIndex:
        """
        获取文档符号索引, 文档变动后按需重建, 并限制重建频率

        Args:
            self: 当前管理器实例

        Returns:
            DocumentIndex 实例
        """
        if not self._index_dirty:
            return self._index

        # 连续输入时沿用稍旧的索引, 避免每次按键都全量扫描文档
        if self._index.symbols and time.monotonic() - self._index_built_at < vocabulary.INDEX_MIN_INTERVAL:
            return self._index
        try:
            text = self._editor.text_all()
        except UnicodeDecodeError as e:
            safe_log(f"读取编辑器文本失败: {e}", "debug")
            return self._index
        self._index = build_index(text)
        self._index_dirty = False
        self._index_built_at = time.monotonic()
        return self._index

    def _build_candidates(self, context: CompletionContext, pos: int) -> tuple[list[str], int, str]:
        """
        根据上下文构建候选词, 待替换前缀长度与已输入前缀

        Args:
            self: 当前管理器实例
            context: 补全上下文
            pos: 光标字节位置

        Returns:
            候选词列表, 待替换前缀字节长度, 已输入前缀文本
        """
        editor = self._editor
        typed = context.prefix
        entered = len(typed.encode('utf-8'))

        if context.kind == 'library':
            ops = self._lib_ops.get(context.lib_name or '', { })
            return dedupe(list(ops.keys())), entered, typed

        if context.kind == 'import':
            return vocabulary.IMPORT_ITEMS, entered, typed

        index = self._document_index()

        if context.kind == 'member':
            line = editor.lineFromPosition(pos)
            return vocabulary.member_items(context.receiver, line, index), entered, typed

        # 全局补全, 以 Scintilla 的词首位置为准, 并向前吞并 @ 前缀, 如 @库 / @界面库
        start = editor.wordStartPosition(pos, True)
        if start > 0:
            prev = bytes(editor.get_text_range(start - 1, start))  # type: ignore
            if prev == b'@':
                start -= 1
        typed = bytes(editor.get_text_range(start, pos)).decode('utf-8', errors='ignore')  # type: ignore
        entered = pos - start
        core = typed.lstrip('@')
        if not typed:
            return [], 0, ''
        if core[:1].isdigit():
            return [], 0, ''  # 数字字面量不弹补全

        # 中文 1 字即可触发, ASCII 需 2 字符以减少噪音, 单独的 @ 除外
        if core.isascii() and 0 < len(core) < 2:
            return [], 0, ''
        return vocabulary.global_items(index), entered, typed

    def _request_completion(self):
        """
        按当前上下文弹出补全列表, 候选由本模块自行按前缀筛选

        Args:
            self: 当前管理器实例
        """
        editor = self._editor
        if self._ime_composing or not self._should_complete():
            return

        pos = editor.currentPos()
        line = editor.lineFromPosition(pos)
        prefix = editor.line_text(line)[:editor.column_of_position(pos)]

        context = detect_context(prefix, tuple(self._lib_ops))
        if context.kind == 'none':
            editor.autoCCancel()
            return

        items, entered, typed = self._build_candidates(context, pos)

        # 不依赖 Scintilla 的过滤, 它按"词"比较, @ 等前缀与中文输入法提交都会失效
        filtered = filter_items(items, typed)[:vocabulary.MAX_CANDIDATES]
        if not filtered:
            editor.autoCCancel()
            return

        # 同样的候选重复触发时不重建列表, 避免打断用户的方向键选择
        signature = (entered, tuple(filtered))
        if editor.autoCActive() and signature == self._last_shown:
            return
        self._last_shown = signature

        editor.autoCShow(entered, ' '.join(filtered))

        # 列表没弹出来时不能再选, 否则 Scintilla 会访问空列表导致崩溃
        if editor.autoCActive():
            # 让首个候选处于选中态, 回车可直接采纳, Scintilla 自身的匹配可能选不中
            editor.autoCSelect(filtered[0])

    def _on_char_added(self, ch: int):
        """
        字符插入信号, 点号立即成员补全, 括号与逗号参数提示

        Args:
            self: 当前管理器实例
            ch: 插入字符的码点
        """
        if not self._should_complete():
            return
        char = chr(ch)
        editor = self._editor

        if char in '（(':
            self._show_call_tip()
            return
        if char in '，,':
            if editor.callTipActive():
                self._show_call_tip()
            self._debounce_timer.start()
            return
        if char in '）)':
            if editor.callTipActive():
                editor.callTipCancel()
            if editor.autoCActive():
                editor.autoCCancel()
            return
        if char in '.。':
            self._request_completion()
            return

        # 词字符与 @ 才触发补全, 中文属于词字符, 其余符号直接关闭列表
        if char == '@' or char == '_' or char.isalnum():
            self._debounce_timer.start()
            return
        if editor.autoCActive():
            editor.autoCCancel()

from typing import List, Optional, Set, cast
from PySide6.QtCore import QEvent, QObject, QStringListModel, QThread, QTimer, Qt, Signal
from PySide6.QtGui import QInputMethodEvent, QKeyEvent, QTextCursor
from PySide6.QtWidgets import QCompleter, QPlainTextEdit
import src.module.builtin_funcs as BuiltinLibraryMethods
import src.module.builtins as BuiltinLibraries
import src.module.keywords as KeyWords
import src.module.punctuations as PunctuationMark


class FilterWorker(QObject):
    """后台过滤线程"""
    resultReady = Signal(list, str)  # 匹配结果列表, 当前前缀

    def __init__(self, all_items: List[str]):
        super().__init__()
        self.all_items = all_items  # 全部候选项
        self._last_prefix = ""  # 上一次处理的前缀（避免重复）

    def filter_items(self, prefix: str):
        """执行过滤逻辑"""
        if not prefix:
            self.resultReady.emit([], prefix)
            return

        # 前缀没变 → 不需要重复过滤
        if prefix == self._last_prefix: return
        self._last_prefix = prefix

        # 简单的包含匹配
        prefix_lower = prefix.lower()
        matched = [item for item in self.all_items if prefix_lower in item.lower()]

        # 把结果通过信号发回主线程
        self.resultReady.emit(matched, prefix)


class SyntaxCompleter(QCompleter):
    """自定义补全器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)  # 弹出列表模式
        self.setFilterMode(Qt.MatchFlag.MatchContains)  # 支持包含匹配
        self.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)  # 忽略大小写

        # 样式美化
        self.popup().setStyleSheet(
            """
            QListView {
                background-color: #1e1e1e;
                color: #dcdcdc;
                border: 1px solid #3c3c3c;
                border-radius: 8px;
                padding: 4px;
                min-width: 150px;
                max-height: 420px;
                font-size: 16px;
                outline: 0;
            }
            QListView::item { padding: 6px 12px; border-radius: 4px; margin: 1px 0; }
            QListView::item:selected { background-color: #0078d7; color: #ffffff; }
            QListView::item:hover:not(:selected) { background-color: RGBA(255, 255, 255, 0.08); }
            QScrollBar:vertical { background: transparent; width: 8px; margin: 2px; }
            QScrollBar::handle:vertical { background: #555; border-radius: 4px; min-height: 20px; }
            QScrollBar::handle:vertical:hover { background: #777; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            """,
        )


class SyntaxHintManager(QObject):
    """语法提示管理器"""

    def __init__(self, text_edit: QPlainTextEdit):
        super().__init__(parent=text_edit)
        self.text_edit = text_edit
        if not self.text_edit: return

        # 创建自定义补全器
        self.completer = SyntaxCompleter(text_edit)
        self.completer.setWidget(text_edit)
        self.completer.activated.connect(self.insert_completion)
        self.completer.popup().installEventFilter(self)

        # 防抖计时器
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(120)  # 停顿 120ms 后触发
        self._debounce_timer.timeout.connect(self._do_request_completion)

        # 监听输入事件
        self.text_edit.installEventFilter(self)

        # 定义触发字符集
        self.base_trigger: Set[str] = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789")
        self.chinese_punctuation: Set[str] = set('，。、；：？！"\'‘’"（）【】《》@*')

        # 缓存
        self._last_prefix = ""  # 上一次前缀
        self._popup_min_width: Optional[int] = None  # 补全框最小宽度

        # 初始化候选数据
        self._init_completion_data()

    def _init_completion_data(self):
        """一次性加载补全数据，并开启后台线程"""
        items = set()
        items.update(KeyWords.key_words.keys())
        items.update(BuiltinLibraries.builtins.keys())
        items.update(BuiltinLibraryMethods.builtin_funcs.keys())
        items.update(PunctuationMark.punctuations.keys())

        # 排序并去重
        all_items = sorted(items, key=lambda x: (-len(x), x))
        self.all_items = all_items

        # 启动后台线程
        self._thread = QThread()
        self.worker = FilterWorker(all_items)
        self.worker.moveToThread(self._thread)
        self.worker.resultReady.connect(self._update_completion)  # 绑定结果回调
        self._thread.start()

    def cleanup(self):
        """清理资源"""
        if hasattr(self, '_thread') and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait()

    def _get_current_word(self) -> str:
        """获取光标前的当前单词"""
        cursor = self.text_edit.textCursor()
        block_text = cursor.block().text()[:cursor.positionInBlock()]
        chars = []
        for char in reversed(block_text):
            if char in self.base_trigger or '\u4e00' <= char <= '\u9fff' or char in self.chinese_punctuation: chars.append(char)
            else: break
        return "".join(reversed(chars))

    def insert_completion(self, completion: str):
        """插入补全内容"""
        if not completion: return
        cursor = self.text_edit.textCursor()
        word = self._get_current_word()
        if word == completion: return
        cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor, len(word))
        cursor.insertText(completion)
        self.text_edit.setTextCursor(cursor)

    def show_completion(self):
        """触发防抖计时器（延迟请求后台过滤）"""
        self._debounce_timer.start(120)

    def _do_request_completion(self):
        """请求后台线程过滤数据"""
        prefix = self._get_current_word()
        self.worker.filter_items(prefix)  # 发给后台 worker 处理

    def _update_completion(self, matched: List[str], prefix: str):
        """主线程更新 UI 显示补全结果"""
        if not prefix:
            self.completer.popup().hide()
            self._last_prefix = ""
            return
        if prefix != self._get_current_word(): return  # 光标变化 → 丢弃旧结果

        # 更新模型
        model = QStringListModel(matched, self.completer)
        self.completer.setModel(model)
        self.completer.setCompletionPrefix(prefix)

        # 定位补全框
        rect = self.text_edit.cursorRect()
        rect.translate(0, self.text_edit.fontMetrics().height() * 2)

        # 只计算一次补全框宽度，避免重复消耗
        if self._popup_min_width is None:
            popup = self.completer.popup()
            self._popup_min_width = max(200, popup.sizeHintForColumn(0) + popup.verticalScrollBar().sizeHint().width())

        rect.setWidth(self._popup_min_width or rect.width())
        self.completer.complete(rect)

    def eventFilter(self, obj, event):
        # 回车选中补全
        if obj == self.completer.popup() and event.type() == QEvent.Type.KeyPress:
            key_event = cast(QKeyEvent, event)
            if key_event.key() == Qt.Key.Key_Return or key_event.key() == Qt.Key.Key_Enter:
                # 使用popup的currentIndex来获取当前选中的项目
                popup = self.completer.popup()
                current_row = popup.currentIndex().row()
                if current_row >= 0:
                    # 从模型中获取指定行的数据
                    model = self.completer.model()
                    index = model.index(current_row, 0)
                    if index.isValid():
                        current_completion = model.data(index)
                        if current_completion:
                            self.insert_completion(current_completion)
                            self.completer.popup().hide()
                else:
                    current_completion = self.completer.currentCompletion()
                    if current_completion:
                        self.insert_completion(current_completion)
                        self.completer.popup().hide()
                return True

        """事件过滤器，拦截键盘/输入事件触发补全"""
        if obj is not self.text_edit: return super().eventFilter(obj, event)
        et = event.type()

        # 中文输入法事件
        if et == QEvent.Type.InputMethod and isinstance(event, QInputMethodEvent):
            if event.preeditString() or event.commitString(): self.show_completion()
            return False

        # 按键释放事件
        if et == QEvent.Type.KeyRelease and isinstance(event, QKeyEvent):
            key = event.key()
            # 过滤掉无关按键
            if key in (
                    Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Tab,
                    Qt.Key.Key_Backspace, Qt.Key.Key_Delete,
                    Qt.Key.Key_Left, Qt.Key.Key_Right,
                    Qt.Key.Key_Up, Qt.Key.Key_Down,
                    Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt,
            ):
                return False
            self.show_completion()
            return False

        # 输入法查询事件
        if et == QEvent.Type.InputMethodQuery:
            self.show_completion()
            return False

        return super().eventFilter(obj, event)

    def __del__(self):
        """析构函数，确保资源被正确释放"""
        self.cleanup()

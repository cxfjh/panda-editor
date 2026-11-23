from PySide6.QtCore import QEvent, QObject, Qt, QTimer
from PySide6.QtGui import QInputMethodEvent, QKeyEvent
from pyside6_scintilla import Scintilla
from src.utils import theme
from src.utils.completion_index import DocumentIndex
from src.utils.library_docs import get_library_ops
from src.utils.syntax_hint.completion import CompletionMixin
from src.utils.syntax_hint.tip import TipMixin


class SyntaxHintManager(CompletionMixin, TipMixin, QObject):
    """语法提示管理器, 补全列表与参数提示"""

    def __init__(self, editor, dark_mode=True):
        """
        初始化语法提示管理器

        Args:
            self: 当前管理器实例
            editor: CodeEditor 实例 需要补全功能的编辑器
            dark_mode: 是否使用深色模式
        """
        super().__init__(parent=editor)
        self._editor = editor
        self._dark_mode = dark_mode
        self._current_file: str | None = None  # 当前文件路径
        self._lib_ops = get_library_ops()  # type: ignore   扩展库操作表, 进程内缓存

        self._index = DocumentIndex()  # 文档符号索引
        self._index_dirty = True
        self._index_built_at = 0.0  # 上次索引重建时间, time.monotonic
        self._ime_composing = False  # 输入法预编辑中
        self._last_shown: tuple[int, tuple[str, ...]] = (0, ())  # 上次弹出的列表签名

        # 补全列表行为配置
        editor.autoCSetIgnoreCase(True)  # 不区分大小写
        editor.autoCSetCancelAtStart(True)  # 退格回到词首时关闭列表
        editor.autoCSetChooseSingle(False)  # 单个候选也显示列表
        editor.autoCSetMaxHeight(12)  # 列表最多显示 12 行

        # 关闭自动隐藏, Scintilla 按词判断匹配, @ 前缀与中文会误判成不匹配
        editor.autoCSetAutoHide(False)
        editor.autoCSetDropRestOfWord(False)  # 保留光标后已有的词尾
        editor.autoCSetSeparator(32)  # 候选用空格分隔

        # 词库未排序, 使用自定义顺序, 文档标识符在前, 由我们自行排好
        editor.autoCSetOrder(2)  # SC_ORDER_CUSTOM
        self._apply_theme(editor)

        # 防抖计时器
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)  # 单次触发
        self._debounce_timer.setInterval(120)  # 120ms 延迟
        self._debounce_timer.timeout.connect(self._request_completion)  # 超时后请求补全

        # 点号立即成员补全 / 括号参数提示
        editor.charAdded.connect(self._on_char_added)

        # 文本变化时标记索引失效
        editor.notifyChange.connect(self._mark_index_dirty)

        # 监听编辑器输入事件, 输入法提交, 英文括号按键
        editor.installEventFilter(self)

    @staticmethod
    def _apply_theme(editor):
        """
        应用参数提示配色, 补全列表跟随编辑器默认样式

        Args:
            editor: CodeEditor 实例
        """
        message = Scintilla.Message
        c = theme.colors(editor.dark_mode)
        pairs = [
            (message.CallTipSetBack, theme.bgr_int(c['menu_bg'])),
            (message.CallTipSetFore, theme.bgr_int(c['fg'])),
            (message.CallTipSetForeHlt, theme.bgr_int(c['accent'])),
        ]
        for msg, colour in pairs:
            editor.send(int(msg), colour)

    def update_theme(self, dark_mode: bool):
        """
        更新补全列表主题

        Args:
            self: 当前管理器实例
            dark_mode: True 为深色主题 False 为浅色主题
        """
        if self._dark_mode == dark_mode:
            return
        self._dark_mode = dark_mode
        self._apply_theme(self._editor)

    def set_current_file(self, file_path: str | None) -> None:
        """
        设置当前文件路径用于判断是否为 .cn 文件

        Args:
            self: 当前管理器实例
            file_path: 当前文件路径
        """
        self._current_file = file_path
        self._index_dirty = True
        self._index_built_at = 0.0  # 换文件后立即重建索引

    def eventFilter(self, obj, event):
        """
        事件过滤器, 输入法状态跟踪, 英文括号参数提示, 按键防抖补全

        Args:
            self: 当前管理器实例
            obj: QObject 实例 事件目标对象
            event: QEvent 实例 包含事件类型和详细信息

        Returns:
            True 表示事件已处理 False 表示继续传递
        """
        if obj is not self._editor:
            return super().eventFilter(obj, event)
        et = event.type()

        # 中文输入法事件
        if et == QEvent.Type.InputMethod and isinstance(event, QInputMethodEvent):
            preedit = event.preeditString()
            self._ime_composing = bool(preedit)

            # 预编辑期间 Scintilla 会将候选字以 tentative 字节插入文档
            if preedit:
                if self._editor.autoCActive():
                    self._editor.autoCCancel()
                return False
            if event.commitString() and self._should_complete():  # 提交后才触发防抖补全
                self._debounce_timer.start()
            return False  # 不拦截继续传递

        # 英文括号, 编辑器会自行插入成对括号, 不产生 charAdded, 这里补上参数提示
        if et == QEvent.Type.KeyPress and isinstance(event, QKeyEvent):
            if event.modifiers() in (Qt.KeyboardModifier.NoModifier, Qt.KeyboardModifier.ShiftModifier):
                if event.key() == Qt.Key.Key_ParenLeft:
                    QTimer.singleShot(0, self._show_call_tip)
                elif event.key() == Qt.Key.Key_ParenRight and self._editor.callTipActive():
                    self._editor.callTipCancel()
            return False

        # 按键释放事件
        if et == QEvent.Type.KeyRelease and isinstance(event, QKeyEvent):
            key = event.key()

            # 排除特殊键
            if key in (
                    Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Tab,
                    Qt.Key.Key_Backspace, Qt.Key.Key_Delete,
                    Qt.Key.Key_Left, Qt.Key.Key_Right,
                    Qt.Key.Key_Up, Qt.Key.Key_Down,
                    Qt.Key.Key_Escape,
                    Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt,
            ):
                return False  # 特殊键不触发补全
            if self._should_complete() and not self._ime_composing:
                self._debounce_timer.start()
            return False  # 不拦截继续传递

        return super().eventFilter(obj, event)

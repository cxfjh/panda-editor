from PySide6 import QtCore
from PySide6.QtCore import QEvent
from PySide6.QtGui import QInputMethodEvent
from src.views.components.editor import constants
from src.views.components.editor.brackets import CN_BRACKET_MAP, BracketMixin
from src.views.components.editor.editing import EditingMixin
from src.views.components.editor.theme_style import ThemeMixin


class CodeEditor(BracketMixin, EditingMixin, ThemeMixin):
    """基于 Scintilla 的代码编辑器"""

    # 语法高亮等依赖自定义样式的模块需要据此重新应用配色
    fontChanged = QtCore.Signal()

    def __init__(self, parent=None, dark_mode=True):
        """
        初始化代码编辑器

        Args:
            self: 类实例自身
            parent: 父窗口部件
            dark_mode: 是否使用深色模式
        """
        super().__init__(parent)
        self._dark_mode = dark_mode
        self._show_line_numbers = True

        # UTF-8 编码与统一换行符
        self.setCodePage(constants.SC.CpUtf8)
        self.setEOLMode(constants.SC.EndOfLine.Lf)
        self.setPasteConvertEndings(True)

        # 缩进行为, Tab 插入 4 个空格
        self.setUseTabs(False)
        self.setTabWidth(4)
        self.setIndent(4)
        self.setTabIndents(True)
        self.setBackSpaceUnIndents(True)

        # 缩进参考线在浅色模式下很显眼, 整体关闭
        self.setIndentationGuides(constants.SC.IndentView.None_)

        # 多光标与列块编辑
        self.setMultipleSelection(True)
        self.setAdditionalSelectionTyping(True)
        self.setScrollWidthTracking(True)

        # 行号边栏
        self.setMarginTypeN(0, constants.SC.MarginType.Number)
        self.linesAdded.connect(self._update_line_margin_width)

        self._setup_fold_margin()

        # 当前行高亮
        self.setCaretLineVisible(True)

        # 括号配对高亮
        self.updateUi.connect(self._on_update_ui)

        self._apply_theme()

        # 中文输入法括号补全 + Ctrl+/ 注释切换
        self.installEventFilter(self)

    def _setup_fold_margin(self):
        """
        配置代码折叠边栏与折叠标记

        Args:
            self: 类实例自身
        """
        self.setMarginTypeN(1, constants.SC.MarginType.Symbol)
        self.setMarginMaskN(1, constants.SC.MaskFolders)
        self.setMarginSensitiveN(1, True)
        self.setMarginWidthN(1, 18)

        # 折叠的展开 收起 点击全部交给 Scintilla 自动处理
        self.setAutomaticFold(constants.SC.AutomaticFold.Show | constants.SC.AutomaticFold.Click | constants.SC.AutomaticFold.Change)

        # 定义折叠标记, 25-31 为 Scintilla 约定的折叠标记位
        fold_markers = {
            25: constants.SC.MarkerSymbol.BoxMinus,
            26: constants.SC.MarkerSymbol.BoxMinusConnected,
            27: constants.SC.MarkerSymbol.BoxPlus,
            28: constants.SC.MarkerSymbol.BoxPlusConnected,
            29: constants.SC.MarkerSymbol.VLine,
            30: constants.SC.MarkerSymbol.LCorner,
            31: constants.SC.MarkerSymbol.TCorner,
        }

        for number, symbol in fold_markers.items():
            self.markerDefine(number, symbol)

    def _on_update_ui(self, updated):
        """
        光标或选区变化时更新括号配对高亮

        Args:
            self: 类实例自身
            updated: Scintilla 更新标志位
        """
        if not (updated & constants.SC.Update.Selection):
            return

        pos = self.currentPos()
        brace_pos = -1

        # 优先检查光标前的字符, 再检查光标后的字符
        for p in (pos - 1, pos):
            if p < 0:
                continue
            if self.charAt(p) in constants.BRACE_CODES:
                brace_pos = p
                break

        if brace_pos == -1:
            self.braceHighlight(constants.SC.InvalidPosition, constants.SC.InvalidPosition)
            self.braceBadLight(constants.SC.InvalidPosition)
            return

        match_pos = self.braceMatch(brace_pos, 0)
        if match_pos != constants.SC.InvalidPosition:
            self.braceHighlight(brace_pos, match_pos)
            self.braceBadLight(constants.SC.InvalidPosition)
        else:
            # 找不到配对时标红, 提示括号不匹配
            self.braceHighlight(constants.SC.InvalidPosition, constants.SC.InvalidPosition)
            self.braceBadLight(brace_pos)

    def eventFilter(self, obj, event):
        """
        事件过滤器, 中文输入法括号补全, 括号配对输入, Ctrl 加 / 注释切换

        Args:
            self: 类实例自身
            obj: 事件目标对象
            event: QEvent 实例

        Returns:
            事件已被处理返回 True, 否则返回 False
        """
        if obj is self:
            # 中文输入法提交的开括号, 不拦截事件本体, 因为 Scintilla 的输入法预编辑字节
            if event.type() == QEvent.Type.InputMethod and isinstance(event, QInputMethodEvent):
                commit = event.commitString()
                if commit and commit in CN_BRACKET_MAP:
                    close_char = CN_BRACKET_MAP[commit]
                    QtCore.QTimer.singleShot(0, lambda ch=commit, cl=close_char: self._pair_cn_bracket_after_commit(ch, cl))
                return False

            if event.type() == QEvent.Type.KeyPress:
                # Ctrl+/ 切换注释
                if event.key() == QtCore.Qt.Key.Key_Slash and event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier:
                    self._toggle_comment()
                    return True

                # 避免拦截 Ctrl+/ 等组合键
                if event.modifiers() in (QtCore.Qt.KeyboardModifier.NoModifier, QtCore.Qt.KeyboardModifier.ShiftModifier):
                    # 闭括号或闭引号 若光标后已是相同字符则直接越过不再插入
                    if self._skip_closing_bracket(event):
                        return True

                    # 开括号或开引号自动补全
                    if self._handle_english_bracket_completion(event):
                        return True

        return super().eventFilter(obj, event)

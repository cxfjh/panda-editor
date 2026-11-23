from PySide6.QtGui import QFont
from src.utils import theme
from src.views.components.editor import constants
from src.views.components.editor.refs import EditorRefs


class ThemeMixin(EditorRefs):
    """配色与字体相关方法, 由编辑器混入使用"""

    def _apply_theme(self):
        """
        根据当前模式应用编辑器配色

        Args:
            self: 类实例自身
        """
        common = constants.COMMON
        c = theme.colors(self._dark_mode)
        bg_int, fg_int = theme.bgr_int(c['bg']), theme.bgr_int(c['fg'])

        # 基础样式, 先设置默认样式再复制到全部样式
        self.styleSetFore(common.Default, fg_int)
        self.styleSetBack(common.Default, bg_int)
        self.styleClearAll()

        # 选区颜色
        self.setSelBack(True, theme.bgr_int(c['selected']))
        self.setSelFore(False, 0)

        # 光标与当前行
        self.setCaretFore(fg_int)
        self.setCaretLineBack(theme.bgr_int(c['caret_line']))

        # 行号边栏颜色
        self.styleSetFore(common.LineNumber, theme.bgr_int(c['margin_fg']))
        self.styleSetBack(common.LineNumber, theme.bgr_int(c['margin_bg']))

        # 括号配对高亮颜色
        self.styleSetFore(common.BraceLight, theme.bgr_int(c['accent']))
        self.styleSetBold(common.BraceLight, True)
        self.styleSetFore(common.BraceBad, theme.bgr_int(c['brace_bad']))

        # 折叠边栏与折叠标记颜色
        self.setFoldMarginColour(True, bg_int)
        self.setFoldMarginHiColour(True, bg_int)
        for number in range(25, 32):
            self.markerSetBack(number, theme.bgr_int(c['fold']))
            self.markerSetFore(number, bg_int)

        self._update_line_margin_width()

    def set_dark_mode(self, dark_mode: bool):
        """
        设置深色模式

        Args:
            self: 类实例自身
            dark_mode: True 为深色模式, False 为浅色模式
        """
        if self._dark_mode == dark_mode:
            return
        self._dark_mode = dark_mode
        self._apply_theme()

    @property
    def dark_mode(self) -> bool:
        """
        获取当前是否为深色模式

        Returns:
            当前为深色模式返回 True, 否则返回 False
        """
        return self._dark_mode

    def set_editor_font(self, font: QFont):
        """
        设置编辑器文本字体, 同步应用到全部样式

        Args:
            self: 类实例自身
            font: QFont 实例
        """
        self.setFont(font)  # 部件级字体, 事件过滤器读取用
        self.styleSetFont(constants.COMMON.Default, font.family())
        self.styleSetSize(constants.COMMON.Default, max(1, font.pointSize()))

        # 将默认字体复制到全部样式后重新应用配色
        self.styleClearAll()
        self._apply_theme()
        self._update_line_margin_width()
        self.fontChanged.emit()  # 通知语法高亮等重新上色

    def _update_line_margin_width(self, *_):
        """
        根据总行数更新行号边栏宽度

        Args:
            self: 类实例自身
            _: 未使用的位置参数, 仅用于接收信号附带的参数
        """
        if not self._show_line_numbers:
            self.setMarginWidthN(0, 0)
            return
        digits = max(3, len(str(self.lineCount())))
        width = self.textWidth(constants.COMMON.LineNumber, '9' * digits) + 10
        self.setMarginWidthN(0, width)

    def set_show_line_numbers(self, show: bool):
        """
        设置是否显示行号

        Args:
            self: 类实例自身
            show: True 表示显示行号, False 表示隐藏
        """
        self._show_line_numbers = show
        self._update_line_margin_width()

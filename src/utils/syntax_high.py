import re
from PySide6.QtCore import QObject
from PySide6.QtGui import QColor
from pyside6_scintilla import Scintilla
import src.module.builtin_map as BuiltinMap
import src.module.keyword_map as KeyWordMap
import src.module.lib_map as LibMap
import src.module.method_map as MethodMap
import src.module.punctuation_map as PunctuationMap
import src.module.stdlib_map as stdlib
from src.utils.cn_tokens import TOKEN_CODE, TOKEN_COMMENT, TOKEN_STRING, tokenize_line
from src.utils.theme import color_int


SC = Scintilla
_COMMON = SC.StylesCommon

# 自定义样式编号, 0-31 可供业务使用
STYLE_TEXT = 0  # 普通文本
STYLE_KEYWORD = 1  # 关键字, 如果, 否则, 遍历...
STYLE_BUILTIN = 2  # 内置函数, 输出, 输入, 长度...
STYLE_LIB = 3  # 库/模块名, 数学库, 系统库...
STYLE_STDLIB = 4  # 标准库函数, 平方根, 随机整数...
STYLE_PUNCTUATION = 5  # 标点符号, 如逗号 句号 顿号 分号 冒号
STYLE_METHOD = 6  # 对象方法, 追加, 删除, 查找...
STYLE_COMMENT = 7  # 注释
STYLE_STRING = 8  # 字符串字面量, 含引号本身

# 深色语法高亮颜色
DARcula_COLORS = {
    'keyword': [86, 156, 214],  # #569CDE - 亮蓝色 - 关键字, 如果, 否则, 遍历, 定义, 返回
    'builtin': [220, 220, 170],  # #DCDC87 - 淡黄色 - 内置函数, 输出, 输入, 长度, 转整数
    'lib': [210, 160, 210],  # #D2A0D2 - 淡紫色 - 库/模块名, 数学库, 系统库
    'stdlib': [130, 200, 170],  # #82C8AA - 薄荷绿 - 标准库函数, 平方根, 随机整数
    'punctuation': [180, 140, 140],  # #B48C8C - 淡红棕色 - 标点符号, 如逗号 句号 顿号 分号 冒号
    'method': [230, 160, 120],  # #E6A078 - 珊瑚橙 - 对象方法, 追加, 删除, 查找
    'comment': [106, 153, 85],  # #6A9955 - 浅绿色 - 注释行
    'string': [206, 145, 120],  # #CE9178 - 砖橙色 - 字符串字面量
}

# 浅色语法高亮颜色
LIGHT_COLORS = {
    'keyword': [30, 80, 180],  # #1E50B4 - 宝蓝色 - 关键字, 如果, 否则, 遍历, 定义, 返回
    'builtin': [160, 120, 20],  # #A07814 - 琥珀色 - 内置函数, 输出, 输入, 长度, 转整数
    'lib': [140, 80, 160],  # #8C50A0 - 深紫色 - 库/模块名, 数学库, 系统库
    'stdlib': [40, 140, 100],  # #288C64 - 翠绿色 - 标准库函数, 平方根, 随机整数
    'punctuation': [180, 100, 100],  # #B46464 - 红棕色 - 标点符号, 如逗号 句号 顿号 分号 冒号
    'method': [200, 100, 40],  # #C86428 - 橙红色 - 对象方法, 追加, 删除, 查找
    'comment': [0, 128, 0],  # #008000 - 绿色 - 注释行
    'string': [163, 21, 21],  # #A31515 - 深红色 - 字符串字面量
}

# 词表模块与样式编号的对应关系, 按优先级排序
_CATEGORY_STYLES: list[tuple[str, int]] = [
    ('keyword', STYLE_KEYWORD),
    ('builtin', STYLE_BUILTIN),
    ('lib', STYLE_LIB),
    ('stdlib', STYLE_STDLIB),
    ('method', STYLE_METHOD),
    ('punctuation', STYLE_PUNCTUATION),
]

# 自定义样式编号与配色键的对应关系
_STYLE_KEYS: dict[int, str] = {
    STYLE_KEYWORD: 'keyword',
    STYLE_BUILTIN: 'builtin',
    STYLE_LIB: 'lib',
    STYLE_STDLIB: 'stdlib',
    STYLE_PUNCTUATION: 'punctuation',
    STYLE_METHOD: 'method',
    STYLE_COMMENT: 'comment',
    STYLE_STRING: 'string',
}

# 折叠级别缩进深度查找上限
_FOLD_LOOKAHEAD = 100


def _extract_keys(module_name: str) -> tuple[str, ...]:
    """
    从映射字典中提取键

    Args:
        module_name: 模块名称

    Returns:
        词法单元元组
    """
    module_map = {
        'keyword': KeyWordMap.keyword,  # 关键字, 如果, 否则, 遍历...
        'builtin': BuiltinMap.builtin,  # 内置函数, 输出, 输入, 长度...
        'lib': LibMap.lib,  # 库/模块名, 数学库, 系统库...
        'stdlib': stdlib.stdlib,  # 标准库函数, 平方根, 随机整数...
        'punctuation': PunctuationMap.punctuation,  # 标点符号, 如逗号 句号 顿号 分号 冒号
        'method': MethodMap.method,  # 对象方法, 追加, 删除, 查找...
    }
    mapping_dict = module_map.get(module_name, { })
    return tuple(str(k) for k in mapping_dict.keys())


def _build_pattern(items: list[str], is_punctuation: bool = False) -> str | None:
    """
    构建正则模式字符串

    Args:
        items: 词法单元列表
        is_punctuation: 是否为标点符号

    Returns:
        正则模式字符串, 若 items 为空则返回 None
    """
    if not items:
        return None

    # 标点符号使用字符类匹配
    if is_punctuation:
        escaped = "".join(re.escape(str(ch)) for ch in items)
        return f"[{escaped}]"

    # @ 开头的词
    if all(str(item).startswith("@") for item in items):
        escaped_items = [re.escape(str(w)) for w in items]

        # 负向前瞻断言确保后面不跟词字符, 含中文
        return "(?:" + "|".join(escaped_items) + r")(?!\w)"

    # 普通词法单元使用前后词边界断言, Python 的 \w 含中文
    escaped_items = [re.escape(str(w)) for w in items]
    return r"(?<!\w)(?:" + "|".join(escaped_items) + r")(?!\w)"


class CnHighlighter(QObject):
    """CnLang 语法高亮器, 容器词法模式, 由 Scintilla 的 styleNeeded 信号驱动"""

    def __init__(self, editor, dark_mode=True):
        """
        初始化语法高亮器

        Args:
            editor: CodeEditor 实例
            dark_mode: 是否使用深色主题
        """
        super().__init__(editor)
        self._editor = editor
        self._dark_mode = dark_mode
        self._rules: list[tuple[re.Pattern, int]] = []
        self._styling = False  # 正在着色, 用于拦截 setFoldLevel 引发的重入
        self._compile_rules()
        editor.styleNeeded.connect(self._on_style_needed)

        # 字号变化后 styleClearAll 会清掉自定义样式颜色, 只需把配色写回, 无需重新着色
        editor.fontChanged.connect(self.refresh_colors)

        # 编辑后 Scintilla 只把着色进度推到改动处, 由这里补完后续部分
        editor.notifyChange.connect(self._on_doc_changed)
        self.refresh_styles()

    def _on_doc_changed(self):
        """
        文档变化后补着色, Scintilla 已把着色进度停在改动处

        Args:
            self: 高亮器实例
        """
        if self._styling:
            return  # 折叠级别变化同样会发来修改通知, 着色期间忽略
        editor = self._editor

        # 只补改动点之后的部分, 避免每次按键都整篇重绘
        start = editor.endStyled()
        if start < editor.textLength():
            editor.colourise(start, -1)

    def _compile_rules(self):
        """
        预编译全部高亮正则规则

        Args:
            self: 高亮器实例
        """
        rules: list[tuple[re.Pattern, int]] = []
        for module_name, style in _CATEGORY_STYLES:
            items = list(_extract_keys(module_name))
            pattern = _build_pattern(items, is_punctuation=(module_name == 'punctuation'))
            if pattern:
                rules.append((re.compile(pattern), style))
        self._rules = rules

    def refresh_colors(self):
        """
        仅重新应用语法配色, 不做整篇重新着色

        Args:
            self: 高亮器实例
        """
        colors = DARcula_COLORS if self._dark_mode else LIGHT_COLORS
        for style, key in _STYLE_KEYS.items():
            self._editor.styleSetFore(style, color_int(QColor(*colors[key])))

    def refresh_styles(self):
        """
        重新应用语法颜色并重绘整个文档

        Args:
            self: 高亮器实例
        """
        self.refresh_colors()
        self._editor.colourise(0, -1)

    def update_theme(self, dark_mode: bool):
        """
        更新主题

        Args:
            dark_mode: True 为深色主题, False 为浅色主题
        """
        if self._dark_mode == dark_mode:
            return
        self._dark_mode = dark_mode
        self.refresh_styles()

    def remove(self):
        """
        解除高亮, 断开信号并将语法样式还原为默认文本色

        Args:
            self: 高亮器实例
        """
        for signal, slot in (
                (self._editor.styleNeeded, self._on_style_needed),
                (self._editor.fontChanged, self.refresh_colors),
                (self._editor.notifyChange, self._on_doc_changed),
        ):
            try:
                signal.disconnect(slot)
            except RuntimeError:
                pass
        default_fore = self._editor.styleFore(_COMMON.Default)
        for style in range(STYLE_KEYWORD, STYLE_STRING + 1):
            self._editor.styleSetFore(style, default_fore)
        self._editor.colourise(0, -1)

    def _on_style_needed(self, end_pos: int):
        """
        Scintilla 请求样式化时按行着色

        Args:
            end_pos: 需要样式化到的字节位置
        """
        if self._styling:
            return
        self._styling = True
        try:
            editor = self._editor
            start = editor.endStyled()
            start = min(start, end_pos)
            first_line = editor.lineFromPosition(start)
            last_line = editor.lineFromPosition(end_pos)

            # 从行首开始样式化, 保证字节计数整齐
            editor.startStyling(editor.positionFromLine(first_line), 0)
            for line in range(first_line, last_line + 1):
                self._style_line(line)

            # 折叠级别必须等整段着色完成后再设, 见 _apply_fold_levels 的说明
            self._apply_fold_levels(first_line, last_line)
        finally:
            self._styling = False

    def _apply_fold_levels(self, first_line: int, last_line: int):
        """
        为指定行区间设置折叠级别

        Args:
            first_line: 起始行
            last_line: 结束行
        """
        editor = self._editor
        try:
            editor.styleNeeded.disconnect(self._on_style_needed)
        except RuntimeError:
            return
        try:
            for line in range(first_line, last_line + 1):
                self._set_fold_level(line, editor.line_text(line))
        finally:
            editor.styleNeeded.connect(self._on_style_needed)

    def _style_line(self, line: int):
        """
        样式化单行文本

        Args:
            line: 行号
        """
        editor = self._editor
        text = editor.line_text(line)

        # 按共享分词器切分, 代码段做着色, 字符串/注释各自独立配色
        for token_type, seg in tokenize_line(text):
            if token_type == TOKEN_COMMENT:
                self._style_segment(seg, STYLE_COMMENT)
            elif token_type == TOKEN_STRING:
                self._style_segment(seg, STYLE_STRING)
            elif token_type == TOKEN_CODE:
                self._style_code_segment(seg)
            else:
                self._style_segment(seg, STYLE_TEXT)

        # 行尾换行符使用普通文本样式
        line_end = editor.lineEndPosition(line)
        if line + 1 < editor.lineCount():
            eol_len = editor.positionFromLine(line + 1) - line_end
            if eol_len > 0:
                editor.setStyling(eol_len, STYLE_TEXT)

    def _style_segment(self, seg: str, style: int):
        """
        将文本段整体设为指定样式

        Args:
            seg: 文本段
            style: 样式编号
        """
        self._editor.setStyling(len(seg.encode('utf-8')), style)

    def _style_code_segment(self, seg: str):
        """
        对代码段应用正则规则着色, 未命中部分使用普通文本样式

        Args:
            seg: 代码段文本
        """
        matches: list[tuple[int, int, int, int]] = []
        for rule_index, (regex, style) in enumerate(self._rules):
            for m in regex.finditer(seg):
                matches.append((m.start(), m.end(), style, rule_index))

        # 按起点与规则优先级排序, 丢弃重叠匹配, 先到者优先
        matches.sort(key=lambda item: (item[0], item[3]))
        kept: list[tuple[int, int, int]] = []
        covered_end = 0
        for start, end, style, _ in matches:
            if start >= covered_end:
                kept.append((start, end, style))
                covered_end = end

        cursor = 0
        for start, end, style in kept:
            if start > cursor:
                self._style_segment(seg[cursor:start], STYLE_TEXT)
            self._style_segment(seg[start:end], style)
            cursor = end
        if cursor < len(seg):
            self._style_segment(seg[cursor:], STYLE_TEXT)

    def _set_fold_level(self, line: int, text: str):
        """
        按缩进深度设置行的折叠级别, 类 Python 折叠

        Args:
            line: 行号
            text: 行文本
        """
        editor = self._editor
        fold_level = SC.FoldLevel

        if not text.strip():
            # 空行沿用上一行级别并标记为空白行
            if line > 0:
                prev = editor.foldLevel(line - 1) & fold_level.NumberMask
            else:
                prev = fold_level.Base
            editor.setFoldLevel(line, prev | fold_level.WhiteFlag)
            return

        indent = len(text) - len(text.lstrip())
        depth = indent // max(1, editor.tabWidth())
        level = fold_level.Base + depth

        # 向后查找下一个非空行的缩进深度, 更深则当前行为折叠头
        next_depth = None
        total = editor.lineCount()
        for ahead in range(line + 1, min(line + 1 + _FOLD_LOOKAHEAD, total)):
            ahead_text = editor.line_text(ahead)
            if ahead_text.strip():
                next_depth = (len(ahead_text) - len(ahead_text.lstrip())) // max(1, editor.tabWidth())
                break
        if next_depth is not None and next_depth > depth:
            level |= fold_level.HeaderFlag

        editor.setFoldLevel(line, level)

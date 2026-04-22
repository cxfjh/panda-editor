import re
from typing import List, Optional
from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat
import src.module.builtin_funcs as BuiltinLibraryMethods
import src.module.builtins as BuiltinLibraries
import src.module.keywords as KeyWords
import src.module.punctuations as PunctuationMark


# 直接提取各模块的键值并过滤括号字符
keywords: List[str] = [str(k) for k in KeyWords.key_words.keys() if str(k) not in { "(", ")" }]
builtin_funcs: List[str] = [str(k) for k in BuiltinLibraryMethods.builtin_funcs.keys() if str(k) not in { "(", ")" }]
builtin_libraries: List[str] = [str(k) for k in BuiltinLibraries.builtins.keys() if str(k) not in { "(", ")" }]
punctuations: List[str] = [str(k) for k in PunctuationMark.punctuations.keys() if str(k) not in { "(", ")" }]

# 组织数据结构以匹配原有索引方式
merged_highlight_data: List[List[str]] = [keywords, builtin_funcs, builtin_libraries, punctuations]


class ChineseHighlighter(QSyntaxHighlighter):
    """中文语法高亮器"""

    def __init__(self, document):
        super().__init__(document)
        self.keyword_regex: Optional[QRegularExpression] = None
        self.builtin_method_regex: Optional[QRegularExpression] = None
        self.builtin_library_regex: Optional[QRegularExpression] = None
        self.punctuation_regex: Optional[QRegularExpression] = None
        self.highlight_styles = {
            "KeyWords": self._create_text_format([197, 134, 192]),  # 紫色
            "BuiltinLibraryMethods": self._create_text_format([78, 201, 176]),  # 绿色
            "BuiltinLibraries": self._create_text_format([156, 220, 254]),  # 蓝色
            "PunctuationMark": self._create_text_format([172, 110, 89]),  # 棕色
        }
        self._precompile_patterns()  # 预编译所有正则模式

    @staticmethod
    def _create_text_format(rgb_color: List[int], style: str = "") -> QTextCharFormat:
        """创建文本格式"""
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(*rgb_color))
        if "bold" in style: fmt.setFontWeight(QFont.Weight.Bold)
        if "italic" in style: fmt.setFontItalic(True)
        return fmt

    @staticmethod
    def _join_patterns(items: List[str], is_punctuation: bool = False) -> Optional[QRegularExpression]:
        """将多个关键字/符号合并为一个正则模式"""
        if not items:
            return None

        if is_punctuation:
            # 标点符号合并为字符类
            escaped = "".join(re.escape(str(ch)) for ch in items)
            return QRegularExpression(f"[{escaped}]")

        # @开头的关键字
        if all(str(item).startswith("@") for item in items):
            escaped_items = [re.escape(str(w)) for w in items]
            pattern = "(?:" + "|".join(escaped_items) + r")(?![\p{Han}\p{L}\p{N}_])"  # 左边不加边界，右边加边界
            return QRegularExpression(pattern)

        # 默认关键字
        escaped_items = [re.escape(str(w)) for w in items]
        pattern = (r"(?<![\p{Han}\p{L}\p{N}_])(?:" + "|".join(escaped_items) + ")(?![\\p{Han}\\p{L}\\p{N}_])")
        return QRegularExpression(pattern)

    def _precompile_patterns(self):
        """预编译正则模式"""
        self.keyword_regex = self._join_patterns(merged_highlight_data[0])
        self.builtin_method_regex = self._join_patterns(merged_highlight_data[1])
        self.builtin_library_regex = self._join_patterns(merged_highlight_data[2])
        self.punctuation_regex = self._join_patterns(merged_highlight_data[3], is_punctuation=True)

    def _apply_highlight(self, text: str, regex: Optional[QRegularExpression], style: QTextCharFormat):
        """通用高亮函数"""
        if not regex: return
        it = regex.globalMatch(text)
        while it.hasNext():
            m = it.next()
            self.setFormat(m.capturedStart(), m.capturedLength(), style)

    def highlightBlock(self, text: str):
        """对文本块进行高亮"""
        self._apply_highlight(text, self.keyword_regex, self.highlight_styles["KeyWords"])
        self._apply_highlight(text, self.builtin_method_regex, self.highlight_styles["BuiltinLibraryMethods"])
        self._apply_highlight(text, self.builtin_library_regex, self.highlight_styles["BuiltinLibraries"])
        self._apply_highlight(text, self.punctuation_regex, self.highlight_styles["PunctuationMark"])
        self.setCurrentBlockState(0)

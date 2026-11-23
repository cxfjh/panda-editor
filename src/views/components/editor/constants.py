from pyside6_scintilla import Scintilla


SC = Scintilla

# 默认样式等公共样式编号
COMMON = SC.StylesCommon

# 括号字符编码 ASCII
BRACE_CODES = frozenset(ord(c) for c in '()[]{}')

import re
from src.utils.completion_index.types import NAME


# 文档结构
FUNC_HEAD = re.compile(rf'^[ \t]*(?:异步[ \t]+)?定义[ \t]+({NAME})')
CLASS_HEAD = re.compile(rf'^[ \t]*类[ \t]+({NAME})')
SELF_MEMBER = re.compile(rf'自身[ \t]*[.。][ \t]*({NAME})')
ASSIGN = re.compile(rf'^[ \t]*({NAME})[ \t]*=(?!=)[ \t]*(.*)$')
TUPLE_ASSIGN = re.compile(rf'^[ \t]*({NAME}(?:[ \t]*[,，][ \t]*{NAME})+)[ \t]*=(?!=)[ \t]*(.*)$')
FOR_EACH = re.compile(rf'遍历[ \t]+({NAME})(?:[ \t]*[,，][ \t]*({NAME}))?[ \t]+在')
CATCH = re.compile(rf'捕获[ \t]+({NAME})')
IMPORT_HEAD = re.compile(rf'^[ \t]*(?:引入|来自)[ \t]+({NAME})(?:[ \t]+简称[ \t]+({NAME}))?')
FROM_NAMES = re.compile(r'引入[ \t]+(.+)$')
NUMBER_START = re.compile(r'^[-+]?\d')
CLASS_CALL = re.compile(rf'^({NAME})[ \t]*[（(]')

# 补全上下文判定
MEMBER_CTX = re.compile(rf'[.。][ \t]*({NAME})?$')
RECEIVER = re.compile(rf'({NAME})[ \t]*$')
TAIL_WORD = re.compile(rf'({NAME})$')
IMPORT_CTX = re.compile(rf'(?:引入|来自)[ \t]+({NAME})?$')
NUMBER_TAIL = re.compile(r'(?<!\w)\d[\d.]*$')

# 纯字母输入, 用于判定是否启用拼音首字母匹配
ASCII_ALPHA = re.compile(r'[a-z]+')

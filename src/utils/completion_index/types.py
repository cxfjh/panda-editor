TYPE_UNKNOWN = 'unknown'
TYPE_LIST = 'list'
TYPE_TUPLE = 'tuple'
TYPE_DICT = 'dict'
TYPE_SET = 'set'
TYPE_STR = 'str'
TYPE_NUM = 'num'
TYPE_FILE = 'file'
TYPE_SEQ = 'seq'
TYPE_CLASS_PREFIX = 'class:'

# 标识符, Unicode 词字符且不以数字开头, 中文可作标识符
NAME = r'[^\W\d]\w*'

# 各类对象的可用成员, 键必须存在于 method_map, 否则转译后无法运行
LIST_METHODS: tuple[str, ...] = ('追加', '插入', '弹出', '删除', '清空', '反转', '排序', '计数', '扩展', '索引')
DICT_METHODS: tuple[str, ...] = ('取键', '取值', '取项', '获取', '更新', '设默认', '清空', '弹出')
SET_METHODS: tuple[str, ...] = ('添加', '丢弃', '清空', '交集', '并集', '差集', '弹出')
STR_METHODS: tuple[str, ...] = ('分割', '连接', '替换', '查找', '大写', '小写', '去空格', '开头匹配', '结尾匹配', '计数', '索引')
FILE_METHODS: tuple[str, ...] = ('读取', '读取行', '写入', '关闭')
SEQ_METHODS: tuple[str, ...] = ('索引', '计数')

# 类型对应成员列表
TYPE_METHODS: dict[str, tuple[str, ...]] = {
    TYPE_LIST: LIST_METHODS,
    TYPE_TUPLE: SEQ_METHODS,
    TYPE_SEQ: SEQ_METHODS,
    TYPE_DICT: DICT_METHODS,
    TYPE_SET: SET_METHODS,
    TYPE_STR: STR_METHODS,
    TYPE_FILE: FILE_METHODS,
}

# 赋值右侧前缀对应类型, 按前缀长度降序匹配
TYPE_HINTS: tuple[tuple[str, str], ...] = tuple(
    sorted(
        {
            '列表*': TYPE_LIST,
            '字典*': TYPE_DICT,
            '集合*': TYPE_SET,
            '元组*': TYPE_TUPLE,
            '转文本*': TYPE_STR,
            '转整数*': TYPE_NUM,
            '转小数*': TYPE_NUM,
            '打开*': TYPE_FILE,
            '打开': TYPE_FILE,
            '区间*': TYPE_SEQ,
            '排序*': TYPE_LIST,
            '反转*': TYPE_SEQ,
            '筛选*': TYPE_LIST,
            '映射*': TYPE_LIST,
            '分割': TYPE_LIST,
        }.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ),
)

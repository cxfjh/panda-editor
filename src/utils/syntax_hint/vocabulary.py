from itertools import chain
from src.module.builtin_map import builtin
from src.module.keyword_map import keyword
from src.module.lib_map import lib
from src.module.method_map import method
from src.module.stdlib_map import stdlib
from src.utils.completion_index import TYPE_CLASS_PREFIX, TYPE_METHODS, DocumentIndex
from src.utils.syntax_signature import build_module_members, dedupe


# 文档索引最短重建间隔, 单位为秒, 连续输入时避免每次按键都全量扫描
INDEX_MIN_INTERVAL = 0.25

# 单次弹出的候选数量上限
MAX_CANDIDATES = 300

# 静态词库, 按类别排序, 自定义顺序由 Scintilla 保持
STATIC_GLOBALS: list[str] = dedupe(
    list(
        chain(
            keyword.keys(), builtin.keys(), stdlib.keys(), lib.keys(), method.keys(),
        ),
    ),
)

# 静态成员词库, 按类别排序, 自定义顺序由 Scintilla 保持
STATIC_MEMBERS: list[str] = dedupe(list(chain(method.keys(), stdlib.keys())))
IMPORT_ITEMS: list[str] = dedupe(list(lib.keys()))
MODULE_MEMBERS = build_module_members()


def member_items(receiver: str | None, line: int, index: DocumentIndex) -> list[str]:
    """
    构建成员补全候选, 按接收者类型收敛范围

    Args:
        receiver: 点号前的接收者标识符
        line: 光标所在行号
        index: 文档索引

    Returns:
        候选词列表
    """
    if receiver:
        if receiver == '自身':
            class_name = index.class_at(line)
            if class_name:
                return dedupe(tuple(index.methods_of(class_name)) + tuple(index.self_members))
        tag = index.variables.get(receiver)
        if tag in TYPE_METHODS:
            return list(TYPE_METHODS[tag])  # type: ignore
        if tag and tag.startswith(TYPE_CLASS_PREFIX):
            names = index.methods_of(tag[len(TYPE_CLASS_PREFIX):])
            if names:
                return names

        # 先按 import 别名找模块
        module_members = (MODULE_MEMBERS.get(index.aliases.get(receiver, '')) or MODULE_MEMBERS.get(receiver))
        if module_members:
            return list(module_members)

    # 接收者类型未知时给出全部候选, 保证不漏
    return dedupe(tuple(index.self_members) + tuple(index.symbols) + tuple(STATIC_MEMBERS))


def global_items(index: DocumentIndex) -> list[str]:
    """
    构建全局补全候选, 文档标识符优先

    Args:
        index: 文档索引

    Returns:
        候选词列表
    """
    return dedupe(tuple(index.symbols) + tuple(STATIC_GLOBALS))

"""
文档符号索引与补全上下文判定
"""

from src.utils.completion_index.context import detect_context, enclosing_call, first_string_arg
from src.utils.completion_index.model import NONE_CONTEXT, CallContext, CompletionContext, DocumentIndex
from src.utils.completion_index.parse import build_index, filter_items, infer_type, split_params
from src.utils.completion_index.types import TYPE_CLASS_PREFIX, TYPE_DICT, TYPE_FILE, TYPE_LIST, TYPE_METHODS, TYPE_NUM, TYPE_SEQ, TYPE_SET, TYPE_STR, TYPE_TUPLE, TYPE_UNKNOWN


__all__ = [
    "NONE_CONTEXT",
    "TYPE_CLASS_PREFIX",
    "TYPE_DICT",
    "TYPE_FILE",
    "TYPE_LIST",
    "TYPE_METHODS",
    "TYPE_NUM",
    "TYPE_SEQ",
    "TYPE_SET",
    "TYPE_STR",
    "TYPE_TUPLE",
    "TYPE_UNKNOWN",
    "CallContext",
    "CompletionContext",
    "DocumentIndex",
    "build_index",
    "detect_context",
    "enclosing_call",
    "filter_items",
    "first_string_arg",
    "infer_type",
    "split_params",
]

from __future__ import annotations
from functools import lru_cache


def _is_han(ch: str) -> bool:
    """
    判断字符是否属于汉字区, 含扩展 A 区

    Args:
        ch: 单个字符

    Returns:
        bool, True 表示汉字
    """
    return '\u4e00' <= ch <= '\u9fff' or '\u3400' <= ch <= '\u4dbf'


@lru_cache(maxsize=4096)
def _char_letters(ch: str) -> tuple[str, ...]:
    """
    取单个汉字的首字母, 多音字全部保留

    Args:
        ch: 单个汉字

    Returns:
        首字母元组, 首个为主读音, 如 长 返回 z, c
    """
    from pypinyin import Style, pinyin
    groups = pinyin(ch, style=Style.FIRST_LETTER, heteronym=True, errors='ignore')
    return tuple(letter.lower() for group in groups for letter in group if letter)


@lru_cache(maxsize=8192)
def letters_of(text: str) -> tuple[tuple[str, ...], ...]:
    """
    逐字取候选词的首字母, 跳过非汉字字符

    Args:
        text: 候选词, 如 数组长度

    Returns:
        按字序排列的首字母元组, 如 s, z, z c, d z
    """
    return tuple(_char_letters(ch) for ch in text if _is_han(ch))


@lru_cache(maxsize=8192)
def initials_of(text: str) -> str:
    """
    取候选词每个汉字的主读音首字母

    Args:
        text: 候选词, 如 数字

    Returns:
        首字母串, 小写, 如 sz; 不含汉字时返回空串
    """
    return ''.join(group[0] for group in letters_of(text) if group)


def starts_with_initials(text: str, typed: str) -> bool:
    """
    判断已输入缩写是否逐字对上候选词的首字母, 多音字任选其一即可

    Args:
        text: 候选词, 如 数组长度
        typed: 已输入的缩写

    Returns:
        bool, True 表示按字序命中
    """
    groups = letters_of(text)
    if not groups or not typed or len(typed) > len(groups):
        return False
    return all(typed[i] in groups[i] for i in range(len(typed)))


def is_subsequence(needle: str, haystack: str) -> bool:
    """
    判断 needle 的字符是否按顺序出现在 haystack 中, 允许中间跳过字符

    Args:
        needle: 已输入的缩写
        haystack: 候选词的首字母串

    Returns:
        bool, True 表示按序命中
    """
    if not needle:
        return True
    if len(needle) > len(haystack):
        return False
    cursor = iter(haystack)
    return all(ch in cursor for ch in needle)

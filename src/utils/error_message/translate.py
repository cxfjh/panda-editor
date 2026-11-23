import re
from src.utils.error_message.names import _PHRASE_NAMES, _WIN_ERROR_LINE, _WIN_ERRORS, EXCEPTION_NAMES, TYPE_NAMES
from src.utils.error_message.rules import _MESSAGE_RULES


_TYPE_GROUPS = ("t1", "t2", "t3", "what")

_PHRASE_GROUPS = ("expect",)

_EMPTY_MESSAGES = {
    "KeyError": "字典里没有对应的键",
    "IndexError": "下标越界",
    "AttributeError": "对象没有这个属性",
    "ValueError": "传进去的值不合法",
}


def exception_name(type_name: str) -> str:
    """
    把异常类型名翻成中文

    Args:
        type_name: 异常类型名, 如 NameError

    Returns:
        中文名, 未收录时原样返回
    """
    short = type_name.rsplit(".", 1)[-1]
    return EXCEPTION_NAMES.get(short, short)


def _type_phrase(text: str) -> str:
    """
    把类型短语里的英文说法换成中文

    Args:
        text: 形如 str or a tuple of str 的类型短语

    Returns:
        中文类型短语, 认不出的部分保持原样
    """
    phrase = _PHRASE_NAMES.get(text)
    if phrase:
        return phrase
    text = text.replace("bytes-like", "字节类")
    for english, chinese in TYPE_NAMES.items():
        text = re.sub(rf"\b{re.escape(english)}\b", chinese, text)
    return text.replace(" or ", " 或 ")


def translate_message(type_name: str, message: str) -> str:
    """
    把异常消息翻成中文

    Args:
        type_name: 异常类型名, 消息为空时靠它给说明
        message: 异常消息原文

    Returns:
        中文说明, 没有对应模板时返回原文
    """
    text = message.strip()

    # 消息为空时只能靠类型名说明
    if not text:
        return _EMPTY_MESSAGES.get(type_name, exception_name(type_name))

    # 键错误的消息就是缺失的那个键本身
    if type_name == "KeyError":
        return "字典里没有键 %s, 检查键名是否写错" % text

    # Windows 的文件错误带系统错误码, 按码给说明
    win_error = _WIN_ERROR_LINE.match(text)
    if win_error:
        code = int(win_error.group("code"))
        hint = _WIN_ERRORS.get(code, "系统调用失败")
        return "%s, 路径 %s" % (hint, win_error.group("path"))

    for pattern, template in _MESSAGE_RULES:
        found = pattern.match(text)
        if not found:
            continue
        groups = found.groupdict()
        for key in _TYPE_GROUPS:
            if groups.get(key):
                groups[key] = TYPE_NAMES.get(groups[key], groups[key])
        for key in _PHRASE_GROUPS:
            if groups.get(key):
                groups[key] = _type_phrase(groups[key])
        try:
            return template.format(**groups)
        except (KeyError, IndexError):
            continue
    return text

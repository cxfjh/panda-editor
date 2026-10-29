"""文本读写, 依次尝试的编码, gb18030 兼容 gbk 与 gb2312"""

_ENCODINGS: list[str] = ["utf-8", "gb18030"]

# UTF-8 BOM, 需要在尝试编码前单独判断, 否则无 BOM 的文件也会被当成 utf-8-sig
_UTF8_BOM = b"\xef\xbb\xbf"

# 判断二进制文件时检查的字节数
_SNIFF_SIZE = 8192


class BinaryFileError(ValueError):
    """文件内容看起来不是文本"""


def read_text_file_with_encoding(file_path: str) -> tuple[str, str]:
    """
    读取文本文件, 自动兼容 UTF-8 与 GBK 编码

    Args:
        file_path: 文件完整路径

    Returns:
        文件内容, 探测到的编码, 换行符统一为 \\n, 保存时按该编码写回

    Raises:
        OSError, 文件无法读取
        BinaryFileError, 文件含有空字节, 判定为二进制
        UnicodeDecodeError, 三种编码都无法解码
    """
    with open(file_path, "rb") as f:
        raw = f.read()

    # 文本文件不出现空字节, 借此拦下图片/可执行文件, 避免显示成一堆乱码
    if b"\x00" in raw[:_SNIFF_SIZE]:
        raise BinaryFileError("该文件不是文本文件, 无法用编辑器打开")

    # 带 BOM 的文件按 utf-8-sig 处理, 保存时把 BOM 写回去
    if raw.startswith(_UTF8_BOM):
        return raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n"), "utf-8-sig"

    last_error: UnicodeDecodeError | None = None
    for encoding in _ENCODINGS:
        try:
            content = raw.decode(encoding)
        except UnicodeDecodeError as e:
            last_error = e
            continue
        return content.replace("\r\n", "\n").replace("\r", "\n"), encoding

    assert last_error is not None
    raise last_error

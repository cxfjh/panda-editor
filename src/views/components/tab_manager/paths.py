import os


def is_within(path: str, root: str) -> bool:
    """
    判断路径是否位于指定目录之内

    Args:
        path: 待判断的路径
        root: 父目录路径

    Returns:
        path 在 root 之下返回 True, 否则返回 False
    """
    try:
        absolute_path = os.path.abspath(path)
        absolute_root = os.path.abspath(root)
        return os.path.commonpath([absolute_path, absolute_root]) == absolute_root
    except ValueError:
        return False

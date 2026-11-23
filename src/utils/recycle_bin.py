import os
from send2trash import send2trash


def move_to_recycle_bin(path: str) -> bool:
    """
    把文件或目录移入系统回收站

    Args:
        path: 文件或目录路径

    Returns:
        bool, True 表示已移入回收站 False 表示失败
    """
    if not os.path.exists(path):
        return False
    try:
        send2trash(path)
        return True
    except OSError:
        return False

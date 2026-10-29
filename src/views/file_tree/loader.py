import os
from PySide6.QtCore import QThread, Signal
from src.utils.exceptions import safe_log


# 需要过滤的大型目录, 点号开头的目录由 should_ignore 统一拦截
_IGNORED_DIRS = {
    '__pycache__', 'node_modules', 'bower_components',
    'venv', 'env', 'dist', 'build',
}


def should_ignore(name: str) -> bool:
    """
    判断是否应该忽略该目录或文件

    Args:
        name: 目录或文件名

    Returns:
        True 表示应该忽略, False 表示应该显示
    """
    if name.startswith('.'): return True  # 隐藏文件 隐藏目录
    if name in _IGNORED_DIRS: return True  # 已知的大型目录
    if name.endswith('.egg-info'): return True  # Python 包信息目录
    return False


def scan_directory(path: str) -> list:
    """
    扫描目录并返回排序后的子项

    Args:
        path: 要扫描的目录路径

    Returns:
        三元组列表, 依次为名称 完整路径 是否为目录, 文件夹在前文件在后
    """
    dirs = []
    files = []
    try:
        if not os.path.isdir(path):
            return []

        # 遍历目录内容
        for name in os.listdir(path):
            if should_ignore(name):
                continue
            full_path = os.path.join(path, name)
            if os.path.isdir(full_path):
                dirs.append((name, full_path, True))
            else:
                files.append((name, full_path, False))
    except (PermissionError, OSError) as e:
        safe_log(f"目录扫描失败: {e}")

    # 先文件夹后文件按名称字母排序
    dirs.sort(key=lambda x: x[0].lower())
    files.sort(key=lambda x: x[0].lower())
    return dirs + files


class DirectoryLoader(QThread):
    """异步目录加载线程"""

    # 信号名不能叫 finished, 会遮蔽 QThread 自带的 finished 引发原生崩溃
    loaded = Signal(object, list)

    def __init__(self, parent_item, parent_path):
        """
        初始化加载器

        Args:
            parent_item: 父树节点对象
            parent_path: 要扫描的目录路径
        """
        super().__init__()
        self._parent_item = parent_item
        self._parent_path = parent_path

    def run(self):
        """
        执行目录扫描

        Args:
            self: 当前加载器实例
        """
        self.loaded.emit(self._parent_item, scan_directory(self._parent_path))

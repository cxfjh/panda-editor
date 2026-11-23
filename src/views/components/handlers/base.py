from collections.abc import Callable
from PySide6 import QtCore, QtGui


# 外部链接常量
URL_WEBSITE = 'https://cxfjh.github.io'
URL_REPO = 'https://github.com/cxfjh/panda-editor'
URL_AUTHOR = 'https://github.com/cxfjh'
URL_TUTORIAL = f'{URL_REPO}/blob/main/docs/USAGE.md'
URL_EMAIL = 'mailto:2449579731@qq.com'


def is_cn_path(file_path) -> bool:
    """
    检查给定路径是否为 .cn 格式文件

    Args:
        file_path: 待检查的文件路径

    Returns:
        路径以 .cn 结尾返回 True, 否则返回 False
    """
    return bool(file_path) and file_path.endswith('.cn')


class HandlerBase:
    """处理器基类, 持有主窗口 UI 引用"""

    # 跨动作类调用的方法, 实现在各自动作类中, 这里只声明可调用类型
    on_cursor_position_changed: Callable[..., None]
    toggle_blockly: Callable[..., None]

    def __init__(self, ui):
        """
        初始化事件处理器

        Args:
            self: 类实例自身
            ui: MainWindowUI 实例
        """
        self.ui = ui

        # 面板折叠前的分割器尺寸, 展开时按原样还原
        self._panel_sizes: dict[str, int] = { }

    @staticmethod
    def open_url(url: str):
        """
        用系统默认程序打开链接或邮件地址

        Args:
            url: 要打开的链接或邮件地址
        """
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))

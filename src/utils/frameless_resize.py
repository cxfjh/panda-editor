import ctypes
import os
from ctypes import wintypes
from PySide6 import QtCore, QtWidgets
from src.utils.exceptions import safe_log


# Windows 消息与命中码
_WM_NCHITTEST = 0x0084
_HTCLIENT = 1
_HTLEFT = 10
_HTRIGHT = 11
_HTTOP = 12
_HTTOPLEFT = 13
_HTTOPRIGHT = 14
_HTBOTTOM = 15
_HTBOTTOMLEFT = 16
_HTBOTTOMRIGHT = 17

# 可拉伸边缘的逻辑宽度, 会按 DPI 缩放换算成物理像素
_DEFAULT_BORDER = 6

# 去掉标题栏后仍保留可缩放边框, 否则系统不会进入调整大小循环
_GWL_STYLE = -16
_WS_THICKFRAME = 0x00040000
_SWP_NOSIZE = 0x0001
_SWP_NOMOVE = 0x0002
_SWP_NOZORDER = 0x0004
_SWP_NOACTIVATE = 0x0010
_SWP_FRAMECHANGED = 0x0020


def _apply_thick_frame(window: QtWidgets.QWidget) -> None:
    """
    给无边框窗口补上 WS_THICKFRAME

    Args:
        window: 目标窗口
    """
    if os.name != "nt":
        return
    try:
        hwnd = int(window.winId())
    except RuntimeError as e:
        safe_log(f"读取窗口句柄失败: {e}", "debug")
        return

    user32 = ctypes.windll.user32
    style = user32.GetWindowLongW(hwnd, _GWL_STYLE)  # type: ignore
    if style & _WS_THICKFRAME:
        return
    user32.SetWindowLongW(hwnd, _GWL_STYLE, style | _WS_THICKFRAME)  # type: ignore
    user32.SetWindowPos(hwnd, None, 0, 0, 0, 0, _SWP_NOSIZE | _SWP_NOMOVE | _SWP_NOZORDER | _SWP_NOACTIVATE | _SWP_FRAMECHANGED)  # type: ignore


class _FramelessResizeFilter(QtCore.QAbstractNativeEventFilter):
    """在无边框窗口的四边与四角返回拉伸命中码"""

    def __init__(self, window: QtWidgets.QWidget, border: int = _DEFAULT_BORDER):
        """
        初始化命中测试过滤器

        Args:
            window: 无边框主窗口
            border: 边缘宽度, 逻辑像素
        """
        super().__init__()
        self._window = window
        self._border = border

    def nativeEventFilter(self, event_type, message):
        """
        拦截 WM_NCHITTEST 判断是否落在窗口边缘

        Args:
            event_type: 原生事件类型
            message: 指向 MSG 结构的指针

        Returns:
            是否已处理与结果码组成的两元组
        """
        if event_type != b"windows_generic_MSG":
            return False, 0

        msg = wintypes.MSG.from_address(int(message))
        if msg.message != _WM_NCHITTEST:
            return False, 0

        window = self._window
        if window is None or not window.isVisible():
            return False, 0

        # 最大化/全屏时没有可拉伸的边缘
        if window.isMaximized() or window.isFullScreen():
            return False, 0
        try:
            if msg.hWnd != int(window.winId()):
                return False, 0
        except RuntimeError as e:
            safe_log(f"读取窗口位置失败: {e}", "debug")
            return False, 0

        # lParam 的高低位是屏幕坐标, 符号扩展后才是真实值
        x = ctypes.c_short(msg.lParam & 0xFFFF).value
        y = ctypes.c_short((msg.lParam >> 16) & 0xFFFF).value

        rect = wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(msg.hWnd, ctypes.byref(rect))  # type: ignore

        # 命中范围按 DPI 缩放, 高分屏上不至于太窄
        border = max(4, round(self._border * window.devicePixelRatioF()))
        on_left = x < rect.left + border
        on_right = x >= rect.right - border
        on_top = y < rect.top + border
        on_bottom = y >= rect.bottom - border

        if on_top and on_left:
            return True, _HTTOPLEFT
        if on_top and on_right:
            return True, _HTTOPRIGHT
        if on_bottom and on_left:
            return True, _HTBOTTOMLEFT
        if on_bottom and on_right:
            return True, _HTBOTTOMRIGHT
        if on_left:
            return True, _HTLEFT
        if on_right:
            return True, _HTRIGHT
        if on_top:
            return True, _HTTOP
        if on_bottom:
            return True, _HTBOTTOM
        return True, _HTCLIENT


class FramelessResizer(QtCore.QObject):
    """为无边框窗口安装边缘拉伸支持"""

    def __init__(self, window: QtWidgets.QWidget, border: int = _DEFAULT_BORDER):
        """
        初始化拉伸支持

        Args:
            window: 无边框主窗口
            border: 边缘宽度, 逻辑像素
        """
        super().__init__(window)
        self._window = window
        self._filter = _FramelessResizeFilter(window, border)
        app = QtWidgets.QApplication.instance()
        if app is not None:
            app.installNativeEventFilter(self._filter)

        # 保留引用, 否则过滤器会被回收
        self._app = app

        # 窗口首次显示与重建
        window.installEventFilter(self)
        _apply_thick_frame(window)

    def eventFilter(self, obj, event):
        """
        窗口显示后确保带可缩放边框

        Args:
            obj: 事件目标
            event: 事件对象

        Returns:
            bool, 是否拦截事件
        """
        if obj is self._window and event.type() in (QtCore.QEvent.Type.Show, QtCore.QEvent.Type.WinIdChange):
            _apply_thick_frame(self._window)
        return False

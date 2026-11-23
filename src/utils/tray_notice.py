import os
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QSystemTrayIcon
from src.utils.config_service import ROOT_DIR
from src.utils.exceptions import safe_log


# 气泡提示的默认标题与停留时长
DEFAULT_TITLE = "PandaEditor 通知"
DEFAULT_DURATION = 5000

# 全局唯一的托盘图标, 建好后各调用方共用
_tray_icon: QSystemTrayIcon | None = None


def ensure_tray_icon(app=None) -> QSystemTrayIcon | None:
    """
    取全局托盘图标, 没有就创建并显示

    Args:
        app: Qt 应用实例, 不传时取当前实例

    Returns:
        已显示的托盘图标, 没有应用实例时返回 None
    """
    global _tray_icon
    if _tray_icon is not None:
        return _tray_icon

    instance = app or QApplication.instance()
    if instance is None:
        return None

    icon_path = os.path.join(ROOT_DIR, "src", "static", "logo.ico")
    _tray_icon = QSystemTrayIcon(QIcon(icon_path), instance)
    _tray_icon.show()  # type: ignore
    return _tray_icon


def show_tray_message(content: str, title: str = DEFAULT_TITLE, duration: int = DEFAULT_DURATION) -> bool:
    """
    通过托盘图标弹出气泡提示

    Args:
        content: 提示正文
        title: 气泡标题
        duration: 停留时长, 单位毫秒

    Returns:
        True 表示已交给系统托盘显示, False 表示当前没有可用的托盘图标
    """
    icon = ensure_tray_icon()
    if icon is None:
        safe_log(f"没有可用的托盘图标, 提示未弹出: {content}", "debug")
        return False

    icon.showMessage(title, content, QSystemTrayIcon.MessageIcon.Information, duration)
    return True

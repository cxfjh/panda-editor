import logging
import sys
import traceback
from PySide6.QtWidgets import QMessageBox, QWidget


# 配置日志记录器
logger = logging.getLogger("PandaEditor")


def safe_log(message: str, level: str = "error") -> None:
    """
    安全日志输出避免在无控制台 GUI 打包环境下 print 崩溃

    Args:
        message: 日志内容
        level: 日志级别
    """
    try:
        func = getattr(logger, level, logger.error)
        func(message)
    except Exception as e:
        logger.error(f"安全日志记录失败: {e}")


class PandaEditorException(Exception):
    """基础异常类"""

    def __init__(self, message: str, detail: str | None = None):
        """
        初始化异常实例

        Args:
            message: 简短的错误消息
            detail: 详细的错误信息
        """
        self.message = message  # 简短错误消息
        self.detail = detail  # 详细错误信息
        super().__init__(message)


class ConfigException(PandaEditorException):
    """配置相关异常"""


class GlobalExceptionHandler:
    """全局异常处理器, 捕获未处理异常并弹窗提示"""

    def __init__(self, parent_widget: QWidget | None = None):
        """
        初始化全局异常处理器

        Args:
            parent_widget: 父窗口引用用于展示模态对话框
        """
        self.parent_widget = parent_widget

    def handle_exception(self, exc_type, exc_value, exc_tb) -> None:
        """
        统一异常处理入口

        Args:
            exc_type: 异常类型
            exc_value: 异常实例
            exc_tb: 异常追踪信息
        """

        # 忽略 KeyboardInterrupt
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return

        # 格式化异常详情
        error_detail = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        error_message = str(exc_value)

        # 写入日志
        logger.error(f"未捕获异常: {exc_type.__name__}\n{error_detail}")

        # 展示错误对话框
        self._show_error_dialog(exc_type.__name__, error_message, error_detail)

    def _show_error_dialog(self, error_type: str, message: str, detail: str) -> None:
        """
        展示错误对话框

        Args:
            error_type: 异常类型名称
            message: 简短错误消息
            detail: 详细错误信息
        """
        if self.parent_widget:
            # 有父窗口展示模态错误对话框
            msg_box = QMessageBox(self.parent_widget)
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("程序错误")
            msg_box.setText(f"<b>{error_type}</b>")
            msg_box.setInformativeText(message)
            msg_box.setDetailedText(detail)
            msg_box.exec()
        else:
            # 无父窗口时回退到日志输出
            safe_log(f"[ERROR] {error_type}: {message}\n{detail}")


def install_global_exception_handler(parent_widget: QWidget | None = None) -> GlobalExceptionHandler:
    """
    安装全局异常处理器

    Args:
        parent_widget: 父窗口引用用于展示模态错误对话框

    Returns:
        GlobalExceptionHandler, 异常处理器实例
    """

    # 确保日志有输出目标
    if not logger.handlers and not logging.getLogger().handlers:
        logging.basicConfig(level=logging.ERROR, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    handler = GlobalExceptionHandler(parent_widget)
    sys.excepthook = handler.handle_exception
    return handler

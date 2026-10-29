import logging
import os
import threading
import traceback
from datetime import datetime
from src.utils.exceptions import safe_log


# 日志目录名, 建在配置里 Python 解释器的同级目录下
_LOG_DIR_NAME = "log"

# 日志格式, 时间 级别 记录器名 冒号 消息
_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

# 已经挂上文件输出的日志路径, 避免重复调用时加两个 handler
_attached_files: set[str] = set()


def log_file_path(python_path: str) -> str:
    """
    按当天日期算出日志文件路径

    Args:
        python_path: 配置里的 Python 解释器路径

    Returns:
        日志文件完整路径, 未配置解释器时返回空字符串
    """
    if not python_path:
        return ""
    directory = os.path.join(os.path.dirname(python_path), _LOG_DIR_NAME)
    return os.path.join(directory, datetime.now().strftime("%Y-%m-%d") + ".log")


def setup_file_logging() -> str:
    """
    把日志写到解释器同级的 log 目录, 按日期一个文件

    Returns:
        日志文件路径, 未配置解释器或创建失败时返回空字符串
    """
    from src.utils.config_service import get_config_service

    python_path = get_config_service().get_app_config("python_path") or ""
    file_path = log_file_path(python_path)
    if not file_path:
        return ""

    if file_path in _attached_files:
        return file_path

    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        handler = logging.FileHandler(file_path, encoding="utf-8")
    except OSError as e:
        safe_log(f"创建日志文件失败: {e}")
        return ""

    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))

    # 根记录器默认只放 WARNING, 要显式放开到 DEBUG 才能记全所有级别
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(handler)
    _attached_files.add(file_path)
    return file_path


def install_thread_exception_hook() -> None:
    """给线程兜底, 子线程里漏出去的异常也写进日志"""

    def handle(args) -> None:
        """
        线程异常回调

        Args:
            args: threading.excepthook 传来的异常信息
        """
        detail = "".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback))
        logging.getLogger("PandaEditor").error("线程 %s 未捕获异常: %s\n%s", args.thread.name if args.thread else "未知", args.exc_type.__name__ if args.exc_type else "未知", detail)

    threading.excepthook = handle

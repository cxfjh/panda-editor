import json
import os
import socket
import sys
from datetime import datetime
from functools import partial
from typing import Callable
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox


# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.config_service import get_config_service
from src.utils.dependency_setup import run_first_launch_setup
from src.utils.exceptions import install_global_exception_handler, safe_log
from src.utils.log_service import install_thread_exception_hook, setup_file_logging
from src.utils.tray_notice import ensure_tray_icon, show_tray_message
from src.views.main_win import MainWindowUI


# 设置高 DPI 缩放因子四舍五入策略为向下取整
QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.Floor)

# 远程通知的地址
NOTICE_URL = "https://cxfjh.cn/notice/panda_editor/notice.json"


def _handle_notice_reply(reply, timer, on_notice: Callable[[str], None]) -> None:
    """
    处理通知请求的响应, 校验通过后把正文交给回调

    Args:
        reply: 网络响应对象
        timer: 超时定时器, 收到响应后停掉
        on_notice: 通知正文回调
    """
    timer.stop()
    try:
        if reply.error() != QNetworkReply.NoError:  # type: ignore
            safe_log(f"检查通知失败: {reply.errorString()}", "debug")
            return

        data = json.loads(reply.readAll().data().decode("utf-8"))  # type: ignore
        if not data.get("enable", False):
            return

        end_time_str = data.get("endTime", "")
        if end_time_str:
            try:
                if datetime.now() >= datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S"):
                    return
            except ValueError as e:
                safe_log(f"通知日期格式非法: {e}", "debug")

        content = data.get("content", "")
        if content:
            on_notice(content)
    except Exception as e:
        safe_log(f"解析通知异常: {e}", "debug")
    finally:
        reply.deleteLater()


def request_notice(app, on_notice: Callable[[str], None]) -> None:
    """
    请求远程通知, 校验通过后把正文交给回调

    Args:
        app: Qt 应用实例, 同时作为网络请求与超时定时器的父对象
        on_notice: 通知正文回调, 由调用方决定如何展示
    """
    nam = QNetworkAccessManager(app)
    req = QNetworkRequest(QUrl(NOTICE_URL))
    req.setRawHeader(b"User-Agent", b"PandaEditor/0.1.0")

    reply: QNetworkReply = nam.get(req)

    # 5 秒超时定时器
    timer = QTimer(app)
    timer.setSingleShot(True)
    timer.timeout.connect(reply.abort)
    timer.start(5000)

    reply.finished.connect(partial(_handle_notice_reply, reply, timer, on_notice))


def check_network(timeout: int = 2) -> bool:
    """
    探测本机是否能连上外网

    Args:
        timeout: 连接超时时间, 单位秒

    Returns:
        True 表示有网络, False 表示无网络
    """
    try:
        socket.create_connection(("223.5.5.5", 53), timeout=timeout)
        return True
    except OSError:
        return False


def start_editor(app) -> None:
    """
    创建并显示主窗口

    Args:
        app: Qt 应用实例, 远程通知请求挂在它名下
    """
    main_window = QMainWindow()

    # 安装全局异常处理器
    install_global_exception_handler(main_window)

    # 处理命令行参数
    if len(sys.argv) > 1:
        main_window.setProperty("launch_path", sys.argv[1])

    # 初始化主窗口 UI
    MainWindowUI().setup_ui(main_window)
    main_window.show()

    # 请求远程通知, 有内容就弹托盘提示
    request_notice(app, show_tray_message)  # type: ignore


def main():
    """初始化配置并启动主窗口"""
    try:
        get_config_service().init_config()
    except Exception as e:
        app_tmp = QApplication(sys.argv)
        QMessageBox.critical(None, "启动失败", f"配置文件初始化失败：\n{e}")
        app_tmp.exec()
        sys.exit(1)

    # 日志初始化
    log_path = setup_file_logging()
    install_thread_exception_hook()
    if log_path:
        safe_log(f"应用启动, 日志文件 {log_path}", "info")

    # 创建应用实例
    app = QApplication(sys.argv)

    # 托盘图标初始化
    ensure_tray_icon(app)

    # 首次启动先把依赖装齐再进编辑器
    setup_worker = run_first_launch_setup(app, None, check_network)
    if setup_worker is None:
        start_editor(app)
    else:
        setup_worker.completed.connect(lambda: start_editor(app))

    # 运行应用主循环
    exit_code = app.exec()

    # 依赖还在装时给线程一点时间收尾
    if setup_worker is not None and setup_worker.isRunning():
        setup_worker.wait(3000)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()

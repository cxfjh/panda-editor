import os
import shutil
import subprocess
import sys
import time
from PySide6 import QtCore
from src.utils.config_service import CONFIG_DIR, get_config_service
from src.utils.dialog_utils import DialogUtils
from src.utils.exceptions import safe_log


def _get_root_path() -> str:
    """
    获取程序根目录

    Returns:
        程序根目录的完整路径若配置缺失则返回空字符串
    """
    root = get_config_service().get_app_config("root_dir")
    if not root:
        DialogUtils.show_error(DialogUtils.parent_widget(), "错误", "未获取到程序根目录！")
        return ""
    return root


def _remove_config_dir() -> None:
    """删除用户配置目录, 目录不存在时直接跳过"""
    if os.path.isdir(CONFIG_DIR):
        shutil.rmtree(CONFIG_DIR)


def reset_program() -> None:
    """重置程序到初始状态"""
    root = _get_root_path()
    if not root: return
    if not DialogUtils.ask_question(DialogUtils.parent_widget(), "重置程序", "确定要重置程序吗？所有设置和会话记录都会被清除。"): return

    # 分步处理, 失败时能说清是删不掉还是重建不了, 日志里也留一条
    try:
        _remove_config_dir()
    except OSError as e:
        safe_log(f"重置程序失败, 删除配置目录出错: {e}")
        DialogUtils.show_error(DialogUtils.parent_widget(), "重置失败", f"无法删除配置目录：\n{CONFIG_DIR}\n\n{e!s}")
        return

    try:
        svc = get_config_service()
        svc._initialized = False  # 允许重新初始化
        svc.init_config()
    except Exception as e:
        safe_log(f"重置程序失败, 重建配置出错: {e}")
        DialogUtils.show_error(DialogUtils.parent_widget(), "重置失败", f"配置重建失败：\n{e!s}\n\n请尝试使用管理员身份运行！")
        return

    DialogUtils.show_info(DialogUtils.parent_widget(), "重置成功", "程序已重置，即将重启！")
    restart_program()


def uninstall_program() -> None:
    """调用卸载程序执行卸载"""
    root = _get_root_path()
    if not root: return
    if not DialogUtils.ask_question(DialogUtils.parent_widget(), "卸载程序", "确定要卸载程序吗？程序文件和所有设置都会被删除。"): return

    try:
        # 卸载程序路径
        uninstaller = os.path.join(root, "uninst.exe")
        if not os.path.exists(uninstaller):
            DialogUtils.show_error(DialogUtils.parent_widget(), "卸载失败", "未找到卸载程序：uninst.exe")
            return

        # 卸载前清掉用户配置, 免得重装后还留着上一次的设置
        try:
            _remove_config_dir()
        except OSError as e:
            safe_log(f"卸载前清理用户配置失败: {e}")

        # 先启动卸载程序
        subprocess.Popen([uninstaller])
        os._exit(0)
    except Exception as e:
        DialogUtils.show_error(DialogUtils.parent_widget(), "卸载失败", f"错误信息：{e!s}\n\n请尝试使用管理员身份运行！")


def _restart_target() -> str:
    """
    取重启时应该运行的可执行文件

    Returns:
        已存在的 exe 绝对路径, 找不到时返回空字符串
    """
    for raw in (sys.argv[0] if sys.argv else "", sys.executable):
        if not raw:
            continue
        path = os.path.abspath(raw)
        if path.lower().endswith(".exe") and os.path.isfile(path):
            return path
    return ""


def restart_program() -> None:
    """重启程序"""
    main_module = sys.modules.get("__main__")
    compiled = getattr(sys, "frozen", False) or hasattr(main_module, "__compiled__")
    if compiled:
        executable = _restart_target()
        if not executable:
            safe_log(f"重启程序失败, 找不到可执行文件, argv0 {sys.argv[0] if sys.argv else ''} 可执行文件 {sys.executable}")
            DialogUtils.show_error(DialogUtils.parent_widget(), "重启失败", "找不到程序本体, 请手动重新打开。")
            return

        # 分离启动, 父进程退出不会带走子进程; 返回值是 成功标志与进程号 组成的元组
        result = QtCore.QProcess.startDetached(executable, [ ], os.path.dirname(executable))
        started = result[0] if isinstance(result, tuple) else bool(result)

        # 分离启动被拒绝时退回 Popen, 显式脱离父进程并丢弃输出句柄
        if not started:
            try:
                subprocess.Popen(
                    [executable],
                    cwd=os.path.dirname(executable),
                    close_fds=True,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=getattr(subprocess, "DETACHED_PROCESS", 0),
                )
                started = True
            except OSError as e:
                safe_log(f"重启程序回退启动失败: {e}")

        safe_log(f"重启程序: {executable} 启动结果 {started}")
        if not started:
            DialogUtils.show_error(DialogUtils.parent_widget(), "重启失败", f"无法启动程序：\n{executable}\n\n请手动重新打开。")
            return
    else:
        # 开发环境用当前解释器重新启动入口脚本
        try:
            subprocess.Popen([sys.executable] + sys.argv)
        except Exception as e:
            safe_log(f"重启程序失败: {e}")
            DialogUtils.show_error(DialogUtils.parent_widget(), "重启失败", f"无法重启程序：\n{e!s}")
            return

    # 等新进程起来再结束当前进程
    time.sleep(0.5)
    sys.exit(0)

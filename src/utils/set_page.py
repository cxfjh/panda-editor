import os
import shutil
import subprocess
import sys
import time
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

    try:
        _remove_config_dir()
        svc = get_config_service()
        svc._initialized = False  # 允许重新初始化
        svc.init_config()
        DialogUtils.show_info(DialogUtils.parent_widget(), "重置成功", "程序已重置，即将重启！")
        restart_program()
    except Exception as e:
        DialogUtils.show_error(DialogUtils.parent_widget(), "重置失败", f"错误信息：{e!s}\n\n请尝试使用管理员身份运行！")


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


def restart_program() -> None:
    """重启程序"""
    try:
        main_module = sys.modules.get("__main__")
        if getattr(sys, "frozen", False) or hasattr(main_module, "__compiled__"):
            # 编译环境直接启动当前可执行文件
            subprocess.Popen([sys.argv[0]])
        else:
            # 开发环境用当前解释器重新启动入口脚本
            subprocess.Popen([sys.executable] + sys.argv)
    except Exception as e:
        DialogUtils.show_error(DialogUtils.parent_widget(), "重启失败", f"无法重启程序：\n{e}")
        return

    # 等待重启完成
    time.sleep(0.3)
    sys.exit(0)

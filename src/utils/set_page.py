import os
import psutil
import shutil
import subprocess
from tkinter import messagebox
from src.utils.config import read_config, init_config


# 获取程序根目录
def _get_root_path() -> str | None:
    """获取程序根目录"""
    root = read_config("FileConfig.json", "Root")
    if not root:
        messagebox.showerror("错误", "未获取到程序根目录！")
        return None
    return root


# 重置程序
def reset_program() -> None:
    """重置程序：删除配置 → 初始化 → 重启"""
    root = _get_root_path()
    if not root: return
    config_dir = os.path.join(root, "src", "config")
    if messagebox.askquestion("重置程序", "确定要重置程序吗？") != "yes": return
    try:
        # 删除配置目录
        if os.path.exists(config_dir): shutil.rmtree(config_dir)

        # 重新初始化
        init_config()
        messagebox.showinfo("重置成功", "程序已重置，即将重启！")

        # 重启
        restart_program()
    except Exception as e:
        messagebox.showerror("重置失败", f"错误信息：{str(e)}\n\n请尝试使用管理员身份运行！")


# 卸载程序
def uninstall_program() -> None:
    """调用卸载程序执行卸载"""
    root = _get_root_path()
    if not root: return
    if messagebox.askquestion("卸载程序", "确定要卸载程序吗？") != "yes": return
    try:
        uninstaller = os.path.join(root, "uninst.exe")
        if not os.path.exists(uninstaller):
            messagebox.showerror("卸载失败", "未找到卸载程序：uninst.exe")
            return
        subprocess.run(uninstaller, check=True)  # 执行卸载
    except Exception as e:
        messagebox.showerror("卸载失败", f"错误信息：{str(e)}\n\n请尝试使用管理员身份运行！", )


# 重启程序
def restart_program() -> None:
    """安全关闭当前进程"""
    try:
        current_pid = os.getpid()
        proc = psutil.Process(current_pid)
        proc.kill()
    except Exception as e:
        print(e)

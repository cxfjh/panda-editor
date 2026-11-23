import os
import shutil
import subprocess
import threading
from src.utils.code_proc.config import apply_file_path, get_config
from src.utils.code_proc.signals import signals
from src.utils.code_proc.translate import parse_code
from src.utils.config_service import get_config_service
from src.utils.exceptions import safe_log


# 编译任务互斥锁防止并发编译竞态
_compile_lock = threading.Lock()


def _clean_build_files(work_dir: str, code_name: str) -> None:
    """
    清理 PyInstaller 生成的临时文件

    Args:
        work_dir: 项目工作目录
        code_name: 当前的入口文件名不含扩展名
    """
    try:
        # 删除 build 目录
        build_path = os.path.join(work_dir, "build")
        if os.path.isdir(build_path): shutil.rmtree(build_path)

        # 只删本次生成的 .spec, 用户自己的 spec 不能被误删
        spec_path = os.path.join(work_dir, f"{code_name}.spec")
        if os.path.isfile(spec_path): os.remove(spec_path)
    except Exception as e:
        safe_log(f"清理编译临时文件失败: {e!s}")
        signals.error.emit("清理异常", f"清理临时文件失败：\n{e!s}", "")


def _resolve_icon(config: dict, code_dir: str) -> str | None:
    """
    按配置决定打包图标

    Args:
        config: 路径配置
        code_dir: 入口文件所在目录

    Returns:
        图标路径, 没有可用图标时返回 None
    """
    local_icon = os.path.join(code_dir, "icon.ico")
    fallback = config.get("icon_path")
    if get_config_service().get_personal_config("useDefaultCompileIcon"):
        # 默认图标优先项目目录下的 icon.ico 其次配置中的 icon_path
        return local_icon if os.path.isfile(local_icon) else fallback

    custom_icon = get_config_service().get_personal_config("compileIconPath")
    if custom_icon and os.path.isfile(custom_icon):
        return custom_icon
    if os.path.isfile(local_icon):
        return local_icon
    return fallback


def _build_command(config: dict, base_name: str, single_file: bool, icon_path: str | None) -> list:
    """
    拼出 PyInstaller 命令行

    Args:
        config: 路径配置
        base_name: 输出名称
        single_file: True 表示单文件模式
        icon_path: 图标路径

    Returns:
        命令行参数列表
    """
    cmd = [
        config["python_dir"], "-m", "PyInstaller",
        "-F" if single_file else "-D",
        f"--name={base_name}",
        f"--distpath={config['source_code_path']}",
        "--log-level=INFO",
    ]

    if icon_path and os.path.isfile(icon_path):
        cmd.append(f"-i{icon_path}")

    if get_config_service().get_personal_config("hideWindow"):
        cmd.append("-w")

    if get_config_service().get_personal_config("adminPrivilege"):
        cmd.append("--uac-admin")

    # 添加资源文件与目录, 文件直接放到打包根目录, 目录保留其目录名
    for data_path in get_config_service().get_personal_config("addDataPaths") or []:
        if os.path.exists(data_path):
            target_dir = "." if os.path.isfile(data_path) else os.path.basename(data_path)
            cmd.append(f"--add-data={data_path}{os.pathsep}{target_dir}")

    cmd.append(config["code_path"])
    return cmd


def _move_dist_files(source_code_path: str, base_name: str) -> None:
    """
    目录模式下把子目录里的产物移到源码目录

    Args:
        source_code_path: 源码目录
        base_name: 输出名称
    """
    dist_subdir = os.path.join(source_code_path, base_name)
    if not os.path.isdir(dist_subdir):
        return

    for item in os.listdir(dist_subdir):
        src_item = os.path.join(dist_subdir, item)
        dst_item = os.path.join(source_code_path, item)
        if os.path.exists(dst_item):
            # 同名内容先备份再覆盖, 避免误删用户已有文件
            backup_item = f"{dst_item}.bak"
            try:
                if os.path.isdir(backup_item):
                    shutil.rmtree(backup_item)
                elif os.path.exists(backup_item):
                    os.remove(backup_item)
                os.replace(dst_item, backup_item)
                signals.compile_log.emit(f"已备份同名文件: {backup_item}")
            except OSError as e:
                safe_log(f"编译输出备份同名文件失败: {e}")
                signals.compile_log.emit(f"备份 {dst_item} 失败, 跳过: {e}")
                continue
        shutil.move(src_item, dst_item)

    shutil.rmtree(dist_subdir)


def _compile_thread(file_path: str | None) -> None:
    """
    PyInstaller 打包线程任务

    Args:
        file_path: 编译时指定的 .cn 文件路径
    """
    try:
        config = get_config()
        if not config:
            safe_log("编译配置缺失, 已取消编译")
            signals.error.emit("配置错误", "缺少必要配置，无法编译！", "")
            return

        config = apply_file_path(config, file_path)
        code_dir = os.path.dirname(config["code_path"])
        single_file = get_config_service().get_personal_config("singleFileMode")
        base_name = os.path.splitext(os.path.basename(config["code_path"]))[0]

        cmd = _build_command(config, base_name, single_file, _resolve_icon(config, code_dir))  # type: ignore
        signals.compile_log.emit(f"开始编译: {os.path.basename(config['code_path'])}")

        process = subprocess.Popen(
            cmd,
            cwd=config["source_code_path"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        # 实时转发编译日志
        if process.stdout:
            for log_line in process.stdout:
                stripped_log = log_line.rstrip()
                if stripped_log:
                    signals.compile_log.emit(stripped_log)

        process.wait()

        if process.returncode == 0:
            if not single_file:
                _move_dist_files(config["source_code_path"], base_name)

            subprocess.Popen(["explorer", config["source_code_path"]])
            _clean_build_files(config["source_code_path"], base_name)
            signals.compile_finished.emit(True, "")
        else:
            safe_log(f"编译失败, 退出码 {process.returncode}, 入口 {config['code_path']}")
            signals.compile_finished.emit(False, f"编译失败（退出码: {process.returncode}）")

    except Exception as e:
        safe_log(f"打包异常: {e!s}")
        signals.compile_finished.emit(False, f"打包失败：\n{e!s}")
    finally:
        _compile_lock.release()  # 无论成功失败都释放编译锁


def compile_code(text_code: str, file_path: str | None = None) -> None:
    """
    编译代码入口函数

    Args:
        text_code: 中文代码文本
        file_path: 当前 .cn 文件路径
    """

    # 防止并发编译已有编译任务时直接提示
    if not _compile_lock.acquire(blocking=False):
        signals.error.emit("正在编译", "已有编译任务正在进行，请等待完成后再试。", "")
        return

    if parse_code(text_code, file_path):
        try:
            thread = threading.Thread(target=_compile_thread, args=(file_path,), daemon=True)
            thread.start()
        except RuntimeError as e:
            # 线程创建失败时释放锁, 否则后续编译会一直被拒绝
            _compile_lock.release()
            safe_log(f"启动编译线程失败: {e}")
            signals.error.emit("编译失败", f"无法启动编译线程：\n{e}", "")
    else:
        _compile_lock.release()  # 解析失败未启动线程立即释放锁

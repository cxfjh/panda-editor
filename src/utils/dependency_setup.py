import json
import os
import re
import subprocess
import time
from functools import partial
from typing import Callable
from PySide6 import QtWidgets
from PySide6.QtCore import Qt, QThread, QTimer, Signal
from src.utils.dialog_utils import DialogUtils
from src.utils.config_service import get_config_service, is_compiled
from src.utils.exceptions import safe_log
from src.utils.tray_notice import show_tray_message


# 依赖清单文件名, 固定放在解释器同目录
MANIFEST_NAME = "requirements.txt"

# 安装依赖时使用的镜像源
MIRROR_URL = "https://mirrors.aliyun.com/pypi/simple/"

# 单次 pip 安装允许的最长耗时, 单位秒
INSTALL_TIMEOUT = 1800

# 安装失败时写进日志的尾部输出行数
_TAIL_LINES = 5

# 进度条走满后停留的时长, 单位毫秒
_CLOSE_DELAY = 250

# 依赖清单里的包名, 忽略版本约束与 extras
_RE_NAME = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)")

# 行内注释
_RE_COMMENT = re.compile(r"(^|\s)#.*$")

# 依赖写法里锁定的版本
_RE_PIN = re.compile(r"==\s*([^\s,;]+)")


def normalize_name(name: str) -> str:
    """
    把包名规范成可以互相比较的写法

    Args:
        name: 原始包名, 如 pyside6_scintilla

    Returns:
        小写并把点线统一成横线的包名
    """
    return re.sub(r"[-_.]+", "-", str(name)).lower()


def parse_requirements(path: str) -> list[tuple[str, str]]:
    """
    读取依赖清单里声明的包

    Args:
        path: 依赖清单文件路径

    Returns:
        规范化包名与安装写法的二元组列表, 安装写法保留清单里的版本约束
    """
    items: list[tuple[str, str]] = []
    seen: set[str] = set()
    try:
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                text = _RE_COMMENT.sub("", line).strip()
                if not text or text.startswith("-"):
                    continue
                match = _RE_NAME.match(text)
                if not match:
                    continue
                name = normalize_name(match.group(1))
                if name in seen:
                    continue
                seen.add(name)
                items.append((name, text))
    except OSError as e:
        safe_log(f"读取依赖清单失败: {e}")
    return items


def installed_packages(python_path: str) -> dict[str, str]:
    """
    取目标解释器里已经装好的包

    Args:
        python_path: 目标 Python 解释器路径

    Returns:
        规范化包名到版本的映射, 查询失败时返回空字典
    """
    args = [python_path, "-m", "pip", "list", "--format=json", "--disable-pip-version-check"]
    try:
        result = subprocess.run(
            args, capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=120,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        data = json.loads(result.stdout or "[]")
        found: dict[str, str] = {}
        for item in data:
            name = item.get("name") or ""
            if name:
                found[normalize_name(name)] = str(item.get("version", ""))
        return found
    except Exception as e:
        safe_log(f"查询已安装依赖失败: {e}")
        return {}


def pinned_version(spec: str) -> str:
    """
    取依赖写法里锁定的版本

    Args:
        spec: 依赖写法, 如 altgraph==0.17.5

    Returns:
        版本号, 没有锁定版本时返回空字符串
    """
    match = _RE_PIN.search(spec)
    return match.group(1) if match else ""


def needed_packages(required: list[tuple[str, str]], installed: dict[str, str]) -> list[str]:
    """
    挑出没装或者版本对不上的依赖

    Args:
        required: 依赖清单解析结果
        installed: 已安装的包名与版本

    Returns:
        需要交给 pip 的安装写法列表
    """
    todo: list[str] = []
    for name, spec in required:
        current = installed.get(name)
        if current is None:
            todo.append(spec)
            continue
        pinned = pinned_version(spec)
        if pinned and current != pinned:
            safe_log(f"依赖版本不一致: {name} 当前 {current}, 清单要求 {pinned}", "debug")
            todo.append(spec)
    return todo


def find_manifest(python_path: str) -> str:
    """
    取依赖清单文件路径, 清单与解释器固定在同一目录

    Args:
        python_path: 目标 Python 解释器路径

    Returns:
        清单路径, 解释器同级没有清单时返回空字符串
    """
    path = os.path.join(os.path.dirname(python_path), MANIFEST_NAME)
    return path if os.path.isfile(path) else ""


def _local_ratio(text: str) -> float:
    """
    按 pip 输出阶段估算单包内部进度

    Args:
        text: pip 的一行输出

    Returns:
        0 到 1 的包内进度
    """
    if text.startswith("Successfully installed"):
        return 0.7
    if text.startswith("Installing collected packages"):
        return 0.55
    if text.startswith("Downloading") or text.startswith("Using cached"):
        return 0.4
    if text.startswith("Collecting"):
        return 0.2
    return 0.1


def _install_one(python_path: str, package: str, progress=None) -> bool:
    """
    安装单个包, pip 输出逐行回传

    Args:
        python_path: 目标 Python 解释器路径
        package: 单个包的安装写法
        progress: 进度回调, 接收 pip 的一行输出与包内 0 到 1 的进度, 可以为 None

    Returns:
        True 表示这个包装成功
    """
    args = [
        python_path, "-m", "pip", "install", "--disable-pip-version-check",
        "--progress-bar", "off", "-i", MIRROR_URL, package,
    ]

    try:
        process = subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            encoding="utf-8", errors="ignore", bufsize=1,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception as e:
        safe_log(f"启动 pip 失败: {e}")
        return False

    if process.stdout is None:
        safe_log("读取 pip 输出失败")
        return False

    tail: list[str] = []
    deadline = time.monotonic() + INSTALL_TIMEOUT
    for line in process.stdout:
        text = line.strip()
        if text:
            tail.append(text)
            if len(tail) > _TAIL_LINES:
                tail.pop(0)
            if progress:
                progress(text, _local_ratio(text))
        if time.monotonic() > deadline:
            process.kill()
            safe_log(f"安装 {package} 超时, 已终止 pip")
            return False

    if process.wait() != 0:
        safe_log(f"安装 {package} 失败: {' / '.join(tail)}")
        return False

    return True


def _scaled(progress, base: float, span: float, text: str, ratio: float) -> None:
    """
    把单个包的内部进度换算成整体进度

    Args:
        progress: 整体进度回调
        base: 这个包在整体里的起始进度
        span: 这个包占据的进度区间
        text: pip 的一行输出
        ratio: 这个包内部的 0 到 1 进度
    """
    if progress:
        progress(text, base + span * ratio)


def install_packages(python_path: str, packages: list[str], progress=None) -> bool:
    """
    逐个安装缺少的包, 每装完一个推进一次进度

    Args:
        python_path: 目标 Python 解释器路径
        packages: 安装写法列表, 可以带版本约束
        progress: 进度回调, 接收提示文本与 0 到 1 的进度, 可以为 None

    Returns:
        True 表示全部安装成功
    """
    total = len(packages)
    if not total:
        return True

    for index, package in enumerate(packages):
        base = 0.1 + 0.85 * index / total
        span = 0.85 / total

        if progress:
            progress(f"正在安装 {package}", base)

        if not _install_one(python_path, package, partial(_scaled, progress, base, span)):
            return False

        if progress:
            progress(f"已完成 {index + 1} 个, 共 {total} 个", base + span)

    safe_log(f"依赖安装完成: {'，'.join(packages)}")
    return True


def ensure_runtime_dependencies(progress=None) -> bool:
    """
    按依赖清单补齐目标解释器缺少的库

    Args:
        progress: 进度回调, 接收提示文本与 0 到 1 的进度, 可以为 None

    Returns:
        True 表示依赖齐全或安装成功, False 表示仍有缺失
    """
    python_path = get_config_service().get_app_config("python_path") or ""
    if not python_path or not os.path.isfile(python_path):
        return True

    manifest = find_manifest(python_path)
    if not manifest:
        safe_log("解释器同级没有依赖清单, 跳过自动安装", "warning")
        return True

    required = parse_requirements(manifest)
    if not required:
        return True

    if progress:
        progress("正在检查已安装的依赖", 0.05)
    installed = installed_packages(python_path)
    if not installed:
        safe_log("查询已安装依赖失败, 跳过自动安装")
        return False

    todo = needed_packages(required, installed)
    if not todo:
        safe_log("Python 依赖齐全")
        if progress:
            progress("Python 依赖齐全", 1.0)
        return True

    if progress:
        progress(f"正在安装 {len(todo)} 个依赖, 请稍候", 0.1)

    ok = install_packages(python_path, todo, progress)
    if ok and progress:
        progress("依赖安装完成", 1.0)
    return ok


class DependencyWorker(QThread):
    """在后台线程补齐依赖, 避免阻塞主窗口"""

    progressed = Signal(str, float)  # 当前进度提示与 0 到 1 的进度
    completed = Signal(object)  # True 依赖就绪, False 安装失败, None 没网跳过

    def __init__(self, network_check: Callable[[], bool], parent=None):
        """
        初始化后台任务

        Args:
            network_check: 网络探测函数, 返回 True 表示有网络
            parent: Qt 父对象, 由它接管线程生命周期
        """
        super().__init__(parent)
        self._network_check = network_check

    def run(self) -> None:
        """探测网络并补齐依赖, 结果通过信号交回主线程"""
        if not self._network_check():
            safe_log("当前没有网络, 跳过首次启动的依赖安装", "warning")
            self.completed.emit(None)
            return

        try:
            self.completed.emit(ensure_runtime_dependencies(self.progressed.emit))
        except Exception as e:
            safe_log(f"首次启动依赖准备异常: {e}")
            self.completed.emit(False)


def _update_progress(dialog, text: str, ratio: float) -> None:
    """
    把提示文本与进度刷到进度框

    Args:
        dialog: 进度框
        text: pip 或流程给出的一行提示, 过长时截断避免撑宽窗口
        ratio: 0 到 1 的进度, 换算成百分比后给进度条
    """
    dialog.setLabelText(text.strip()[:70])
    dialog.setValue(int(ratio * 100))


def _close_dialog(dialog) -> None:
    """
    关闭并释放进度框

    Args:
        dialog: 进度框
    """
    dialog.close()
    dialog.deleteLater()


def _finish_setup(dialog, manager, result) -> None:
    """
    关闭进度框并给出结果提示

    Args:
        dialog: 进度框
        manager: 配置服务, 用于写首次启动标记
        result: True 表示依赖就绪, False 表示安装失败, None 表示没网跳过
    """
    # 装完先把进度条走满再停一下, 关得太快会像没跑完
    if result:
        dialog.setValue(100)
        QTimer.singleShot(_CLOSE_DELAY, partial(_close_dialog, dialog))
    else:
        _close_dialog(dialog)

    # 没网时装也装不上, 不写首次标记, 下次联网启动还能自动重试
    if result is None:
        show_tray_message("当前没有网络连接, 首次启动的依赖安装已跳过, 联网后重启会自动补齐")
        return

    # 装不上也写下标记, 免得每次启动都卡在这里, 失败原因已进日志
    manager.update_app_config("first_run", False)
    if not result:
        DialogUtils.show_warning(
            DialogUtils.parent_widget(),
            "依赖安装未完成",
            "部分 Python 库没有装上, 相关功能可能无法使用。\n详情见日志, 也可以稍后在终端里执行 pip install 重试。",
        )


def run_first_launch_setup(app, parent=None, network_check: Callable[[], bool] | None = None) -> DependencyWorker | None:
    """
    首次启动时在后台补齐依赖

    Args:
        app: Qt 应用实例, 作为后台线程的父对象
        parent: 进度框的父窗口, 可以为 None
        network_check: 网络探测函数, 不传时视为有网络

    Returns:
        已启动的后台任务, 脚本模式或不是首次启动时返回 None
    """
    # 脚本模式的依赖由开发者在环境里装好, 不走自动安装也不弹进度框
    if not is_compiled():
        return None

    manager = get_config_service()
    if not manager.get_app_config("first_run"):
        return None

    dialog = QtWidgets.QProgressDialog("正在检查网络, 请稍候", "", 0, 100, parent)
    dialog.setWindowTitle("正在安装环境依赖，请保持网络连接并耐心等待")
    dialog.setCancelButton(None)
    dialog.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
    dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
    dialog.setMinimumWidth(460)
    dialog.setMinimumDuration(0)
    dialog.setAutoClose(False)
    dialog.setAutoReset(False)
    dialog.setValue(0)

    worker = DependencyWorker(network_check or (lambda: True), app)
    worker.progressed.connect(partial(_update_progress, dialog))
    worker.completed.connect(partial(_finish_setup, dialog, manager))

    dialog.show()
    worker.start()
    return worker

import os
import shutil
import subprocess
import tempfile
from xml.etree import ElementTree
from src.utils.config_service import get_config_service
from src.utils.dialog_utils import DialogUtils
from src.utils.exceptions import safe_log
from src.views.components.handlers.base import HandlerBase


def _identifier(text: str) -> str:
    """
    把文本清洗成可用的 Python 标识符

    Args:
        text: 待清洗的文本, 如 .ui 里的类名或部件名

    Returns:
        仅含字母 数字 下划线的标识符, 无法清洗时返回空字符串
    """
    cleaned = "".join(char if char.isalnum() or char == "_" else "_" for char in (text or "").strip())
    if not cleaned or cleaned[0].isdigit():
        return ""
    return cleaned


class UiToolActions(HandlerBase):
    """界面设计器与 ui 转换动作"""

    def on_compile_ui(self):
        """
        把当前的 .ui 文件转换成同名的 .cn 文件

        Args:
            self: 类实例自身
        """
        ui_path = self.ui.tab_manager.get_current_file_path() or ""
        if not ui_path.lower().endswith(".ui"):
            DialogUtils.show_warning(self.ui.main_window, "无法编译", "请先打开一个 .ui 界面文件。")
            return

        if not os.path.isfile(ui_path):
            DialogUtils.show_warning(self.ui.main_window, "无法编译", f"文件不存在：\n{ui_path}")
            return

        uic = self._pyside_tool_path("pyside6-uic.exe")
        if not uic or not os.path.isfile(uic):
            safe_log(f"找不到 uic 转换工具: {uic or '未配置程序根目录'}")
            DialogUtils.show_error(self.ui.main_window, "编译失败", f"找不到 uic 转换工具：\n{uic or '未配置程序根目录'}")
            return

        py_code = self._run_uic(uic, ui_path)
        if py_code is None:
            return

        # 末尾补上入口, 生成的文件直接点运行就能看到窗口
        py_code = py_code.rstrip() + self._ui_main_block(ui_path)

        target = self._unique_ui_output(ui_path)
        try:
            with open(target, "w", encoding="utf-8") as handle:
                handle.write(py_code)
        except OSError as e:
            safe_log(f"写入 {target} 失败: {e}")
            DialogUtils.show_error(self.ui.main_window, "编译失败", f"无法写入文件：\n{target}\n{e}")
            return

        # 生成完直接打开, 用户能立刻看到转换结果
        self.ui.open_file(target)

    def _run_uic(self, uic: str, ui_path: str) -> str | None:
        """
        调用 uic 把界面文件转成 Python 代码

        Args:
            self: 类实例自身
            uic: uic 工具路径
            ui_path: 待转换的 .ui 文件路径

        Returns:
            生成的 Python 代码, 失败时返回 None
        """
        temp_dir = tempfile.mkdtemp(prefix="panda_uic_")
        temp_file = os.path.join(temp_dir, "ui_output.py")
        try:
            process = subprocess.run(
                [uic, ui_path, "-o", temp_file],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
                env=self._uic_env(uic),
            )
            if process.returncode != 0:
                detail = (process.stderr or process.stdout or "").strip() or f"退出码 {process.returncode}"
                safe_log(f"uic 转换 {ui_path} 失败: {detail}")
                DialogUtils.show_error(self.ui.main_window, "编译失败", f"uic 转换失败：\n{detail}")
                return None

            if not os.path.isfile(temp_file):
                safe_log(f"uic 未生成输出文件: {temp_file}")
                DialogUtils.show_error(self.ui.main_window, "编译失败", "uic 没有生成输出文件。")
                return None

            with open(temp_file, "r", encoding="utf-8", errors="replace") as handle:
                return handle.read()
        except subprocess.TimeoutExpired:
            safe_log(f"uic 转换 {ui_path} 超时")
            DialogUtils.show_error(self.ui.main_window, "编译失败", "uic 转换超时，请检查界面文件是否过大。")
            return None
        except OSError as e:
            safe_log(f"运行 uic 失败: {e}")
            DialogUtils.show_error(self.ui.main_window, "编译失败", f"无法运行 uic：\n{e}")
            return None
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @staticmethod
    def _unique_ui_output(ui_path: str) -> str:
        """
        生成不重名的 .cn 输出路径, 重名时依次加序号

        Args:
            ui_path: .ui 文件路径

        Returns:
            可用的 .cn 文件路径
        """
        base = os.path.splitext(ui_path)[0]
        candidate = base + ".cn"
        index = 1
        while os.path.exists(candidate):
            candidate = f"{base}_{index}.cn"
            index += 1
        return candidate

    @staticmethod
    def _ui_main_block(ui_path: str) -> str:
        """
        读取界面文件的根部件与类名, 生成可直接运行的启动代码

        Args:
            ui_path: .ui 文件路径

        Returns:
            追加到转换结果末尾的代码, 读取失败时返回空字符串
        """
        try:
            root = ElementTree.parse(ui_path).getroot()
        except (ElementTree.ParseError, OSError) as e:
            safe_log(f"读取界面文件失败, 跳过启动代码: {e}")
            return ""

        class_node = root.find("class")
        ui_class = _identifier(class_node.text if class_node is not None else "")  # type: ignore

        # uic 的类名是 Ui_ 加上 class 节点的内容, 缺失时退回文件名
        if not ui_class:
            ui_class = _identifier(os.path.splitext(os.path.basename(ui_path))[0]) or "Form"

        # 根部件的 class 决定要实例化哪个容器, QWidget 之外的窗口必须对得上
        widget_node = root.find("widget")
        widget_class = _identifier(widget_node.get("class", "") if widget_node is not None else "") or "QWidget"

        return (
            "\n\nif __name__ == \"__main__\":\n"
            "    import sys\n"
            "    app = QApplication(sys.argv)\n"
            "    widget = %s()\n"
            "    ui = Ui_%s()\n"
            "    ui.setupUi(widget)\n"
            "    widget.show()\n"
            "    sys.exit(app.exec())\n"
        ) % (widget_class, ui_class)

    def on_open_gui_designer(self):
        """
        打开 Qt Designer 编辑界面文件

        Args:
            self: 类实例自身
        """
        designer = self._pyside_tool_path("designer.exe")
        if not designer:
            DialogUtils.show_error(self.ui.main_window, "打开失败", "未配置程序根目录，无法定位 Qt Designer。")
            return

        if not os.path.isfile(designer):
            safe_log(f"找不到 Qt Designer: {designer}")
            DialogUtils.show_error(self.ui.main_window, "打开失败", f"找不到 Qt Designer：\n{designer}")
            return

        # 当前正在编辑 .ui 时直接带过去, 省得在 Designer 里再找一遍
        args = [designer]
        current = self.ui.tab_manager.get_current_file_path() or ""
        if current.lower().endswith(".ui") and os.path.isfile(current):
            args.append(current)

        try:
            subprocess.Popen(args)
        except OSError as e:
            safe_log(f"启动 Qt Designer 失败: {e}")
            DialogUtils.show_error(self.ui.main_window, "打开失败", f"无法启动 Qt Designer：\n{e}")

    @staticmethod
    def _pyside_tool_dir() -> list:
        """
        按优先级列出 PySide6 工具所在目录, 安装版与开发版各有一套

        Returns:
            目录列表, 设计器在包目录下 uic 在 Scripts 下, 未配置程序根目录时为空列表
        """
        root = get_config_service().get_app_config("root_dir") or ""
        if not root:
            return []
        return [
            os.path.join(root, "Lib", "site-packages", "PySide6"),
            os.path.join(root, "Scripts"),
            os.path.join(root, "Environment", "Lib", "site-packages", "PySide6"),
            os.path.join(root, "Environment", "Scripts"),
        ]

    @classmethod
    def _pyside_tool_path(cls, name: str) -> str:
        """
        按目录顺序找 PySide6 自带工具

        Args:
            cls: 类自身
            name: 工具文件名

        Returns:
            第一个存在的完整路径, 都找不到时返回首选组合便于提示
        """
        directories = cls._pyside_tool_dir()
        if not directories:
            return ""
        for directory in directories:
            path = os.path.join(directory, name)
            if os.path.isfile(path):
                return path
        return os.path.join(directories[0], name)

    @staticmethod
    def _uic_env(uic: str) -> dict:
        """
        构造 uic 需要的运行环境, Scripts 下的 pyside6-uic.exe 是 Python 入口脚本

        Args:
            uic: uic 工具路径

        Returns:
            补好 PATH 与 PYTHONPATH 的环境变量字典, 不补时 uic 找不到 PySide6 包
        """
        env = os.environ.copy()

        # Scripts 的上一级就是运行时根目录, 包在同级 Lib/site-packages 下
        env_root = os.path.dirname(os.path.dirname(os.path.abspath(uic)))
        site_packages = os.path.join(env_root, "Lib", "site-packages")

        if os.path.isdir(site_packages):
            env["PYTHONPATH"] = site_packages + os.pathsep + env.get("PYTHONPATH", "")
        if os.path.isdir(env_root):
            env["PATH"] = env_root + os.pathsep + env.get("PATH", "")
        return env

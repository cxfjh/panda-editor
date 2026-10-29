import os
from PySide6.QtGui import QColor, QLinearGradient, QPainter
from src.utils.config_service import get_config_service
from src.utils.dialog_utils import DialogUtils


def paint_gradient(widget, gradient_colors: list[str], gradient_alpha: float = 0.85) -> None:
    """
    绘制水平渐变背景

    Args:
        widget: Qt 控件实例
        gradient_colors: 渐变色列表
        gradient_alpha: 透明度
    """
    painter = QPainter(widget)  # 创建 QPainter 对象
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 创建水平线性渐变
    gradient = QLinearGradient(0, 0, widget.width(), 0)
    for i, color_hex in enumerate(gradient_colors):
        color = QColor(color_hex)  # 将十六进制颜色转换为 QColor
        color.setAlphaF(gradient_alpha)

        # 计算颜色位置
        gradient.setColorAt(i / max(len(gradient_colors) - 1, 1), color)

    # 用渐变填充控件矩形区域
    painter.fillRect(widget.rect(), gradient)
    painter.end()


def _get_file_dir() -> str:
    """
    获取扩展库目录路径

    Returns:
        扩展库目录的完整路径若配置缺失或目录不存在则返回空字符串
    """
    root_path = get_config_service().get_app_config("root_dir")
    if not root_path: return ""
    file_dir = os.path.join(root_path, "File")
    if not os.path.isdir(file_dir):
        if DialogUtils.parent_widget() is not None:
            DialogUtils.show_warning(DialogUtils.parent_widget(), "目录不存在", f"扩展库目录不存在：\n{file_dir}")
        return ""
    return file_dir


def _iter_py_files(file_dir: str):
    """
    遍历目录下所有 .py 文件

    Args:
        file_dir: 要遍历的目录路径

    Returns:
        生成器, 逐个产出文件名与文件完整路径组成的元组
    """
    for filename in os.listdir(file_dir):
        if filename.endswith(".py"):
            yield filename, os.path.join(file_dir, filename)


def extend_library(directory: dict) -> None:
    """
    加载扩展库文件内容

    Args:
        directory: 用于存储扩展库内容的字典将被原地修改
    """
    file_dir = _get_file_dir()
    if not file_dir: return
    for filename, file_path in _iter_py_files(file_dir):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lib_name = os.path.splitext(filename)[0]
                directory[lib_name] = f.read()
        except Exception as e:
            DialogUtils.show_error(DialogUtils.parent_widget(), "加载失败", f"文件 {filename} 加载失败：\n{e}")

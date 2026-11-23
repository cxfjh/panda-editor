from PySide6.QtCore import QObject, Signal
from src.utils.dialog_utils import DialogUtils


class DialogSignals(QObject):
    """跨线程弹窗信号类"""
    error = Signal(str, str, str)
    compile_finished = Signal(bool, str)
    compile_log = Signal(str)  # 编译日志输出信号


# 全局信号实例
signals = DialogSignals()


def _on_error(title: str, msg: str, detail: str) -> None:
    """
    错误弹窗槽函数

    Args:
        title: 弹窗标题
        msg: 错误消息
        detail: 详细错误信息
    """
    DialogUtils.show_error(DialogUtils.parent_widget(), title, msg, detail)


signals.error.connect(_on_error)

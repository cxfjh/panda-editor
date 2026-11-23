from PySide6 import QtCore


class BlocklyBridge(QtCore.QObject):
    """Blockly 页面与 Python 之间的 QWebChannel 通信对象"""

    # Python 侧下发指令
    load_workspace_requested = QtCore.Signal(str)
    clear_workspace_requested = QtCore.Signal()
    workspace_requested = QtCore.Signal()
    generate_requested = QtCore.Signal()
    theme_changed = QtCore.Signal(bool)
    palette_pinned_changed = QtCore.Signal(bool)

    # 页面回传结果
    page_ready = QtCore.Signal()
    code_submitted = QtCore.Signal(str)
    workspace_submitted = QtCore.Signal(str)
    status_reported = QtCore.Signal(str)
    notice_reported = QtCore.Signal(str)

    @staticmethod
    def _defer(signal, *args):
        """
        延后一拍再发出信号

        Args:
            signal: 待发出的信号
            args: 信号参数
        """
        QtCore.QTimer.singleShot(0, lambda: signal.emit(*args))

    @QtCore.Slot()
    def notify_ready(self):
        """
        页面脚本初始化完成

        Args:
            self: 类实例自身
        """
        self._defer(self.page_ready)

    @QtCore.Slot(str)
    def submit_code(self, code: str):
        """
        页面回传生成的 CnLang 代码

        Args:
            code: 生成的代码文本, 工作区为空时为空字符串
        """
        self._defer(self.code_submitted, code)

    @QtCore.Slot(str)
    def submit_workspace_xml(self, xml: str):
        """
        页面回传工作区 XML

        Args:
            xml: Blockly 原生 XML 文本
        """
        self._defer(self.workspace_submitted, xml)

    @QtCore.Slot(str)
    def report_status(self, message: str):
        """
        页面回传状态信息

        Args:
            message: 供状态标签显示的中文提示
        """
        self._defer(self.status_reported, message)

    @QtCore.Slot(str)
    def report_notice(self, message: str):
        """
        页面回传需要停留较久的提示

        Args:
            message: 提示文本
        """
        self._defer(self.notice_reported, message)

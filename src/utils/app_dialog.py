from PySide6 import QtCore, QtWidgets
from src.utils import theme


# 各类提示图标使用的字符与颜色键
_ICON_GLYPH = {
    "info": ("ℹ️", "accent"),
    "warning": ("⚠️", "brace_bad"),
    "error": ("❌", "brace_bad"),
    "question": ("❓", "accent"),
}


def _dialog_style(dark_mode: bool) -> str:
    """
    生成弹窗整体样式

    Args:
        dark_mode: True 为暗夜模式, False 为浅色模式

    Returns:
        可直接设置到弹窗的样式表
    """
    c = theme.colors(dark_mode)
    return f"""
            QDialog {{
                background-color: {c['panel_bg']};
                border: 1px solid {c['border_strong']};
            }}
            QWidget#DialogTitleBar {{
                background-color: {c['menu_bg']};
                border-bottom: 1px solid {c['border']};
            }}
            QLabel#DialogTitleLabel {{
                color: {c['fg_strong']};
                font-size: 14px;
            }}
            QPushButton#DialogCloseButton {{
                background-color: transparent;
                color: {c['fg']};
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }}
            QPushButton#DialogCloseButton:hover {{
                background-color: {c['danger_hover']};
                color: #FFFFFF;
            }}
            QLabel#DialogText {{
                color: {c['fg']};
                font-size: 13px;
            }}
            QLineEdit {{
                background-color: {c['input_bg']};
                color: {c['fg']};
                border: 1px solid {c['border']};
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {c['accent']};
            }}
            QPushButton {{
                background-color: {c['menu_bg']};
                color: {c['fg']};
                border: 1px solid {c['border']};
                border-radius: 6px;
                padding: 6px 18px;
                font-size: 13px;
                min-width: 68px;
            }}
            QPushButton:hover {{
                background-color: {c['hover']};
                border-color: {c['border_strong']};
                color: {c['fg_strong']};
            }}
            QPushButton:default {{
                background-color: {c['accent']};
                color: #FFFFFF;
                border: none;
            }}
            QPushButton:default:hover {{
                background-color: #6BAEEF;
            }}
        """


class DialogTitleBar(QtWidgets.QWidget):
    """自绘的弹窗标题栏, 负责标题显示与拖动窗口"""

    close_clicked = QtCore.Signal()

    def __init__(self, title: str = "", parent=None):
        """
        构造标题栏

        Args:
            title: 标题文字
            parent: 父控件
        """
        super().__init__(parent)
        self.setObjectName("DialogTitleBar")
        self.setFixedHeight(42)
        self._drag_pos = None
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 8, 0)
        layout.setSpacing(8)
        self.title_label = QtWidgets.QLabel(title, self)
        self.title_label.setObjectName("DialogTitleLabel")
        layout.addWidget(self.title_label)
        layout.addStretch(1)
        self.close_button = QtWidgets.QPushButton("✕", self)
        self.close_button.setObjectName("DialogCloseButton")
        self.close_button.setFixedSize(30, 26)
        self.close_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.close_button.setToolTip("关闭")
        self.close_button.clicked.connect(self.close_clicked)
        layout.addWidget(self.close_button)

    def mousePressEvent(self, event):
        """
        按住标题栏记录拖拽起点

        Args:
            event: 鼠标事件
        """
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """
        拖动标题栏时移动窗口

        Args:
            event: 鼠标事件
        """
        if self._drag_pos is not None and event.buttons() == QtCore.Qt.MouseButton.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        松开鼠标结束拖拽

        Args:
            event: 鼠标事件
        """
        self._drag_pos = None
        super().mouseReleaseEvent(event)


class AppDialog(QtWidgets.QDialog):
    """应用内自绘弹窗基类, 不使用系统边框"""

    def __init__(self, parent=None, title: str = "", dark_mode: bool = True):
        """
        构造无边框弹窗

        Args:
            parent: 父控件, 内部会换成它所在的最外层窗口
            title: 标题栏文字
            dark_mode: 是否使用深色主题
        """
        owner = parent.window() if parent is not None else None
        super().__init__(owner, QtCore.Qt.WindowType.Dialog | QtCore.Qt.WindowType.FramelessWindowHint)
        self._dark_mode = dark_mode
        self.setWindowTitle(title)
        self.setModal(True)
        self.setStyleSheet(_dialog_style(dark_mode))
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self.title_bar = DialogTitleBar(title, self)
        self.title_bar.close_clicked.connect(self.reject)
        outer.addWidget(self.title_bar)
        self.body = QtWidgets.QWidget(self)
        self.body.setObjectName("DialogBody")
        self.body_layout = QtWidgets.QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(20, 18, 20, 16)
        self.body_layout.setSpacing(14)
        outer.addWidget(self.body)

    def exec_centered(self) -> int:
        """
        居中显示并进入模态循环

        Returns:
            对话框 exec 的返回值
        """
        self.adjustSize()
        anchor = self._anchor_rect()
        if anchor is not None:
            center = anchor.center()
            self.move(center.x() - self.width() // 2, center.y() - self.height() // 2)
        return self.exec()

    def _anchor_rect(self) -> QtCore.QRect | None:
        """
        取用于居中的参考区域

        父窗口存在时按父窗口算, 否则退到当前活动窗口, 都没有就不挪位置

        Returns:
            参考区域, 无法确定时返回 None
        """
        parent = self.parentWidget()
        if parent is not None:
            return parent.window().frameGeometry()
        active = QtWidgets.QApplication.activeWindow()
        if active is not None:
            return active.frameGeometry()
        screen = QtWidgets.QApplication.primaryScreen()
        return screen.availableGeometry() if screen is not None else None


class MessageDialog(AppDialog):
    """提示与确认弹窗, 按钮文字与返回值由调用方指定"""

    def __init__(self, parent=None, title: str = "提示", text: str = "", icon: str = "info",
                 buttons: tuple[str, ...] = ("确定",), dark_mode: bool = True):
        """
        构造提示弹窗

        Args:
            parent: 父控件
            title: 标题栏文字
            text: 正文内容
            icon: 图标类型, info / warning / error / question
            buttons: 按钮文字, 第一个为默认按钮
            dark_mode: 是否使用深色主题
        """
        super().__init__(parent, title, dark_mode)
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(12)
        glyph, color_key = _ICON_GLYPH.get(icon, _ICON_GLYPH["info"])
        icon_label = QtWidgets.QLabel(glyph, self.body)
        icon_label.setFixedWidth(22)
        icon_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignHCenter)
        icon_label.setStyleSheet(f"color: {theme.colors(dark_mode)[color_key]}; font-size: 16px;")
        row.addWidget(icon_label)
        text_label = QtWidgets.QLabel(text, self.body)
        text_label.setObjectName("DialogText")
        text_label.setWordWrap(True)
        text_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        row.addWidget(text_label, 1)
        self.body_layout.addLayout(row)
        button_row = QtWidgets.QHBoxLayout()
        button_row.addStretch(1)
        self.clicked_button = ""
        for index, label in enumerate(buttons):
            button = QtWidgets.QPushButton(label, self.body)
            button.clicked.connect(lambda _checked=False, name=label: self._choose(name))
            if index == 0:
                button.setDefault(True)
            button_row.addWidget(button)
        self.body_layout.addLayout(button_row)

    def _choose(self, name: str) -> None:
        """
        记录点中的按钮并关闭弹窗

        Args:
            name: 按钮文字
        """
        self.clicked_button = name
        self.accept()


class InputDialog(AppDialog):
    """单行文本输入弹窗"""

    def __init__(self, parent=None, title: str = "", label: str = "", default: str = "", dark_mode: bool = True):
        """
        构造输入弹窗

        Args:
            parent: 父控件
            title: 标题栏文字
            label: 输入框上方的说明文字
            default: 输入框默认内容
            dark_mode: 是否使用深色主题
        """
        super().__init__(parent, title, dark_mode)
        self.text_value = ""
        hint = QtWidgets.QLabel(label, self.body)
        hint.setObjectName("DialogText")
        self.body_layout.addWidget(hint)
        self.edit = QtWidgets.QLineEdit(default, self.body)
        self.edit.selectAll()
        self.body_layout.addWidget(self.edit)
        button_row = QtWidgets.QHBoxLayout()
        button_row.addStretch(1)
        cancel_button = QtWidgets.QPushButton("取消", self.body)
        cancel_button.clicked.connect(self.reject)
        ok_button = QtWidgets.QPushButton("确定", self.body)
        ok_button.setDefault(True)
        ok_button.clicked.connect(self.accept)
        button_row.addWidget(cancel_button)
        button_row.addWidget(ok_button)
        self.body_layout.addLayout(button_row)

    def accept(self) -> None:
        """
        确认时记下输入内容

        Args:
            self: 类实例自身
        """
        self.text_value = self.edit.text()
        super().accept()


def show_message(parent=None, title: str = "提示", text: str = "", icon: str = "info", dark_mode: bool = True) -> None:
    """
    显示一条提示

    Args:
        parent: 父控件, 内部会换成它所在的最外层窗口
        title: 弹窗标题
        text: 正文内容
        icon: 图标类型, info / warning / error / question
        dark_mode: 是否使用深色主题
    """
    MessageDialog(parent, title, text, icon, ("确定",), dark_mode).exec_centered()


def ask_question(parent=None, title: str = "确认", text: str = "", dark_mode: bool = True) -> bool:
    """
    询问用户是否继续

    Args:
        parent: 父控件
        title: 弹窗标题
        text: 正文内容
        dark_mode: 是否使用深色主题

    Returns:
        True 表示点了"是"
    """
    dialog = MessageDialog(parent, title, text, "question", ("是", "否"), dark_mode)
    dialog.exec_centered()
    return dialog.clicked_button == "是"


def get_text(parent=None, title: str = "", label: str = "", default: str = "", dark_mode: bool = True) -> str | None:
    """
    弹窗让用户输入一行文本

    Args:
        parent: 父控件
        title: 弹窗标题
        label: 输入框上方的说明
        default: 默认内容
        dark_mode: 是否使用深色主题

    Returns:
        用户输入的文本, 取消时返回 None
    """
    dialog = InputDialog(parent, title, label, default, dark_mode)
    if dialog.exec_centered() == QtWidgets.QDialog.DialogCode.Accepted:
        return dialog.text_value
    return None

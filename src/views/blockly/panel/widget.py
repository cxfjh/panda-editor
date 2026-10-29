import os
from PySide6 import QtCore, QtGui
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
from src.utils import theme
from src.utils.config_service import get_config_service
from src.views.blockly.panel import styles
from src.views.blockly.panel.codegen import CodegenMixin
from src.views.blockly.panel.constants import CONFIG_TARGET_FILE
from src.views.blockly.panel.webview import WebViewMixin
from src.views.blockly.panel.workspace import WorkspaceMixin


class BlocklyPanel(WebViewMixin, WorkspaceMixin, CodegenMixin):
    """积木编程面板"""

    code_written = QtCore.Signal(str)  # 生成的代码已写入文件, 参数为文件路径

    def __init__(self, parent: QWidget | None = None, dark_mode: bool = True):
        """
        初始化积木编程面板

        Args:
            self: 当前面板实例
            parent: 父窗口部件
            dark_mode: 是否使用深色模式
        """
        super().__init__(parent)
        self.setObjectName("BlocklyPanel")
        self.setMinimumWidth(320)

        self._dark_mode = dark_mode
        self._page_ready = False  # 页面脚本是否完成初始化
        self._pending_save_mode = ""  # 等待页面回传工作区时要做的事, 取值见 _on_workspace_submitted
        self._buttons: list[QPushButton] = []
        self._target_path = self._load_target_path()  # 代码输出文件
        if self._target_path and not os.path.isfile(self._target_path):
            # 目标文件已经不在磁盘上了, 清掉配置, 免得界面挂着一个不存在的路径
            self._target_path = ""
            get_config_service().update_app_config(CONFIG_TARGET_FILE, "")
        self._workspace_file = self._load_workspace_file()  # 与代码文件同名的积木文件
        self._palette_pinned = False  # 积木区是否固定显示, 每次打开都从默认模式开始
        self._confirmed_paths: set[str] = set()  # 本次会话中已确认可覆盖的文件

        # 操作结果展示期间忽略页面的积木数回报, 免得刚出的提示被立刻冲掉
        self._status_hold_until = 0.0

        self._setup_ui()
        self._setup_web_view()
        self.apply_theme(dark_mode)

    @staticmethod
    def _load_target_path() -> str:
        """
        从配置读取上次使用的输出文件

        Returns:
            文件路径, 未配置时返回空字符串
        """
        value = get_config_service().get_app_config(CONFIG_TARGET_FILE)
        return value if isinstance(value, str) else ""

    def _setup_ui(self):
        """
        初始化工具栏, 目标文件行与工作区容器

        Args:
            self: 当前面板实例
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # 工具栏, 做成卡片浮在面板底色之上
        self.toolbar = QFrame(self)
        self.toolbar.setObjectName("BlocklyToolbar")
        self.toolbar.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
        toolbar_layout = QHBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(8, 6, 8, 6)
        toolbar_layout.setSpacing(6)

        self.generate_btn = self._create_button(self.toolbar, "保存积木", "把当前积木工作区保存为 Blockly XML 文件并生成 CnLang 代码到指定的 .cn 文件", self._on_generate_clicked)
        self.save_btn = self._create_button(self.toolbar, "另存积木", "把当前积木工作区另存为 Blockly XML 文件", self.save_workspace)
        self.load_btn = self._create_button(self.toolbar, "加载积木", "从 Blockly XML 文件恢复积木工作区", self.load_workspace)
        self.palette_btn = self._create_button(self.toolbar, "默认", "拖出积木后自动收起积木区", self._on_palette_pin_toggled, checkable=True)
        self.clear_btn = self._create_button(self.toolbar, "清空", "清空当前积木工作区", self.clear_workspace)

        for button in (self.generate_btn, self.save_btn, self.load_btn, self.palette_btn, self.clear_btn):
            toolbar_layout.addWidget(button)
        toolbar_layout.addStretch(1)

        self.status_label = QLabel("积木编辑器加载中…", self.toolbar)
        toolbar_layout.addWidget(self.status_label)

        layout.addWidget(self.toolbar)

        # 目标文件行: 生成的代码写入这里手动指定的 .cn 文件
        self.target_row = QFrame(self)
        self.target_row.setObjectName("BlocklyTargetRow")
        self.target_row.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
        target_layout = QHBoxLayout(self.target_row)
        target_layout.setContentsMargins(8, 6, 8, 6)
        target_layout.setSpacing(6)

        self.target_label = QLabel("目标文件", self.target_row)
        self.target_edit = QLineEdit(self.target_row)
        self.target_edit.setReadOnly(True)
        self.target_edit.setPlaceholderText("未指定, 点击「选择…」指定 .cn 文件")
        self.target_edit.setText(self._target_path)
        self.target_edit.setToolTip(self._target_path)
        self.target_edit.setMinimumHeight(26)
        self.target_edit.setCursorPosition(0)
        self.choose_btn = self._create_button(self.target_row, "选择…", "指定积木代码写入哪个 .cn 文件", self.choose_target, needs_page=False)

        self.mode_combo = QComboBox(self.target_row)
        self.mode_combo.addItems(["覆盖", "追加"])
        self.mode_combo.setToolTip("覆盖=用生成的代码替换文件内容, 追加=写到文件末尾")
        self.mode_combo.setMinimumHeight(26)
        self.mode_combo.setMinimumWidth(72)
        self.mode_combo.setCurrentIndex(1 if self._load_append_mode() else 0)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)

        target_layout.addWidget(self.target_label)
        target_layout.addWidget(self.target_edit, 1)
        target_layout.addWidget(self.choose_btn)
        target_layout.addWidget(self.mode_combo)
        layout.addWidget(self.target_row)

        # Blockly 视图容器, 始终占满剩余空间
        self.view = QWebEngineView(self)
        self.view.setMinimumHeight(200)
        layout.addWidget(self.view, 1)

        # 页面未就绪前禁用依赖页面的按钮
        self._set_ready(False)

    def _sync_palette_button(self):
        """
        按当前模式更新积木区按钮的文字与提示

        Args:
            self: 当前面板实例
        """
        pinned = self._palette_pinned
        self.palette_btn.setText("固定" if pinned else "默认")
        self.palette_btn.setToolTip("积木区固定在左侧不收起" if pinned else "拖出积木后自动收起积木区")

    def _create_button(self, parent: QWidget, text: str, tip: str, slot, needs_page: bool = True, checkable: bool = False) -> QPushButton:
        """
        创建工具栏按钮

        Args:
            self: 当前面板实例
            parent: 父部件
            text: 按钮文本
            tip: 悬停提示
            slot: 点击后执行的槽函数
            needs_page: 是否依赖页面就绪状态
            checkable: 是否为可切换按下状态的开关按钮

        Returns:
            创建好的按钮
        """
        button = QPushButton(text, parent)
        button.setToolTip(tip)
        button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        button.setCheckable(checkable)
        button.clicked.connect(slot)
        if needs_page:
            self._buttons.append(button)
        return button

    def apply_theme(self, dark_mode: bool):
        """
        应用主题样式

        Args:
            self: 当前面板实例
            dark_mode: True 为深色主题, False 为浅色主题
        """
        self._dark_mode = dark_mode
        c = theme.colors(dark_mode)

        self.setStyleSheet(styles.panel_style(c))

        # 工具栏与目标文件行做成两张卡片, 与画布拉开层次
        card_style = styles.card_style(c)
        self.toolbar.setStyleSheet(card_style)
        self.target_row.setStyleSheet(card_style)

        self.generate_btn.setStyleSheet(styles.button_style(c, primary=True))
        self.palette_btn.setStyleSheet(styles.button_style(c, toggle=True))
        for button in (self.save_btn, self.load_btn, self.clear_btn, self.choose_btn):
            button.setStyleSheet(styles.button_style(c))
        self.status_label.setStyleSheet(styles.status_style(c))
        self.target_label.setStyleSheet(styles.target_label_style(c))
        self.target_edit.setStyleSheet(styles.target_edit_style(c))
        self.mode_combo.setStyleSheet(styles.mode_combo_style(c))
        self.view.page().setBackgroundColor(QtGui.QColor(c["bg"]))

        # 页面尚未就绪时只记录状态, 就绪后 _on_page_ready 会主动同步一次
        if self._page_ready:
            self.bridge.theme_changed.emit(dark_mode)

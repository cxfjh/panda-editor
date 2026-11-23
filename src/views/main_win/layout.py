import os
from PySide6 import QtCore, QtWidgets
from src.utils import theme
from src.utils.extend import paint_gradient
from src.views.blockly import BlocklyPanel
from src.views.components.custom_title_bar import CustomTitleBar
from src.views.components.tab_manager import TabManager
from src.views.file_tree import FileTreeView
from src.views.terminal import TerminalWidget
from src.views.main_win.refs import UiRefs


class GradientBackgroundWidget(QtWidgets.QWidget):
    """渐变背景容器"""

    def __init__(self, parent=None, gradient_colors=None, gradient_alpha=0.85):
        """
        初始化渐变背景容器

        Args:
            self: 当前部件实例
            parent: 父窗口
            gradient_colors: 渐变色列表
            gradient_alpha: 渐变背景透明度
        """
        super().__init__(parent)
        self._gradient_colors = gradient_colors or ["#667eea", "#764ba2", "#f093fb"]
        self._gradient_alpha = gradient_alpha

    def paintEvent(self, event):
        """
        绘制渐变背景

        Args:
            self: 当前部件实例
            event: 绘制事件对象
        """
        paint_gradient(self, self._gradient_colors, self._gradient_alpha)


class LayoutMixin(UiRefs):
    """中央部件 分割器与各面板的搭建"""

    def _setup_central_widget(self, main_window):
        """
        设置中央部件及布局

        Args:
            self: 当前 UI 实例
            main_window: 主窗口对象
        """
        self.central_widget = GradientBackgroundWidget(parent=main_window, gradient_colors=["#667eea", "#764ba2", "#f093fb"], gradient_alpha=0.85)
        self.central_widget.setObjectName("central_widget")

        main_layout = QtWidgets.QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(1, 0, 1, 0)  # 极窄边距 最大化可用空间
        main_layout.setSpacing(0)

        self.custom_title_bar = CustomTitleBar(title="熊猫编辑器", parent=main_window, gradient_colors=["#667eea", "#764ba2", "#f093fb"], fg_color="#FFFFFF")
        main_layout.addWidget(self.custom_title_bar)

        self.custom_title_bar.minimize_clicked.connect(main_window.showMinimized)
        self.custom_title_bar.maximize_clicked.connect(self._on_toggle_maximize)
        self.custom_title_bar.close_clicked.connect(main_window.close)

        content_widget = QtWidgets.QWidget()
        content_widget.setStyleSheet("background: transparent;")
        content_layout = QtWidgets.QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.main_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal, content_widget)
        self.main_splitter.setObjectName("main_splitter")
        self.main_splitter.setStyleSheet(
            """
            QSplitter { background-color: transparent; }
            QSplitter::handle { background-color: transparent; }
            QSplitter::handle:horizontal { width: 6px; }
            """,
        )

        self._build_file_tree_panel()

        self.right_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical, self.main_splitter)
        self.right_splitter.setObjectName("right_splitter")
        self.right_splitter.setStyleSheet(
            """
            QSplitter { background-color: transparent; }
            QSplitter::handle { background-color: transparent; }
            QSplitter::handle:vertical { height: 6px; }
            """,
        )

        self._build_editor_panel(main_window)
        self._build_terminal_panel()

        self.main_splitter.addWidget(self.right_splitter)
        self.right_splitter.addWidget(self.editor_wrapper)
        self.right_splitter.addWidget(self.terminal_wrapper)

        # 积木面板最后加入, 分割器里的顺序与初始比例一一对应
        self._build_blockly_panel()

        # 积木面板给真实宽度而非 0, 折叠后才记得住这个值, 展开时能原样还原
        self.main_splitter.setSizes([100, 1100, 800])
        self.right_splitter.setSizes([700, 200])

        self.main_splitter.setHandleWidth(1)
        self.right_splitter.setHandleWidth(1)

        content_layout.addWidget(self.main_splitter)
        main_layout.addWidget(content_widget, 1)  # stretch=1 占据剩余空间

        self._build_status_bar(main_window)
        self._init_file_tree()

    def _build_file_tree_panel(self):
        """
        创建左侧文件树面板

        Args:
            self: 当前 UI 实例
        """
        c = theme.colors(True)
        self.file_tree_wrapper = QtWidgets.QWidget(self.main_splitter)
        self.file_tree_wrapper.setObjectName("file_tree_wrapper")
        self.file_tree_wrapper.setStyleSheet(
            f"""
            QWidget#file_tree_wrapper {{
                background-color: {c['panel_bg']};
                border-radius: 6px;
                margin: 4px;
            }}
            """,
        )
        self.file_tree_layout = QtWidgets.QVBoxLayout(self.file_tree_wrapper)
        self.file_tree_layout.setContentsMargins(4, 4, 6, 6)
        self.file_tree = FileTreeView(self.file_tree_wrapper)  # 异步加载的文件树组件
        self.file_tree.setMinimumWidth(180)
        self.file_tree_layout.addWidget(self.file_tree)
        self.main_splitter.addWidget(self.file_tree_wrapper)

    def _build_editor_panel(self, main_window):
        """
        创建编辑区面板与标签页管理器

        Args:
            self: 当前 UI 实例
            main_window: 主窗口对象
        """
        c = theme.colors(True)
        self.editor_wrapper = QtWidgets.QWidget(self.right_splitter)
        self.editor_wrapper.setObjectName("editor_wrapper")
        self.editor_wrapper.setStyleSheet(
            f"""
            QWidget#editor_wrapper {{
                background-color: {c['bg']};
                border-radius: 6px;
                margin: 4px;
            }}
            """,
        )
        self.editor_wrapper_layout = QtWidgets.QVBoxLayout(self.editor_wrapper)
        self.editor_wrapper_layout.setContentsMargins(6, 4, 6, 6)

        self.tab_widget = QtWidgets.QTabWidget(self.editor_wrapper)
        self.tab_widget.setObjectName("tab_widget")
        self.tab_widget.setStyleSheet(
            """
            QTabWidget::pane {
                background-color: transparent;
                border: none;
            }
            """,
        )
        self.editor_wrapper_layout.addWidget(self.tab_widget)

        self.tab_manager = TabManager(self.tab_widget, parent=main_window)
        self.tab_manager.tab_changed.connect(self.handlers.on_cursor_position_changed)  # 切换标签时更新状态栏
        self.tab_manager.file_saved_as.connect(self._on_tab_saved_as)  # 另存为后同步文件树与终端目录

    def _build_terminal_panel(self):
        """
        创建底部终端面板

        Args:
            self: 当前 UI 实例
        """
        c = theme.colors(True)
        self.terminal_wrapper = QtWidgets.QWidget(self.right_splitter)
        self.terminal_wrapper.setObjectName("terminal_wrapper")
        self.terminal_wrapper.setStyleSheet(
            f"""
            QWidget#terminal_wrapper {{
                background-color: {c['bg']};
                border-radius: 6px;
                margin: 4px;
            }}
            """,
        )
        self.terminal_wrapper_layout = QtWidgets.QVBoxLayout(self.terminal_wrapper)
        self.terminal_wrapper_layout.setContentsMargins(4, 4, 4, 4)
        self.terminal = TerminalWidget(self.terminal_wrapper)
        self.terminal.setMinimumHeight(100)
        self.terminal.setStyleSheet(
            """
            QWidget#TerminalWidget {
                background-color: transparent;
                border: none;
            }
            """,
        )
        self.terminal.setObjectName("TerminalWidget")
        self.terminal_wrapper_layout.addWidget(self.terminal)

    def _build_blockly_panel(self):
        """
        创建积木面板, 默认隐藏由视图菜单开启

        Args:
            self: 当前 UI 实例
        """
        c = theme.colors(True)
        self.blockly_wrapper = QtWidgets.QWidget(self.main_splitter)
        self.blockly_wrapper.setObjectName("blockly_wrapper")
        self.blockly_wrapper.setStyleSheet(
            f"""
            QWidget#blockly_wrapper {{
                background-color: {c['bg']};
                border-radius: 6px;
                margin: 4px;
            }}
            """,
        )
        self.blockly_wrapper_layout = QtWidgets.QVBoxLayout(self.blockly_wrapper)
        self.blockly_wrapper_layout.setContentsMargins(0, 0, 0, 0)
        self.blockly_panel = BlocklyPanel(self.blockly_wrapper, dark_mode=True)
        self.blockly_panel.code_written.connect(self.handlers.on_blockly_code_written)  # 生成的代码已写入指定文件
        self.blockly_wrapper_layout.addWidget(self.blockly_panel)
        self.main_splitter.addWidget(self.blockly_wrapper)
        self.blockly_wrapper.setVisible(True)

    def _build_status_bar(self, main_window):
        """
        创建状态栏

        Args:
            self: 当前 UI 实例
            main_window: 主窗口对象
        """
        c = theme.colors(True)
        self.status_bar = main_window.statusBar()
        self.status_bar.setStyleSheet(
            f"""
            QStatusBar {{
                background-color: {c['panel_bg']};
                color: {c['fg']};
                border-top: 1px solid {c['border']};
            }}
            QStatusBar QLabel {{
                color: {c['fg']};
                background-color: transparent;
            }}
            """,
        )
        self.status_label = QtWidgets.QLabel()
        self.status_label.setText("Ready")
        self.status_bar.addPermanentWidget(self.status_label)  # 右侧固定显示
        main_window.setStatusBar(self.status_bar)
        main_window.setCentralWidget(self.central_widget)

    def _on_tab_saved_as(self, file_path: str):
        """
        未命名标签另存为后, 把文件树与终端切到新文件所在目录

        Args:
            self: 当前 UI 实例
            file_path: 另存为后的完整路径
        """
        file_dir = os.path.dirname(file_path)
        if not file_dir or not os.path.isdir(file_dir):
            return
        self.file_tree.set_root_path(file_dir)
        self.terminal.set_working_directory(file_dir)
        self.handlers.on_cursor_position_changed()

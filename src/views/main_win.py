import os
import keyboard
from PySide6 import QtCore, QtGui, QtWidgets
from src.utils.syntax_high import ChineseHighlighter
from src.utils.code_proc import run_code, compile_code
from src.utils.config import read_config
from src.views.set_win import SettingsDialogUI, DialogSignals
from src.utils.set_page import reset_program, uninstall_program
from src.utils.file_ops import open_file, read_file_content, save_file, save_as_file, import_file


class MainWindowUI:
    def setup_ui(self, main_window):
        """初始化主窗口UI布局和组件"""
        self._setup_main_window(main_window)
        self._setup_icon(main_window)
        self._setup_settings_dialog()
        self._setup_central_widget(main_window)
        self._setup_text_edit(main_window)
        self._setup_style(main_window)
        self._setup_menus(main_window)
        self._setup_menu_actions(main_window)
        self._setup_menu_structure()
        self._setup_translations(main_window)
        self._setup_signals_and_slots()
        self._setup_global_shortcuts()
        QtCore.QMetaObject.connectSlotsByName(main_window)  # 自动连接信号槽

    @staticmethod
    def _setup_main_window(main_window):
        """设置主窗口基本属性"""
        main_window.setObjectName("MainWindow")
        main_window.resize(1500, 900)

        # 设置窗口大小策略
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(main_window.sizePolicy().hasHeightForWidth())
        main_window.setSizePolicy(size_policy)

    @staticmethod
    def _setup_icon(main_window):
        """设置窗口图标"""
        icon = QtGui.QIcon()
        icon.addPixmap(
            QtGui.QPixmap(read_config("FileConfig.json", "ICON")),
            QtGui.QIcon.Mode.Normal,
            QtGui.QIcon.State.Off,
        )
        main_window.setWindowIcon(icon)

    def _setup_settings_dialog(self):
        """初始化设置对话框"""
        icon = QtGui.QIcon()
        icon.addPixmap(
            QtGui.QPixmap(read_config("FileConfig.json", "ICON")),
            QtGui.QIcon.Mode.Normal,
            QtGui.QIcon.State.Off,
        )

        self.settings_dialog = QtWidgets.QDialog()
        self.settings_dialog.ui = SettingsDialogUI()
        self.settings_dialog.ui.setup_ui(self.settings_dialog)
        self.settings_dialog.setWindowTitle("设置")
        self.settings_dialog.setWindowIcon(icon)
        self.settings_dialog.hide()

        # 初始化信号对象，用于设置对话框关闭后同步样式
        self.signals = DialogSignals()
        self.settings_dialog.ui.signals.dialogClosed.connect(self.change_style)

    def _setup_central_widget(self, main_window):
        """设置中央部件及布局"""
        # 初始化中心部件（主窗口内容容器）
        self.central_widget = QtWidgets.QWidget(parent=main_window)
        self.central_widget.setObjectName("central_widget")

        # 初始化水平布局容器（用于放置文本编辑区）
        self.horizontal_layout_widget = QtWidgets.QWidget(parent=self.central_widget)
        self.horizontal_layout_widget.setGeometry(QtCore.QRect(50, 20, 691, 521))
        self.horizontal_layout_widget.setObjectName("horizontal_layout_widget")

        # 初始化水平布局管理器（管理文本编辑区的布局）
        self.horizontal_layout = QtWidgets.QHBoxLayout(self.horizontal_layout_widget)
        self.horizontal_layout.setContentsMargins(0, 0, 0, 0)  # 消除内边距
        self.horizontal_layout.setObjectName("horizontal_layout")

        # 初始化状态栏（显示程序状态信息）
        self.status_bar = main_window.statusBar()
        self.status_label = QtWidgets.QLabel()
        self.status_label.setText("Ready")  # 初始状态文本
        self.status_bar.addPermanentWidget(self.status_label)  # 永久显示标签
        main_window.setStatusBar(self.status_bar)

        # 初始化中心布局管理器（管理整个中心部件的布局）
        self.central_layout = QtWidgets.QVBoxLayout(self.central_widget)
        self.central_layout.addWidget(self.horizontal_layout_widget)
        main_window.setCentralWidget(self.central_widget)  # 设置中心部件为主窗口内容

    def _setup_text_edit(self, main_window):
        """设置文本编辑区域"""
        # 初始化文本编辑区（核心输入组件）
        self.text_edit = QtWidgets.QPlainTextEdit(parent=self.horizontal_layout_widget)
        # 绑定光标位置变化事件（用于实时更新行号）
        self.text_edit.cursorPositionChanged.connect(self.on_cursor_position_changed)
        from src.utils.syntax_hint import SyntaxHintManager  # 假设管理器在该路径
        self.syntax_hint = SyntaxHintManager(self.text_edit)

    def _setup_style(self, main_window):
        """设置编辑器样式"""

        def init_style(font_size=25, dark_mode=True, syntax_highlight=True, window_top=False):
            """初始化文本编辑区样式（字体、主题、语法高亮等）"""
            # 设置字体
            font = QtGui.QFont()
            font.setFamily("YaHei Consolas Hybrid")
            font.setPointSize(font_size)
            self.text_edit.setFont(font)

            # 初始化语法高亮（根据配置决定是否启用）
            if syntax_highlight: self.highlighter = ChineseHighlighter(self.text_edit.document())
            else: self.highlighter = None  # 禁用高亮

            # 设置深色/浅色主题
            if dark_mode: self.text_edit.setStyleSheet("background-color: #1f1f1f; color: #cccccc;")
            else: self.text_edit.setStyleSheet("background-color: #ffffff; color: #0d0d10;")

            # 设置窗口是否置顶
            main_window.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint, window_top)
            main_window.show()  # 刷新窗口显示

        # 保存样式初始化函数引用（方便后续修改样式时调用）
        self.init_style_func = init_style

        # 从配置文件加载样式设置（如果配置存在）
        if read_config("PersonalConfig.json"):
            try:
                settings = read_config("PersonalConfig.json")
                init_style(settings['fontSize'], settings['darkMode'], settings['highlightSyntax'], settings['windowTop'])
            except Exception as e:
                QtWidgets.QMessageBox.critical(main_window, "样式配置", "配置样式文件读取失败，请检查配置文件内容。\n 错误信息：\n" + str(e))
        else: init_style()  # 无配置时使用默认样式

        # 文本编辑区其他设置
        self.text_edit.setTabChangesFocus(True)  # Tab键切换焦点（而非插入制表符）
        self.text_edit.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)  # 禁用自动换行
        self.text_edit.setTabStopDistance(60.0)  # 设置Tab键缩进距离
        self.text_edit.setObjectName("text_edit")
        self.horizontal_layout.addWidget(self.text_edit)  # 将文本编辑区添加到布局

    def _setup_menus(self, main_window):
        """初始化菜单栏和各个菜单"""
        # 初始化菜单栏
        self.menu_bar = QtWidgets.QMenuBar(parent=main_window)
        self.menu_bar.setGeometry(QtCore.QRect(0, 0, 800, 21))
        self.menu_bar.setObjectName("menu_bar")

        # 初始化各菜单
        self.file_menu = QtWidgets.QMenu(parent=self.menu_bar)
        self.file_menu.setObjectName("file_menu")
        self.code_menu = QtWidgets.QMenu(parent=self.menu_bar)
        self.code_menu.setObjectName("code_menu")
        self.about_menu = QtWidgets.QMenu(parent=self.menu_bar)
        self.about_menu.setObjectName("about_menu")
        self.help_menu = QtWidgets.QMenu(parent=self.menu_bar)
        self.help_menu.setObjectName("help_menu")
        self.contact_submenu = QtWidgets.QMenu(parent=self.help_menu)
        self.contact_submenu.setObjectName("contact_submenu")
        self.settings_menu = QtWidgets.QMenu(parent=self.menu_bar)
        self.settings_menu.setObjectName("settings_menu")
        main_window.setMenuBar(self.menu_bar)  # 将菜单栏添加到主窗口

    def _setup_menu_actions(self, main_window):
        """初始化菜单项动作"""
        # 初始化各菜单项动作（功能按钮）
        self.open_action = QtGui.QAction(parent=main_window)
        self.open_action.setObjectName("open_action")
        self.save_action = QtGui.QAction(parent=main_window)
        self.save_action.setObjectName("save_action")
        self.save_as_action = QtGui.QAction(parent=main_window)
        self.save_as_action.setObjectName("save_as_action")
        self.import_action = QtGui.QAction(parent=main_window)
        self.import_action.setObjectName("import_action")
        self.run_action = QtGui.QAction(parent=main_window)
        self.run_action.setObjectName("run_action")
        self.compile_action = QtGui.QAction(parent=main_window)
        self.compile_action.setObjectName("compile_action")
        self.website_action = QtGui.QAction(parent=main_window)
        self.website_action.setObjectName("website_action")
        self.github_action = QtGui.QAction(parent=main_window)
        self.github_action.setObjectName("github_action")
        self.tutorial_action = QtGui.QAction(parent=main_window)
        self.tutorial_action.setObjectName("tutorial_action")
        self.email_action = QtGui.QAction(parent=main_window)
        self.email_action.setObjectName("email_action")
        self.view_settings_action = QtGui.QAction(parent=main_window)
        self.view_settings_action.setCheckable(False)  # 非复选框类型
        self.view_settings_action.setChecked(False)
        self.view_settings_action.setObjectName("view_settings_action")
        self.update_action = QtGui.QAction(parent=main_window)
        self.update_action.setObjectName("update_action")
        self.uninstall_action = QtGui.QAction(parent=main_window)
        self.uninstall_action.setObjectName("uninstall_action")
        self.reset_action = QtGui.QAction(parent=main_window)
        self.reset_action.setObjectName("reset_action")

    def _setup_menu_structure(self):
        """设置菜单结构"""
        # 为菜单添加菜单项
        self.file_menu.addAction(self.open_action)
        self.file_menu.addAction(self.save_action)
        self.file_menu.addAction(self.save_as_action)
        self.file_menu.addAction(self.import_action)
        self.code_menu.addAction(self.run_action)
        self.code_menu.addAction(self.compile_action)
        self.about_menu.addAction(self.website_action)
        self.about_menu.addAction(self.github_action)
        self.contact_submenu.addAction(self.email_action)
        self.help_menu.addAction(self.tutorial_action)
        self.help_menu.addAction(self.contact_submenu.menuAction())
        self.settings_menu.addAction(self.view_settings_action)
        self.settings_menu.addSeparator()  # 添加分隔线
        self.settings_menu.addAction(self.update_action)
        self.settings_menu.addAction(self.uninstall_action)
        self.settings_menu.addAction(self.reset_action)

        # 将菜单添加到菜单栏
        self.menu_bar.addAction(self.file_menu.menuAction())
        self.menu_bar.addAction(self.code_menu.menuAction())
        self.menu_bar.addAction(self.about_menu.menuAction())
        self.menu_bar.addAction(self.help_menu.menuAction())
        self.menu_bar.addAction(self.settings_menu.menuAction())

    def change_style(self, message):
        """接收设置对话框的样式参数，更新文本编辑区样式"""
        self.init_style_func(message['fontSize'], message['darkMode'], message['highlightSyntax'], message['windowTop'])

    def on_cursor_position_changed(self):
        """光标位置变化时，更新状态栏的行号和文件信息"""
        cursor = self.text_edit.textCursor()
        cursor_position = cursor.position()  # 获取光标位置

        # 计算当前行号（QTextBlock从0开始，+1转为自然行号）
        cursor_block = self.text_edit.document().findBlock(cursor_position)
        cursor_line_number = cursor_block.blockNumber() + 1

        # 更新状态栏文本（显示行号、文件路径、版本）
        self.status_label.setText(
            f"行号: {cursor_line_number}{" " * 10}文件: {read_config('FileConfig.json', 'SourceCodePath')}\\"
            f"{read_config('FileConfig.json', 'CodeName')}.cn{" " * 10}版本: v0.1.0",
        )

    def _setup_translations(self, main_window):
        """设置菜单和按钮的文本（支持翻译）"""
        _translate = QtCore.QCoreApplication.translate
        main_window.setWindowTitle(_translate("MainWindow", "熊猫编辑器"))  # 窗口标题

        # 菜单标题
        self.file_menu.setTitle(_translate("MainWindow", "文件"))
        self.code_menu.setTitle(_translate("MainWindow", "代码"))
        self.about_menu.setTitle(_translate("MainWindow", "关于"))
        self.help_menu.setTitle(_translate("MainWindow", "帮助"))
        self.contact_submenu.setTitle(_translate("MainWindow", "联系作者"))
        self.settings_menu.setTitle(_translate("MainWindow", "设置"))

        # 菜单项文本（包含快捷键提示）
        self.open_action.setText(_translate("MainWindow", "打开文件  Ctrl+O"))
        self.save_action.setText(_translate("MainWindow", "保存文件  Ctrl+S"))
        self.save_as_action.setText(_translate("MainWindow", "另存文件  Ctrl+Shift+S"))
        self.import_action.setText(_translate("MainWindow", "导入扩展  Ctrl+I"))
        self.run_action.setText(_translate("MainWindow", "运行代码  Ctrl+R"))
        self.compile_action.setText(_translate("MainWindow", "编译代码  Ctrl+B"))
        self.website_action.setText(_translate("MainWindow", "官方网站"))
        self.github_action.setText(_translate("MainWindow", "开源地址"))
        self.tutorial_action.setText(_translate("MainWindow", "使用教程"))
        self.email_action.setText(_translate("MainWindow", "2449579731@qq.com"))
        self.view_settings_action.setText(_translate("MainWindow", "视图设置"))
        self.update_action.setText(_translate("MainWindow", "更新程序  Ctrl+U"))
        self.uninstall_action.setText(_translate("MainWindow", "卸载程序  Ctrl+Shift+U"))
        self.reset_action.setText(_translate("MainWindow", "重置程序  Ctrl+Shift+R"))

        # 如果有最近打开的文件，加载文件内容到文本编辑区
        if read_config("FileConfig.json", "SourceCodePath") != "": self.text_edit.setPlainText(read_file_content() or "")

    def _setup_signals_and_slots(self):
        """设置信号与槽连接"""
        # 打开文件：调用openFile()选择文件，然后读取内容到文本编辑区
        self.open_action.triggered.connect(self._on_open_file)

        # 保存文件：将文本编辑区内容保存到当前文件
        self.save_action.triggered.connect(self._on_save_file)

        # 另存为：将内容保存到新文件
        self.save_as_action.triggered.connect(self._on_save_as_file)

        # 导入扩展：调用importExtension()导入扩展
        self.import_action.triggered.connect(import_file)

        # 运行代码：先保存内容，再执行runCode()
        self.run_action.triggered.connect(self._on_run_code)

        # 编译代码：先保存内容，再执行compileCode()
        self.compile_action.triggered.connect(self._on_compile_code)

        # 打开官方网站
        self.website_action.triggered.connect(self._open_website)

        # 打开GitHub开源地址
        self.github_action.triggered.connect(self._open_github)

        # 卸载程序
        self.uninstall_action.triggered.connect(uninstall_program)

        # 重置程序
        self.reset_action.triggered.connect(reset_program)

        # 显示设置对话框
        self.view_settings_action.triggered.connect(self.settings_dialog.show)

        # 打开更新页面（同官方网站）
        self.update_action.triggered.connect(self._open_website)

        # 打开使用教程（GitHub文档）
        self.tutorial_action.triggered.connect(self._open_tutorial)

    def _setup_global_shortcuts(self):
        """设置全局快捷键"""
        keyboard.add_hotkey('Ctrl+O', self._on_open_file)
        keyboard.add_hotkey('ctrl+S', self._on_save_file)
        keyboard.add_hotkey('Ctrl+Shift+S', self._on_save_as_file)
        keyboard.add_hotkey('Ctrl+I', import_file)
        keyboard.add_hotkey('Ctrl+R', self._on_run_code)
        keyboard.add_hotkey('Ctrl+B', self._on_compile_code)
        keyboard.add_hotkey('Ctrl+Shift+U', uninstall_program)
        keyboard.add_hotkey('Ctrl+Shift+R', reset_program)
        keyboard.add_hotkey('Ctrl+U', self._open_website)

    # 信号处理方法
    def _on_open_file(self):
        """处理打开文件操作"""
        open_file()
        self.text_edit.setPlainText(read_file_content() or "")

    def _on_save_file(self):
        """处理保存文件操作"""
        save_file(self.text_edit.toPlainText())

    def _on_save_as_file(self):
        """处理另存为文件操作"""
        save_as_file(self.text_edit.toPlainText())

    def _on_run_code(self):
        """处理运行代码操作"""
        run_code(self.text_edit.toPlainText())
        save_file(self.text_edit.toPlainText())

    def _on_compile_code(self):
        """处理编译代码操作"""
        compile_code(self.text_edit.toPlainText())
        save_file(self.text_edit.toPlainText())

    @staticmethod
    def _open_website():
        """打开官方网站"""
        os.startfile('https://cxfjh.github.io')

    @staticmethod
    def _open_github():
        """打开GitHub开源地址"""
        os.startfile('https://github.com/cxfjh/panda-editor')

    @staticmethod
    def _open_tutorial():
        """打开使用教程"""
        os.startfile('https://github.com/cxfjh/panda-editor/blob/main/docs/USAGE.md')

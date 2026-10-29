from PySide6 import QtCore, QtGui, QtWidgets
from src.views.components.custom_title_bar import TitleMenuBar


class MenuBuilder:
    """菜单构建器类"""

    @staticmethod
    def _create_action(parent, name, checkable=False, checked=False):
        """
        创建 QAction 的辅助方法

        Args:
            parent: 父对象
            name: 动作对象名称
            checkable: 是否可勾选
            checked: 初始勾选状态

        Returns:
            配置好的 QAction 实例
        """
        action = QtGui.QAction(parent=parent)
        action.setObjectName(name)
        action.setCheckable(checkable)
        if checked:
            action.setChecked(True)
        return action

    @staticmethod
    def create_menus(main_window, ui):
        """
        初始化菜单栏和各个菜单

        Args:
            main_window: QMainWindow 实例
            ui: MainWindowUI 实例
        """

        # 创建菜单栏
        menu_bar = TitleMenuBar(parent=main_window)
        menu_bar.setGeometry(QtCore.QRect(0, 0, 800, 20))
        menu_bar.setObjectName("menu_bar")
        ui.menu_bar = menu_bar

        # 创建 9 个主菜单容器
        ui.file_menu = QtWidgets.QMenu(parent=menu_bar)
        ui.file_menu.setObjectName("file_menu")
        ui.edit_menu = QtWidgets.QMenu(parent=menu_bar)
        ui.edit_menu.setObjectName("edit_menu")
        ui.code_menu = QtWidgets.QMenu(parent=menu_bar)
        ui.code_menu.setObjectName("code_menu")
        ui.view_menu = QtWidgets.QMenu(parent=menu_bar)
        ui.view_menu.setObjectName("view_menu")
        ui.compile_menu = QtWidgets.QMenu(parent=menu_bar)
        ui.compile_menu.setObjectName("compile_menu")
        ui.settings_menu = QtWidgets.QMenu(parent=menu_bar)
        ui.settings_menu.setObjectName("settings_menu")
        ui.program_menu = QtWidgets.QMenu(parent=menu_bar)
        ui.program_menu.setObjectName("program_menu")
        ui.help_menu = QtWidgets.QMenu(parent=menu_bar)
        ui.help_menu.setObjectName("help_menu")
        ui.about_menu = QtWidgets.QMenu(parent=menu_bar)
        ui.about_menu.setObjectName("about_menu")

        # 将菜单栏设置到主窗口
        main_window.setMenuBar(menu_bar)

    @staticmethod
    def create_actions(main_window, ui):
        """
        初始化菜单项动作并挂到 ui 对象上

        Args:
            main_window: 主窗口, 作为动作的父对象
            ui: 主窗口 UI 对象, 动作以属性形式挂载
        """

        # 文件菜单动作
        ui.open_action = MenuBuilder._create_action(main_window, "open_action")
        ui.save_action = MenuBuilder._create_action(main_window, "save_action")
        ui.save_as_action = MenuBuilder._create_action(main_window, "save_as_action")

        # 编辑菜单动作
        ui.find_action = MenuBuilder._create_action(main_window, "find_action")

        # 代码菜单动作
        ui.run_action = MenuBuilder._create_action(main_window, "run_action")
        ui.compile_action = MenuBuilder._create_action(main_window, "compile_action")
        ui.compile_ui_action = MenuBuilder._create_action(main_window, "compile_ui_action")

        # 帮助/关于菜单动作
        ui.website_action = MenuBuilder._create_action(main_window, "website_action")
        ui.github_action = MenuBuilder._create_action(main_window, "github_action")
        ui.tutorial_action = MenuBuilder._create_action(main_window, "tutorial_action")
        ui.email_action = MenuBuilder._create_action(main_window, "email_action")
        ui.author_github_action = MenuBuilder._create_action(main_window, "author_github_action")

        # 设置菜单动作
        ui.dark_mode_action = MenuBuilder._create_action(main_window, "dark_mode_action", checkable=True)
        ui.syntax_highlight_action = MenuBuilder._create_action(main_window, "syntax_highlight_action", checkable=True)
        ui.window_top_action = MenuBuilder._create_action(main_window, "window_top_action", checkable=True)
        ui.pip_taobao_action = MenuBuilder._create_action(main_window, "pip_taobao_action", checkable=True)
        ui.independent_run_action = MenuBuilder._create_action(main_window, "independent_run_action", checkable=True, checked=False)

        # 编译菜单动作
        ui.hide_window_action = MenuBuilder._create_action(main_window, "hide_window_action", checkable=True)
        ui.admin_privilege_action = MenuBuilder._create_action(main_window, "admin_privilege_action", checkable=True)
        ui.compile_default_icon_action = MenuBuilder._create_action(main_window, "compile_default_icon_action", checkable=True, checked=True)
        ui.compile_icon_action = MenuBuilder._create_action(main_window, "compile_icon_action")
        ui.single_file_action = MenuBuilder._create_action(main_window, "single_file_action", checkable=True, checked=True)
        ui.add_data_action = MenuBuilder._create_action(main_window, "add_data_action")

        # 视图菜单动作
        ui.toggle_file_tree_action = MenuBuilder._create_action(main_window, "toggle_file_tree_action", checkable=True, checked=True)
        ui.toggle_terminal_action = MenuBuilder._create_action(main_window, "toggle_terminal_action", checkable=True, checked=True)
        ui.toggle_blockly_action = MenuBuilder._create_action(main_window, "toggle_blockly_action", checkable=True)
        ui.toggle_line_numbers_action = MenuBuilder._create_action(main_window, "toggle_line_numbers_action", checkable=True, checked=True)
        ui.fold_all_action = MenuBuilder._create_action(main_window, "fold_all_action")
        ui.unfold_all_action = MenuBuilder._create_action(main_window, "unfold_all_action")
        ui.gui_designer_action = MenuBuilder._create_action(main_window, "gui_designer_action")

        # 其他菜单动作
        ui.update_action = MenuBuilder._create_action(main_window, "update_action")
        ui.uninstall_action = MenuBuilder._create_action(main_window, "uninstall_action")
        ui.reset_action = MenuBuilder._create_action(main_window, "reset_action")

    @staticmethod
    def build_menu_structure(ui):
        """
        把已创建的动作按菜单分组挂到菜单栏上

        Args:
            ui: 主窗口 UI 对象, 包含菜单与动作引用
        """

        # 文件菜单
        ui.file_menu.addAction(ui.open_action)
        ui.file_menu.addAction(ui.save_action)
        ui.file_menu.addAction(ui.save_as_action)

        # 编辑菜单
        ui.edit_menu.addAction(ui.find_action)

        # 代码菜单
        ui.code_menu.addAction(ui.run_action)
        ui.code_menu.addAction(ui.compile_action)
        ui.code_menu.addSeparator()
        ui.code_menu.addAction(ui.compile_ui_action)

        # 视图菜单
        ui.view_menu.addAction(ui.toggle_file_tree_action)
        ui.view_menu.addAction(ui.toggle_terminal_action)
        ui.view_menu.addAction(ui.toggle_blockly_action)
        ui.view_menu.addSeparator()
        ui.view_menu.addAction(ui.toggle_line_numbers_action)
        ui.view_menu.addSeparator()
        ui.view_menu.addAction(ui.fold_all_action)
        ui.view_menu.addAction(ui.unfold_all_action)
        ui.view_menu.addSeparator()
        ui.view_menu.addAction(ui.gui_designer_action)

        # 设置菜单
        ui.settings_menu.addAction(ui.dark_mode_action)
        ui.settings_menu.addAction(ui.syntax_highlight_action)
        ui.settings_menu.addAction(ui.window_top_action)
        ui.settings_menu.addSeparator()
        ui.settings_menu.addAction(ui.pip_taobao_action)
        ui.settings_menu.addAction(ui.independent_run_action)

        # 编译菜单
        ui.compile_menu.addAction(ui.single_file_action)
        ui.compile_menu.addSeparator()
        ui.compile_menu.addAction(ui.hide_window_action)
        ui.compile_menu.addAction(ui.admin_privilege_action)
        ui.compile_menu.addSeparator()
        ui.compile_menu.addAction(ui.compile_default_icon_action)
        ui.compile_menu.addAction(ui.compile_icon_action)
        ui.compile_menu.addSeparator()
        ui.compile_menu.addAction(ui.add_data_action)

        # 帮助菜单
        ui.help_menu.addAction(ui.tutorial_action)
        ui.help_menu.addSeparator()
        ui.help_menu.addAction(ui.update_action)

        # 程序菜单
        ui.program_menu.addAction(ui.uninstall_action)
        ui.program_menu.addAction(ui.reset_action)

        # 关于菜单
        ui.about_menu.addAction(ui.website_action)
        ui.about_menu.addAction(ui.github_action)
        ui.about_menu.addSeparator()
        ui.about_menu.addAction(ui.email_action)
        ui.about_menu.addAction(ui.author_github_action)

        # 将所有主菜单添加到菜单栏
        ui.menu_bar.addAction(ui.file_menu.menuAction())
        ui.menu_bar.addAction(ui.edit_menu.menuAction())
        ui.menu_bar.addAction(ui.code_menu.menuAction())
        ui.menu_bar.addAction(ui.view_menu.menuAction())
        ui.menu_bar.addAction(ui.compile_menu.menuAction())
        ui.menu_bar.addAction(ui.settings_menu.menuAction())
        ui.menu_bar.addAction(ui.program_menu.menuAction())
        ui.menu_bar.addAction(ui.help_menu.menuAction())
        ui.menu_bar.addAction(ui.about_menu.menuAction())

    @staticmethod
    def setup_translations(main_window, ui):
        """
        设置菜单和按钮的文本

        Args:
            main_window: QMainWindow 实例
            ui: MainWindowUI 实例
        """
        _translate = QtCore.QCoreApplication.translate
        main_window.setWindowTitle(_translate("MainWindow", "熊猫编辑器"))

        # 设置菜单标题
        ui.file_menu.setTitle(_translate("MainWindow", "文件"))
        ui.edit_menu.setTitle(_translate("MainWindow", "编辑"))
        ui.code_menu.setTitle(_translate("MainWindow", "代码"))
        ui.view_menu.setTitle(_translate("MainWindow", "视图"))
        ui.compile_menu.setTitle(_translate("MainWindow", "编译"))
        ui.settings_menu.setTitle(_translate("MainWindow", "设置"))
        ui.program_menu.setTitle(_translate("MainWindow", "程序"))
        ui.help_menu.setTitle(_translate("MainWindow", "帮助"))
        ui.about_menu.setTitle(_translate("MainWindow", "关于"))

        # 文件菜单项
        ui.open_action.setText(_translate("MainWindow", "打开目录  Ctrl+O"))
        ui.save_action.setText(_translate("MainWindow", "保存文件  Ctrl+S"))
        ui.save_as_action.setText(_translate("MainWindow", "另存文件  Ctrl+Shift+S"))

        # 编辑菜单项
        ui.find_action.setText(_translate("MainWindow", "查找和替换  Ctrl+F"))

        # 代码菜单项
        ui.run_action.setText(_translate("MainWindow", "运行代码  Ctrl+R"))
        ui.compile_action.setText(_translate("MainWindow", "编译代码  Ctrl+B"))
        ui.compile_ui_action.setText(_translate("MainWindow", "编译 UI"))

        # 视图菜单项
        ui.toggle_file_tree_action.setText(_translate("MainWindow", "文件窗口  Shift+Esc"))
        ui.toggle_terminal_action.setText(_translate("MainWindow", "终端窗口  Ctrl+`"))
        ui.toggle_blockly_action.setText(_translate("MainWindow", "积木编程  Ctrl+Shift+B"))
        ui.toggle_line_numbers_action.setText(_translate("MainWindow", "显示行号"))
        ui.fold_all_action.setText(_translate("MainWindow", "折叠全部  Ctrl+Shift+["))
        ui.unfold_all_action.setText(_translate("MainWindow", "展开全部  Ctrl+Shift+]"))
        ui.gui_designer_action.setText(_translate("MainWindow", "GUI 编辑"))

        # 设置菜单项文本
        ui.dark_mode_action.setText(_translate("MainWindow", "深色模式"))
        ui.syntax_highlight_action.setText(_translate("MainWindow", "语法高亮"))
        ui.window_top_action.setText(_translate("MainWindow", "窗口置顶"))
        ui.pip_taobao_action.setText(_translate("MainWindow", "高速源安装库"))
        ui.independent_run_action.setText(_translate("MainWindow", "独立窗口运行"))

        # 编译菜单项文本
        ui.single_file_action.setText(_translate("MainWindow", "单文件模式"))
        ui.add_data_action.setText(_translate("MainWindow", "导入资源"))
        ui.hide_window_action.setText(_translate("MainWindow", "隐藏控制台"))
        ui.admin_privilege_action.setText(_translate("MainWindow", "管理员权限"))
        ui.compile_default_icon_action.setText(_translate("MainWindow", "默认图标"))
        ui.compile_icon_action.setText(_translate("MainWindow", "设置图标"))

        # 帮助菜单项
        ui.tutorial_action.setText(_translate("MainWindow", "使用教程"))
        ui.update_action.setText(_translate("MainWindow", "检查更新"))

        # 关于菜单项
        ui.website_action.setText(_translate("MainWindow", "官方网站"))
        ui.github_action.setText(_translate("MainWindow", "开源地址"))
        ui.email_action.setText(_translate("MainWindow", "2449579731@qq.com"))
        ui.author_github_action.setText(_translate("MainWindow", "GitHub: github.com/cxfjh"))
        ui.uninstall_action.setText(_translate("MainWindow", "卸载程序"))
        ui.reset_action.setText(_translate("MainWindow", "重置程序"))

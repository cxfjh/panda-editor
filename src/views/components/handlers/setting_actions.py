import os
from PySide6 import QtCore
from PySide6.QtWidgets import QDialog, QFileDialog
from src.utils.config_service import get_config_service
from src.utils.dialog_utils import DialogUtils
from src.utils.exceptions import safe_log
from src.views.components.add_data_dialog import AddDataDialog
from src.views.components.handlers.base import HandlerBase


class SettingActions(HandlerBase):
    """设置项切换动作"""

    def init_menu_states(self):
        """
        初始化菜单项的选中状态, 从配置读取

        Args:
            self: 类实例自身
        """
        try:
            settings = get_config_service().get_personal_config()
            if settings:
                # 读取并应用各项配置
                self.ui.dark_mode_action.setChecked(settings.get('darkMode', True))
                self.ui.syntax_highlight_action.setChecked(settings.get('highlightSyntax', True))
                self.ui.window_top_action.setChecked(settings.get('windowTop', False))
                pip_mirror = settings.get('pipMirror', 'taobao')
                self.ui.pip_taobao_action.setChecked(pip_mirror == 'taobao')
                self.ui.hide_window_action.setChecked(settings.get('hideWindow', False))
                self.ui.admin_privilege_action.setChecked(settings.get('adminPrivilege', False))
                self.ui.single_file_action.setChecked(settings.get('singleFileMode', True))
                use_default_icon = settings.get('useDefaultCompileIcon', True)
                self.ui.compile_default_icon_action.setChecked(use_default_icon)
                self.ui.compile_icon_action.setEnabled(not use_default_icon)  # 使用默认图标时禁用自定义选项
                self.ui.independent_run_action.setChecked(settings.get('independentRun', False))
                blockly_visible = bool(settings.get('blocklyPanel', False))
                self.ui.toggle_blockly_action.blockSignals(True)
                self.ui.toggle_blockly_action.setChecked(blockly_visible)
                self.ui.toggle_blockly_action.blockSignals(False)
                self.toggle_blockly(blockly_visible, persist=False)
        except Exception as e:
            safe_log(f"初始化菜单项选中状态时出错: {e}")

    def on_pip_mirror_changed(self):
        """
        切换 pip 源设置

        Args:
            self: 类实例自身
        """
        is_taobao = self.ui.pip_taobao_action.isChecked()
        get_config_service().update_personal_config("pipMirror", "taobao" if is_taobao else "default")

    def on_independent_run_changed(self):
        """
        切换独立运行设置

        Args:
            self: 类实例自身
        """
        independent = self.ui.independent_run_action.isChecked()
        get_config_service().update_personal_config("independentRun", independent)

    def on_hide_window_changed(self):
        """
        切换编译时隐藏窗口设置

        Args:
            self: 类实例自身
        """
        hide = self.ui.hide_window_action.isChecked()
        get_config_service().update_personal_config("hideWindow", hide)

    def on_admin_privilege_changed(self):
        """
        切换编译时管理员权限设置

        Args:
            self: 类实例自身
        """
        admin = self.ui.admin_privilege_action.isChecked()
        get_config_service().update_personal_config("adminPrivilege", admin)

    def on_single_file_changed(self):
        """
        切换编译单文件模式设置

        Args:
            self: 类实例自身
        """
        single_file = self.ui.single_file_action.isChecked()
        get_config_service().update_personal_config("singleFileMode", single_file)

    def on_add_data_changed(self):
        """
        设置编译时导入的资源文件或目录

        Args:
            self: 类实例自身
        """
        try:
            existing_paths = get_config_service().get_personal_config("addDataPaths") or []
            dialog = AddDataDialog(existing_paths, self.ui.main_window)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                paths = dialog.paths()
                get_config_service().update_personal_config("addDataPaths", paths)
                if paths:
                    DialogUtils.show_info(self.ui.main_window, "资源已添加", f"已添加 {len(paths)} 个资源路径\n编译时将自动打包这些资源")
        except Exception as e:
            DialogUtils.show_error(self.ui.main_window, "设置失败", f"无法管理资源路径：\n{e}")

    def on_compile_default_icon_changed(self):
        """
        切换编译默认图标设置

        Args:
            self: 类实例自身
        """
        use_default = self.ui.compile_default_icon_action.isChecked()
        get_config_service().update_personal_config("useDefaultCompileIcon", use_default)

        # 如果切换为使用默认图标, 禁用自定义图标菜单
        self.ui.compile_icon_action.setEnabled(not use_default)

    def on_compile_icon_changed(self):
        """
        设置编译时使用的图标

        Args:
            self: 类实例自身
        """
        try:
            icon_path = QFileDialog.getOpenFileName(self.ui.main_window, "选择编译图标", "", "图标文件 (*.ico);;所有文件 (*)")[0]
            if icon_path:
                icon_path = os.path.normpath(icon_path)
                get_config_service().update_personal_config("compileIconPath", icon_path)
                DialogUtils.show_info(self.ui.main_window, "图标已设置", f"编译图标已设置为：\n{icon_path}\n\n编译时将使用此图标")
        except Exception as e:
            DialogUtils.show_error(self.ui.main_window, "设置失败", f"无法设置编译图标：\n{e}")

    def on_dark_mode_changed(self):
        """
        切换深色模式

        Args:
            self: 类实例自身
        """
        dark_mode = self.ui.dark_mode_action.isChecked()
        get_config_service().update_personal_config("darkMode", dark_mode)

        # 使用标签页管理器应用主题
        self.ui.tab_manager.apply_theme(dark_mode)

        # 更新终端和文件树主题
        self.ui.terminal.apply_theme(dark_mode)
        self.ui.file_tree.apply_theme(dark_mode)
        self.ui.blockly_panel.apply_theme(dark_mode)

    def on_syntax_highlight_changed(self):
        """
        切换语法高亮

        Args:
            self: 类实例自身
        """
        highlight = self.ui.syntax_highlight_action.isChecked()
        get_config_service().update_personal_config("highlightSyntax", highlight)

        # 使用标签页管理器切换语法高亮
        self.ui.tab_manager.toggle_syntax_highlight(highlight)

    def on_window_top_changed(self):
        """
        切换窗口置顶

        Args:
            self: 类实例自身
        """
        window_top = self.ui.window_top_action.isChecked()
        get_config_service().update_personal_config("windowTop", window_top)
        main_window = self.ui.central_widget.window()
        if main_window:
            main_window.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint, window_top)
            main_window.show()

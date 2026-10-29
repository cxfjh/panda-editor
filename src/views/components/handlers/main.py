from src.views.components.handlers.file_actions import FileActions
from src.views.components.handlers.find_actions import FindActions
from src.views.components.handlers.run_actions import RunActions
from src.views.components.handlers.setting_actions import SettingActions
from src.views.components.handlers.ui_tool_actions import UiToolActions
from src.views.components.handlers.view_actions import ViewActions


class MainWindowHandlers(FileActions, FindActions, RunActions, UiToolActions, ViewActions, SettingActions):
    """主窗口动作处理器, 各业务域的方法由 mixin 提供"""

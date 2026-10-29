from PySide6 import QtCore
from src.utils.dialog_utils import DialogUtils
from src.utils.frameless_resize import FramelessResizer
from src.views.components.handlers import MainWindowHandlers
from src.views.components.menus import MenuBuilder
from src.views.main_win.binding import BindingMixin
from src.views.main_win.chrome import WindowChromeMixin
from src.views.main_win.layout import LayoutMixin
from src.views.main_win.startup import StartupMixin
from src.views.main_win.style import StyleMixin


class MainWindowUI(LayoutMixin, StartupMixin, StyleMixin, BindingMixin, WindowChromeMixin):
    """主窗口用户界面类"""

    def __init__(self):
        """
        初始化 UI 组件引用

        Args:
            self: 当前 UI 实例
        """
        self._window_focus_filter = None  # 窗口焦点事件过滤器
        self._shortcuts = []  # 全局快捷键列表
        self.tab_widget = None  # 标签页组件
        self.frameless_resizer = None  # 无边框窗口拉伸支持

    def setup_ui(self, main_window):
        """
        初始化主窗口 UI 布局和组件

        Args:
            self: 当前 UI 实例
            main_window: 主窗口对象
        """
        self.main_window = main_window
        self.handlers = MainWindowHandlers(self)  # 创建事件处理器 绑定所有菜单动作

        # 窗口基础设置
        self._setup_main_window(main_window)  # 设置窗口大小, 无边框等属性
        self._setup_icon(main_window)
        self.frameless_resizer = FramelessResizer(main_window)

        # 菜单系统
        MenuBuilder.create_menus(main_window, self)
        MenuBuilder.create_actions(main_window, self)
        self._setup_central_widget(main_window)

        # 菜单集成与翻译
        self.custom_title_bar.set_menu_bar(self.menu_bar)
        MenuBuilder.build_menu_structure(self)
        self._init_menu_states()  # 从配置恢复菜单勾选状态
        MenuBuilder.setup_translations(main_window, self)
        QtCore.QTimer.singleShot(0, self._fix_menu_bar_width)

        # 编辑器和功能设置, 先注入父窗口, 启动阶段的目录选择等弹窗要靠它挂到主窗口上
        self._init_service_parents(main_window)
        self._setup_text_edit()
        self._setup_style(main_window)  # 应用主题, 字体, 语法高亮
        self._setup_signals_and_slots()
        self._setup_global_shortcuts(main_window)
        self._setup_auto_save()
        self._setup_close_event(main_window)  # 拦截关闭事件 保存状态
        QtCore.QMetaObject.connectSlotsByName(main_window)

    @staticmethod
    def _init_service_parents(main_window):
        """
        为服务模块注入父窗口引用

        Args:
            main_window: 主窗口对象
        """
        DialogUtils.set_parent_widget(main_window)

    def _setup_text_edit(self):
        """
        设置文本编辑区域及相关组件

        Args:
            self: 当前 UI 实例
        """

        # 启动时不预先建空标签, 没有打开文件就保持空白, 需要时由新建/打开动作创建
        self.terminal.set_get_code_callback(lambda: self.tab_manager.get_current_editor().text_all() if self.tab_manager.get_current_editor() else "")  # type: ignore
        self.terminal.set_get_file_path_callback(self.tab_manager.get_current_file_path)  # 当前文件路径以 TabManager 为唯一真相源

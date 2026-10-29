from PySide6 import QtCore, QtGui, QtWidgets
from src.utils.config_service import get_config_service
from src.views.main_win.refs import UiRefs


class WindowChromeMixin(UiRefs):
    """窗口尺寸 位置 图标与最大化按钮相关方法"""

    @staticmethod
    def _setup_main_window(main_window):
        """
        设置主窗口基本属性

        Args:
            main_window: 主窗口对象
        """
        main_window.setObjectName("MainWindow")
        WindowChromeMixin._fit_to_screen(main_window)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(main_window.sizePolicy().hasHeightForWidth())
        main_window.setSizePolicy(size_policy)

        # 隐藏原生标题栏使用自定义标题栏
        main_window.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint |
            QtCore.Qt.WindowType.WindowSystemMenuHint |
            QtCore.Qt.WindowType.WindowMinimizeButtonHint |
            QtCore.Qt.WindowType.WindowMaximizeButtonHint |
            QtCore.Qt.WindowType.WindowCloseButtonHint,
        )

    @staticmethod
    def _fit_to_screen(main_window):
        """
        按屏幕可用区域确定初始大小并居中

        Args:
            main_window: 主窗口对象
        """
        screen = QtWidgets.QApplication.primaryScreen()
        available = screen.availableGeometry()
        width = min(1600, int(available.width() * 0.9))
        height = min(1000, int(available.height() * 0.9))
        main_window.resize(width, height)
        main_window.move(
            available.x() + (available.width() - width) // 2,
            available.y() + (available.height() - height) // 2,
        )

    @staticmethod
    def _setup_icon(main_window):
        """
        设置窗口图标

        Args:
            main_window: 主窗口对象
        """
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(get_config_service().get_app_config("icon_path")), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        main_window.setWindowIcon(icon)

    def _fix_menu_bar_width(self):
        """
        菜单栏宽度固化

        Args:
            self: 当前 UI 实例
        """
        if getattr(self, "menu_bar", None) is None:
            return

        # 临界宽度随字体度量取整浮动, 留 64px 余量确保安全
        self.menu_bar.setMinimumWidth(self.menu_bar.sizeHint().width() + 64)

        # 菜单最小宽度可能把窗口撑大, 等布局稳定后再摆一次位置
        QtCore.QTimer.singleShot(0, lambda: self._center_on_screen(self.main_window))

    @staticmethod
    def _center_on_screen(main_window):
        """
        把窗口摆到主屏可用区域中间

        Args:
            main_window: 主窗口对象
        """
        screen = QtWidgets.QApplication.primaryScreen()
        available = screen.availableGeometry()
        size = main_window.frameSize()
        x = available.x() + max(0, (available.width() - size.width()) // 2)
        y = available.y() + max(0, (available.height() - size.height()) // 2)
        main_window.move(x, y)

    def _on_toggle_maximize(self):
        """
        最大化或还原窗口

        Args:
            self: 当前 UI 实例
        """
        if self.main_window.isMaximized():
            self.main_window.showNormal()
        else:
            self.main_window.showMaximized()

    def _sync_maximize_button(self):
        """
        根据窗口实际状态同步最大化按钮图标, 避免状态失同步

        Args:
            self: 当前 UI 实例
        """
        maximized = self.main_window.isMaximized()
        self.custom_title_bar.max_btn.setText("❐" if maximized else "□")
        self.custom_title_bar.max_btn.setToolTip("还原" if maximized else "最大化")

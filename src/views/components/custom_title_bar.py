from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMenuBar, QPushButton, QWidget
from src.utils.extend import paint_gradient


class TitleMenuBar(QMenuBar):
    """标题栏内嵌菜单栏"""

    def __init__(self, parent=None):
        """
        初始化菜单栏并开启鼠标追踪

        Args:
            parent: 父组件, 一般为自定义标题栏
        """
        super().__init__(parent)
        self._hover_action = None  # 当前悬停的菜单项
        self._last_pad_v = -1  # 上次应用的纵向 padding, 避免重复设样式触发布局抖动
        self.setMouseTracking(True)  # 悬停高亮需要追踪鼠标移动
        self._apply_stylesheet(0)  # 首次给一个空样式, 真正值等 resizeEvent 算出栏高后填

    def resizeEvent(self, event):
        """
        栏高变化后重算纵向 padding, 让命中区铺满整栏

        Args:
            event: QResizeEvent 实例
        """
        super().resizeEvent(event)
        self._apply_stylesheet(self.height())

    def _apply_stylesheet(self, bar_h: int):
        """
        根据栏高动态生成样式表, 纵向 padding 让 QMenuBar 内部 action rect 高度等于栏高

        Args:
            bar_h: 当前菜单栏高度, <=0 时退化为纵向 0 padding
        """
        font_h = self.fontMetrics().height()
        pad_v = max(0, (bar_h - font_h) // 2) if bar_h > 0 else 0
        if pad_v == self._last_pad_v:
            return
        self._last_pad_v = pad_v
        self.setStyleSheet(
            f"""
            QMenuBar {{
                background-color: transparent;
                border: none;
            }}
            QMenuBar::item {{
                padding: {pad_v}px 10px;
                background-color: transparent;
                color: #FFFFFF;
                margin: 0 6px 0 0;
            }}
            QMenuBar::item:selected {{
                background-color: transparent;
            }}
            QMenu {{
                background-color: #2b2d30;
                color: #A9B7C6;
                border: 1px solid #3c3f41;
                border-radius: 6px;
                padding: 4px 0;
            }}
            QMenu::item {{
                padding: 10px 16px;
                border-radius: 4px;
                margin: 2px 4px;
            }}
            QMenu::item:selected {{
                background-color: #214283;
            }}
            QMenu::separator {{
                height: 1px;
                background-color: #515356;
                margin: 4px 8px;
            }}
            """,
        )

    def mouseMoveEvent(self, event):
        """
        悬停位置变化时刷新高亮菜单项

        Args:
            event: QMouseEvent 实例
        """
        super().mouseMoveEvent(event)
        hover = self.actionAt(event.pos())
        if hover is not self._hover_action:
            self._hover_action = hover
            self.update()

    def leaveEvent(self, event):
        """
        鼠标离开时清除菜单项高亮

        Args:
            event: QEvent 实例
        """
        super().leaveEvent(event)
        self._hover_action = None
        self.update()

    def paintEvent(self, event):
        """
        自绘菜单栏底部的悬停高亮条

        Args:
            event: QPaintEvent 实例
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        active = self.activeAction()
        bar_height = self.height()
        for action in self.actions():
            rect = self.actionGeometry(action)
            if not rect.isValid():
                continue

            # 拉高到整栏再居中绘制, 保证文字垂直居中
            rect.setY(0)
            rect.setHeight(bar_height)

            # 项之间留出水平外边距, 避免高亮块贴在一起
            item_rect = rect.adjusted(0, 2, 0, -2)

            # 悬停或已展开的菜单项画圆角半透明高亮底
            if action is self._hover_action or action is active:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(255, 255, 255, 50))
                painter.drawRoundedRect(item_rect, 4, 4)
            painter.setPen(QColor("#FFFFFF"))
            painter.drawText(item_rect, Qt.AlignmentFlag.AlignCenter, action.text())


class _WindowDragMixin:
    """让宿主控件支持按住左键拖动窗口, 需与 QWidget 子类一起使用"""

    _drag_pos = None  # 按下时记录的全局偏移

    def _window_drag_press(self, event) -> bool:
        """
        处理按下事件, 记录拖拽起点

        Args:
            event: 鼠标事件

        Returns:
            bool, True 表示已进入拖拽状态
        """
        if event.button() != Qt.MouseButton.LeftButton:
            return False

        # 点击在按钮上时不拖拽, 交给按钮自身处理
        child = self.childAt(event.pos())  # type: ignore
        if child and isinstance(child, QPushButton):
            return False
        self._drag_pos = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()  # type: ignore
        event.accept()
        return True

    def _window_drag_move(self, event) -> None:
        """
        处理移动事件, 窗口跟随鼠标

        Args:
            event: 鼠标事件
        """
        if self._drag_pos is None or event.buttons() != Qt.MouseButton.LeftButton:
            return
        window = self.window()  # type: ignore

        # 最大化状态下拖拽先还原窗口再移动
        if window.isMaximized():
            window.showNormal()
            self._drag_pos = event.globalPosition().toPoint() - window.frameGeometry().topLeft()
        window.move(event.globalPosition().toPoint() - self._drag_pos)
        event.accept()

    def _window_drag_release(self, event) -> None:
        """
        处理释放事件, 清除拖拽状态

        Args:
            event: 鼠标事件
        """
        self._drag_pos = None
        event.accept()


class CustomTitleBar(_WindowDragMixin, QWidget):
    """自定义标题栏组件"""

    minimize_clicked = Signal()  # 最小化信号
    maximize_clicked = Signal()  # 最大化/还原信号
    close_clicked = Signal()  # 关闭信号

    def __init__(self, title="熊猫编辑器", parent=None, gradient_colors=None, fg_color="#FFFFFF", gradient_alpha=0.85):
        """
        初始化自定义标题栏

        Args:
            title: 窗口标题
            parent: 父窗口
            gradient_colors: 渐变色列表
            fg_color: 文字颜色
            gradient_alpha: 渐变背景透明度
        """
        super().__init__(parent)
        self._drag_pos = None  # 拖拽偏移量
        self._gradient_colors = gradient_colors or ["#667eea", "#764ba2"]  # 默认渐变色
        self._fg_color = fg_color
        self._gradient_alpha = gradient_alpha
        self._menu_bar = None  # 菜单栏引用

        # 启用半透明背景融合效果
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)  # 禁用系统默认背景
        self.setAutoFillBackground(False)  # 禁用自动填充背景
        self._setup_ui(title)

    def _setup_ui(self, title):
        """
        初始化标题栏布局, 左侧放标题文字, 右侧放窗口按钮

        Args:
            title: 标题文字
        """
        self.setFixedHeight(50)
        self.setObjectName("CustomTitleBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标题标签
        self.title_label = _DraggableWidget()  # 使用可拖拽容器包裹标题
        self.title_label.setStyleSheet(
            f"""
            QLabel {{
                color: {self._fg_color};
                font-size: 13px;
                font-weight: bold;
                padding-left: 12px;
                background: transparent;
            }}
        """,
        )

        # 添加标签文字
        title_label_inner = QLabel(title)
        title_label_inner.setStyleSheet(
            f"""
            QLabel {{
                color: {self._fg_color};
                font-size: 13px;
                font-weight: bold;
                padding-left: 12px;
                background: transparent;
            }}
        """,
        )
        title_label_inner.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)  # 垂直居中, 左对齐
        title_layout = QHBoxLayout(self.title_label)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.addWidget(title_label_inner)
        layout.addWidget(self.title_label, 0)  # stretch=0 固定大小

        # 菜单栏容器
        self.menu_container = QWidget()
        self.menu_container.setStyleSheet("background: transparent;")  # 透明背景
        self.menu_layout = QHBoxLayout(self.menu_container)
        self.menu_layout.setContentsMargins(16, 2, 8, 2)  # 与标题文字, 右侧拖拽区留出间距
        self.menu_layout.setSpacing(0)
        layout.addWidget(self.menu_container, 0)  # stretch=0 固定大小

        # 空白拖拽区域
        self.drag_area = _DraggableWidget()
        self.drag_area.setStyleSheet("background: transparent;")
        layout.addWidget(self.drag_area, 1)  # stretch=1 占据剩余空间

        # 最小化按钮
        self.min_btn = QPushButton("─")
        self._setup_button_style(self.min_btn)
        self.min_btn.setToolTip("最小化")
        self.min_btn.clicked.connect(self.minimize_clicked.emit)  # 连接最小化信号
        layout.addWidget(self.min_btn)

        # 最大化/还原按钮
        self.max_btn = QPushButton("□")
        self._setup_button_style(self.max_btn)
        self.max_btn.setToolTip("最大化")
        self.max_btn.clicked.connect(self._on_maximize)  # 连接内部处理方法
        layout.addWidget(self.max_btn)

        # 关闭按钮
        self.close_btn = QPushButton("✕")
        self._setup_button_style(self.close_btn, is_close=True)  # 关闭按钮特殊样式
        self.close_btn.setToolTip("关闭")
        self.close_btn.clicked.connect(self.close_clicked.emit)  # 连接关闭信号
        layout.addWidget(self.close_btn)

    def _setup_button_style(self, btn, is_close=False):
        """
        设置按钮样式

        Args:
            btn: QPushButton 实例
            is_close: 是否为关闭按钮
        """
        hover_color = "#E81123" if is_close else "rgba(255, 255, 255, 0.2)"  # 关闭按钮悬停红色 其他按钮半透明白色
        btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {self._fg_color};
                font-size: 16px;
                font-weight: bold;
                min-width: 45px;
                max-width: 45px;
                min-height: 40px;
                max-height: 40px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """,
        )

    def set_menu_bar(self, menu_bar):
        """
        设置菜单栏 - 将菜单栏集成到标题栏中

        Args:
            menu_bar: TitleMenuBar 实例, 样式表由其自身按栏高动态管理
        """
        self._menu_bar = menu_bar
        self.menu_layout.addWidget(menu_bar)  # 将菜单栏添加到标题栏布局中

    def _on_maximize(self):
        """
        最大化/还原按钮点击处理

        Args:
            self: 类实例自身
        """
        self.maximize_clicked.emit()

    def mouseDoubleClickEvent(self, event):
        """
        双击标题栏最大化/还原

        Args:
            event: QMouseEvent 实例
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self._on_maximize()

    def mousePressEvent(self, event):
        """
        鼠标按下事件 - 用于拖拽窗口

        Args:
            event: QMouseEvent 实例
        """
        if self._window_drag_press(event):
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """
        鼠标移动事件

        Args:
            event: QMouseEvent 实例
        """
        self._window_drag_move(event)

    def mouseReleaseEvent(self, event):
        """
        鼠标释放事件

        Args:
            event: QMouseEvent 实例
        """
        self._window_drag_release(event)

    def paintEvent(self, event):
        """
        绘制半透明渐变背景

        Args:
            event: QPaintEvent 实例
        """
        paint_gradient(self, self._gradient_colors, self._gradient_alpha)


class _DraggableWidget(_WindowDragMixin, QWidget):
    """支持拖拽的空白容器"""

    def mousePressEvent(self, event):
        """
        鼠标按下事件 - 用于拖拽窗口

        Args:
            event: QMouseEvent 实例
        """
        if self._window_drag_press(event):
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """
        鼠标移动事件

        Args:
            event: QMouseEvent 实例
        """
        self._window_drag_move(event)

    def mouseReleaseEvent(self, event):
        """
        鼠标释放事件 - 清除拖拽状态

        Args:
            event: QMouseEvent 实例
        """
        self._window_drag_release(event)

from PySide6 import QtCore
from PySide6.QtWidgets import QApplication
from src.utils.config_service import get_config_service
from src.utils.exceptions import safe_log


class WindowFocusFilter(QtCore.QObject):
    """窗口焦点事件过滤器"""

    def __init__(self, auto_save_callback):
        """
        初始化窗口焦点事件过滤器

        Args:
            auto_save_callback: 自动保存回调函数
        """
        super().__init__()
        self._auto_save_callback = auto_save_callback

    def eventFilter(self, obj, event):
        """
        事件过滤器核心方法

        Args:
            obj: QObject 实例 事件目标对象
            event: QEvent 实例 事件类型和详细信息

        Returns:
            bool, 如果事件已被处理则返回 True 否则返回父类实现的结果
        """

        # 监听窗口失焦事件
        if event.type() == QtCore.QEvent.Type.WindowDeactivate:
            # 应用内弹窗/模态对话框激活导致的失焦不触发自动保存
            if QApplication.activeModalWidget() is None and QApplication.activePopupWidget() is None:
                self._auto_save_callback()  # 触发自动保存
        return super().eventFilter(obj, event)


class FontSizeFilter(QtCore.QObject):
    """字体大小事件过滤器, Ctrl+滚轮缩放并持久化字号"""

    def __init__(self, text_edit, size_changed_callback=None):
        """
        初始化字体大小事件过滤器

        Args:
            text_edit: 编辑器控件 需要应用字体缩放功能的文本编辑器
            size_changed_callback: 字号变化后的回调用于同步外部状态
        """
        super().__init__(text_edit)
        self._text_edit = text_edit
        self._size_changed_callback = size_changed_callback

        # 连续滚动时把写盘合并成一次, 避免每一格都刷一次磁盘
        self._pending_size = None
        self._save_timer = QtCore.QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(400)
        self._save_timer.timeout.connect(self._flush_font_size)
        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self._flush_font_size)

        # 过滤器装在外层控件收不到, 必须一并监听 viewport
        self._viewport = text_edit.viewport() if hasattr(text_edit, "viewport") else None
        if self._viewport is not None:
            self._viewport.installEventFilter(self)  # type: ignore

    def eventFilter(self, obj, event):
        """
        拦截并处理鼠标滚轮事件

        Args:
            obj: QObject 实例 事件目标对象
            event: QEvent 实例 事件类型和详细信息

        Returns:
            bool, 如果事件已被处理则返回 True 否则返回父类实现的结果
        """
        if obj is self._text_edit or obj is self._viewport:
            # 拦截 Ctrl+滚轮事件, 用位与判断, 避免 NumLock 等附加修饰键导致失效
            if event.type() == QtCore.QEvent.Type.Wheel and event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier:  # type: ignore
                font = self._text_edit.font()
                current_size = font.pointSize()
                if current_size <= 0:  # 字体以像素定义时按 96 DPI 折算成磅值
                    current_size = round((font.pixelSize() or 16) * 0.75)

                # 检查滚轮方向
                new_size = current_size + 1 if event.angleDelta().y() > 0 else current_size - 1  # type: ignore

                # 限制字体大小在 6 磅到 90 磅之间
                new_size = max(6, min(90, new_size))
                if new_size == current_size:
                    return True  # 已达边界, 仍拦截事件避免滚动
                font.setPointSize(new_size)
                self._text_edit.set_editor_font(font)

                # 保存字体大小到配置并通知外部同步状态
                self._save_font_size(new_size)
                if self._size_changed_callback:
                    self._size_changed_callback(new_size)
                return True  # 事件已处理, 阻止传递给编辑器

        return super().eventFilter(obj, event)  # 其他事件交给父类处理

    def _save_font_size(self, size):
        """
        记录待保存的字号, 停顿后再写盘

        Args:
            size: 字体大小
        """
        self._pending_size = size
        self._save_timer.start()

    def _flush_font_size(self):
        """
        把待保存的字号写进配置文件, 没有待保存内容时直接返回

        Args:
            self: 类实例自身
        """
        if self._pending_size is None:
            return
        size = self._pending_size
        self._pending_size = None
        try:
            config_service = get_config_service()
            config_service.update_personal_config("fontSize", size)
        except Exception as e:
            safe_log(f"保存字体大小失败: {e}")

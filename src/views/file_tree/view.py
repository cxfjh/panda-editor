import os
import shiboken6
from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget
from src.utils.exceptions import safe_log
from src.views.file_tree import styles
from src.views.file_tree.items import PATH_ROLE, find_item_by_path, set_item_appearance
from src.views.file_tree.loader import DirectoryLoader
from src.views.file_tree.operations import FileOperations


class FileTreeSignals(QObject):
    """文件树信号类"""
    file_selected = Signal(str)  # 文件路径
    file_renamed = Signal(str, str)  # 重命名, 旧路径, 新路径
    file_deleted = Signal(str)  # 删除, 被删除的路径


class FileTreeView(FileOperations, QWidget):
    """文件树视图组件"""

    # 双击时交给系统默认程序打开的二进制类型, 避免以文本方式载入乱码
    _BINARY_EXTS = {
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.ico', '.svg',
        '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
        '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt',
        '.mp3', '.wav', '.flac', '.mp4', '.mkv', '.avi',
        '.ttf', '.otf', '.exe', '.dll', '.pyd', '.pyc', '.so', '.bin',
    }

    def __init__(self, parent=None):
        """
        初始化文件树视图

        Args:
            self: 当前视图实例
            parent: 父窗口部件
        """
        super().__init__(parent)
        self.signals = FileTreeSignals()  # 信号对象用于发出文件选中事件
        self._root_path = ""  # 当前根目录路径
        self._loaders = []  # 活跃的异步加载器列表
        self._dark_mode = True  # 默认深色主题
        self._setup_ui()

    def _setup_ui(self):
        """
        初始化 UI 布局

        Args:
            self: 当前视图实例
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 3, 0, 1)  # 极窄边距
        self.setObjectName("FileTreeView")

        self.tree = QTreeWidget(self)
        self.tree.setHeaderHidden(True)  # 隐藏表头
        self.tree.setAnimated(True)  # 启用展开 折叠动画
        self.tree.setIndentation(20)  # 缩进 20px
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        self.tree.customContextMenuRequested.connect(self._on_context_menu)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree.itemExpanded.connect(self._on_item_expanded)

        self.apply_theme(True)  # 首次按深色主题初始化外观
        layout.addWidget(self.tree)

    def apply_theme(self, dark_mode: bool):
        """
        应用主题样式

        Args:
            self: 当前视图实例
            dark_mode: True 为暗夜模式, False 为浅色模式
        """
        self._dark_mode = dark_mode
        self.setStyleSheet(styles.panel_style(dark_mode))
        self.tree.setStyleSheet(styles.tree_style(dark_mode))

    def set_root_path(self, path: str):
        """
        设置根目录路径并初始化文件树

        Args:
            self: 当前视图实例
            path: 根目录的完整路径
        """
        if not os.path.isdir(path): return
        self._root_path = path
        self.tree.clear()

        root_name = os.path.basename(path) or path
        root_item = QTreeWidgetItem(self.tree, [root_name])
        root_item.setData(0, PATH_ROLE, path)  # 存储路径数据
        root_item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)
        set_item_appearance(root_item, root_name, path)  # 系统文件夹图标
        self._load_children_async(root_item, path)

    def _load_children_async(self, parent_item, parent_path):
        """
        异步加载子节点

        Args:
            self: 当前视图实例
            parent_item: 父树节点对象
            parent_path: 要加载的目录路径
        """
        loader = DirectoryLoader(parent_item, parent_path)
        loader.loaded.connect(lambda item, children, l=loader: self._on_loader_finished(item, children, l))

        # 原生 finished 在线程真正结束后才发, 此时销毁才是安全的
        loader.finished.connect(loader.deleteLater)
        self._loaders.append(loader)
        loader.start()

    def _on_loader_finished(self, parent_item, children_data, loader):
        """
        加载完成回调

        Args:
            self: 当前视图实例
            parent_item: 父树节点
            children_data: 子节点数据列表
            loader: 完成的加载器实例
        """

        # 清理加载器引用, 线程对象等原生 finished 后再销毁, 避免销毁运行中的线程
        if loader in self._loaders:
            self._loaders.remove(loader)

        # 树可能已被重建, 父节点可能已随旧根节点销毁, 这时直接丢弃结果
        if not shiboken6.isValid(parent_item) or parent_item.treeWidget() is None:
            return

        for name, full_path, is_dir in children_data:
            child = QTreeWidgetItem(parent_item, [name])
            child.setData(0, PATH_ROLE, full_path)  # 存储路径
            if is_dir:
                child.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)
            set_item_appearance(child, name, full_path)

        self.tree.viewport().update()

    def _on_item_expanded(self, item: QTreeWidgetItem):
        """
        节点展开时加载子节点

        Args:
            self: 当前视图实例
            item: 被展开的树节点
        """
        if item.childCount() > 0:
            return  # 子节点已加载过 避免重复加载丢失已展开的子树
        path = item.data(0, PATH_ROLE)
        if not path or not os.path.isdir(path): return
        self._load_children_async(item, path)

    def _on_item_double_clicked(self, item: QTreeWidgetItem):
        """
        双击节点时发出文件选中信号

        Args:
            self: 当前视图实例
            item: 被双击的树节点
        """
        path = item.data(0, PATH_ROLE)
        if not path or not os.path.isfile(path):
            return

        # 图片 压缩包等二进制文件用系统默认程序打开, 不塞进编辑器
        if os.path.splitext(path)[1].lower() in self._BINARY_EXTS:
            try:
                os.startfile(path)
            except OSError as e:
                safe_log(f"打开文件失败: {e}")
                self._show_message("error", "错误", f"无法打开文件:\n{e}")
            return

        self.signals.file_selected.emit(path)

    def _on_context_menu(self, pos):
        """
        右键菜单

        Args:
            self: 当前视图实例
            pos: 鼠标点击位置
        """
        item = self.tree.itemAt(pos)
        if not item: return

        path = item.data(0, PATH_ROLE)
        if not path: return

        assert isinstance(path, str)
        dir_path = path if os.path.isdir(path) else os.path.dirname(path)
        assert isinstance(dir_path, str)

        menu = QMenu(self)
        menu.setStyleSheet(styles.menu_style(self._dark_mode))

        new_file_action = QAction("新建文件", menu)
        new_file_action.triggered.connect(lambda: self._new_file(dir_path))
        menu.addAction(new_file_action)

        new_folder_action = QAction("新建文件夹", menu)
        new_folder_action.triggered.connect(lambda: self._new_folder(dir_path))
        menu.addAction(new_folder_action)
        menu.addSeparator()

        rename_action = QAction("重命名", menu)
        rename_action.triggered.connect(lambda: self._rename_item(item, path))
        menu.addAction(rename_action)

        delete_action = QAction("删除", menu)
        delete_action.triggered.connect(lambda: self._delete_item(item, path))
        menu.addAction(delete_action)
        menu.addSeparator()

        # 删除后路径可能已不存在, 只在仍然存在时提供资源管理器入口
        if os.path.exists(path):
            explorer_action = QAction("在资源管理器中打开", menu)
            explorer_action.triggered.connect(lambda: self._open_in_explorer(path))
            menu.addAction(explorer_action)
            menu.addSeparator()

        refresh_action = QAction("刷新", menu)
        refresh_action.triggered.connect(self._refresh)
        menu.addAction(refresh_action)

        menu.exec(self.tree.mapToGlobal(pos))  # 在鼠标位置显示菜单

    def _refresh_parent(self, dir_path: str):
        """
        刷新父目录

        Args:
            self: 当前视图实例
            dir_path: 要刷新的目录路径
        """
        root_item = self.tree.topLevelItem(0)
        if not root_item:
            return

        parent_item = find_item_by_path(root_item, dir_path)
        if not parent_item:
            return

        # 清除所有子节点并重新加载
        parent_item.takeChildren()
        parent_item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)
        self._load_children_async(parent_item, dir_path)

    def _refresh(self):
        """
        刷新整个文件树

        Args:
            self: 当前视图实例
        """
        if self._root_path:
            self.set_root_path(self._root_path)  # 复用建根逻辑

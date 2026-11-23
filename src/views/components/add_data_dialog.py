import os
from PySide6.QtWidgets import QDialog, QFileDialog, QHBoxLayout, QListWidget, QPushButton, QVBoxLayout, QWidget


class AddDataDialog(QDialog):
    """管理编译时导入的资源路径列表"""

    def __init__(self, paths: list[str], parent: QWidget = None):  # type: ignore
        """
        初始化对话框

        Args:
            paths: 已添加的资源路径列表, 对话框内部操作副本不修改入参
            parent: 父窗口
        """
        super().__init__(parent)
        self._paths = list(paths)
        self.setWindowTitle("管理编译资源")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # 列表显示已添加的资源
        self._list_widget = QListWidget()
        for path in self._paths:
            self._list_widget.addItem(path)
        layout.addWidget(self._list_widget)

        # 按钮区域
        btn_layout = QHBoxLayout()
        add_file_btn = QPushButton("添加文件")
        add_folder_btn = QPushButton("添加文件夹")
        remove_btn = QPushButton("移除选中")
        clear_btn = QPushButton("清空全部")
        ok_btn = QPushButton("确定")
        btn_layout.addWidget(add_file_btn)
        btn_layout.addWidget(add_folder_btn)
        btn_layout.addWidget(remove_btn)
        btn_layout.addWidget(clear_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)

        add_file_btn.clicked.connect(self._add_file)
        add_folder_btn.clicked.connect(self._add_folder)
        remove_btn.clicked.connect(self._remove_selected)
        clear_btn.clicked.connect(self._clear_all)
        ok_btn.clicked.connect(self.accept)

    def paths(self) -> list[str]:
        """
        取用户确认后的资源路径列表

        Returns:
            规范化后的资源路径列表
        """
        return self._paths

    def _add_file(self):
        """
        添加文件到资源列表

        Args:
            self: 类实例自身
        """
        paths, _ = QFileDialog.getOpenFileNames(self, "选择资源文件")
        for path_s in paths:
            path_s = os.path.normpath(path_s)
            if path_s not in self._paths:
                self._paths.append(path_s)
                self._list_widget.addItem(path_s)

    def _add_folder(self):
        """
        添加文件夹到资源列表

        Args:
            self: 类实例自身
        """
        folder = QFileDialog.getExistingDirectory(self, "选择资源文件夹")
        if folder:
            folder = os.path.normpath(folder)
            if folder not in self._paths:
                self._paths.append(folder)
                self._list_widget.addItem(folder)

    def _remove_selected(self):
        """
        移除选中的资源

        Args:
            self: 类实例自身
        """
        for item in self._list_widget.selectedItems():
            text = item.text()
            if text in self._paths:
                self._paths.remove(text)
            self._list_widget.takeItem(self._list_widget.row(item))

    def _clear_all(self):
        """
        清空所有资源

        Args:
            self: 类实例自身
        """
        self._list_widget.clear()
        self._paths.clear()

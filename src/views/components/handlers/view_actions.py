from src.utils.config_service import get_config_service
from src.views.components.handlers.base import HandlerBase


# 面板展开时的默认尺寸占比, 记录值无效时使用
_FILE_TREE_RATIO = 0.10
_TERMINAL_RATIO = 0.22
_BLOCKLY_RATIO = 0.40

# 面板展开后的最小像素, 避免窄窗口下按比例算出的尺寸小到看不见
_PANEL_MIN_PX = 160

# 让出尺寸时编辑区保留的最小占比与最小像素, 取两者中的较大值
_EDITOR_MIN_RATIO = 0.20
_EDITOR_MIN_PX = 160


class ViewActions(HandlerBase):
    """视图面板显示动作"""

    def toggle_file_tree(self, checked: bool):
        """
        切换文件窗口显示状态

        Args:
            self: 类实例自身
            checked: True 表示显示, False 表示隐藏
        """
        panel = self.ui.file_tree_wrapper
        self._toggle_panel("file_tree", panel, self.ui.main_splitter, self.ui.right_splitter, _FILE_TREE_RATIO, checked)

    def toggle_terminal(self, checked: bool):
        """
        切换终端窗口显示状态

        Args:
            self: 类实例自身
            checked: True 表示显示, False 表示隐藏
        """
        panel = self.ui.terminal_wrapper
        self._toggle_panel("terminal", panel, self.ui.right_splitter, self.ui.editor_wrapper, _TERMINAL_RATIO, checked)

    def toggle_blockly(self, checked: bool, persist: bool = True):
        """
        切换积木编程面板显示状态

        Args:
            self: 类实例自身
            checked: True 表示显示, False 表示隐藏
            persist: 是否把勾选状态写入配置, 启动恢复时传 False 避免重复落盘
        """
        panel = self.ui.blockly_wrapper
        self._toggle_panel("blockly", panel, self.ui.main_splitter, self.ui.right_splitter, _BLOCKLY_RATIO, checked)
        if persist:
            # 记住开关状态, 下次启动按上次的样子恢复
            get_config_service().update_personal_config("blocklyPanel", checked)

    def _toggle_panel(self, key: str, panel, splitter, donor, ratio: float, visible: bool) -> None:
        """
        切换分割器内某个面板的显示, 折叠出来的空间全部让给指定面板

        Args:
            self: 类实例自身
            key: 面板标识, 用于记录折叠前的尺寸
            panel: 面板控件, 必须是分割器的直接子控件
            splitter: 面板所在的分割器
            donor: 让出或收回空间的面板, 通常是编辑区
            ratio: 记录值无效时按此比例取分割器总长作为默认尺寸
            visible: True 表示显示, False 表示隐藏
        """
        index = splitter.indexOf(panel)
        donor_index = splitter.indexOf(donor)
        sizes = splitter.sizes()
        if index < 0 or donor_index < 0 or len(sizes) <= max(index, donor_index):  # type: ignore
            return

        # 窗口还没显示时尺寸尚未确定, 只折叠不调整, 交给布局的初始比例
        if not self.ui.main_window.isVisible():
            panel.setVisible(visible)
            return

        # 面板已经显示且有正常尺寸时不再重新分配, 避免启动恢复把布局挤动
        if visible and panel.isVisible() and sizes[index] > 0:
            return

        if not visible:
            size = sizes[index]

            # 拖到 0 的面板没有尺寸可让出, 保留上一次记录的值供展开时使用
            if size > 0:
                self._panel_sizes[key] = size
            sizes[index] = 0
            sizes[donor_index] += size
            panel.setVisible(False)
            splitter.setSizes(sizes)
            return

        panel.setVisible(True)
        sizes = splitter.sizes()
        total = sum(sizes)

        # 用户手动拖过的尺寸优先, 但小于最小像素时按最小像素兜底
        size = max(self._panel_sizes.get(key, 0) or self._default_size(total, ratio), _PANEL_MIN_PX)
        available = sizes[donor_index] - self._editor_min_size(total)

        # 编辑区让不出足够尺寸时至少分一半, 避免展开后仍是 0 宽看不见
        size = min(size, available) if available > 0 else sizes[donor_index] // 2

        # 按增量交换尺寸, 面板原本可见时不会凭空少掉一块总长度
        sizes[donor_index] -= size - sizes[index]
        sizes[index] = size
        splitter.setSizes(sizes)

    @staticmethod
    def _default_size(total: int, ratio: float) -> int:
        """
        按分割器总长计算面板的默认尺寸

        Args:
            total: 分割器沿排列方向的总长度
            ratio: 默认尺寸占总长的比例

        Returns:
            计算出的尺寸, 不小于面板最小像素
        """
        return max(int(total * ratio), _PANEL_MIN_PX)

    @staticmethod
    def _editor_min_size(total: int) -> int:
        """
        计算编辑区让出空间时必须保留的最小尺寸

        Args:
            total: 分割器沿排列方向的总长度

        Returns:
            编辑区最小尺寸, 不小于编辑区最小像素
        """
        return max(int(total * _EDITOR_MIN_RATIO), _EDITOR_MIN_PX)

    def on_blockly_code_written(self, file_path: str):
        """
        积木代码写入文件后刷新已打开的标签页

        Args:
            self: 类实例自身
            file_path: 生成的代码写入的文件路径
        """

        # 文件未在编辑器中打开时无需处理, 写入本身已在积木面板内完成
        if not self.ui.tab_manager.reload_tab(file_path):
            return
        self.on_cursor_position_changed()  # 同步状态栏的行列信息

    def toggle_line_numbers(self, checked: bool):
        """
        切换行号显示状态

        Args:
            self: 类实例自身
            checked: True 表示显示行号, False 表示隐藏行号
        """
        self.ui.tab_manager.toggle_line_numbers(checked)

    def on_fold_all(self):
        """
        折叠当前标签页的全部代码

        Args:
            self: 类实例自身
        """
        self.ui.tab_manager.fold_all(expand=False)

    def on_unfold_all(self):
        """
        展开当前标签页的全部代码

        Args:
            self: 类实例自身
        """
        self.ui.tab_manager.fold_all(expand=True)

    def toggle_file_tree_shortcut(self):
        """
        快捷键切换文件窗口

        Args:
            self: 类实例自身
        """
        action = self.ui.toggle_file_tree_action
        action.setChecked(not action.isChecked())

    def toggle_terminal_shortcut(self):
        """
        快捷键切换终端窗口

        Args:
            self: 类实例自身
        """
        action = self.ui.toggle_terminal_action
        action.setChecked(not action.isChecked())

    def toggle_blockly_shortcut(self):
        """
        快捷键切换积木编程面板

        Args:
            self: 类实例自身
        """
        action = self.ui.toggle_blockly_action
        action.setChecked(not action.isChecked())

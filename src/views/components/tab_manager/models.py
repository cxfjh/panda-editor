from src.utils.syntax_high import CnHighlighter
from src.views.components.editor import CodeEditor
from src.views.components.find_replace import FindReplaceDialog


class TabData:
    """单个标签页的数据容器"""

    def __init__(self, file_path: str | None = None):
        """
        初始化标签页数据

        Args:
            self: 类实例自身
            file_path: 文件路径
        """
        self.file_path = file_path  # 文件完整路径
        self.encoding = "utf-8"  # 文件原始编码, 保存时按此写回
        self.has_unsaved_changes = False  # 是否有未保存的修改
        self.editor: CodeEditor | None = None  # 代码编辑器实例
        self.highlighter: CnHighlighter | None = None  # 语法高亮器
        self.syntax_hint = None  # 语法补全管理器
        self.find_replace_dialog: FindReplaceDialog | None = None  # 查找替换对话框
        self.font_filter = None  # 字体大小事件过滤器

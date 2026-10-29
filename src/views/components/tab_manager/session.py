import os
from src.utils.config_service import get_config_service
from src.utils.exceptions import safe_log
from src.utils.text_io import read_text_file_with_encoding
from src.views.components.tab_manager.refs import TabsRefs


class SessionMixin(TabsRefs):
    """标签页会话持久化方法, 由标签管理器混入使用"""

    def save_tabs_state(self):
        """
        保存当前标签页状态到配置

        Args:
            self: 类实例自身
        """
        tabs_info = []
        for index in range(self.tab_widget.count()):
            tab_data = self.tab_data_map.get(index)
            if not tab_data:
                continue

            # 未保存或未命名的标签才需要把全文写进会话, 其余从磁盘恢复
            content = ""
            if tab_data.editor and (tab_data.has_unsaved_changes or not tab_data.file_path):
                content = tab_data.editor.text_all()

            # 没有文件也没有内容的空标签不写进会话, 下次启动就不会多出一个未命名
            if not tab_data.file_path and not content.strip():
                continue

            tabs_info.append(
                {
                    "file_path": tab_data.file_path or "",
                    "content": content,
                    "has_unsaved": tab_data.has_unsaved_changes,
                },
            )

        get_config_service().update_session_config("last_tabs", tabs_info)
        get_config_service().update_session_config("last_active_tab", self.tab_widget.currentIndex())

    def restore_tabs_state(self):
        """
        从配置恢复上次打开的标签页

        Args:
            self: 类实例自身
        """
        tabs_info = get_config_service().get_session_config("last_tabs") or []
        last_active_tab = get_config_service().get_session_config("last_active_tab") or 0

        if not tabs_info:
            return

        # 释放现有标签页的控件资源再清空
        for tab_data in self.tab_data_map.values():
            if tab_data.editor:
                tab_data.editor.deleteLater()
            if tab_data.find_replace_dialog:
                tab_data.find_replace_dialog.deleteLater()
        self.tab_widget.clear()
        self.tab_data_map.clear()

        for tab_info in tabs_info:
            file_path = tab_info.get("file_path") or None
            content = tab_info.get("content", "")
            encoding = "utf-8"
            has_unsaved = bool(tab_info.get("has_unsaved", False))

            # 没有关联文件也没有内容的空标签不必恢复, 否则会凭空多出一个未命名
            if not file_path and not content.strip():
                continue

            # 关联的文件已经不在了, 标签没有恢复的意义, 直接丢掉
            if file_path and not os.path.exists(file_path):  # type: ignore
                safe_log(f"标签 {file_path} 对应的文件已不存在, 跳过恢复")
                continue

            # 仅当文件存在且没有未保存修改时才用磁盘内容覆盖
            if file_path and not has_unsaved:
                try:
                    content, encoding = read_text_file_with_encoding(file_path)  # type: ignore
                except Exception as e:
                    safe_log(f"读取文件 {file_path} 失败: {e}")

            tab_index = self.create_new_tab(file_path=file_path, content=content, encoding=encoding)

            # 恢复未保存标记
            if has_unsaved:
                restored_data = self.tab_data_map.get(tab_index)
                if restored_data:
                    restored_data.has_unsaved_changes = True
                    self._update_tab_title(tab_index)

        # 恢复上次激活的标签页
        if 0 <= last_active_tab < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(last_active_tab)

    def _remap_tab_data(self):
        """
        重新映射标签页数据

        Args:
            self: 类实例自身
        """
        new_map = { }
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)

            # 查找与该编辑器组件对应的 TabData
            for old_index, tab_data in self.tab_data_map.items():
                if tab_data.editor == widget:
                    new_map[i] = tab_data
                    break
        self.tab_data_map = new_map

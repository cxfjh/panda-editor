import os
from PySide6.QtWidgets import QFileDialog
from src.utils import plugin_loader
from src.utils.app_dialog import MessageDialog, select_item
from src.utils.dialog_utils import DialogUtils
from src.utils.exceptions import safe_log
from src.views.components.handlers.base import HandlerBase


class PluginActions(HandlerBase):
    """插件导入 导出 与重载"""

    def import_plugin(self):
        """
        选择插件压缩包导入, 导入后立即刷新积木

        Args:
            self: 类实例自身
        """
        parent = self.ui.main_window
        zip_path, _ = QFileDialog.getOpenFileName(parent, "导入插件", "", "插件包 (*.zip)")
        if not zip_path:
            return

        # 导入会整个替换同名目录, 先问一次, 免得把改过的插件覆盖掉
        existing_id = plugin_loader.zip_plugin_id(zip_path)
        root = plugin_loader.plugins_root()
        if existing_id and root and os.path.isdir(os.path.join(root, existing_id)):
            if not DialogUtils.ask_question(parent, "插件已存在", f"已安装 {existing_id}，覆盖安装吗？\n\n旧目录会被整个替换。", ):
                return

        try:
            plugin_id = plugin_loader.import_zip(zip_path)
        except Exception as e:
            safe_log(f"导入插件失败: {e}")
            DialogUtils.show_error(parent, "导入失败", f"无法导入插件：\n{e!s}")
            return

        added = self.ui.blockly_panel.reload_plugins()
        info = next((item for item in plugin_loader.loaded_plugins() if item["id"] == plugin_id), None)
        name = info["name"] if info else plugin_id
        DialogUtils.show_info(parent, "导入成功", f"插件 {name} 已导入, 新增积木 {added} 块。")

    def export_plugin(self):
        """
        把已安装的插件打包成可分享的压缩包

        Args:
            self: 类实例自身
        """
        parent = self.ui.main_window
        infos = [item for item in plugin_loader.loaded_plugins() if item["ok"]]
        if not infos:
            DialogUtils.show_warning(parent, "没有插件", "当前没有可导出的插件。")
            return

        chosen = infos[0]
        if len(infos) > 1:
            dialog = MessageDialog(
                parent, "导出插件", "选择要导出的插件：", "question",
                tuple(item["name"] for item in infos), True,
            )
            dialog.exec_centered()
            chosen = next((item for item in infos if item["name"] == dialog.clicked_button), None)
            if chosen is None:
                return

        target, _ = QFileDialog.getSaveFileName(parent, "导出插件", os.path.join(os.path.expanduser("~"), f"{chosen['id']}.zip"), "插件包 (*.zip)")
        if not target:
            return
        try:
            plugin_loader.export_zip(chosen["id"], target)
        except Exception as e:
            safe_log(f"导出插件失败: {e}")
            DialogUtils.show_error(parent, "导出失败", f"无法导出插件：\n{e!s}")
            return
        DialogUtils.show_info(parent, "导出成功", f"插件已保存到：\n{target}\n\n把它发给别人, 对方导入后即可使用。")

    def delete_plugin(self):
        """
        选择一个插件删除, 目录移入回收站并同步积木面板

        Args:
            self: 类实例自身
        """
        parent = self.ui.main_window
        infos = [item for item in plugin_loader.loaded_plugins() if item["ok"]]
        if not infos:
            DialogUtils.show_warning(parent, "没有插件", "当前没有可删除的插件。")
            return

        labels = [f"{item['name']}  ({item['id']})" for item in infos]
        choice = select_item(
            parent, "删除插件", labels, "选择要删除的插件, 插件目录会移入回收站:", DialogUtils.dark_mode(),
        )
        if not choice:
            return

        target = infos[labels.index(choice)]
        if not DialogUtils.ask_question(
                parent, "确认删除", f"确定要删除插件 {target['name']} 吗？\n\n目录会移入回收站, 积木面板同步移除。",
        ):
            return

        try:
            plugin_loader.remove_plugin(target["id"])
        except Exception as e:
            safe_log(f"删除插件失败: {e}")
            DialogUtils.show_error(parent, "删除失败", f"无法删除插件：\n{e!s}")
            return

        self.ui.blockly_panel.reload_plugins()
        sync = getattr(self.ui.blockly_panel, "_plugin_sync", { })
        detail = f"插件 {target['name']} 已移入回收站。"
        if sync.get("removed"):
            detail += f"\n\n已从积木面板移除 {sync['removed']} 块积木。"
        if sync.get("orphans"):
            detail += f"\n\n当前工作区还有 {sync['orphans']} 块来自该插件, 运行前请先删掉。"
        DialogUtils.show_info(parent, "已删除", detail)

    def reload_plugins(self):
        """
        重新扫描插件目录并刷新积木

        Args:
            self: 类实例自身
        """
        self.ui.blockly_panel.reload_plugins()
        sync = getattr(self.ui.blockly_panel, "_plugin_sync", { })
        infos = plugin_loader.loaded_plugins()
        total = sum(1 for item in infos if item["ok"])
        parts = [f"共 {total} 个插件"]
        if sync.get("added"):
            parts.append(f"新增积木 {sync['added']} 块")
        if sync.get("removed"):
            parts.append(f"移除积木 {sync['removed']} 块")
        detail = "，".join(parts) + "。"
        failed = [item for item in infos if not item["ok"]]
        if failed:
            names = "、".join(f"{item['id']} ({item['reason']})" for item in failed)
            detail += f"\n\n未能加载：{names}"
        DialogUtils.show_info(self.ui.main_window, "插件已重新加载", detail)

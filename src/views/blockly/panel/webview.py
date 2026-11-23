import json
import time
from PySide6 import QtCore, QtGui
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEngineSettings
from src.utils import plugin_loader, theme
from src.utils.blockly.bridge import BlocklyBridge
from src.views.blockly.panel import constants
from src.views.blockly.panel.refs import PanelRefs


class WebViewMixin(PanelRefs):
    """页面通道与状态栏相关方法, 由积木面板混入使用"""

    def _setup_web_view(self):
        """
        注册 QWebChannel 通信对象并加载积木页面

        Args:
            self: 当前面板实例
        """
        page = self.view.page()
        settings = self.view.settings()

        # Blockly 页面与其 js 资源同处本地目录, 需放开本地文件互访
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)

        self.bridge = BlocklyBridge(self)  # type: ignore
        self.channel = QWebChannel(self)  # type: ignore
        self.channel.registerObject(constants.CHANNEL_OBJECT, self.bridge)
        page.setWebChannel(self.channel)

        # 页面下发信号 -> Python 侧处理
        self.bridge.page_ready.connect(self._on_page_ready)
        self.bridge.code_submitted.connect(self._on_code_submitted)
        self.bridge.workspace_submitted.connect(self._on_workspace_submitted)
        self.bridge.status_reported.connect(self._on_page_status)
        self.bridge.notice_reported.connect(self._on_page_notice)

        page.setBackgroundColor(QtGui.QColor(theme.colors(self._dark_mode)["bg"]))
        self.view.load(QtCore.QUrl.fromLocalFile(constants.INDEX_PATH))

    def _set_ready(self, ready: bool):
        """
        更新页面就绪状态与按钮可用性

        Args:
            self: 当前面板实例
            ready: True 表示页面可以接收指令
        """
        self._page_ready = ready
        for button in self._buttons:
            button.setEnabled(ready)
        if not ready:
            self._set_status("积木编辑器加载中…")

    def _on_page_ready(self):
        """
        页面初始化完成, 同步主题并允许操作

        Args:
            self: 当前面板实例
        """
        self._set_ready(True)
        self._set_status("积木编辑器已就绪")
        self.bridge.theme_changed.emit(self._dark_mode)
        self.bridge.palette_pinned_changed.emit(self._palette_pinned)

        # 插件积木要先注册再恢复工作区, 否则存档里的插件积木会被当成未知类型丢掉
        self._inject_plugin_blocks()

    def _inject_plugin_blocks(self):
        """
        把插件积木注册进页面, 完成后恢复上次的积木

        Args:
            self: 当前面板实例
        """
        payload = plugin_loader.block_payload()
        if not payload.get("categories"):
            self._restore_workspace()
            return
        script = "window.CN_PLUGIN_API ? window.CN_PLUGIN_API.addBlocks(%s) : 0" % json.dumps(
            payload, ensure_ascii=False,
        )
        self.view.page().runJavaScript(script, lambda _count: self._restore_workspace())

    def reload_plugins(self):
        """
        重新扫描插件并同步到页面, 已删除插件的积木会被移除

        Returns:
            本次新增的积木数量
        """
        self._plugin_sync = { "added": 0, "removed": 0, "orphans": 0 }
        if not self._page_ready:
            return 0
        plugin_loader.load_all()
        payload = plugin_loader.block_payload()
        script = "window.CN_PLUGIN_API ? window.CN_PLUGIN_API.syncBlocks(%s) : null" % json.dumps(
            payload, ensure_ascii=False,
        )
        box = { "result": None }
        loop = QtCore.QEventLoop()

        def done(result):
            """
            收到页面返回值后结束等待

            Args:
                result: 页面返回的新增 移除 残留数量
            """
            box["result"] = result
            loop.quit()

        self.view.page().runJavaScript(script, done)
        QtCore.QTimer.singleShot(3000, loop.quit)
        loop.exec()
        result = self._parse_sync_result(box["result"])
        self._plugin_sync = {
            "added": int(result.get("added") or 0),
            "removed": int(result.get("removed") or 0),
            "orphans": int(result.get("orphans") or 0),
        }
        self._set_status_result(f"插件已重新加载, 新增积木 {self._plugin_sync['added']} 块")
        return self._plugin_sync["added"]

    @staticmethod
    def _parse_sync_result(raw) -> dict:
        """
        解析页面回传的同步结果

        Args:
            raw: 页面返回的 JSON 文本或映射

        Returns:
            含 added removed orphans 的字典, 无法解析时返回空字典
        """
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, str) and raw.strip():
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                return { }
            return data if isinstance(data, dict) else { }
        return { }

    def _set_status(self, message: str):
        """
        更新状态标签

        Args:
            self: 当前面板实例
            message: 状态文本
        """
        self.status_label.setText(message)

    def _set_status_result(self, message: str, hold: float = 3.0):
        """
        显示操作结果, 短时间内不被页面的积木数回报覆盖

        Args:
            self: 当前面板实例
            message: 状态文本
            hold: 屏蔽页面回报的秒数
        """
        self._set_status(message)
        self._status_hold_until = time.monotonic() + hold

    def _on_page_status(self, message: str):
        """
        接收页面回报的状态, 刚展示过操作结果时让位

        Args:
            self: 当前面板实例
            message: 页面给出的状态文本
        """
        if time.monotonic() < self._status_hold_until:
            return
        self._set_status(message)

    def _on_page_notice(self, message: str):
        """
        展示页面发来的重要提示, 停留时间比普通状态更长

        Args:
            self: 当前面板实例
            message: 提示文本
        """
        self._set_status_result(message, hold=8.0)

    def _on_palette_pin_toggled(self, checked: bool):
        """
        切换积木展示区的固定与默认模式

        Args:
            self: 当前面板实例
            checked: True 为固定显示, False 为拖出积木后自动收起
        """
        self._palette_pinned = checked
        self._sync_palette_button()
        if not self._page_ready:
            return
        self._set_status_result("积木区已固定, 会挤占画布" if checked else "积木区已恢复默认")
        self.bridge.palette_pinned_changed.emit(checked)

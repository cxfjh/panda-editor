import os


# 积木页面资源目录, 位于面板包的上一级
ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")  # type: ignore

INDEX_PATH = os.path.join(ASSET_DIR, "index.html")

# QWebChannel 注册名, 需与 assets/js/bridge.js 中的 OBJECT_NAME 保持一致
CHANNEL_OBJECT = "blockly_bridge"

# 目标文件与写入方式在配置中的键名
CONFIG_TARGET_FILE = "blockly_target_file"
CONFIG_WRITE_APPEND = "blockly_write_append"
CONFIG_WORKSPACE_FILE = "blockly_workspace_file"

from PySide6.QtCore import QFileInfo, Qt
from PySide6.QtWidgets import QFileIconProvider, QTreeWidgetItem


# 节点上存放文件路径的数据角色
PATH_ROLE = Qt.ItemDataRole.UserRole

# 系统图标提供器, 跟随操作系统显示文件 文件夹图标
ICON_PROVIDER = QFileIconProvider()


def set_item_appearance(item: QTreeWidgetItem, name: str, full_path: str):
    """
    设置节点显示文本与系统图标

    Args:
        item: 树节点
        name: 文件或目录名
        full_path: 完整路径, 用于取图标
    """
    item.setText(0, name)
    item.setIcon(0, ICON_PROVIDER.icon(QFileInfo(full_path)))


def find_item_by_path(item: QTreeWidgetItem, path: str):
    """
    递归查找路径对应的树节点

    Args:
        item: 起始树节点
        path: 目标路径

    Returns:
        匹配的树节点, 未找到时返回 None
    """
    if item.data(0, PATH_ROLE) == path:
        return item
    for index in range(item.childCount()):
        result = find_item_by_path(item.child(index), path)  # type: ignore
        if result:
            return result
    return None

from src.utils import theme
from src.views.components.panel_styles import container_style


def panel_style(dark_mode: bool) -> str:
    """
    生成文件树面板的样式

    Args:
        dark_mode: True 为暗夜模式, False 为浅色模式

    Returns:
        可直接设置到文件树视图的样式表
    """
    c = theme.colors(dark_mode)
    return container_style(c, "FileTreeView", "panel_bg")


def tree_style(dark_mode: bool) -> str:
    """
    生成树控件的样式

    Args:
        dark_mode: True 为暗夜模式, False 为浅色模式

    Returns:
        可直接设置到树控件的样式表
    """
    c = theme.colors(dark_mode)
    return f"""
            QTreeWidget {{
                background-color: {c['panel_bg']};
                color: {c['fg']};
                border: none;
                border-right: 1px solid {c['border']};
            }}
            QTreeWidget::viewport {{
                background-color: {c['panel_bg']};
            }}
            QTreeWidget::item {{
                padding: 4px;
            }}
            QTreeWidget::item:hover {{
                background-color: {c['hover']};
            }}
            QTreeWidget::item:selected {{
                background-color: {c['selected']};
            }}
        """


def menu_style(dark_mode: bool) -> str:
    """
    生成右键菜单的样式

    Args:
        dark_mode: True 为暗夜模式, False 为浅色模式

    Returns:
        可直接设置到菜单的样式表
    """
    if dark_mode:
        menu_bg = "#3c3f41"
        menu_fg = "#A9B7C6"
        menu_border = "#515356"
        menu_selected = "#214283"
        menu_separator = "#515356"
    else:
        menu_bg = "#FFFFFF"
        menu_fg = "#000000"
        menu_border = "#D1D5DB"
        menu_selected = "#B4D7FF"
        menu_separator = "#D1D5DB"
    return f"""
            QMenu {{
                background-color: {menu_bg};
                color: {menu_fg};
                border: 1px solid {menu_border};
                border-radius: 6px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 8px 24px;
                border-radius: 4px;
                margin: 2px 4px;
            }}
            QMenu::item:selected {{
                background-color: {menu_selected};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {menu_separator};
                margin: 4px 8px;
            }}
            """

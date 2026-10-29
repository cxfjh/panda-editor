def build_tab_style(colors: dict[str, str]) -> str:
    """
    生成标签页的样式表

    Args:
        colors: 主题色板

    Returns:
        可直接设置到标签控件的样式表
    """
    return f"""
            QTabWidget::pane {{
                border: none;
                background-color: transparent;
            }}
            QTabBar::tab {{
                background-color: {colors['panel_bg']};
                color: {colors['fg']};
                padding: 8px 12px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {colors['bg']};
                border-bottom: 2px solid #569CDE;
            }}
            QTabBar::tab:hover {{
                background-color: {colors['border']};
            }}
            """

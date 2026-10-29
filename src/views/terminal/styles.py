from src.views.components.panel_styles import compact_button_style, container_style as panel_container_style, line_edit_style


def stop_button_style(fg: str, border: str, danger: str) -> str:
    """
    生成停止按钮样式

    Args:
        fg: 文字颜色
        border: 边框颜色
        danger: 悬停警示色

    Returns:
        样式表文本
    """
    return compact_button_style(fg, border, danger)


def panel_style(colors: dict[str, str]) -> str:
    """
    生成终端面板样式

    Args:
        colors: 主题色板

    Returns:
        可直接设置到终端组件的样式表
    """
    return panel_container_style(colors, "TerminalWidget")


def output_style(colors: dict[str, str]) -> str:
    """
    生成输出区样式

    Args:
        colors: 主题色板

    Returns:
        可直接设置到输出控件的样式表
    """
    return f"QPlainTextEdit {{ background-color: {colors['bg']}; color: {colors['fg']}; border: none; border-top: 1px solid {colors['border']}; }}"


def input_style(colors: dict[str, str]) -> str:
    """
    生成输入行样式

    Args:
        colors: 主题色板

    Returns:
        可直接设置到输入框的样式表
    """
    return line_edit_style(colors, borderless=True)


def container_style(colors: dict[str, str]) -> str:
    """
    生成输入行容器样式

    Args:
        colors: 主题色板

    Returns:
        可直接设置到容器的样式表
    """
    return f"QWidget {{ background-color: {colors['input_bg']}; }}"

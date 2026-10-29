from src.views.components.panel_styles import container_style, line_edit_style, tool_button_style


def button_style(c: dict[str, str], primary: bool = False, toggle: bool = False) -> str:
    """
    生成工具栏按钮样式

    Args:
        c: 主题色板
        primary: 是否为主按钮
        toggle: 是否为开关按钮, 按下时高亮

    Returns:
        样式表文本
    """
    return tool_button_style(c, primary, toggle)


def panel_style(c: dict[str, str]) -> str:
    """
    生成面板底色样式

    Args:
        c: 主题色板

    Returns:
        样式表文本
    """
    return container_style(c, "BlocklyPanel", border=False)


def card_style(c: dict[str, str]) -> str:
    """
    生成工具栏与目标文件行的卡片样式

    Args:
        c: 主题色板

    Returns:
        样式表文本
    """
    return (
        f"QFrame#BlocklyToolbar, QFrame#BlocklyTargetRow {{ "
        f"background-color: {c['panel_bg']}; "
        f"border: 1px solid {c['border']}; border-radius: 8px; }}"
    )


def status_style(c: dict[str, str]) -> str:
    """
    生成状态徽标样式

    Args:
        c: 主题色板

    Returns:
        样式表文本
    """
    return (
        f"QLabel {{ color: {c['margin_fg']}; background-color: {c['bg']}; "
        f"border: 1px solid {c['border']}; border-radius: 10px; "
        f"padding: 1px 10px; font-size: 11px; }}"
    )


def target_label_style(c: dict[str, str]) -> str:
    """
    生成目标文件标签样式

    Args:
        c: 主题色板

    Returns:
        样式表文本
    """
    return f"QLabel {{ color: {c['margin_fg']}; background-color: transparent; font-size: 12px; }}"


def target_edit_style(c: dict[str, str]) -> str:
    """
    生成目标文件输入框样式

    Args:
        c: 主题色板

    Returns:
        样式表文本
    """
    return line_edit_style(c, mono=True)


def mode_combo_style(c: dict[str, str]) -> str:
    """
    生成写入方式下拉框样式

    Args:
        c: 主题色板

    Returns:
        样式表文本
    """
    return (
        f"QComboBox {{ background-color: {c['bg']}; color: {c['fg']}; "
        f"border: 1px solid {c['border']}; border-radius: 6px; padding: 4px 8px; font-size: 12px; }}"
        f"QComboBox:hover {{ border-color: {c['border_strong']}; }}"
        f"QComboBox::drop-down {{ border: none; width: 16px; }}"
        f"QComboBox QAbstractItemView {{ background-color: {c['panel_bg']}; color: {c['fg']}; "
        f"padding: 2px; outline: none; "
        f"selection-background-color: {c['accent']}; selection-color: #FFFFFF; "
        f"border: 1px solid {c['border']}; }}"
    )

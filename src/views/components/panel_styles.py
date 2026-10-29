def container_style(colors: dict[str, str], object_name: str, background_key: str = "bg", border: bool = True) -> str:
    """
    生成面板容器样式, 文件树 终端 积木面板共用

    Args:
        colors: 主题色板
        object_name: 控件的 objectName
        background_key: 背景色取自哪个色名
        border: 是否描边

    Returns:
        样式表文本
    """
    style = f"QWidget#{object_name} {{ background-color: {colors[background_key]};"
    if border:
        style += f" border: 1px solid {colors['border']};"
    return style + " }"


def tool_button_style(colors: dict[str, str], primary: bool = False, toggle: bool = False) -> str:
    """
    生成工具栏按钮样式

    Args:
        colors: 主题色板
        primary: 是否为主按钮
        toggle: 是否为开关按钮, 按下时高亮

    Returns:
        样式表文本
    """
    c = colors
    if primary:
        return (
            f"QPushButton {{ background-color: {c['accent']}; color: #FFFFFF; border: none; "
            f"border-radius: 6px; padding: 5px 14px; font-size: 12px; min-height: 16px; }}"
            f"QPushButton:hover {{ background-color: #6BAEEF; }}"
            f"QPushButton:pressed {{ background-color: #4A8AC7; }}"
            f"QPushButton:disabled {{ background-color: {c['border']}; color: {c['margin_fg']}; }}"
        )
    checked_style = (
        f"QPushButton:checked {{ background-color: {c['accent']}; border-color: {c['accent']}; color: #FFFFFF; }}"
        f"QPushButton:checked:hover {{ background-color: #6BAEEF; border-color: #6BAEEF; }}"
        if toggle
        else ""
    )
    return (
        f"QPushButton {{ background-color: transparent; color: {c['fg']}; "
        f"border: 1px solid {c['border']}; border-radius: 6px; padding: 5px 12px; font-size: 12px; min-height: 16px; }}"
        f"QPushButton:hover {{ background-color: {c['hover']}; border-color: {c['border_strong']}; color: {c['fg_strong']}; }}"
        f"QPushButton:pressed {{ background-color: {c['input_bg']}; }}"
        f"QPushButton:disabled {{ color: {c['margin_fg']}; border-color: {c['border']}; }}"
        f"{checked_style}"
    )


def compact_button_style(fg: str, border: str, danger: str) -> str:
    """
    生成小尺寸按钮样式, 终端停止按钮使用

    Args:
        fg: 文字颜色
        border: 边框颜色
        danger: 悬停警示色

    Returns:
        样式表文本
    """
    return (
        f"QPushButton {{ background-color: transparent; color: {fg}; "
        f"border: 1px solid {border}; border-radius: 3px; padding: 2px 6px; }}"
        f"QPushButton:hover {{ background-color: {danger}; color: #FFFFFF; border-color: {danger}; }}"
        f"QPushButton:disabled {{ color: {border}; border-color: {border}; }}"
    )


def line_edit_style(colors: dict[str, str], borderless: bool = False, mono: bool = False) -> str:
    """
    生成单行输入框样式

    Args:
        colors: 主题色板
        borderless: 是否去掉边框, 终端输入行用
        mono: 是否使用等宽字体, 路径输入用

    Returns:
        样式表文本
    """
    c = colors
    if borderless:
        return f"QLineEdit {{ background-color: {c['input_bg']}; color: {c['fg']}; border: none; }}"
    font = "font-family: Consolas, 'Courier New', monospace; font-size: 11px; " if mono else ""
    return (
        f"QLineEdit {{ background-color: {c['bg']}; color: {c['fg']}; "
        f"border: 1px solid {c['border']}; border-radius: 6px; padding: 4px 8px; "
        f"{font}}}"
        f"QLineEdit:focus {{ border-color: {c['accent']}; }}"
    )

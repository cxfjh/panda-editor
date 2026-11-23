"""主题配色表, 深色与浅色两套"""

# 深色主题
DARK: dict[str, str] = {
    "bg": "#1e1f22",  # 主背景
    "panel_bg": "#2b2d30",  # 面板背景, 文件树/终端/标签栏
    "input_bg": "#2b2d30",  # 输入框背景
    "fg": "#A9B7C6",  # 主文字
    "fg_strong": "#E8E8E8",  # 强调文字
    "border": "#3c3f41",  # 常规边框
    "border_strong": "#515356",  # 菜单/弹窗边框
    "hover": "#323438",  # 列表悬停背景
    "selected": "#214283",  # 选中背景
    "menu_bg": "#3c3f41",  # 右键菜单背景
    "margin_bg": "#252526",  # 行号边栏背景
    "margin_fg": "#858585",  # 行号边栏文字
    "caret_line": "#2A2D2E",  # 当前行背景
    "fold": "#858585",  # 折叠标记
    "danger_hover": "#C42B1C",  # 终止按钮悬停
    "accent": "#569CDE",  # 强调色, 参数高亮/括号配对
    "brace_bad": "#F44747",  # 括号配对失败
}

# 浅色主题
LIGHT: dict[str, str] = {
    "bg": "#FFFFFF",
    "panel_bg": "#F0F0F0",
    "input_bg": "#F0F0F0",
    "fg": "#000000",
    "fg_strong": "#000000",
    "border": "#D1D5DB",
    "border_strong": "#D1D5DB",
    "hover": "#E4E7EB",
    "selected": "#B4D7FF",
    "menu_bg": "#FFFFFF",
    "margin_bg": "#F3F3F3",
    "margin_fg": "#6E6E6E",
    "caret_line": "#E8E8E8",
    "fold": "#6E6E6E",
    "danger_hover": "#C42B1C",
    "accent": "#1E50B4",
    "brace_bad": "#C80000",
}


def colors(dark_mode: bool) -> dict[str, str]:
    """
    取指定主题的色板

    Args:
        dark_mode: True 返回深色主题

    Returns:
        色名到色值的字典
    """
    return DARK if dark_mode else LIGHT


def bgr_int(hex_color: str) -> int:
    """
    '#RRGGBB' 转 Scintilla 需要的 0xBBGGRR 整数颜色

    Args:
        hex_color: 十六进制颜色文本

    Returns:
        Scintilla 颜色整数
    """
    text = hex_color.lstrip('#')
    red, green, blue = int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)
    return (blue << 16) | (green << 8) | red


def color_int(color) -> int:
    """
    QColor 转 Scintilla 需要的 0xBBGGRR 整数颜色

    Args:
        color: 待转换的颜色对象

    Returns:
        Scintilla 颜色整数
    """
    return (color.blue() << 16) | (color.green() << 8) | color.red()

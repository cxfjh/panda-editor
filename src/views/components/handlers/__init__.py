"""
主窗口动作处理器
"""
from src.views.components.handlers.base import URL_AUTHOR, URL_EMAIL, URL_REPO, URL_TUTORIAL, URL_WEBSITE, HandlerBase, is_cn_path
from src.views.components.handlers.main import MainWindowHandlers


__all__ = [
    "URL_AUTHOR",
    "URL_EMAIL",
    "URL_REPO",
    "URL_TUTORIAL",
    "URL_WEBSITE",
    "HandlerBase",
    "MainWindowHandlers",
    "is_cn_path",
]

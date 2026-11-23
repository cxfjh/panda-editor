"""
多标签编辑器管理
"""

from src.views.components.tab_manager.manager import TabManager
from src.views.components.tab_manager.models import TabData
from src.views.components.tab_manager.paths import is_within


__all__ = ["TabData", "TabManager", "is_within"]

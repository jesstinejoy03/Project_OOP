"""One ttk.Frame subclass per screen of the application.

Importing from `gui.tabs` gives the whole set, so `gui.app` does not need to know
which module each tab lives in.
"""
from gui.tabs.common import ALL, EMOTION_COLORS, EXPECTED_ERRORS, show_error
from gui.tabs.coping_tab import CopingTab
from gui.tabs.history_tab import HistoryTab
from gui.tabs.journal_tab import JournalTab
from gui.tabs.resources_tab import ResourcesTab

__all__ = ["ALL", "EMOTION_COLORS", "EXPECTED_ERRORS", "show_error",
           "JournalTab", "CopingTab", "HistoryTab", "ResourcesTab"]

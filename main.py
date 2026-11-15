"""Entry point: python main.py"""
import sys
import tkinter as tk
from tkinter import messagebox

import config
from gui.app import MoodJournalApp
from services.classifier import ClassifierError, EmotionClassifier
from services.database import DatabaseError, DatabaseManager
from services.journal_service import JournalService
from services.recommender import CopingRecommender
from services.safety import SafetyCheck


def enable_high_dpi() -> None:
    """Let Windows scale the window instead of bitmap-stretching it.

    Without this Tk text looks blurry on any display with scaling above 100%.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)     # type: ignore[attr-defined]
    except (AttributeError, OSError, ValueError):
        pass                                              # older Windows: keep the default


def show_startup_error(message: str) -> None:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Cannot start", message)
    root.destroy()


def main() -> int:
    enable_high_dpi()
    try:
        database = DatabaseManager(config.DB_PATH)
        classifier = EmotionClassifier()
        classifier.load()          # raises if the real model has not been trained
    except (DatabaseError, ClassifierError) as exc:
        show_startup_error(str(exc))
        return 1

    service = JournalService(database, classifier, CopingRecommender(database), SafetyCheck())
    app = MoodJournalApp(service)
    try:
        app.mainloop()
    finally:
        database.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

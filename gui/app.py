"""Main application window."""
import tkinter as tk
from tkinter import ttk

from gui.exercise_window import ExerciseWindow
from gui.tabs import (CopingTab, EXPECTED_ERRORS, HistoryTab, JournalTab,
                      ResourcesTab, show_error)

WINDOW_SIZE = "860x700"
MIN_SIZE = (760, 600)


class MoodJournalApp(tk.Tk):
    def __init__(self, service):
        super().__init__()
        self.title("Mood Journal & Coping Companion")
        self.geometry(WINDOW_SIZE)
        self.minsize(*MIN_SIZE)
        ttk.Style(self).theme_use("clam")

        self.service = service
        self.last_emotion = None

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)
        self._journal = JournalTab(self.notebook, self)
        self._coping = CopingTab(self.notebook, self)
        self._history = HistoryTab(self.notebook, self)
        self._resources = ResourcesTab(self.notebook, self)
        for tab, title in ((self._journal, "Journal"), (self._coping, "Coping toolkit"),
                           (self._history, "History"), (self._resources, "About & support")):
            self.notebook.add(tab, text=title)

    def start_exercise(self, exercise, emotion):
        """Open the exercise window; save the rating against `emotion` afterwards.

        `emotion` may be None when the user did not come from a classification;
        the recommender then files the rating under every emotion the exercise
        helps with.
        """
        def on_rated(rated_exercise, rating):
            try:
                self.service.rate_exercise(rated_exercise, emotion, rating)
            except EXPECTED_ERRORS as exc:
                show_error(exc)

        ExerciseWindow(self, exercise, on_rated)

    def refresh_history(self):
        self._history.refresh()

    def focus_coping(self):
        """Bring the coping toolkit to the front (used when a guess is uncertain)."""
        self.notebook.select(self._coping)

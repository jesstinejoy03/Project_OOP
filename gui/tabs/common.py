"""Shared helpers for the tab frames: error dialogs and UI constants."""
from tkinter import messagebox

from services.classifier import ClassifierError
from services.database import DatabaseError
from services.export import ExportError

ALL = "All"

EMOTION_COLORS = {"sadness": "#4c78a8", "joy": "#f2cf5b", "love": "#e377c2",
                  "anger": "#d62728", "fear": "#9467bd", "surprise": "#ff9f4a"}

# Errors the GUI knows how to explain to the user instead of crashing.
EXPECTED_ERRORS = (ValueError, DatabaseError, ClassifierError, ExportError, RuntimeError)


def show_error(exc: Exception) -> None:
    """Translate any expected exception into a friendly dialog."""
    if isinstance(exc, ValueError):
        messagebox.showwarning("Please check your input", str(exc))
    else:
        messagebox.showerror("Something went wrong", str(exc))

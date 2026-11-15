"""About & support tab: disclaimer, model details, and data ownership."""
from tkinter import filedialog, messagebox, ttk

from gui.tabs.common import EXPECTED_ERRORS, show_error
from services.export import EXPORT_FILETYPES

DISCLAIMER = (
    "This app is a self-reflection tool. It is not a medical device and cannot "
    "diagnose, treat or replace professional help.\n\n"
    "If you are struggling, talk to someone you trust, your university counselling "
    "service or a mental health professional. If you think you might hurt yourself "
    "or someone else, contact your local emergency number straight away."
)

HOW_IT_WORKS = (
    "How emotion detection works: your text is cleaned, split into sentence-sized "
    "chunks, converted to TF-IDF features and classified by a logistic regression "
    "model. It can miss sarcasm and context, so treat its guess as a prompt for "
    "reflection, not as a fact."
)


class ResourcesTab(ttk.Frame):
    """Disclaimer, support advice and model details."""

    def __init__(self, master, app):
        super().__init__(master, padding=14)
        self._app = app
        ttk.Label(self, text="About & support",
                  font=("TkDefaultFont", 14, "bold")).pack(anchor="w")
        ttk.Label(self, text=self._about_text(), wraplength=780,
                  justify="left").pack(anchor="w", pady=10)

        ttk.Label(self, text="Your data", font=("TkDefaultFont", 12, "bold")).pack(anchor="w")
        ttk.Label(self, text="Entries live only on this computer, in a local SQLite "
                             "file. Nothing is uploaded. You can copy them out or "
                             "delete them at any time.",
                  wraplength=780, justify="left").pack(anchor="w", pady=(0, 8))

        buttons = ttk.Frame(self)
        buttons.pack(anchor="w")
        ttk.Button(buttons, text="Export my data…",
                   command=self._export).pack(side="left")
        ttk.Button(buttons, text="Delete all data…",
                   command=self._delete_all).pack(side="left", padx=8)

        self._status = ttk.Label(self, text="", wraplength=780, foreground="#2c7a3f")
        self._status.pack(anchor="w", pady=10)

    def _about_text(self) -> str:
        info = self._app.service.model_info()
        accuracy = f"{info['accuracy']:.1%}" if "accuracy" in info else "unknown"
        lines = [DISCLAIMER, HOW_IT_WORKS,
                 f"Model trained on: {info.get('trained_on', 'unknown')}",
                 f"Test accuracy: {accuracy}"]
        if self._app.service.is_demo_model():
            lines.append("WARNING: this is the small built-in demo model, not a real "
                         "training run. Its accuracy is far too low to rely on. "
                         "Rebuild it with: python -m ml.train_model")
        return "\n\n".join(lines)

    # ---- data ownership -----------------------------------------------------
    def _export(self):
        path = filedialog.asksaveasfilename(title="Export journal",
                                            defaultextension=".csv",
                                            filetypes=EXPORT_FILETYPES,
                                            initialfile="mood_journal_export.csv")
        if not path:
            return
        try:
            count = self._app.service.export_journal(path)
        except EXPECTED_ERRORS as exc:
            show_error(exc)
            return
        self._status.config(text=f"Exported {count} entr"
                                 f"{'y' if count == 1 else 'ies'} to {path}",
                            foreground="#2c7a3f")

    def _delete_all(self):
        if not messagebox.askyesno(
                "Delete all data",
                "This permanently deletes every journal entry and every exercise "
                "rating on this computer.\n\nThere is no undo. Export a copy first "
                "if you want to keep them.\n\nContinue?"):
            return
        try:
            removed = self._app.service.clear_all()
        except EXPECTED_ERRORS as exc:
            show_error(exc)
            return
        self._app.refresh_history()
        self._status.config(text=f"Deleted {removed} entr"
                                 f"{'y' if removed == 1 else 'ies'}. The journal is empty.",
                            foreground="#a33")

"""Journal tab: write an entry, see the detected emotion, get suggestions."""
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from gui.tabs.common import EXPECTED_ERRORS, show_error
from services.safety import SUPPORT_MESSAGE


class JournalTab(ttk.Frame):
    """Write an entry, see the detected emotion, get exercise suggestions."""

    def __init__(self, master, app):
        super().__init__(master, padding=14)
        self._app = app
        ttk.Label(self, text="How are you feeling right now?",
                  font=("TkDefaultFont", 14, "bold")).pack(anchor="w")
        ttk.Label(self, text="Write freely. The app will detect the emotion "
                             "and suggest an exercise.").pack(anchor="w", pady=(0, 8))

        box = ttk.Frame(self)
        box.pack(fill="both", expand=True)
        self._text = tk.Text(box, height=9, wrap="word", font=("TkDefaultFont", 11))
        scroll = ttk.Scrollbar(box, command=self._text.yview)
        self._text.config(yscrollcommand=scroll.set)
        self._text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        buttons = ttk.Frame(self)
        buttons.pack(fill="x", pady=8)
        ttk.Button(buttons, text="Analyse & save", command=self._analyse).pack(side="left")
        ttk.Button(buttons, text="Clear",
                   command=lambda: self._text.delete("1.0", "end")).pack(side="left", padx=6)
        ttk.Button(buttons, text="Voice entry (.wav)…", command=self._voice).pack(side="left")

        self._result = ttk.Label(self, text="", font=("TkDefaultFont", 13, "bold"))
        self._result.pack(anchor="w", pady=(10, 0))
        self._note = ttk.Label(self, text="", foreground="#8a6d3b", wraplength=760)
        self._note.pack(anchor="w")
        self._suggestions = ttk.Frame(self)
        self._suggestions.pack(anchor="w", pady=8, fill="x")

    # ---- actions ------------------------------------------------------------
    def _analyse(self):
        try:
            result = self._app.service.submit_text(self._text.get("1.0", "end"))
        except EXPECTED_ERRORS as exc:
            show_error(exc)
            return
        self._show_result(result)
        self._text.delete("1.0", "end")

    def _voice(self):
        path = filedialog.askopenfilename(title="Choose a .wav recording",
                                          filetypes=[("WAV audio", "*.wav")])
        if not path:
            return
        try:
            result = self._app.service.submit_voice(path)
        except EXPECTED_ERRORS as exc:
            show_error(exc)
            return
        self._show_result(result)

    # ---- rendering ----------------------------------------------------------
    def _show_result(self, result):
        prediction = result.prediction
        emotion = prediction.emotion
        self._app.last_emotion = emotion

        if result.low_confidence:
            self._result.config(
                text=f"Emotion unclear (best guess: {emotion.capitalize()}, "
                     f"{prediction.confidence:.0%} confident)")
        else:
            self._result.config(
                text=f"Detected emotion: {emotion.capitalize()} "
                     f"({prediction.confidence:.0%} confident)")
        self._note.config(text=self._note_text(result))

        for child in self._suggestions.winfo_children():
            child.destroy()
        ttk.Label(self._suggestions, text="Suggested for you:").pack(anchor="w")
        for exercise in result.recommendations:
            ttk.Button(self._suggestions, text=f"{exercise.name}  ({exercise.kind})",
                       command=lambda e=exercise: self._app.start_exercise(e, emotion)
                       ).pack(anchor="w", pady=2)
        if result.low_confidence:
            ttk.Button(self._suggestions, text="Browse the whole toolkit",
                       command=self._app.focus_coping).pack(anchor="w", pady=(6, 0))

        self._app.refresh_history()
        if result.needs_support:
            self._show_support_dialog()

    def _show_support_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Support is available")
        dialog.geometry("700x420")
        dialog.minsize(560, 300)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        title = ttk.Label(dialog, text="Support is available",
                          font=("TkDefaultFont", 14, "bold"))
        title.pack(anchor="w", padx=20, pady=(20, 10))

        text = tk.Label(dialog, text=SUPPORT_MESSAGE,
                        font=("TkDefaultFont", 11), justify="left",
                        anchor="w", wraplength=620, padx=20, pady=10)
        text.pack(fill="both", expand=True)

        ttk.Button(dialog, text="Close",
                   command=dialog.destroy).pack(anchor="e", padx=20, pady=(0, 18))

    @staticmethod
    def _note_text(result) -> str:
        notes = []
        if result.low_confidence:
            notes.append("I am not sure about this one. Treat it as a guess: write a "
                         "bit more, or choose an exercise yourself.")
        if result.prediction.chunks > 1:
            notes.append(f"Long entry: the emotion was averaged over "
                         f"{result.prediction.chunks} sentences.")
        return "\n".join(notes)

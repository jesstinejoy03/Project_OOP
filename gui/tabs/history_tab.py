"""History tab: past entries (edit / delete) and an emotion chart."""
import tkinter as tk
from collections import Counter
from tkinter import messagebox, ttk

import config
from gui.tabs.common import ALL, EXPECTED_ERRORS, show_error
from gui.tabs.emotion_chart import EmotionChart

TEXT_WIDTH = 460


class HistoryTab(ttk.Frame):
    """Past entries (edit / delete) and an emotion chart."""

    def __init__(self, master, app):
        super().__init__(master, padding=14)
        self._app = app
        ttk.Label(self, text="Your journal history",
                  font=("TkDefaultFont", 14, "bold")).pack(anchor="w")

        top = ttk.Frame(self)
        top.pack(fill="x", pady=8)
        ttk.Label(top, text="Filter:").pack(side="left")
        self._filter = ttk.Combobox(top, values=[ALL] + config.EMOTIONS,
                                    state="readonly", width=12)
        self._filter.set(ALL)
        self._filter.pack(side="left", padx=6)
        self._filter.bind("<<ComboboxSelected>>", lambda _e: self.refresh())
        ttk.Button(top, text="Edit selected", command=self._edit).pack(side="left", padx=6)
        ttk.Button(top, text="Delete selected", command=self._delete).pack(side="left")

        ttk.Label(self, text="Double-click a row to edit it. Editing re-detects the emotion.",
                  foreground="#5a5a5a").pack(anchor="w", pady=(0, 6))

        self._summary = ttk.Label(self, text="", foreground="#2c7a3f",
                                 wraplength=760)
        self._summary.pack(anchor="w", pady=(0, 6))

        self._tree = ttk.Treeview(self, columns=("date", "emotion", "conf", "text"),
                                  show="headings", height=8)
        for column, title, width in (("date", "Date", 130), ("emotion", "Emotion", 80),
                                     ("conf", "Confidence", 80), ("text", "Entry", TEXT_WIDTH)):
            self._tree.heading(column, text=title)
            self._tree.column(column, width=width)
        self._tree.pack(fill="both", expand=True)
        self._tree.bind("<Double-1>", lambda _e: self._edit())

        self._chart = EmotionChart(self, title="Emotions in the entries shown above")
        self._chart.pack(fill="both", expand=True, pady=(8, 0))
        self.refresh()

    # ---- data ---------------------------------------------------------------
    def refresh(self):
        try:
            entries = self._app.service.history(
                None if self._filter.get() == ALL else self._filter.get())
        except EXPECTED_ERRORS as exc:
            show_error(exc)
            return
        self._tree.delete(*self._tree.get_children())
        for entry in entries:
            self._tree.insert("", "end", iid=str(entry.entry_id), values=(
                entry.created_at.strftime("%Y-%m-%d %H:%M"), entry.emotion or "-",
                f"{entry.confidence:.0%}" if entry.confidence is not None else "-",
                entry.summary(90)))
        # Counts come from the rows on screen, so the chart and the table agree
        # when a filter is applied.
        self._chart.draw(Counter(entry.emotion for entry in entries if entry.emotion))

        summary = self._app.service.mood_summary(days=7)
        total = summary["total_entries"]
        if total:
            dominant = summary["dominant_emotion"]
            counts = summary["counts"]
            detail = ", ".join(f"{emotion.capitalize()}: {count}"
                                for emotion, count in sorted(counts.items()))
            self._summary.config(text=f"Last 7 days: {total} entries • dominant mood: "
                                      f"{dominant.capitalize() if dominant != 'none' else 'none'} • "
                                      f"{detail}")
        else:
            self._summary.config(text="No entries in the last 7 days yet.")

    # ---- actions ------------------------------------------------------------
    def _selected_id(self):
        selection = self._tree.selection()
        if not selection:
            messagebox.showinfo("Choose an entry", "Select an entry from the list first.")
            return None
        return int(selection[0])

    def _edit(self):
        entry_id = self._selected_id()
        if entry_id is None:
            return
        try:
            entry = self._app.service.get_entry(entry_id)
        except EXPECTED_ERRORS as exc:
            show_error(exc)
            return
        if entry is None:
            messagebox.showinfo("Entry not found",
                               "That entry no longer exists. Refreshing the list.")
            self.refresh()
            return

        window = tk.Toplevel(self)
        window.title("Edit entry")
        window.transient(self.winfo_toplevel())
        window.grab_set()
        text = tk.Text(window, width=60, height=10, wrap="word")
        text.insert("1.0", entry.content)
        text.pack(padx=12, pady=12)

        def save():
            try:
                self._app.service.edit_entry(entry_id, text.get("1.0", "end"))
            except EXPECTED_ERRORS as exc:
                show_error(exc)
                return
            window.destroy()
            self._app.refresh_history()

        ttk.Button(window, text="Save changes (re-detects emotion)",
                   command=save).pack(pady=(0, 12))

    def _delete(self):
        entry_id = self._selected_id()
        if entry_id is None:
            return
        if messagebox.askyesno("Delete entry", "Delete this entry permanently?"):
            try:
                self._app.service.delete_entry(entry_id)
            except EXPECTED_ERRORS as exc:
                show_error(exc)
                return
            self.refresh()

"""Coping toolkit tab: browse every exercise and start any of them."""
from tkinter import messagebox, ttk

import config
from gui.tabs.common import ALL


class CopingTab(ttk.Frame):
    """Browse the whole exercise library and start any exercise."""

    def __init__(self, master, app):
        super().__init__(master, padding=14)
        self._app = app
        self._shown = []
        ttk.Label(self, text="Coping toolkit",
                  font=("TkDefaultFont", 14, "bold")).pack(anchor="w")

        top = ttk.Frame(self)
        top.pack(fill="x", pady=8)
        ttk.Label(top, text="Show exercises for:").pack(side="left")
        self._filter = ttk.Combobox(top, values=[ALL] + config.EMOTIONS,
                                    state="readonly", width=12)
        self._filter.set(ALL)
        self._filter.pack(side="left", padx=6)
        self._filter.bind("<<ComboboxSelected>>", lambda _e: self._fill())

        self._tree = ttk.Treeview(self, columns=("type", "helps"),
                                  show="tree headings", height=9)
        self._tree.heading("#0", text="Exercise")
        self._tree.heading("type", text="Type")
        self._tree.heading("helps", text="Helps with")
        self._tree.column("#0", width=220)
        self._tree.column("type", width=100)
        self._tree.column("helps", width=260)
        self._tree.pack(fill="both", expand=True)
        self._tree.bind("<<TreeviewSelect>>", lambda _e: self._describe())
        self._tree.bind("<Double-1>", lambda _e: self._start())

        self._description = ttk.Label(self, text="", wraplength=760)
        self._description.pack(anchor="w", pady=8)
        ttk.Button(self, text="Start selected exercise",
                   command=self._start).pack(anchor="w")
        self._fill()

    def _fill(self):
        choice = self._filter.get()
        self._shown = self._app.service.exercises_for(None if choice == ALL else choice)
        self._tree.delete(*self._tree.get_children())
        for index, exercise in enumerate(self._shown):
            self._tree.insert("", "end", iid=str(index), text=exercise.name,
                              values=(exercise.kind, ", ".join(exercise.target_emotions)))
        self._description.config(text="")

    def _selected(self):
        selection = self._tree.selection()
        return self._shown[int(selection[0])] if selection else None

    def _describe(self):
        exercise = self._selected()
        self._description.config(text=exercise.description if exercise else "")

    def _start(self):
        exercise = self._selected()
        if exercise is None:
            messagebox.showinfo("Choose an exercise", "Select an exercise from the list first.")
            return
        choice = self._filter.get()
        # No filter and no earlier entry means "no known emotion"; the recommender
        # then credits the rating to every emotion this exercise targets, instead
        # of filing it under a made-up emotion that is never read again.
        emotion = choice if choice != ALL else self._app.last_emotion
        self._app.start_exercise(exercise, emotion)

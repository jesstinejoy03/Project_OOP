"""ExerciseWindow: runs ANY Exercise by walking through its Steps.

The window never checks which subclass it was given; it only reads
exercise.steps(). That is polymorphism in action.
"""
import math
import time
import tkinter as tk
from tkinter import ttk

from models.exercise import Exercise, Step

MIN_RADIUS, MAX_RADIUS = 30, 90
TICK_MS = 50
WINDOW_SIZE = "480x470"


class ExerciseWindow(tk.Toplevel):
    def __init__(self, master, exercise: Exercise, on_rated):
        super().__init__(master)
        self.title(exercise.name)
        self.geometry(WINDOW_SIZE)
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()                     # one exercise at a time

        self._exercise = exercise
        self._steps = exercise.steps()
        self._on_rated = on_rated
        self._index = 0
        self._timer_id = None
        self._radius = MIN_RADIUS
        self._rating = tk.IntVar(value=3)
        self.protocol("WM_DELETE_WINDOW", self._close)

        ttk.Label(self, text=f"{exercise.name}  ·  {exercise.kind}",
                  font=("TkDefaultFont", 12, "bold")).pack(pady=(14, 4))

        self._body = ttk.Frame(self, padding=12)
        self._body.pack(fill="both", expand=True)

        self._canvas = None
        if any(step.animation for step in self._steps):
            self._canvas = tk.Canvas(self._body, width=220, height=200, highlightthickness=0)
            self._canvas.pack()
            self._circle = self._canvas.create_oval(0, 0, 0, 0, fill="#9ecae1",
                                                    outline="#3182bd", width=2)
            self._draw_circle()

        self._instruction = ttk.Label(self._body, wraplength=420, justify="center",
                                      font=("TkDefaultFont", 13))
        self._instruction.pack(pady=10)
        self._countdown = ttk.Label(self._body, text="")
        self._countdown.pack()
        self._input = tk.Text(self._body, height=4, width=48, wrap="word")
        self._input.bind("<KeyRelease>", self._on_input_change)

        self._buttons = ttk.Frame(self)
        self._buttons.pack(pady=(0, 14))
        self._next = ttk.Button(self._buttons, text="Next", command=self._advance)
        self._next.pack(side="left", padx=6)
        ttk.Button(self._buttons, text="Stop", command=self._close).pack(side="left", padx=6)

        self._show_step()

    # ---- step handling ------------------------------------------------------
    def _show_step(self):
        self._cancel_timer()
        step = self._steps[self._index]
        self._instruction.config(text=step.instruction)
        self._countdown.config(text="")

        self._input.delete("1.0", "end")
        if step.needs_input:
            self._input.pack(pady=6)
            self._input.focus_set()
        else:
            self._input.pack_forget()

        if step.duration:
            self._next.config(state="disabled", text="Next")
            self._run_timed_step(step, time.monotonic())
        else:
            self._update_next_button(step)

    def _update_next_button(self, step: Step) -> None:
        """Enable Next only when a question step actually has an answer."""
        label = "Finish" if self._index == len(self._steps) - 1 else "Next"
        answered = not step.needs_input or bool(self._input.get("1.0", "end").strip())
        self._next.config(text=label, state="normal" if answered else "disabled")

    def _on_input_change(self, _event=None) -> None:
        step = self._steps[self._index]
        if step.needs_input and not step.duration:
            self._update_next_button(step)

    def _run_timed_step(self, step: Step, started: float) -> None:
        duration = step.duration
        if not duration:                    # untimed step: nothing to animate
            return
        elapsed = time.monotonic() - started
        fraction = min(elapsed / duration, 1.0)
        if step.animation == "expand":
            self._radius = MIN_RADIUS + (MAX_RADIUS - MIN_RADIUS) * fraction
        elif step.animation == "contract":
            self._radius = MAX_RADIUS - (MAX_RADIUS - MIN_RADIUS) * fraction
        elif step.animation == "hold":
            self._radius = MAX_RADIUS
        self._draw_circle()
        remaining = max(math.ceil(duration - elapsed), 0)
        self._countdown.config(text=f"{remaining} s")
        if fraction >= 1.0:
            self._advance()
        else:
            self._timer_id = self.after(TICK_MS, self._run_timed_step, step, started)

    def _advance(self) -> None:
        self._cancel_timer()
        if self._index >= len(self._steps) - 1:
            self._show_rating()
        else:
            self._index += 1
            self._show_step()

    def _draw_circle(self) -> None:
        if self._canvas is None:
            return
        cx, cy, r = 110, 100, self._radius
        self._canvas.coords(self._circle, cx - r, cy - r, cx + r, cy + r)

    # ---- rating -------------------------------------------------------------
    def _show_rating(self) -> None:
        self._cancel_timer()
        for child in self._body.winfo_children():
            child.destroy()
        self._canvas = None                 # the widget above no longer exists
        for child in self._buttons.winfo_children():
            child.destroy()
        ttk.Label(self._body, text="How helpful was this exercise?",
                  font=("TkDefaultFont", 13)).pack(pady=(40, 10))
        row = ttk.Frame(self._body)
        row.pack()
        for value in range(1, 6):
            ttk.Radiobutton(row, text=str(value), value=value,
                            variable=self._rating).pack(side="left", padx=8)
        ttk.Label(self._body, text="1 = not helpful   ·   5 = very helpful").pack(pady=6)
        ttk.Button(self._buttons, text="Save rating", command=self._save_rating).pack(
            side="left", padx=6)
        ttk.Button(self._buttons, text="Skip", command=self._close).pack(side="left", padx=6)

    def _save_rating(self) -> None:
        self._on_rated(self._exercise, self._rating.get())
        self._close()

    def _cancel_timer(self) -> None:
        if self._timer_id is not None:
            self.after_cancel(self._timer_id)
            self._timer_id = None

    def _close(self) -> None:
        self._cancel_timer()
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()

"""Bar chart of how often each emotion has been detected."""
from typing import Dict
from tkinter import ttk

import config
from gui.tabs.common import EMOTION_COLORS

try:  # the chart is optional; the app still works without matplotlib
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    from matplotlib.ticker import MaxNLocator
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

CHART_SIZE = (6, 2.3)
EMPTY_MESSAGE = "No entries yet - write one on the Journal tab."


class EmotionChart(ttk.Frame):
    """Draws the emotion histogram, or an explanatory label when unavailable."""

    def __init__(self, master, title: str = "How often each emotion was detected"):
        super().__init__(master)
        self._title = title
        self._canvas = None
        if not HAS_MATPLOTLIB:
            # Drawn once, not on every refresh: rebuilding it each time stacked
            # an endless pile of labels inside this frame.
            ttk.Label(self, text="Install matplotlib to see the emotion chart.").pack()

    def draw(self, counts: Dict[str, int]) -> None:
        if not HAS_MATPLOTLIB:
            return
        if self._canvas is not None:
            self._canvas.get_tk_widget().destroy()

        figure = Figure(figsize=CHART_SIZE, dpi=100)
        axes = figure.add_subplot(111)
        names = [emotion for emotion in config.EMOTIONS if counts.get(emotion)]
        if names:
            axes.bar(names, [counts[name] for name in names],
                     color=[EMOTION_COLORS[name] for name in names])
        else:
            axes.text(0.5, 0.5, EMPTY_MESSAGE, ha="center", va="center",
                      transform=axes.transAxes)
            axes.set_xticks([])
        axes.set_title(self._title)
        axes.set_ylabel("Entries")
        axes.yaxis.set_major_locator(MaxNLocator(integer=True))
        figure.tight_layout()

        self._canvas = FigureCanvasTkAgg(figure, master=self)
        self._canvas.draw()
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

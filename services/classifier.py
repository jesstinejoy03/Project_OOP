"""EmotionClassifier: wraps the saved scikit-learn pipeline."""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Union

import joblib

import config
from ml.preprocess import clean_text, split_chunks

MISSING_MODEL_MESSAGE = (
    "No trained emotion model was found at:\n    {path}\n\n"
    "Train it first, from the project folder:\n"
    "    python -m ml.train_model\n\n"
    "If you are offline, `python -m ml.train_model --sample` builds a small "
    "demo model instead - it is only meant for smoke tests, not real use."
)


@dataclass(frozen=True)
class Prediction:
    emotion: str
    confidence: float
    chunks: int = 1


class ClassifierError(Exception):
    """Raised when the model cannot be loaded or used."""


class EmotionClassifier:
    """Loads the trained model once and predicts emotions for journal text."""

    def __init__(self, model_path: Union[str, Path] = config.MODEL_PATH,
                 metrics_path: Union[str, Path] = config.METRICS_PATH,
                 allow_training: bool = False):
        self._model_path = Path(model_path)
        self._metrics_path = Path(metrics_path)
        self._allow_training = allow_training
        self._model: Optional[Any] = None

    def load(self) -> None:
        """Load the saved model.

        A missing model is an error rather than a silent fallback: quietly
        swapping in the tiny synthetic model would make the app report emotions
        with barely-better-than-chance accuracy and no warning. Tests and the
        --sample workflow opt in with `allow_training=True`.
        """
        if not self._model_path.exists():
            if not self._allow_training:
                raise ClassifierError(MISSING_MODEL_MESSAGE.format(path=self._model_path))
            from ml.train_model import load_sample, train_and_save
            train, test, source = load_sample()
            train_and_save(train, test, source, model_path=self._model_path,
                           metrics_path=self._metrics_path,
                           confusion_path=self._model_path.with_name("confusion_matrix.png"),
                           min_df=1)
        try:
            self._model = joblib.load(self._model_path)
        except Exception as exc:
            raise ClassifierError(f"Could not load the emotion model: {exc}") from exc

    @property
    def is_ready(self) -> bool:
        return self._model is not None

    @property
    def is_demo(self) -> bool:
        """True when the loaded model was trained on the built-in sample data."""
        return "sample" in str(self.info().get("trained_on", "")).lower()

    def info(self) -> dict:
        """Training details (dataset, accuracy) for the About/Resources screen."""
        try:
            return json.loads(self._metrics_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def predict(self, text: str) -> Prediction:
        model = self._model
        if model is None:
            raise ClassifierError("Model is not loaded.")
        if not clean_text(text):
            raise ValueError("Please write some words so the emotion can be detected.")
        chunks = self._usable_chunks(text)
        if not chunks:
            raise ValueError("Please write some words so the emotion can be detected.")
        probabilities = model.predict_proba(chunks).mean(axis=0)
        best = int(probabilities.argmax())
        return Prediction(str(model.classes_[best]), float(probabilities[best]), len(chunks))

    @staticmethod
    def _usable_chunks(text: str) -> List[str]:
        """Chunks that still contain letters after cleaning.

        A chunk like "12345" cleans to an empty string and would still get a
        probability vector, dragging the average towards the most common class,
        so those chunks are dropped.
        """
        return [chunk for chunk in split_chunks(text) if clean_text(chunk)]

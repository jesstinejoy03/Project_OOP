"""JournalService: the single entry point the GUI talks to.

It coordinates the classifier, database, recommender and safety check so the
GUI contains no business logic and this class can be unit-tested without Tkinter.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import config
from models.entry import JournalEntry, TextEntry, VoiceEntry
from models.exercise import Exercise
from services.classifier import EmotionClassifier, Prediction
from services.database import DatabaseManager, MoodSummary
from services.export import write_export
from services.recommender import CopingRecommender
from services.safety import SafetyCheck

LOW_CONFIDENCE = 0.40


@dataclass
class AnalysisResult:
    entry: JournalEntry
    prediction: Prediction
    recommendations: List[Exercise] = field(default_factory=list)
    needs_support: bool = False

    @property
    def low_confidence(self) -> bool:
        return self.prediction.confidence < LOW_CONFIDENCE


class JournalService:
    def __init__(self, database: DatabaseManager, classifier: EmotionClassifier,
                 recommender: CopingRecommender, safety: SafetyCheck):
        self._db = database
        self._classifier = classifier
        self._recommender = recommender
        self._safety = safety

    # ---- creating entries ---------------------------------------------------
    def submit_text(self, text: str) -> AnalysisResult:
        return self._analyse_and_save(TextEntry(text))

    def submit_voice(self, wav_path: str) -> AnalysisResult:
        return self._analyse_and_save(VoiceEntry.from_audio(wav_path))

    def _analyse_and_save(self, entry: JournalEntry) -> AnalysisResult:
        prediction = self._classifier.predict(entry.content)   # may raise ValueError
        entry.set_emotion(prediction.emotion, prediction.confidence)
        self._db.add_entry(entry)
        return AnalysisResult(
            entry=entry, prediction=prediction,
            recommendations=self._recommender.recommend(prediction.emotion),
            needs_support=self._safety.needs_support(entry.content))

    # ---- reading / updating / deleting -------------------------------------
    def history(self, emotion: Optional[str] = None,
                limit: int = config.HISTORY_LIMIT) -> List[JournalEntry]:
        return self._db.get_entries(emotion=emotion, limit=limit)

    def get_entry(self, entry_id: int) -> Optional[JournalEntry]:
        """One entry by id, or None if it has been deleted."""
        return self._db.get_entry(entry_id)

    def edit_entry(self, entry_id: int, new_text: str) -> AnalysisResult:
        entry = self._db.get_entry(entry_id)
        if entry is None:
            raise ValueError("That entry no longer exists.")
        entry.content = new_text                                # validates
        prediction = self._classifier.predict(entry.content)    # re-detect emotion
        entry.set_emotion(prediction.emotion, prediction.confidence)
        self._db.update_entry(entry)
        return AnalysisResult(entry=entry, prediction=prediction,
                              needs_support=self._safety.needs_support(entry.content))

    def delete_entry(self, entry_id: int) -> bool:
        return self._db.delete_entry(entry_id)

    def emotion_counts(self) -> Dict[str, int]:
        return self._db.emotion_counts()

    def mood_summary(self, days: int = 7) -> MoodSummary:
        """Return a simple recent emotion overview for the last N days."""
        return self._db.recent_mood_summary(days)

    # ---- data ownership -----------------------------------------------------
    def export_journal(self, path) -> int:
        """Write every entry to `path` (CSV or JSON). Returns how many were written."""
        entries = self._db.all_entries()
        write_export(path, entries)
        return len(entries)

    def clear_all(self) -> int:
        """Delete every entry and rating. Returns how many entries were removed."""
        return self._db.delete_all()

    # ---- coping exercises ---------------------------------------------------
    def all_exercises(self) -> List[Exercise]:
        return self._recommender.exercises

    def exercises_for(self, emotion: Optional[str]) -> List[Exercise]:
        if not emotion:
            return self.all_exercises()
        return [e for e in self.all_exercises() if e.helps_with(emotion)]

    def rate_exercise(self, exercise: Exercise, emotion: Optional[str],
                      rating: int) -> None:
        self._recommender.record_rating(exercise, emotion, rating)

    def model_info(self) -> dict:
        return self._classifier.info()

    def is_demo_model(self) -> bool:
        """True when the classifier is the small sample model, not a real one."""
        return self._classifier.is_demo

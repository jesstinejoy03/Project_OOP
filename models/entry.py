"""Journal entry classes.

JournalEntry is an abstract base class. TextEntry and VoiceEntry extend it,
which demonstrates abstraction, inheritance and polymorphism: the rest of the
app only ever talks to the JournalEntry interface.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional


class JournalEntry(ABC):
    """Abstract base class for everything a user can journal."""

    MAX_LENGTH = 2000

    def __init__(self, content: str, created_at: Optional[datetime] = None,
                 emotion: Optional[str] = None, confidence: Optional[float] = None,
                 entry_id: Optional[int] = None):
        self._content = ""
        self._emotion = None
        self._confidence = None
        self.content = content            # goes through the validating setter
        self.created_at = created_at or datetime.now()
        self.entry_id = entry_id
        if emotion is not None:
            self.set_emotion(emotion, confidence if confidence is not None else 0.0)

    # ---- encapsulated state with validation -------------------------------
    @property
    def content(self) -> str:
        return self._content

    @content.setter
    def content(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Entry text cannot be empty.")
        value = value.strip()
        if len(value) > self.MAX_LENGTH:
            raise ValueError(f"Entry is too long (max {self.MAX_LENGTH} characters).")
        self._content = value

    @property
    def emotion(self) -> Optional[str]:
        return self._emotion

    @property
    def confidence(self) -> Optional[float]:
        return self._confidence

    def set_emotion(self, emotion: str, confidence: float) -> None:
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("Confidence must be between 0 and 1.")
        self._emotion = emotion
        self._confidence = confidence

    # ---- abstract interface -----------------------------------------------
    @property
    @abstractmethod
    def source(self) -> str:
        """Short identifier stored in the database ('text', 'voice', ...)."""

    @abstractmethod
    def summary(self, width: int = 60) -> str:
        """One-line description used in the history list."""

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.entry_id}, emotion={self._emotion})"


class TextEntry(JournalEntry):
    """An entry typed by the user."""

    @property
    def source(self) -> str:
        return "text"

    def summary(self, width: int = 60) -> str:
        text = " ".join(self.content.split())
        return text if len(text) <= width else text[: width - 1] + "…"


class VoiceEntry(JournalEntry):
    """An entry transcribed from a spoken recording (stretch feature)."""

    @property
    def source(self) -> str:
        return "voice"

    def summary(self, width: int = 60) -> str:
        text = "[voice] " + " ".join(self.content.split())
        return text if len(text) <= width else text[: width - 1] + "…"

    @classmethod
    def from_audio(cls, wav_path: str) -> "VoiceEntry":
        """Transcribe a .wav file using the optional SpeechRecognition package."""
        try:
            import speech_recognition as sr
        except ImportError as exc:
            raise RuntimeError(
                "Voice entries need the 'SpeechRecognition' package "
                "(pip install SpeechRecognition).") from exc
        recognizer = sr.Recognizer()
        try:
            with sr.AudioFile(wav_path) as source:
                audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)
        except sr.UnknownValueError as exc:
            raise ValueError("Could not understand the audio.") from exc
        except (sr.RequestError, OSError) as exc:
            raise RuntimeError(f"Speech recognition failed: {exc}") from exc
        return cls(text)


ENTRY_TYPES = {"text": TextEntry, "voice": VoiceEntry}


def entry_from_source(source: str, **kwargs) -> JournalEntry:
    """Factory used by the database layer to rebuild the right subclass."""
    return ENTRY_TYPES.get(source, TextEntry)(**kwargs)

"""Coping exercise classes.

Exercise is an abstract base class. Each subclass builds its own list of Steps,
so the GUI can run any exercise through one generic code path (polymorphism).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class Step:
    """One screen of an exercise.

    duration    - seconds to wait automatically (None = user clicks Next)
    needs_input - show a text box for the user's answer
    animation   - 'expand' / 'hold' / 'contract' drives the breathing circle
    """
    instruction: str
    duration: Optional[int] = None
    needs_input: bool = False
    animation: Optional[str] = None


class Exercise(ABC):
    """Abstract coping exercise."""

    def __init__(self, name: str, description: str, target_emotions: List[str]):
        if not name:
            raise ValueError("Exercise needs a name.")
        self._name = name
        self._description = description
        self._targets = tuple(target_emotions)

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def target_emotions(self) -> tuple:
        return self._targets

    def helps_with(self, emotion: str) -> bool:
        return emotion in self._targets

    @property
    @abstractmethod
    def kind(self) -> str:
        """Category label shown in the GUI."""

    @abstractmethod
    def steps(self) -> List[Step]:
        """The ordered steps the user will go through."""

    def __str__(self) -> str:
        return f"{self.name} ({self.kind})"


class BreathingExercise(Exercise):
    """Timed breathing with an animated circle."""

    def __init__(self, name, description, target_emotions,
                 inhale: int, hold: int, exhale: int, cycles: int = 4):
        super().__init__(name, description, target_emotions)
        if min(inhale, exhale, cycles) <= 0 or hold < 0:
            raise ValueError("Breathing timings must be positive.")
        self._inhale, self._hold, self._exhale, self._cycles = inhale, hold, exhale, cycles

    @property
    def kind(self) -> str:
        return "Breathing"

    def steps(self) -> List[Step]:
        result = [Step("Sit comfortably and relax your shoulders. Press Next when ready.")]
        for i in range(1, self._cycles + 1):
            result.append(Step(f"Breathe in… ({i}/{self._cycles})", self._inhale, animation="expand"))
            if self._hold:
                result.append(Step("Hold…", self._hold, animation="hold"))
            result.append(Step("Breathe out slowly…", self._exhale, animation="contract"))
        result.append(Step("Well done. Notice how your body feels now."))
        return result


class GroundingExercise(Exercise):
    """Sensory checklist that brings attention to the present."""

    def __init__(self, name, description, target_emotions, prompts: List[str]):
        super().__init__(name, description, target_emotions)
        if not prompts:
            raise ValueError("Grounding exercise needs at least one prompt.")
        self._prompts = list(prompts)

    @property
    def kind(self) -> str:
        return "Grounding"

    def steps(self) -> List[Step]:
        result = [Step(p, needs_input=True) for p in self._prompts]
        result.append(Step("Take one slow breath. You are here, and you can pause."))
        return result


class ReflectionPrompt(Exercise):
    """Guided writing questions."""

    def __init__(self, name, description, target_emotions, questions: List[str]):
        super().__init__(name, description, target_emotions)
        if not questions:
            raise ValueError("Reflection needs at least one question.")
        self._questions = list(questions)

    @property
    def kind(self) -> str:
        return "Reflection"

    def steps(self) -> List[Step]:
        result = [Step(q, needs_input=True) for q in self._questions]
        result.append(Step("Thank you for taking time to reflect."))
        return result


def default_exercises() -> List[Exercise]:
    """The built-in exercise catalogue."""
    return [
        BreathingExercise("Box breathing", "Equal in, hold, out, hold counts to steady your nerves.",
                          ["fear", "anger", "surprise"], inhale=4, hold=4, exhale=4, cycles=4),
        BreathingExercise("4-7-8 breathing", "A long exhale to help the body wind down.",
                          ["fear", "sadness"], inhale=4, hold=7, exhale=8, cycles=3),
        GroundingExercise("5-4-3-2-1 grounding", "Use your senses to come back to the present moment.",
                          ["fear", "surprise", "anger"],
                          ["Name 5 things you can see.", "Name 4 things you can touch.",
                           "Name 3 things you can hear.", "Name 2 things you can smell.",
                           "Name 1 thing you can taste."]),
        GroundingExercise("Cool-down check", "A quick body scan to release built-up tension.",
                          ["anger"],
                          ["Where do you feel tension in your body right now?",
                           "Unclench your jaw and drop your shoulders. What changed?"]),
        ReflectionPrompt("Gratitude reflection", "Gently shift attention to what is going okay.",
                         ["sadness", "love", "joy"],
                         ["Name one thing that went well today.",
                          "Who or what are you thankful for right now, and why?"]),
        ReflectionPrompt("Thought check", "Look at a worry from a fairer angle.",
                         ["sadness", "fear", "anger"],
                         ["What is the thought that is bothering you most?",
                          "What evidence do you have for it, and against it?",
                          "What would you say to a friend who felt this way?"]),
        ReflectionPrompt("Savour the moment", "Make a good feeling last a little longer.",
                         ["joy", "love", "surprise"],
                         ["What is happening that feels good right now?",
                          "How could you remember or share this moment?"]),
        ReflectionPrompt("Pause and name it", "Put a surprise into words before reacting.",
                         ["surprise"],
                         ["What just happened, in one sentence?",
                          "What do you need before deciding what to do next?"]),
    ]

import unittest

from models.entry import JournalEntry, TextEntry, VoiceEntry, entry_from_source
from models.exercise import (BreathingExercise, Exercise, GroundingExercise,
                             ReflectionPrompt, default_exercises)


class EntryTests(unittest.TestCase):
    def test_abstract_class_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            JournalEntry("hello")

    def test_empty_text_rejected(self):
        for bad in ("", "   ", None):
            with self.assertRaises(ValueError):
                TextEntry(bad)

    def test_too_long_text_rejected(self):
        with self.assertRaises(ValueError):
            TextEntry("x" * (JournalEntry.MAX_LENGTH + 1))

    def test_confidence_must_be_between_0_and_1(self):
        entry = TextEntry("hi")
        with self.assertRaises(ValueError):
            entry.set_emotion("joy", 1.5)

    def test_polymorphic_summary_and_source(self):
        text, voice = TextEntry("a" * 100), VoiceEntry("hello there")
        self.assertEqual((text.source, voice.source), ("text", "voice"))
        self.assertTrue(text.summary(20).endswith("…") and len(text.summary(20)) == 20)
        self.assertTrue(voice.summary().startswith("[voice]"))

    def test_factory_returns_correct_subclass(self):
        self.assertIsInstance(entry_from_source("voice", content="hi"), VoiceEntry)
        self.assertIsInstance(entry_from_source("unknown", content="hi"), TextEntry)


class ExerciseTests(unittest.TestCase):
    def test_abstract_class_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            Exercise("x", "y", [])

    def test_every_emotion_has_at_least_two_exercises(self):
        import config
        catalogue = default_exercises()
        for emotion in config.EMOTIONS:
            self.assertGreaterEqual(sum(e.helps_with(emotion) for e in catalogue), 2, emotion)

    def test_all_subclasses_produce_steps_polymorphically(self):
        for exercise in default_exercises():
            steps = exercise.steps()
            self.assertGreater(len(steps), 1, exercise.name)

    def test_breathing_has_timed_animated_steps(self):
        steps = BreathingExercise("b", "d", ["fear"], inhale=4, hold=2, exhale=6, cycles=2).steps()
        timed = [s for s in steps if s.duration]
        self.assertEqual(len(timed), 6)
        self.assertEqual({s.animation for s in timed}, {"expand", "hold", "contract"})

    def test_breathing_without_hold_skips_hold_step(self):
        steps = BreathingExercise("b", "d", ["fear"], inhale=3, hold=0, exhale=3, cycles=1).steps()
        self.assertNotIn("hold", {s.animation for s in steps})

    def test_invalid_parameters_rejected(self):
        with self.assertRaises(ValueError):
            BreathingExercise("b", "d", [], inhale=0, hold=0, exhale=3)
        with self.assertRaises(ValueError):
            GroundingExercise("g", "d", [], prompts=[])
        with self.assertRaises(ValueError):
            ReflectionPrompt("r", "d", [], questions=[])


if __name__ == "__main__":
    unittest.main()

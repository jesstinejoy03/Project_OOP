import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from models.entry import TextEntry
from services.classifier import ClassifierError, EmotionClassifier
from services.database import SCHEMA_VERSION, DatabaseError, DatabaseManager
from services.journal_service import JournalService
from services.recommender import CopingRecommender
from services.safety import SafetyCheck


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager(":memory:")

    def test_create_read_update_delete(self):
        entry = TextEntry("feeling okay", emotion="joy", confidence=0.8)
        entry_id = self.db.add_entry(entry)
        loaded = self.db.get_entry(entry_id)
        assert loaded is not None
        self.assertEqual((loaded.content, loaded.emotion), ("feeling okay", "joy"))
        loaded.content = "feeling great"
        self.db.update_entry(loaded)
        updated = self.db.get_entry(entry_id)
        assert updated is not None
        self.assertEqual(updated.content, "feeling great")
        self.assertTrue(self.db.delete_entry(entry_id))
        self.assertIsNone(self.db.get_entry(entry_id))
        self.assertFalse(self.db.delete_entry(entry_id))

    def test_filter_and_counts(self):
        for text, emo in (("a", "joy"), ("b", "joy"), ("c", "fear")):
            self.db.add_entry(TextEntry(text, emotion=emo, confidence=0.5))
        self.assertEqual(len(self.db.get_entries(emotion="joy")), 2)
        self.assertEqual(self.db.emotion_counts(), {"joy": 2, "fear": 1})

    def test_sql_injection_is_treated_as_plain_text(self):
        nasty = "x'); DROP TABLE entries;--"
        self.db.add_entry(TextEntry(nasty, emotion="fear", confidence=0.5))
        self.assertEqual(self.db.get_entries()[0].content, nasty)

    def test_update_unsaved_entry_fails(self):
        with self.assertRaises(DatabaseError):
            self.db.update_entry(TextEntry("never saved"))

    def test_invalid_rating_rejected(self):
        for bad in (0, 6):
            with self.assertRaises(ValueError):
                self.db.add_rating("Box breathing", "fear", bad)

    def test_unknown_entry_returns_none(self):
        self.assertIsNone(self.db.get_entry(12345))

    def test_delete_all_clears_entries_and_ratings(self):
        self.db.add_entry(TextEntry("one", emotion="joy", confidence=0.5))
        self.db.add_entry(TextEntry("two", emotion="fear", confidence=0.5))
        self.db.add_rating("Box breathing", "fear", 4)
        self.assertEqual(self.db.delete_all(), 2)
        self.assertEqual(self.db.get_entries(), [])
        self.assertEqual(self.db.rating_stats("fear"), {})

    def test_schema_version_is_recorded(self):
        self.assertEqual(self.db.schema_version(), SCHEMA_VERSION)

    def test_all_entries_is_oldest_first(self):
        first = self.db.add_entry(TextEntry("first", emotion="joy", confidence=0.5))
        second = self.db.add_entry(TextEntry("second", emotion="joy", confidence=0.5))
        self.assertEqual([e.entry_id for e in self.db.all_entries()], [first, second])


class RecommenderTests(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager(":memory:")
        self.rec = CopingRecommender(self.db)

    def test_only_relevant_exercises_for_emotion(self):
        for exercise in self.rec.recommend("anger", limit=10):
            self.assertTrue(exercise.helps_with("anger"))

    def test_unknown_emotion_falls_back_to_all(self):
        self.assertEqual(len(self.rec.recommend("???", limit=20)), len(self.rec.exercises))

    def test_high_rating_moves_exercise_to_top(self):
        before = self.rec.recommend("fear")
        worst = before[-1]
        for _ in range(3):
            self.rec.record_rating(worst, "fear", 5)
        self.assertEqual(self.rec.recommend("fear")[0].name, worst.name)

    def test_low_rating_moves_exercise_down(self):
        top = self.rec.recommend("fear")[0]
        for _ in range(3):
            self.rec.record_rating(top, "fear", 1)
        self.assertNotEqual(self.rec.recommend("fear")[0].name, top.name)

    def test_rating_without_emotion_counts_for_every_target(self):
        """A rating from the unfiltered toolkit must not be orphaned."""
        exercise = self.rec.exercises[0]
        self.rec.record_rating(exercise, None, 5)
        for emotion in exercise.target_emotions:
            self.assertIn(exercise.name, self.db.rating_stats(emotion))

    def test_rating_for_unrelated_emotion_is_credited_to_its_targets(self):
        exercise = self.rec.exercises[0]
        unrelated = next(e for e in ("joy", "sadness", "anger")
                         if not exercise.helps_with(e))
        self.rec.record_rating(exercise, unrelated, 4)
        self.assertNotIn(exercise.name, self.db.rating_stats(unrelated))
        for emotion in exercise.target_emotions:
            self.assertIn(exercise.name, self.db.rating_stats(emotion))

    def test_out_of_range_rating_rejected(self):
        for bad in (0, 6):
            with self.assertRaises(ValueError):
                self.rec.record_rating(self.rec.exercises[0], "fear", bad)


class ClassifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        base = Path(cls.tmp.name)
        cls.clf = EmotionClassifier(base / "m.joblib", base / "metrics.json",
                                    allow_training=True)
        cls.clf.load()      # trains the built-in sample model on first use

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_obvious_sentences(self):
        self.assertEqual(self.clf.predict("I am so happy and excited today").emotion, "joy")
        self.assertEqual(self.clf.predict("I am furious and angry about this").emotion, "anger")

    def test_confidence_is_probability(self):
        self.assertTrue(0.0 <= self.clf.predict("i feel nervous").confidence <= 1.0)

    def test_text_without_words_rejected(self):
        for bad in ("", "12345 !!!", "😀😀"):
            with self.assertRaises(ValueError):
                self.clf.predict(bad)

    def test_predict_before_load_raises(self):
        with self.assertRaises(ClassifierError):
            EmotionClassifier("nope.joblib").predict("hello")

    def test_missing_model_raises_instead_of_training_silently(self):
        path = Path(self.tmp.name) / "absent.joblib"
        with self.assertRaises(ClassifierError) as caught:
            EmotionClassifier(path, path.with_suffix(".json")).load()
        self.assertIn("ml.train_model", str(caught.exception))

    def test_long_entry_is_chunked(self):
        sentence = "I am so happy today. "
        prediction = self.clf.predict(sentence * 12)
        self.assertGreater(prediction.chunks, 1)
        self.assertTrue(0.0 <= prediction.confidence <= 1.0)

    def test_info_contains_accuracy(self):
        self.assertIn("accuracy", self.clf.info())


class SafetyTests(unittest.TestCase):
    def test_flags_serious_text(self):
        check = SafetyCheck()
        self.assertTrue(check.needs_support("sometimes I want to die"))
        self.assertTrue(check.needs_support("I might HURT MYSELF"))

    def test_ignores_normal_text(self):
        check = SafetyCheck()
        for text in ("this exam is killing me, so stressed",
                     "I am happy today",
                     "I am hopelessly behind on revision",
                     "I feel awful about my marks",
                     "my laptop died and I could scream"):
            self.assertFalse(check.needs_support(text), text)

    def test_flags_despair(self):
        check = SafetyCheck()
        for text in ("I can't go on like this",
                     "nothing matters anymore",
                     "there is no point in trying",
                     "I feel completely worthless",
                     "nobody would notice if I was gone",
                     "I need someone to save me",
                     "I feel completely helpless",
                     "I am trapped and can't do this anymore",
                     "I can't cope anymore",
                     "I don't know how to keep going"):
            self.assertTrue(check.needs_support(text), text)

    def test_flags_harming_others(self):
        check = SafetyCheck()
        for text in ("I want to hurt someone",
                     "I might hurt my friend",
                     "I want to stab people",
                     "I am going to attack them",
                     "I want to smack them",
                     "I want to humiliate my sister",
                     "I want to hang someone"):
            self.assertTrue(check.needs_support(text), text)

    def test_direct_violence_keywords_trigger_immediately(self):
        check = SafetyCheck()
        for text in ("I want to kill someone",
                     "I will hang them",
                     "I am going to stab them",
                     "I want to shoot someone"):
            self.assertTrue(check.needs_support(text), text)


class JournalServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        base = Path(cls.tmp.name)
        cls.clf = EmotionClassifier(base / "m.joblib", base / "metrics.json",
                                    allow_training=True)
        cls.clf.load()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.db = DatabaseManager(":memory:")
        self.service = JournalService(self.db, self.clf, CopingRecommender(self.db),
                                      SafetyCheck())

    def test_submit_saves_and_recommends(self):
        result = self.service.submit_text("I am terrified and so worried")
        self.assertEqual(len(self.service.history()), 1)
        self.assertTrue(result.recommendations)

    def test_empty_submission_saves_nothing(self):
        with self.assertRaises(ValueError):
            self.service.submit_text("   ")
        self.assertEqual(self.service.history(), [])

    def test_edit_redetects_emotion(self):
        entry_id = self.service.submit_text("I am so worried and scared").entry.entry_id
        assert entry_id is not None
        result = self.service.edit_entry(entry_id, "I am so happy and delighted")
        self.assertEqual(result.prediction.emotion, "joy")
        self.assertEqual(self.service.history()[0].emotion, "joy")

    def test_edit_missing_entry(self):
        with self.assertRaises(ValueError):
            self.service.edit_entry(999, "hello there")

    def test_support_flag(self):
        self.assertTrue(self.service.submit_text("I want to die").needs_support)

    def test_get_entry_returns_saved_entry(self):
        entry_id = self.service.submit_text("I am happy").entry.entry_id
        assert entry_id is not None
        saved = self.service.get_entry(entry_id)
        assert saved is not None
        self.assertEqual(saved.content, "I am happy")
        self.assertIsNone(self.service.get_entry(entry_id + 1))

    def test_export_writes_csv_and_json(self):
        from services.export import to_csv, to_json
        self.service.submit_text("I am terrified")
        entries = self.db.all_entries()
        self.assertIn("emotion", to_csv(entries).splitlines()[0])
        self.assertIn("fear", to_csv(entries))
        self.assertEqual(len(self.db.all_entries()), 1)
        self.assertIn('"entry_count": 1', to_json(entries))

    def test_clear_all_empties_the_journal(self):
        self.service.submit_text("I am happy")
        self.assertEqual(self.service.clear_all(), 1)
        self.assertEqual(self.service.history(), [])

    def test_low_confidence_flag_matches_prediction(self):
        result = self.service.submit_text("I am so happy and excited")
        self.assertEqual(result.low_confidence,
                         result.prediction.confidence < 0.40)

    def test_recent_mood_summary_counts_recent_entries(self):
        now = datetime.now()
        self.db.add_entry(TextEntry("happy day", emotion="joy", confidence=0.9,
                                   created_at=now - timedelta(days=0)))
        self.db.add_entry(TextEntry("still happy", emotion="joy", confidence=0.9,
                                   created_at=now - timedelta(days=2)))
        self.db.add_entry(TextEntry("really scared", emotion="fear", confidence=0.8,
                                   created_at=now - timedelta(days=5)))
        summary = self.service.mood_summary(days=7)
        counts = summary["counts"]
        self.assertEqual(summary["total_entries"], 3)
        self.assertEqual(counts["joy"], 2)
        self.assertEqual(counts["fear"], 1)
        self.assertEqual(summary["dominant_emotion"], "joy")


if __name__ == "__main__":
    unittest.main()

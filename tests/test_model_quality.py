"""Quality floor for the REAL trained model.

Unlike the classifier tests, which train a throwaway sample model in a temp
folder, this file loads `ml/emotion_model.joblib` - the artefact the app ships
with - and checks it still behaves. It is skipped when that file is absent.
"""
import unittest

import config
from services.classifier import EmotionClassifier

# Hand-written journal-style sentences with a clear dominant emotion. These are
# deliberately unlike the short social-media sentences the model trained on.
CASES = [
    ("I am so happy and grateful today, everything feels light.", "joy"),
    ("I miss her so much and the house feels empty and grey.", "sadness"),
    ("I am so angry that I could throw this laptop at the wall.", "anger"),
    ("I am scared about what the scan might show tomorrow.", "fear"),
    ("I love my family more than anything in the world.", "love"),
]

MIN_ACCURACY = 0.6
MIN_BENCHMARK_ACCURACY = 0.80


@unittest.skipUnless(config.MODEL_PATH.exists(), "real model has not been trained yet")
class RealModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.clf = EmotionClassifier()
        cls.clf.load()

    def test_saved_metrics_come_from_a_real_training_run(self):
        info = self.clf.info()
        self.assertFalse(self.clf.is_demo, "the app is shipping the demo model")
        self.assertGreaterEqual(info.get("accuracy", 0), MIN_BENCHMARK_ACCURACY)
        self.assertIn("report", info)

    def test_journal_style_sentences_are_recognised(self):
        correct = 0
        for text, expected in CASES:
            if self.clf.predict(text).emotion == expected:
                correct += 1
        accuracy = correct / len(CASES)
        self.assertGreaterEqual(accuracy, MIN_ACCURACY,
                                f"only {correct}/{len(CASES)} journal sentences correct")

    def test_long_mixed_entry_reports_chunk_count(self):
        text = ("Work was fine. " * 20).strip()
        prediction = self.clf.predict(text)
        self.assertGreater(prediction.chunks, 1)
        self.assertIn(prediction.emotion, config.EMOTIONS)


if __name__ == "__main__":
    unittest.main()

"""Central configuration: file locations and shared constants."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "mood_journal.db"
MODEL_PATH = BASE_DIR / "ml" / "emotion_model.joblib"
METRICS_PATH = BASE_DIR / "ml" / "metrics.json"
CONFUSION_PATH = BASE_DIR / "ml" / "confusion_matrix.png"

# Order matches the dair-ai/emotion dataset label ids 0..5.
EMOTIONS = ["sadness", "joy", "love", "anger", "fear", "surprise"]

# How many entries the history screen loads in one go.
HISTORY_LIMIT = 200

# Sentence chunking: entries longer than this are classified piece by piece and
# the probabilities averaged, because the model was trained on short sentences.
CHUNK_WORDS = 40

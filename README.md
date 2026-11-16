# Mood Journal & Coping Companion

A Tkinter desktop app (CSC 2102 – OOP assignment). You write a journal entry, a
machine-learning model detects the emotion, and the app recommends a coping
exercise that you can run inside the app. Entries are stored in SQLite.

> Self-reflection tool only. It is not a medical device and cannot diagnose anything.

## Setup
1. Python 3.9+ (Tkinter ships with Python on Windows/macOS; on Linux run `sudo apt install python3-tk`).
2. Install the libraries:
   ```
   pip install -r requirements.txt
   ```
3. Train the emotion model (needs internet the first time; downloads dair-ai/emotion):
   ```
   python -m ml.train_model
   ```
   The app **refuses to start** until this file exists, rather than quietly using a toy
   model — if you want a throwaway model for a quick smoke test, use
   `python -m ml.train_model --sample` and ignore its accuracy.
4. Run the app:
   ```
   python main.py
   ```

### Windows executable
To build a standalone Windows executable, install PyInstaller and run this from
the project folder:
```
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --clean --onefile --windowed --name MoodJournal --add-data "ml;ml" main.py
```
The executable is created at `dist\MoodJournal.exe`. When packaged, the journal
database is stored in `%LOCALAPPDATA%\MoodJournal` so entries persist between runs.
A prebuilt binary is also provided at `downloads/MoodJournal.exe` using Git LFS;
after cloning, install Git LFS and run `git lfs pull` to download it.

### Training options
```
python -m ml.train_model                       # dair-ai/emotion (86% test accuracy)
python -m ml.train_model --balanced            # class_weight='balanced': better rare-class recall
python -m ml.train_model --char-ngrams         # + character 3-5 grams alongside the word features
python -m ml.train_model --data-dir data       # offline: a folder with train.txt / test.txt ("text;label")
python -m ml.train_model --sample              # tiny built-in dataset (demo only)
```
Each run rewrites `ml/emotion_model.joblib`, `ml/metrics.json` (accuracy, per-class
report, and the options used) and `ml/confusion_matrix.png`.

## How it works
1. `JournalService.submit_text` builds a `TextEntry`, which validates the text.
2. `EmotionClassifier` splits long entries into ~40-word chunks, because the model was
   trained on short sentences — one TF-IDF vector over a 200-word paragraph dilutes
   every feature. Chunk probabilities are averaged.
3. `CopingRecommender` ranks the exercises that target that emotion, best-rated first:
   `score = (sum_of_ratings + 3 × 2) / (count + 2)`, so untried exercises start neutral
   and move as you rate them. A rating with no known emotion is credited to every
   emotion the exercise helps with, so it is never orphaned.
4. `SafetyCheck` scans for explicit self-harm and despair language and shows a support
   message. It is deliberately narrow keyword matching, not a judgement about you.
5. `DatabaseManager` persists the entry; the GUI refreshes history and the chart.

Predictions under 40% confidence are shown as **"Emotion unclear (best guess: …)"** with
a button to browse the whole toolkit, instead of asserting an emotion.

## Tests
```
python -m unittest discover -s tests -t . -v
```
68 tests covering the models, database (including SQL injection), recommender,
safety check, export, preprocessing/chunking, the service layer, and a quality floor
for the **real** trained model (`tests/test_model_quality.py`, skipped if no model).
CI runs the same suite on every push (`.github/workflows/tests.yml`).

## Your data
Everything stays in `mood_journal.db` on this computer; nothing is uploaded. The
"About & support" tab can export every entry to CSV or JSON, and delete all data.

## Structure
- `models/` – abstract `JournalEntry` (+ `TextEntry`, `VoiceEntry`) and abstract `Exercise`
  (+ `BreathingExercise`, `GroundingExercise`, `ReflectionPrompt`)
- `services/` – `DatabaseManager` (SQLite), `EmotionClassifier`, `CopingRecommender`,
  `SafetyCheck`, `export`, and `JournalService` (what the GUI talks to)
- `gui/` – `MoodJournalApp` and `ExerciseWindow`
- `gui/tabs/` – one module per tab: `journal_tab`, `coping_tab`, `history_tab`,
  `resources_tab`, plus `emotion_chart` and shared `common` helpers
- `ml/` – preprocessing (`clean_text`, `split_chunks`), training script, sample data
- `tests/` – unit tests

## Voice entries (optional)
`pip install SpeechRecognition`, then use "Voice entry (.wav)" on the Journal tab.
Transcription uses Google's free web recogniser, so it needs internet.

## Troubleshooting
- *"No trained emotion model was found"* – run `python -m ml.train_model` (step 3).
- *The chart is missing* – `pip install matplotlib`; everything else still works.
- *No `datasets` package / offline* – download `train.txt` and `test.txt` (`text;label`)
  and pass `--data-dir`.

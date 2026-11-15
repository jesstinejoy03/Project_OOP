"""Train the emotion classifier and save it with joblib.

Usage (from the project folder):
    python -m ml.train_model                    # auto-download dair-ai/emotion
    python -m ml.train_model --data-dir data    # folder with train.txt / test.txt ("text;label")
    python -m ml.train_model --sample           # tiny built-in dataset (offline fallback)

Pipeline: clean_text -> TF-IDF (1-2 grams) -> Logistic Regression.
Outputs: emotion_model.joblib, metrics.json and confusion_matrix.png.
"""
import argparse
import json
import sys
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config  # noqa: E402
from ml.preprocess import clean_text  # noqa: E402
from ml.sample_data import sample_dataset  # noqa: E402


def build_pipeline(min_df: int = 2, class_weight=None,
                   char_ngrams: bool = False) -> Pipeline:
    """TF-IDF features -> logistic regression.

    class_weight="balanced" trades a little overall accuracy for much better
    recall on the small classes (surprise, love), which raises macro F1 - the
    honest metric on this 6-way imbalanced task.

    char_ngrams adds character 3-5 grams next to the word features; those catch
    sarcasm markers, slang and typos that word tokens miss, especially in
    journal-style writing the model was not trained on.
    """
    word = TfidfVectorizer(preprocessor=clean_text, ngram_range=(1, 2),
                           min_df=min_df, sublinear_tf=True)
    features = word
    if char_ngrams:
        char = TfidfVectorizer(preprocessor=clean_text, analyzer="char_wb",
                               ngram_range=(3, 5), min_df=min_df, sublinear_tf=True)
        # sklearn's stubs do not model TfidfVectorizer as a TransformerMixin
        features = FeatureUnion([("word", word), ("char", char)])  # type: ignore[arg-type]
    return Pipeline([
        ("tfidf", features),
        ("clf", LogisticRegression(max_iter=1000, C=5.0, class_weight=class_weight)),
    ])


def load_hf_dataset():
    """Download dair-ai/emotion via the Hugging Face `datasets` library."""
    from datasets import load_dataset
    ds = load_dataset("dair-ai/emotion")
    names = ds["train"].features["label"].names

    def unpack(split):
        return list(split["text"]), [names[i] for i in split["label"]]

    return unpack(ds["train"]), unpack(ds["test"]), "dair-ai/emotion (Hugging Face)"


def load_text_files(folder: Path):
    """Read Kaggle-style files where each line is 'text;label'."""
    def read(name):
        texts, labels = [], []
        for line in (folder / name).read_text(encoding="utf-8").splitlines():
            if ";" in line:
                text, label = line.rsplit(";", 1)
                texts.append(text)
                labels.append(label.strip())
        return texts, labels

    return read("train.txt"), read("test.txt"), f"text files in {folder}"


def load_sample():
    texts, labels = sample_dataset()
    x_tr, x_te, y_tr, y_te = train_test_split(texts, labels, test_size=0.25,
                                              stratify=labels, random_state=42)
    return (x_tr, y_tr), (x_te, y_te), "built-in synthetic sample (demo only)"


def train_and_save(train, test, source, model_path=config.MODEL_PATH,
                   metrics_path=config.METRICS_PATH, confusion_path=config.CONFUSION_PATH,
                   min_df: int = 2, class_weight=None, char_ngrams: bool = False) -> dict:
    (x_train, y_train), (x_test, y_test) = train, test
    model = build_pipeline(min_df=min_df, class_weight=class_weight,
                           char_ngrams=char_ngrams)
    model.fit(x_train, y_train)

    predictions = model.predict(x_test)
    labels = list(model.classes_)
    metrics = {
        "trained_on": source,
        "train_size": len(x_train),
        "test_size": len(x_test),
        "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "report": classification_report(y_test, predictions, output_dict=True, zero_division=0),
        "options": {
            "min_df": min_df,
            "class_weight": class_weight,
            "char_ngrams": char_ngrams,
        },
    }
    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    Path(metrics_path).write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    _save_confusion_matrix(confusion_matrix(y_test, predictions, labels=labels), labels,
                           confusion_path)
    return metrics


def _save_confusion_matrix(matrix, labels, path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.imshow(matrix, cmap="Blues")
    ax.set_xticks(range(len(labels)), labels, rotation=45, ha="right")
    ax.set_yticks(range(len(labels)), labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Emotion classifier - confusion matrix")
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, matrix[i, j], ha="center", va="center",
                    color="white" if matrix[i, j] > matrix.max() / 2 else "black")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Train the emotion classifier.")
    parser.add_argument("--data-dir", type=Path, help="folder with train.txt and test.txt")
    parser.add_argument("--sample", action="store_true", help="use the tiny built-in dataset")
    parser.add_argument("--balanced", action="store_true",
                        help="class_weight='balanced': better recall on rare emotions")
    parser.add_argument("--char-ngrams", action="store_true",
                        help="add character 3-5 grams next to the word features")
    args = parser.parse_args()

    min_df = 2
    if args.sample:
        train, test, source = load_sample()
        min_df = 1
    elif args.data_dir:
        train, test, source = load_text_files(args.data_dir)
    else:
        try:
            train, test, source = load_hf_dataset()
        except Exception as exc:  # no internet / library missing
            print(f"Could not download the dataset ({exc}).\n"
                  "Falling back to the tiny built-in sample.\n")
            train, test, source = load_sample()
            min_df = 1

    print(f"Training on: {source}")
    metrics = train_and_save(train, test, source, min_df=min_df,
                             class_weight="balanced" if args.balanced else None,
                             char_ngrams=args.char_ngrams)
    macro_f1 = metrics["report"]["macro avg"]["f1-score"]
    print(f"Train size: {metrics['train_size']}  Test size: {metrics['test_size']}")
    print(f"Test accuracy: {metrics['accuracy']:.2%}   Macro F1: {macro_f1:.3f}")
    print(f"Saved model to {config.MODEL_PATH}")


if __name__ == "__main__":
    main()

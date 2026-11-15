"""Text preprocessing shared by training and prediction.

Steps: lowercase -> remove URLs and @mentions -> keep letters/apostrophes only
-> collapse whitespace. Stop words are deliberately kept, because words like
"not" and "no" change the emotion of a sentence.
"""
import re
from typing import List, Optional

import config

_URL = re.compile(r"https?://\S+|www\.\S+")
_MENTION = re.compile(r"@\w+")
_NON_LETTER = re.compile(r"[^a-z' ]+")
_SPACES = re.compile(r"\s+")
_SENTENCE_END = re.compile(r"(?<=[.!?;])\s+|\n+")


def clean_text(text: str) -> str:
    text = text.lower()
    text = _URL.sub(" ", text)
    text = _MENTION.sub(" ", text)
    text = _NON_LETTER.sub(" ", text)
    return _SPACES.sub(" ", text).strip()


def _words(text: str) -> List[str]:
    return text.split()


def _pack(sentences: List[str], max_words: int) -> List[str]:
    """Greedily join sentences so each chunk stays under `max_words` words."""
    chunks, current = [], []
    for sentence in sentences:
        words = _words(sentence)
        if not words:
            continue
        if current and len(current) + len(words) > max_words:
            chunks.append(" ".join(current))
            current = []
        current.extend(words)
    if current:
        chunks.append(" ".join(current))
    return chunks


def split_chunks(text: str, max_words: Optional[int] = None) -> List[str]:
    """Break a long entry into model-sized pieces.

    The classifier is trained on short social-media sentences, so a 200-word
    journal paragraph handed over whole dilutes every feature. Splitting on
    sentence punctuation and repacking to `max_words` keeps each prediction in
    the same distribution the model was trained on.
    """
    limit = max_words or config.CHUNK_WORDS
    text = text.strip()
    if not text:
        return []
    sentences = [s for s in _SENTENCE_END.split(text) if s.strip()]
    chunks = _pack(sentences, limit)
    if not chunks:
        return []
    # A single sentence can still overshoot the limit; break it on whitespace.
    result: List[str] = []
    for chunk in chunks:
        words = _words(chunk)
        for start in range(0, len(words), limit):
            result.append(" ".join(words[start:start + limit]))
    return result

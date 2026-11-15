"""SQLite persistence layer (CRUD for entries, plus exercise ratings)."""
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, TypedDict, Union

from models.entry import JournalEntry, entry_from_source

SCHEMA_VERSION = 2

SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    content     TEXT NOT NULL,
    source      TEXT NOT NULL DEFAULT 'text',
    emotion     TEXT,
    confidence  REAL,
    created_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ratings (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise_name TEXT NOT NULL,
    emotion       TEXT NOT NULL,
    rating        INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    rated_at      TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_entries_emotion ON entries(emotion, created_at DESC);
"""


class DatabaseError(Exception):
    """Raised when a database operation fails."""


class MoodSummary(TypedDict):
    window_days: int
    total_entries: int
    counts: Dict[str, int]
    dominant_emotion: str


class DatabaseManager:
    """Owns the SQLite connection. No other class touches SQL directly."""

    def __init__(self, path: Union[str, Path] = ":memory:"):
        try:
            self._conn = sqlite3.connect(str(path))
            self._conn.row_factory = sqlite3.Row
            self._conn.executescript(SCHEMA)
            self._conn.execute(
                "INSERT INTO meta (key, value) VALUES ('schema_version', ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (str(SCHEMA_VERSION),))
            self._conn.commit()
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not open database: {exc}") from exc

    def _run(self, sql: str, params: tuple = (), commit: bool = False):
        """Execute a parameterised query (prevents SQL injection)."""
        try:
            cur = self._conn.execute(sql, params)
            if commit:
                self._conn.commit()
            return cur
        except sqlite3.Error as exc:
            raise DatabaseError(f"Database error: {exc}") from exc

    # ---- entries: Create / Read / Update / Delete --------------------------
    def add_entry(self, entry: JournalEntry) -> int:
        cur = self._run(
            "INSERT INTO entries (content, source, emotion, confidence, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (entry.content, entry.source, entry.emotion, entry.confidence,
             entry.created_at.isoformat(timespec="seconds")), commit=True)
        last_id = cur.lastrowid
        if last_id is None:                      # sqlite3 types it as int | None
            raise DatabaseError("The entry could not be saved.")
        entry.entry_id = int(last_id)
        return int(last_id)

    def get_entry(self, entry_id: int) -> Optional[JournalEntry]:
        row = self._run("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
        return self._to_entry(row) if row else None

    def get_entries(self, emotion: Optional[str] = None, limit: int = 200) -> List[JournalEntry]:
        if emotion:
            cur = self._run("SELECT * FROM entries WHERE emotion = ? "
                            "ORDER BY created_at DESC, id DESC LIMIT ?", (emotion, limit))
        else:
            cur = self._run("SELECT * FROM entries ORDER BY created_at DESC, id DESC LIMIT ?",
                            (limit,))
        return [self._to_entry(r) for r in cur.fetchall()]

    def update_entry(self, entry: JournalEntry) -> None:
        if entry.entry_id is None:
            raise DatabaseError("Cannot update an entry that has not been saved.")
        cur = self._run("UPDATE entries SET content = ?, emotion = ?, confidence = ? WHERE id = ?",
                        (entry.content, entry.emotion, entry.confidence, entry.entry_id),
                        commit=True)
        if cur.rowcount == 0:
            raise DatabaseError("Entry not found.")

    def delete_entry(self, entry_id: int) -> bool:
        cur = self._run("DELETE FROM entries WHERE id = ?", (entry_id,), commit=True)
        return cur.rowcount > 0

    def all_entries(self) -> List[JournalEntry]:
        """Every entry, oldest first - used for exporting the journal."""
        cur = self._run("SELECT * FROM entries ORDER BY created_at ASC, id ASC")
        return [self._to_entry(r) for r in cur.fetchall()]

    def delete_all(self) -> int:
        """Remove every entry and rating. Returns how many entries were deleted."""
        removed = self._run("DELETE FROM entries", commit=True).rowcount
        self._run("DELETE FROM ratings", commit=True)
        return removed

    def schema_version(self) -> int:
        row = self._run("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()
        return int(row["value"]) if row else 0

    def emotion_counts(self) -> Dict[str, int]:
        cur = self._run("SELECT emotion, COUNT(*) AS n FROM entries "
                        "WHERE emotion IS NOT NULL GROUP BY emotion")
        return {r["emotion"]: r["n"] for r in cur.fetchall()}

    def recent_mood_summary(self, days: int = 7) -> MoodSummary:
        """Aggregate recent entries into a simple mood snapshot."""
        if days <= 0:
            raise ValueError("days must be positive.")
        cutoff = (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")
        cur = self._run(
            "SELECT emotion, COUNT(*) AS n FROM entries "
            "WHERE emotion IS NOT NULL AND created_at >= ? GROUP BY emotion",
            (cutoff,))
        counts = {r["emotion"]: r["n"] for r in cur.fetchall()}
        total = sum(counts.values())
        dominant = max(counts.items(), key=lambda item: (item[1], item[0]))[0] if counts else "none"
        return {
            "window_days": days,
            "total_entries": total,
            "counts": counts,
            "dominant_emotion": dominant,
        }

    # ---- exercise ratings (feeds the recommender) --------------------------
    def add_rating(self, exercise_name: str, emotion: str, rating: int) -> None:
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5.")
        self._run("INSERT INTO ratings (exercise_name, emotion, rating, rated_at) VALUES (?,?,?,?)",
                  (exercise_name, emotion, rating, datetime.now().isoformat(timespec="seconds")),
                  commit=True)

    def rating_stats(self, emotion: str) -> Dict[str, tuple]:
        """Return {exercise_name: (total_rating, count)} for one emotion."""
        cur = self._run("SELECT exercise_name, SUM(rating) AS total, COUNT(*) AS n "
                        "FROM ratings WHERE emotion = ? GROUP BY exercise_name", (emotion,))
        return {r["exercise_name"]: (r["total"], r["n"]) for r in cur.fetchall()}

    @staticmethod
    def _to_entry(row: sqlite3.Row) -> JournalEntry:
        return entry_from_source(
            row["source"], content=row["content"], emotion=row["emotion"],
            confidence=row["confidence"], entry_id=row["id"],
            created_at=datetime.fromisoformat(row["created_at"]))

    def close(self) -> None:
        self._conn.close()

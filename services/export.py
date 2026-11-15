"""Export journal entries to CSV or JSON.

Entries live in a local SQLite file, so the user needs a way to take their data
with them (and a plain-text backup is easier to inspect than the .db file).
"""
import csv
import io
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Sequence

from models.entry import JournalEntry

CSV_COLUMNS = ("id", "created_at", "source", "emotion", "confidence", "content")


class ExportError(Exception):
    """Raised when an export cannot be written."""


def _record(entry: JournalEntry) -> Dict[str, Any]:
    return {
        "id": entry.entry_id,
        "created_at": entry.created_at.isoformat(sep=" ", timespec="seconds"),
        "source": entry.source,
        "emotion": entry.emotion or "",
        "confidence": "" if entry.confidence is None else round(float(entry.confidence), 4),
        "content": entry.content,
    }


def to_csv(entries: Sequence[JournalEntry]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_COLUMNS)
    for entry in entries:
        record = _record(entry)
        writer.writerow([record[column] for column in CSV_COLUMNS])
    return buffer.getvalue()


def to_json(entries: Sequence[JournalEntry]) -> str:
    payload = {
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "entry_count": len(entries),
        "entries": [_record(entry) for entry in entries],
    }
    return json.dumps(payload, indent=2)


SERIALISERS: Dict[str, Callable[[Sequence[JournalEntry]], str]] = {
    ".csv": to_csv,
    ".json": to_json,
}

EXPORT_FILETYPES = [("CSV spreadsheet", "*.csv"), ("JSON", "*.json")]


def write_export(path, entries: Sequence[JournalEntry]) -> Path:
    """Write `entries` to `path`, picking the format from the file extension."""
    target = Path(path)
    serialise = SERIALISERS.get(target.suffix.lower(), to_csv)
    try:
        target.write_text(serialise(entries), encoding="utf-8")
    except OSError as exc:
        raise ExportError(f"Could not write the export file: {exc}") from exc
    return target

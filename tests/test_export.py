import csv
import io
import json
import tempfile
import unittest
from pathlib import Path

from models.entry import TextEntry, VoiceEntry
from services.export import ExportError, to_csv, to_json, write_export


def sample_entries():
    return [
        TextEntry("I felt calm today", emotion="joy", confidence=0.9123, entry_id=1),
        VoiceEntry("it was a hard day", emotion="sadness", confidence=0.62, entry_id=2),
    ]


class CsvExportTests(unittest.TestCase):
    def test_header_and_rows(self):
        rows = list(csv.DictReader(io.StringIO(to_csv(sample_entries()))))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["emotion"], "joy")
        self.assertEqual(rows[0]["confidence"], "0.9123")
        self.assertEqual(rows[1]["source"], "voice")

    def test_commas_and_newlines_survive_a_round_trip(self):
        tricky = TextEntry('a, b "c"\nnext line', emotion="fear", confidence=0.5)
        rows = list(csv.DictReader(io.StringIO(to_csv([tricky]))))
        self.assertEqual(rows[0]["content"], 'a, b "c"\nnext line')

    def test_empty_journal_still_has_a_header(self):
        self.assertEqual(to_csv([]), "id,created_at,source,emotion,confidence,content\r\n")


class JsonExportTests(unittest.TestCase):
    def test_payload_shape(self):
        payload = json.loads(to_json(sample_entries()))
        self.assertEqual(payload["entry_count"], 2)
        self.assertEqual(payload["entries"][0]["content"], "I felt calm today")
        self.assertEqual(payload["entries"][1]["emotion"], "sadness")
        self.assertIn("exported_at", payload)

    def test_entry_without_emotion_is_exported_as_empty(self):
        payload = json.loads(to_json([TextEntry("no emotion yet")]))
        self.assertEqual(payload["entries"][0]["emotion"], "")
        self.assertEqual(payload["entries"][0]["confidence"], "")


class WriteExportTests(unittest.TestCase):
    def test_format_is_chosen_from_the_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            csv_path = write_export(folder / "a.csv", sample_entries())
            json_path = write_export(folder / "b.json", sample_entries())
            self.assertEqual(csv_path.name, "a.csv")
            self.assertIn("emotion", csv_path.read_text(encoding="utf-8"))
            self.assertIn("entry_count", json_path.read_text(encoding="utf-8"))

    def test_unwritable_path_raises_export_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing_dir = Path(tmp) / "nope" / "out.csv"
            with self.assertRaises(ExportError):
                write_export(missing_dir, sample_entries())


if __name__ == "__main__":
    unittest.main()

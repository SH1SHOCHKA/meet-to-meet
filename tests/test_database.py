"""Небольшие автоматические тесты операций с базой данных."""

import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from database import Database


class DatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.temp_dir.name) / "test.db")
        self.sample = {
            "title": "Тестовая встреча",
            "meeting_date": "2026-11-20",
            "start_time": "10:00",
            "end_time": "11:00",
            "place": "Google Meet",
            "description": "Проверка приложения",
            "notes": "Тестовая запись",
        }

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_add_and_read_meeting(self) -> None:
        meeting_id = self.database.add_meeting(self.sample)
        meeting = self.database.get_meeting(meeting_id)
        self.assertIsNotNone(meeting)
        self.assertEqual(meeting["title"], self.sample["title"])

    def test_update_meeting(self) -> None:
        meeting_id = self.database.add_meeting(self.sample)
        changed = dict(self.sample, title="Новое название")
        self.database.update_meeting(meeting_id, changed)
        self.assertEqual(self.database.get_meeting(meeting_id)["title"], "Новое название")

    def test_delete_meeting(self) -> None:
        meeting_id = self.database.add_meeting(self.sample)
        self.database.delete_meeting(meeting_id)
        self.assertIsNone(self.database.get_meeting(meeting_id))

    def test_time_conflict(self) -> None:
        self.database.add_meeting(self.sample)
        self.assertTrue(
            self.database.has_time_conflict("2026-11-20", "10:30", "11:30")
        )
        self.assertFalse(
            self.database.has_time_conflict("2026-11-20", "11:00", "12:00")
        )

    def test_settings_are_saved(self) -> None:
        self.database.save_settings({"theme": "Тёмная"})
        self.assertEqual(self.database.get_settings()["theme"], "Тёмная")


if __name__ == "__main__":
    unittest.main()

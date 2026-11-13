"""Работа с базой данных SQLite для приложения Meet to meet."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class Database:
    """Небольшой слой для чтения и записи встреч и настроек."""

    DEFAULT_SETTINGS = {
        "theme": "Светлая",
        "time_format": "24 часа",
        "shortcut_add": "Ctrl+N",
        "shortcut_edit": "Ctrl+E",
        "shortcut_delete": "Delete",
        "shortcut_today": "Ctrl+T",
        "shortcut_export": "Ctrl+Shift+E",
        "shortcut_search": "Ctrl+F",
        "reminder_minutes": "10",
        "notifications_enabled": "1",
    }

    def __init__(self, db_path: str | Path | None = None) -> None:
        if db_path is None:
            app_dir = Path.home() / ".meet_to_meet"
            app_dir.mkdir(parents=True, exist_ok=True)
            db_path = app_dir / "meet_to_meet.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        """Создаёт соединение с включёнными внешними ключами."""
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        """Создаёт необходимые таблицы при первом запуске."""
        with self.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS meetings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    meeting_date TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    place TEXT DEFAULT '',
                    description TEXT DEFAULT '',
                    notes TEXT DEFAULT '',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_meetings_date "
                "ON meetings(meeting_date, start_time)"
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    setting_key TEXT PRIMARY KEY,
                    setting_value TEXT NOT NULL
                )
                """
            )
            for key, value in self.DEFAULT_SETTINGS.items():
                connection.execute(
                    "INSERT OR IGNORE INTO settings(setting_key, setting_value) "
                    "VALUES (?, ?)",
                    (key, value),
                )

    def add_meeting(self, data: dict[str, Any]) -> int:
        """Добавляет встречу и возвращает её идентификатор."""
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO meetings
                (title, meeting_date, start_time, end_time, place,
                 description, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                self._meeting_values(data),
            )
            return int(cursor.lastrowid)

    def update_meeting(self, meeting_id: int, data: dict[str, Any]) -> None:
        """Обновляет существующую встречу."""
        values = self._meeting_values(data)
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE meetings SET
                    title = ?, meeting_date = ?, start_time = ?, end_time = ?,
                    place = ?, description = ?, notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (*values, meeting_id),
            )

    @staticmethod
    def _meeting_values(data: dict[str, Any]) -> tuple[str, ...]:
        return (
            str(data.get("title", "")).strip(),
            str(data.get("meeting_date", "")),
            str(data.get("start_time", "")),
            str(data.get("end_time", "")),
            str(data.get("place", "")).strip(),
            str(data.get("description", "")).strip(),
            str(data.get("notes", "")).strip(),
        )

    def delete_meeting(self, meeting_id: int) -> None:
        """Удаляет встречу по идентификатору."""
        with self.connect() as connection:
            connection.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))

    def get_meeting(self, meeting_id: int) -> dict[str, Any] | None:
        """Возвращает одну встречу."""
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM meetings WHERE id = ?", (meeting_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_meetings_for_date(self, date_text: str) -> list[dict[str, Any]]:
        """Возвращает встречи выбранной даты по времени начала."""
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM meetings
                WHERE meeting_date = ?
                ORDER BY start_time, title COLLATE NOCASE
                """,
                (date_text,),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_all_meetings(self) -> list[dict[str, Any]]:
        """Возвращает все встречи в календаре."""
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM meetings
                ORDER BY meeting_date, start_time, title COLLATE NOCASE
                """
            ).fetchall()
            return [dict(row) for row in rows]

    def search_meetings(self, text: str) -> list[dict[str, Any]]:
        """Ищет по названию, месту и описанию."""
        pattern = f"%{text.strip()}%"
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM meetings
                WHERE title LIKE ? OR place LIKE ? OR description LIKE ?
                ORDER BY meeting_date, start_time
                """,
                (pattern, pattern, pattern),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_meetings_between(
        self, start_date: str, end_date: str
    ) -> list[dict[str, Any]]:
        """Возвращает встречи в диапазоне дат включительно."""
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM meetings
                WHERE meeting_date BETWEEN ? AND ?
                ORDER BY meeting_date, start_time
                """,
                (start_date, end_date),
            ).fetchall()
            return [dict(row) for row in rows]

    def has_time_conflict(
        self,
        meeting_date: str,
        start_time: str,
        end_time: str,
        exclude_id: int | None = None,
    ) -> bool:
        """Проверяет пересечение временных интервалов в выбранный день."""
        query = """
            SELECT COUNT(*) FROM meetings
            WHERE meeting_date = ?
              AND start_time < ?
              AND end_time > ?
        """
        parameters: list[Any] = [meeting_date, end_time, start_time]
        if exclude_id is not None:
            query += " AND id != ?"
            parameters.append(exclude_id)
        with self.connect() as connection:
            count = connection.execute(query, parameters).fetchone()[0]
        return int(count) > 0

    def get_settings(self) -> dict[str, str]:
        """Читает настройки и дополняет отсутствующие значениями по умолчанию."""
        result = dict(self.DEFAULT_SETTINGS)
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT setting_key, setting_value FROM settings"
            ).fetchall()
        result.update({row["setting_key"]: row["setting_value"] for row in rows})
        return result

    def save_settings(self, settings: dict[str, str]) -> None:
        """Сохраняет несколько настроек одной транзакцией."""
        with self.connect() as connection:
            connection.executemany(
                """
                INSERT INTO settings(setting_key, setting_value)
                VALUES (?, ?)
                ON CONFLICT(setting_key)
                DO UPDATE SET setting_value = excluded.setting_value
                """,
                [(key, str(value)) for key, value in settings.items()],
            )

    def get_upcoming_meetings(self, until_text: str) -> list[dict[str, Any]]:
        """Возвращает встречи, начинающиеся не позже указанной даты и времени."""
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM meetings
                WHERE meeting_date || ' ' || start_time <= ?
                ORDER BY meeting_date DESC, start_time DESC
                LIMIT 50
                """,
                (until_text,),
            ).fetchall()
            return [dict(row) for row in rows]

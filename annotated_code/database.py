"""Работа с базой данных SQLite для приложения Meet to meet."""  # Участвует в реализации логики текущего компонента

from __future__ import annotations  # Подключает модуль или компонент, используемый в этом файле

import shutil  # Подключает модуль или компонент, используемый в этом файле
import sqlite3  # Подключает модуль или компонент, используемый в этом файле
from collections.abc import Iterator  # Подключает модуль или компонент, используемый в этом файле
from contextlib import contextmanager  # Подключает модуль или компонент, используемый в этом файле
from pathlib import Path  # Подключает модуль или компонент, используемый в этом файле
from typing import Any  # Подключает модуль или компонент, используемый в этом файле


class Database:  # Объявляет класс и его ответственность в приложении
    """Небольшой слой для чтения и записи встреч и настроек."""  # Участвует в реализации логики текущего компонента

    DEFAULT_SETTINGS = {  # Задаёт константу или значение уровня модуля
        "theme": "Светлая",  # Продолжает выражение, список аргументов или структуру данных
        "time_format": "24 часа",  # Продолжает выражение, список аргументов или структуру данных
        "shortcut_add": "Ctrl+N",  # Продолжает выражение, список аргументов или структуру данных
        "shortcut_edit": "Ctrl+E",  # Продолжает выражение, список аргументов или структуру данных
        "shortcut_delete": "Delete",  # Продолжает выражение, список аргументов или структуру данных
        "shortcut_today": "Ctrl+T",  # Продолжает выражение, список аргументов или структуру данных
        "shortcut_export": "Ctrl+Shift+E",  # Продолжает выражение, список аргументов или структуру данных
        "shortcut_search": "Ctrl+F",  # Продолжает выражение, список аргументов или структуру данных
        "reminder_minutes": "10",  # Продолжает выражение, список аргументов или структуру данных
        "notifications_enabled": "1",  # Продолжает выражение, список аргументов или структуру данных
    }  # Продолжает структуру списка, словаря или вызова функции

    @staticmethod  # Объявляет функцию или метод для отдельной операции
    def default_db_path() -> Path:  # Объявляет функцию или метод для отдельной операции
        """Возвращает путь к базе рядом с файлами проекта."""  # Участвует в реализации логики текущего компонента
        return Path(__file__).resolve().parent / "meet_to_meet.db"  # Управляет выполнением алгоритма или возвращает результат

    @staticmethod  # Объявляет функцию или метод для отдельной операции
    def legacy_db_path() -> Path:  # Объявляет функцию или метод для отдельной операции
        """Путь к базе из предыдущей версии приложения."""  # Участвует в реализации логики текущего компонента
        return Path.home() / ".meet_to_meet" / "meet_to_meet.db"  # Управляет выполнением алгоритма или возвращает результат

    def __init__(self, db_path: str | Path | None = None) -> None:  # Объявляет функцию или метод для отдельной операции
        if db_path is None:  # Управляет выполнением алгоритма или возвращает результат
            db_path = self.default_db_path()  # Присваивает значение переменной или атрибуту
            self._migrate_legacy_database(Path(db_path))  # Выполняет файловую операцию, обращение к БД или вывод сообщения
        self.db_path = Path(db_path).expanduser().resolve()  # Сохраняет состояние или компонент внутри текущего объекта
        self.db_path.parent.mkdir(parents=True, exist_ok=True)  # Вызывает метод или функцию для выполнения действия
        self.initialize()  # Вызывает метод или функцию для выполнения действия

    @classmethod  # Объявляет функцию или метод для отдельной операции
    def _migrate_legacy_database(cls, destination: Path) -> None:  # Объявляет функцию или метод для отдельной операции
        """Копирует старую базу в папку проекта, не удаляя исходный файл."""  # Участвует в реализации логики текущего компонента
        legacy = cls.legacy_db_path()  # Присваивает значение переменной или атрибуту
        if destination.exists() or not legacy.is_file():  # Управляет выполнением алгоритма или возвращает результат
            return  # Управляет выполнением алгоритма или возвращает результат
        destination.parent.mkdir(parents=True, exist_ok=True)  # Вызывает метод или функцию для выполнения действия
        shutil.copy2(legacy, destination)  # Вызывает метод или функцию для выполнения действия

    @contextmanager  # Объявляет функцию или метод для отдельной операции
    def connect(self) -> Iterator[sqlite3.Connection]:  # Объявляет функцию или метод для отдельной операции
        """Открывает соединение SQLite и гарантированно закрывает его после работы."""  # Участвует в реализации логики текущего компонента
        connection = sqlite3.connect(self.db_path)  # Связывает сигнал Qt с обработчиком пользовательского действия
        connection.row_factory = sqlite3.Row  # Присваивает значение переменной или атрибуту
        connection.execute("PRAGMA foreign_keys = ON")  # Выполняет SQL-запрос к базе SQLite
        try:  # Управляет выполнением алгоритма или возвращает результат
            yield connection  # Участвует в реализации логики текущего компонента
            connection.commit()  # Вызывает метод или функцию для выполнения действия
        except Exception:  # Управляет выполнением алгоритма или возвращает результат
            connection.rollback()  # Вызывает метод или функцию для выполнения действия
            raise  # Управляет выполнением алгоритма или возвращает результат
        finally:  # Управляет выполнением алгоритма или возвращает результат
            connection.close()  # Вызывает метод или функцию для выполнения действия

    def initialize(self) -> None:  # Объявляет функцию или метод для отдельной операции
        """Создаёт необходимые таблицы при первом запуске."""  # Участвует в реализации логики текущего компонента
        with self.connect() as connection:  # Управляет выполнением алгоритма или возвращает результат
            connection.execute(  # Выполняет SQL-запрос к базе SQLite
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
                """  # Завершает многострочную строку или SQL-шаблон
            )  # Продолжает структуру списка, словаря или вызова функции
            connection.execute(  # Выполняет SQL-запрос к базе SQLite
                "CREATE INDEX IF NOT EXISTS idx_meetings_date "  # Часть SQL-команды для структуры или данных SQLite
                "ON meetings(meeting_date, start_time)"  # Участвует в реализации логики текущего компонента
            )  # Продолжает структуру списка, словаря или вызова функции
            connection.execute(  # Выполняет SQL-запрос к базе SQLite
                """
                CREATE TABLE IF NOT EXISTS settings (
                    setting_key TEXT PRIMARY KEY,
                    setting_value TEXT NOT NULL
                )
                """  # Завершает многострочную строку или SQL-шаблон
            )  # Продолжает структуру списка, словаря или вызова функции
            for key, value in self.DEFAULT_SETTINGS.items():  # Управляет выполнением алгоритма или возвращает результат
                connection.execute(  # Выполняет SQL-запрос к базе SQLite
                    "INSERT OR IGNORE INTO settings(setting_key, setting_value) "  # Участвует в реализации логики текущего компонента
                    "VALUES (?, ?)",  # Продолжает выражение, список аргументов или структуру данных
                    (key, value),  # Продолжает выражение, список аргументов или структуру данных
                )  # Продолжает структуру списка, словаря или вызова функции

    def add_meeting(self, data: dict[str, Any]) -> int:  # Объявляет функцию или метод для отдельной операции
        """Добавляет встречу и возвращает её идентификатор."""  # Участвует в реализации логики текущего компонента
        with self.connect() as connection:  # Управляет выполнением алгоритма или возвращает результат
            cursor = connection.execute(  # Выполняет SQL-запрос к базе SQLite
                """
                INSERT INTO meetings
                (title, meeting_date, start_time, end_time, place,
                 description, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,  # Завершает многострочный литерал и продолжает выражение
                self._meeting_values(data),  # Вызывает метод или функцию для выполнения действия
            )  # Продолжает структуру списка, словаря или вызова функции
            return int(cursor.lastrowid)  # Управляет выполнением алгоритма или возвращает результат

    def update_meeting(self, meeting_id: int, data: dict[str, Any]) -> None:  # Объявляет функцию или метод для отдельной операции
        """Обновляет существующую встречу."""  # Участвует в реализации логики текущего компонента
        values = self._meeting_values(data)  # Присваивает значение переменной или атрибуту
        with self.connect() as connection:  # Управляет выполнением алгоритма или возвращает результат
            connection.execute(  # Выполняет SQL-запрос к базе SQLite
                """
                UPDATE meetings SET
                    title = ?, meeting_date = ?, start_time = ?, end_time = ?,
                    place = ?, description = ?, notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,  # Завершает многострочный литерал и продолжает выражение
                (*values, meeting_id),  # Продолжает выражение, список аргументов или структуру данных
            )  # Продолжает структуру списка, словаря или вызова функции

    @staticmethod  # Объявляет функцию или метод для отдельной операции
    def _meeting_values(data: dict[str, Any]) -> tuple[str, ...]:  # Объявляет функцию или метод для отдельной операции
        return (  # Управляет выполнением алгоритма или возвращает результат
            str(data.get("title", "")).strip(),  # Вызывает метод или функцию для выполнения действия
            str(data.get("meeting_date", "")),  # Вызывает метод или функцию для выполнения действия
            str(data.get("start_time", "")),  # Вызывает метод или функцию для выполнения действия
            str(data.get("end_time", "")),  # Вызывает метод или функцию для выполнения действия
            str(data.get("place", "")).strip(),  # Вызывает метод или функцию для выполнения действия
            str(data.get("description", "")).strip(),  # Вызывает метод или функцию для выполнения действия
            str(data.get("notes", "")).strip(),  # Вызывает метод или функцию для выполнения действия
        )  # Продолжает структуру списка, словаря или вызова функции

    def delete_meeting(self, meeting_id: int) -> None:  # Объявляет функцию или метод для отдельной операции
        """Удаляет встречу по идентификатору."""  # Участвует в реализации логики текущего компонента
        with self.connect() as connection:  # Управляет выполнением алгоритма или возвращает результат
            connection.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))  # Выполняет SQL-запрос к базе SQLite

    def get_meeting(self, meeting_id: int) -> dict[str, Any] | None:  # Объявляет функцию или метод для отдельной операции
        """Возвращает одну встречу."""  # Участвует в реализации логики текущего компонента
        with self.connect() as connection:  # Управляет выполнением алгоритма или возвращает результат
            row = connection.execute(  # Выполняет SQL-запрос к базе SQLite
                "SELECT * FROM meetings WHERE id = ?", (meeting_id,)  # Часть SQL-команды для структуры или данных SQLite
            ).fetchone()  # Продолжает выражение, список аргументов или структуру данных
            return dict(row) if row else None  # Управляет выполнением алгоритма или возвращает результат

    def get_meetings_for_date(self, date_text: str) -> list[dict[str, Any]]:  # Объявляет функцию или метод для отдельной операции
        """Возвращает встречи выбранной даты по времени начала."""  # Участвует в реализации логики текущего компонента
        with self.connect() as connection:  # Управляет выполнением алгоритма или возвращает результат
            rows = connection.execute(  # Выполняет SQL-запрос к базе SQLite
                """
                SELECT * FROM meetings
                WHERE meeting_date = ?
                ORDER BY start_time, title COLLATE NOCASE
                """,  # Завершает многострочный литерал и продолжает выражение
                (date_text,),  # Продолжает выражение, список аргументов или структуру данных
            ).fetchall()  # Продолжает выражение, список аргументов или структуру данных
            return [dict(row) for row in rows]  # Управляет выполнением алгоритма или возвращает результат

    def get_all_meetings(self) -> list[dict[str, Any]]:  # Объявляет функцию или метод для отдельной операции
        """Возвращает все встречи в календаре."""  # Участвует в реализации логики текущего компонента
        with self.connect() as connection:  # Управляет выполнением алгоритма или возвращает результат
            rows = connection.execute(  # Выполняет SQL-запрос к базе SQLite
                """
                SELECT * FROM meetings
                ORDER BY meeting_date, start_time, title COLLATE NOCASE
                """  # Завершает многострочную строку или SQL-шаблон
            ).fetchall()  # Продолжает выражение, список аргументов или структуру данных
            return [dict(row) for row in rows]  # Управляет выполнением алгоритма или возвращает результат

    def search_meetings(self, text: str) -> list[dict[str, Any]]:  # Объявляет функцию или метод для отдельной операции
        """Ищет по названию, месту и описанию."""  # Участвует в реализации логики текущего компонента
        pattern = f"%{text.strip()}%"  # Присваивает значение переменной или атрибуту
        with self.connect() as connection:  # Управляет выполнением алгоритма или возвращает результат
            rows = connection.execute(  # Выполняет SQL-запрос к базе SQLite
                """
                SELECT * FROM meetings
                WHERE title LIKE ? OR place LIKE ? OR description LIKE ?
                ORDER BY meeting_date, start_time
                """,  # Завершает многострочный литерал и продолжает выражение
                (pattern, pattern, pattern),  # Продолжает выражение, список аргументов или структуру данных
            ).fetchall()  # Продолжает выражение, список аргументов или структуру данных
            return [dict(row) for row in rows]  # Управляет выполнением алгоритма или возвращает результат

    def get_meetings_between(  # Объявляет функцию или метод для отдельной операции
        self, start_date: str, end_date: str  # Участвует в реализации логики текущего компонента
    ) -> list[dict[str, Any]]:  # Продолжает выражение, список аргументов или структуру данных
        """Возвращает встречи в диапазоне дат включительно."""  # Участвует в реализации логики текущего компонента
        with self.connect() as connection:  # Управляет выполнением алгоритма или возвращает результат
            rows = connection.execute(  # Выполняет SQL-запрос к базе SQLite
                """
                SELECT * FROM meetings
                WHERE meeting_date BETWEEN ? AND ?
                ORDER BY meeting_date, start_time
                """,  # Завершает многострочный литерал и продолжает выражение
                (start_date, end_date),  # Продолжает выражение, список аргументов или структуру данных
            ).fetchall()  # Продолжает выражение, список аргументов или структуру данных
            return [dict(row) for row in rows]  # Управляет выполнением алгоритма или возвращает результат

    def has_time_conflict(  # Объявляет функцию или метод для отдельной операции
        self,  # Продолжает выражение, список аргументов или структуру данных
        meeting_date: str,  # Продолжает выражение, список аргументов или структуру данных
        start_time: str,  # Продолжает выражение, список аргументов или структуру данных
        end_time: str,  # Продолжает выражение, список аргументов или структуру данных
        exclude_id: int | None = None,  # Продолжает выражение, список аргументов или структуру данных
    ) -> bool:  # Продолжает выражение, список аргументов или структуру данных
        """Проверяет пересечение временных интервалов в выбранный день."""  # Участвует в реализации логики текущего компонента
        query = """
            SELECT COUNT(*) FROM meetings
            WHERE meeting_date = ?
              AND start_time < ?
              AND end_time > ?
        """  # Завершает многострочную строку или SQL-шаблон
        parameters: list[Any] = [meeting_date, end_time, start_time]  # Участвует в реализации логики текущего компонента
        if exclude_id is not None:  # Управляет выполнением алгоритма или возвращает результат
            query += " AND id != ?"  # Участвует в реализации логики текущего компонента
            parameters.append(exclude_id)  # Изменяет коллекцию, состояние или передаёт событие
        with self.connect() as connection:  # Управляет выполнением алгоритма или возвращает результат
            count = connection.execute(query, parameters).fetchone()[0]  # Выполняет SQL-запрос к базе SQLite
        return int(count) > 0  # Управляет выполнением алгоритма или возвращает результат

    def get_settings(self) -> dict[str, str]:  # Объявляет функцию или метод для отдельной операции
        """Читает настройки и дополняет отсутствующие значениями по умолчанию."""  # Участвует в реализации логики текущего компонента
        result = dict(self.DEFAULT_SETTINGS)  # Присваивает значение переменной или атрибуту
        with self.connect() as connection:  # Управляет выполнением алгоритма или возвращает результат
            rows = connection.execute(  # Выполняет SQL-запрос к базе SQLite
                "SELECT setting_key, setting_value FROM settings"  # Часть SQL-команды для структуры или данных SQLite
            ).fetchall()  # Продолжает выражение, список аргументов или структуру данных
        result.update({row["setting_key"]: row["setting_value"] for row in rows})  # Изменяет коллекцию, состояние или передаёт событие
        return result  # Управляет выполнением алгоритма или возвращает результат

    def save_settings(self, settings: dict[str, str]) -> None:  # Объявляет функцию или метод для отдельной операции
        """Сохраняет несколько настроек одной транзакцией."""  # Участвует в реализации логики текущего компонента
        with self.connect() as connection:  # Управляет выполнением алгоритма или возвращает результат
            connection.executemany(  # Выполняет SQL-запрос к базе SQLite
                """
                INSERT INTO settings(setting_key, setting_value)
                VALUES (?, ?)
                ON CONFLICT(setting_key)
                DO UPDATE SET setting_value = excluded.setting_value
                """,  # Завершает многострочный литерал и продолжает выражение
                [(key, str(value)) for key, value in settings.items()],  # Продолжает выражение, список аргументов или структуру данных
            )  # Продолжает структуру списка, словаря или вызова функции

    def get_upcoming_meetings(self, until_text: str) -> list[dict[str, Any]]:  # Объявляет функцию или метод для отдельной операции
        """Возвращает встречи, начинающиеся не позже указанной даты и времени."""  # Участвует в реализации логики текущего компонента
        with self.connect() as connection:  # Управляет выполнением алгоритма или возвращает результат
            rows = connection.execute(  # Выполняет SQL-запрос к базе SQLite
                """
                SELECT * FROM meetings
                WHERE meeting_date || ' ' || start_time <= ?
                ORDER BY meeting_date DESC, start_time DESC
                LIMIT 50
                """,  # Завершает многострочный литерал и продолжает выражение
                (until_text,),  # Продолжает выражение, список аргументов или структуру данных
            ).fetchall()  # Продолжает выражение, список аргументов или структуру данных
            return [dict(row) for row in rows]  # Управляет выполнением алгоритма или возвращает результат

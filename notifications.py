"""Ненавязчивые уведомления через системный трей Qt."""

from __future__ import annotations

from PyQt6.QtCore import QObject, QTimer, QDateTime, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon


class NotificationManager(QObject):
    """Периодически проверяет встречи и показывает системные сообщения."""

    notification_sent = pyqtSignal(int)

    def __init__(self, database, parent=None) -> None:
        super().__init__(parent)
        self.database = database
        self.settings = database.get_settings()
        self.tray = None
        self.sent_ids: set[int] = set()
        self.timer = QTimer(self)
        self.timer.setInterval(30_000)
        self.timer.timeout.connect(self.check_meetings)
        self._create_tray_icon()
        self.timer.start()

    def _create_tray_icon(self) -> None:
        """Создаёт значок трея, если платформа его поддерживает."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray = QSystemTrayIcon(QIcon(), self)
        self.tray.setToolTip("Meet to meet")
        self.tray.show()

    def update_settings(self, settings: dict[str, str]) -> None:
        self.settings = settings

    def check_meetings(self) -> None:
        """Проверяет, не наступило ли время напомнить о встрече."""
        if self.settings.get("notifications_enabled", "1") != "1":
            return
        now = QDateTime.currentDateTime()
        lead = max(0, int(self.settings.get("reminder_minutes", "10")))
        target = now.addSecs(lead * 60)
        now_text = now.toString("yyyy-MM-dd HH:mm")
        target_text = target.toString("yyyy-MM-dd HH:mm")
        for meeting in self.database.get_upcoming_meetings(target_text):
            meeting_id = int(meeting["id"])
            meeting_time = QDateTime.fromString(
                f"{meeting['meeting_date']} {meeting['start_time']}",
                "yyyy-MM-dd HH:mm",
            )
            if meeting_id in self.sent_ids or not meeting_time.isValid():
                continue
            if meeting_time < now or meeting_time > target:
                continue
            self.show_notification(meeting)
            self.sent_ids.add(meeting_id)
            self.notification_sent.emit(meeting_id)

    def show_notification(self, meeting: dict) -> None:
        """Показывает сообщение; без трея приложение просто пропускает его."""
        if self.tray is None:
            return
        place = meeting.get("place") or "Место не указано"
        self.tray.showMessage(
            "Скоро встреча",
            f"{meeting['title']} — {meeting['start_time']}\n{place}",
            QSystemTrayIcon.MessageIcon.Information,
            10_000,
        )

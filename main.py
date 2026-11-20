"""Meet to meet — простое настольное приложение для планирования встреч."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QDate, QLocale, QTime
from PyQt6.QtGui import QAction, QColor, QKeySequence, QTextCharFormat
from PyQt6.QtWidgets import (
    QApplication,
    QCalendarWidget,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from database import Database
from notifications import NotificationManager

APP_NAME = "Meet to meet"


class MeetingDialog(QDialog):
    """Окно добавления или редактирования встречи."""

    def __init__(self, parent=None, meeting=None, time_format="24 часа") -> None:
        super().__init__(parent)
        self.meeting = meeting or {}
        self.time_format = time_format
        self.setWindowTitle("Редактирование встречи" if meeting else "Новая встреча")
        self.setMinimumWidth(440)
        self._build_ui()
        self._fill_values()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Например, Обсуждение проекта")
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        self.start_edit = QTimeEdit(QTime(10, 0))
        self.end_edit = QTimeEdit(QTime(11, 0))
        self.place_edit = QLineEdit()
        self.place_edit.setPlaceholderText("Zoom, Google Meet, офис или ссылка")
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Краткая цель встречи")
        self.notes_edit = QPlainTextEdit()
        self.notes_edit.setPlaceholderText("Дополнительная информация...")
        self.notes_edit.setMaximumHeight(100)

        if self.time_format == "12 часов":
            self.start_edit.setDisplayFormat("hh:mm AP")
            self.end_edit.setDisplayFormat("hh:mm AP")
        else:
            self.start_edit.setDisplayFormat("HH:mm")
            self.end_edit.setDisplayFormat("HH:mm")

        form.addRow("Название *", self.title_edit)
        form.addRow("Дата", self.date_edit)
        form.addRow("Начало", self.start_edit)
        form.addRow("Окончание", self.end_edit)
        form.addRow("Место / ссылка", self.place_edit)
        form.addRow("Описание", self.description_edit)
        form.addRow("Заметки", self.notes_edit)
        layout.addLayout(form)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def _fill_values(self) -> None:
        if not self.meeting:
            return
        self.title_edit.setText(self.meeting.get("title", ""))
        date_value = QDate.fromString(
            self.meeting.get("meeting_date", ""), "yyyy-MM-dd"
        )
        if date_value.isValid():
            self.date_edit.setDate(date_value)
        start_value = QTime.fromString(
            self.meeting.get("start_time", ""), "HH:mm"
        )
        end_value = QTime.fromString(self.meeting.get("end_time", ""), "HH:mm")
        if start_value.isValid():
            self.start_edit.setTime(start_value)
        if end_value.isValid():
            self.end_edit.setTime(end_value)
        self.place_edit.setText(self.meeting.get("place", ""))
        self.description_edit.setText(self.meeting.get("description", ""))
        self.notes_edit.setPlainText(self.meeting.get("notes", ""))

    def get_data(self) -> dict[str, str]:
        """Возвращает данные формы в формате базы данных."""
        return {
            "title": self.title_edit.text().strip(),
            "meeting_date": self.date_edit.date().toString("yyyy-MM-dd"),
            "start_time": self.start_edit.time().toString("HH:mm"),
            "end_time": self.end_edit.time().toString("HH:mm"),
            "place": self.place_edit.text().strip(),
            "description": self.description_edit.text().strip(),
            "notes": self.notes_edit.toPlainText().strip(),
        }

    def accept(self) -> None:
        """Проверяет поля перед закрытием окна."""
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, "Проверка данных", "Введите название встречи.")
            self.title_edit.setFocus()
            return
        if self.start_edit.time() >= self.end_edit.time():
            QMessageBox.warning(
                self,
                "Проверка времени",
                "Время окончания должно быть позже времени начала.",
            )
            return
        super().accept()


class SettingsDialog(QDialog):
    """Окно настроек оформления, времени, уведомлений и горячих клавиш."""

    def __init__(self, parent=None, settings=None) -> None:
        super().__init__(parent)
        self.settings = settings or {}
        self.setWindowTitle("Настройки")
        self.setMinimumWidth(430)
        self._build_ui()
        self._fill_values()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Светлая", "Тёмная"])
        self.time_combo = QComboBox()
        self.time_combo.addItems(["24 часа", "12 часов"])
        self.reminder_spin = QSpinBox()
        self.reminder_spin.setRange(0, 1440)
        self.reminder_spin.setSuffix(" мин.")
        self.notifications_check = QCheckBox("Показывать уведомления")

        self.shortcut_edits: dict[str, QLineEdit] = {}
        shortcut_fields = [
            ("shortcut_add", "Добавить встречу"),
            ("shortcut_edit", "Изменить встречу"),
            ("shortcut_delete", "Удалить встречу"),
            ("shortcut_today", "Перейти к сегодня"),
            ("shortcut_export", "Экспорт календаря"),
            ("shortcut_search", "Поиск"),
        ]
        form.addRow("Оформление", self.theme_combo)
        form.addRow("Формат времени", self.time_combo)
        form.addRow("Напоминать за", self.reminder_spin)
        form.addRow("Уведомления", self.notifications_check)
        for key, label in shortcut_fields:
            edit = QLineEdit()
            edit.setPlaceholderText("Например, Ctrl+N")
            self.shortcut_edits[key] = edit
            form.addRow(label, edit)
        layout.addLayout(form)

        help_text = QLabel(
            "Формат сочетаний — стандартный формат Qt: Ctrl+N, Alt+A, Delete."
        )
        help_text.setWordWrap(True)
        layout.addWidget(help_text)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _fill_values(self) -> None:
        self.theme_combo.setCurrentText(self.settings.get("theme", "Светлая"))
        self.time_combo.setCurrentText(
            self.settings.get("time_format", "24 часа")
        )
        self.reminder_spin.setValue(
            int(self.settings.get("reminder_minutes", "10"))
        )
        self.notifications_check.setChecked(
            self.settings.get("notifications_enabled", "1") == "1"
        )
        for key, edit in self.shortcut_edits.items():
            edit.setText(self.settings.get(key, ""))

    def get_settings(self) -> dict[str, str]:
        result = {
            "theme": self.theme_combo.currentText(),
            "time_format": self.time_combo.currentText(),
            "reminder_minutes": str(self.reminder_spin.value()),
            "notifications_enabled": "1" if self.notifications_check.isChecked() else "0",
        }
        result.update({key: edit.text().strip() for key, edit in self.shortcut_edits.items()})
        return result


class MainWindow(QMainWindow):
    """Главное окно календаря."""

    def __init__(self) -> None:
        super().__init__()
        self.database = Database()
        self.settings = self.database.get_settings()
        self.selected_meeting_id: int | None = None
        self.actions: dict[str, QAction] = {}
        self.setWindowTitle(APP_NAME)
        self.resize(1180, 760)
        self.setMinimumSize(1020, 680)
        self._build_ui()
        self._build_actions()
        self.notification_manager = NotificationManager(self.database, self)
        self.notification_manager.update_settings(self.settings)
        self._apply_theme()
        self.refresh_meetings()
        self.statusBar().showMessage("Готово")

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(22, 18, 22, 16)
        root.setSpacing(16)

        # Верхняя строка: название приложения и основные действия.
        header = QHBoxLayout()
        header.setSpacing(8)
        brand = QVBoxLayout()
        brand.setSpacing(2)
        title = QLabel(APP_NAME)
        title.setObjectName("appTitle")
        subtitle = QLabel("Планируйте встречи и держите расписание под контролем")
        subtitle.setObjectName("appSubtitle")
        brand.addWidget(title)
        brand.addWidget(subtitle)
        header.addLayout(brand, 1)

        self.add_button = QPushButton("Новая встреча")
        self.add_button.setObjectName("primaryButton")
        self.edit_button = QPushButton("Изменить")
        self.delete_button = QPushButton("Удалить")
        self.export_button = QPushButton("Экспорт")
        self.settings_button = QPushButton("Настройки")
        for button in (
            self.add_button,
            self.edit_button,
            self.delete_button,
            self.export_button,
            self.settings_button,
        ):
            button.setMinimumHeight(38)
            header.addWidget(button)
        root.addLayout(header)

        content = QHBoxLayout()
        content.setSpacing(16)

        # Левая панель календаря. Встроенная панель навигации скрыта:
        # собственные кнопки имеют одинаковый размер и не накладываются.
        calendar_panel = QWidget()
        calendar_panel.setObjectName("panel")
        calendar_panel.setMinimumWidth(340)
        calendar_panel.setMaximumWidth(390)
        calendar_layout = QVBoxLayout(calendar_panel)
        calendar_layout.setContentsMargins(16, 15, 16, 16)
        calendar_layout.setSpacing(12)

        calendar_title_row = QHBoxLayout()
        calendar_title = QLabel("Календарь")
        calendar_title.setObjectName("sectionTitle")
        self.today_button = QPushButton("Сегодня")
        self.today_button.setObjectName("quietButton")
        self.today_button.setMinimumHeight(32)
        calendar_title_row.addWidget(calendar_title)
        calendar_title_row.addStretch(1)
        calendar_title_row.addWidget(self.today_button)
        calendar_layout.addLayout(calendar_title_row)

        month_navigation = QHBoxLayout()
        month_navigation.setSpacing(8)
        self.prev_month_button = QPushButton("‹")
        self.prev_month_button.setObjectName("calendarNavButton")
        self.prev_month_button.setToolTip("Предыдущий месяц")
        self.prev_month_button.setAccessibleName("Предыдущий месяц")
        self.next_month_button = QPushButton("›")
        self.next_month_button.setObjectName("calendarNavButton")
        self.next_month_button.setToolTip("Следующий месяц")
        self.next_month_button.setAccessibleName("Следующий месяц")
        self.month_label = QLabel()
        self.month_label.setObjectName("monthLabel")
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        month_navigation.addWidget(self.prev_month_button)
        month_navigation.addWidget(self.month_label, 1)
        month_navigation.addWidget(self.next_month_button)
        calendar_layout.addLayout(month_navigation)

        self.calendar = QCalendarWidget()
        self.calendar.setNavigationBarVisible(False)
        self.calendar.setGridVisible(True)
        self.calendar.setLocale(QLocale("ru_RU"))
        self.calendar.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        self.calendar.setHorizontalHeaderFormat(
            QCalendarWidget.HorizontalHeaderFormat.ShortDayNames
        )
        self.calendar.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )
        self.calendar.setMinimumWidth(305)
        self.calendar.setMinimumHeight(285)
        calendar_layout.addWidget(self.calendar, 1)
        content.addWidget(calendar_panel, 0)

        # Правая панель: дата, поиск, список и подробности.
        meetings_panel = QWidget()
        meetings_panel.setObjectName("panel")
        right = QVBoxLayout(meetings_panel)
        right.setContentsMargins(18, 15, 18, 16)
        right.setSpacing(12)

        self.day_label = QLabel("Встречи на выбранную дату")
        self.day_label.setObjectName("sectionTitle")
        right.addWidget(self.day_label)

        search_row = QHBoxLayout()
        search_row.setSpacing(8)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(
            "Поиск по названию, месту или описанию…"
        )
        self.search_edit.setClearButtonEnabled(True)
        self.clear_search_button = QPushButton("Сбросить")
        self.clear_search_button.setObjectName("quietButton")
        self.clear_search_button.setMinimumHeight(36)
        search_row.addWidget(self.search_edit, 1)
        search_row.addWidget(self.clear_search_button)
        right.addLayout(search_row)

        self.meetings_table = QTableWidget(0, 5)
        self.meetings_table.setObjectName("meetingsTable")
        self.meetings_table.setHorizontalHeaderLabels(
            ["Время", "Название", "Место", "Описание", "ID"]
        )
        self.meetings_table.setColumnHidden(4, True)
        self.meetings_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.meetings_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.meetings_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.meetings_table.setAlternatingRowColors(True)
        self.meetings_table.setShowGrid(False)
        self.meetings_table.setWordWrap(False)
        self.meetings_table.verticalHeader().setVisible(False)
        self.meetings_table.verticalHeader().setDefaultSectionSize(40)
        header = self.meetings_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        right.addWidget(self.meetings_table, 1)

        self.details_label = QLabel(
            "Выберите встречу, чтобы посмотреть подробности."
        )
        self.details_label.setObjectName("detailsPanel")
        self.details_label.setWordWrap(True)
        self.details_label.setMinimumHeight(68)
        right.addWidget(self.details_label)
        content.addWidget(meetings_panel, 1)
        root.addLayout(content, 1)

        self.marked_dates: set[str] = set()

        self.add_button.clicked.connect(self.add_meeting)
        self.edit_button.clicked.connect(self.edit_meeting)
        self.delete_button.clicked.connect(self.delete_meeting)
        self.today_button.clicked.connect(self.go_to_today)
        self.prev_month_button.clicked.connect(self.calendar.showPreviousMonth)
        self.next_month_button.clicked.connect(self.calendar.showNextMonth)
        self.export_button.clicked.connect(self.export_calendar)
        self.settings_button.clicked.connect(self.open_settings)
        self.calendar.selectionChanged.connect(self.refresh_meetings)
        self.calendar.currentPageChanged.connect(self._update_month_label)
        self.meetings_table.itemSelectionChanged.connect(self.show_details)
        self.meetings_table.cellDoubleClicked.connect(
            lambda _row, _column: self.edit_meeting()
        )
        self.search_edit.textChanged.connect(self.search_meetings)
        self.clear_search_button.clicked.connect(self.search_edit.clear)
        self._update_month_label(
            self.calendar.yearShown(), self.calendar.monthShown()
        )

    def _update_month_label(self, year: int, month: int) -> None:
        """Обновляет подпись месяца над календарём."""
        month_date = QDate(year, month, 1)
        month_text = QLocale("ru_RU").toString(month_date, "MMMM yyyy")
        self.month_label.setText(month_text.capitalize())

    def _refresh_calendar_markers(self) -> None:
        """Подсвечивает даты, на которые уже запланированы встречи."""
        for date_text in self.marked_dates:
            old_date = QDate.fromString(date_text, "yyyy-MM-dd")
            if old_date.isValid():
                self.calendar.setDateTextFormat(old_date, QTextCharFormat())
        self.marked_dates.clear()

        marker = QTextCharFormat()
        if self.settings.get("theme", "Светлая") == "Тёмная":
            marker.setForeground(QColor("#FDBA74"))
            marker.setBackground(QColor("#4B2D1D"))
        else:
            marker.setForeground(QColor("#C2410C"))
            marker.setBackground(QColor("#FFEDD5"))
        marker.setFontWeight(700)
        for meeting in self.database.get_all_meetings():
            date_text = meeting["meeting_date"]
            if date_text in self.marked_dates:
                continue
            meeting_date = QDate.fromString(date_text, "yyyy-MM-dd")
            if meeting_date.isValid():
                self.calendar.setDateTextFormat(meeting_date, marker)
                self.marked_dates.add(date_text)

    def _build_actions(self) -> None:
        """Создаёт действия меню и назначает горячие клавиши."""
        file_menu = self.menuBar().addMenu("Файл")
        meeting_menu = self.menuBar().addMenu("Встречи")
        view_menu = self.menuBar().addMenu("Вид")

        self._add_action(file_menu, "export", "Экспорт календаря", "export_calendar")
        self._add_action(file_menu, "settings", "Настройки", "open_settings")
        file_menu.addSeparator()
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        self._add_action(meeting_menu, "add", "Добавить встречу", "add_meeting")
        self._add_action(meeting_menu, "edit", "Изменить встречу", "edit_meeting")
        self._add_action(meeting_menu, "delete", "Удалить встречу", "delete_meeting")
        self._add_action(view_menu, "today", "Перейти к сегодня", "go_to_today")
        self._add_action(view_menu, "search", "Поиск", "focus_search")
        self.update_shortcuts()

    def _add_action(self, menu, key: str, title: str, method_name: str) -> None:
        action = QAction(title, self)
        action.triggered.connect(getattr(self, method_name))
        menu.addAction(action)
        self.actions[key] = action

    def update_shortcuts(self) -> None:
        mapping = {
            "add": "shortcut_add",
            "edit": "shortcut_edit",
            "delete": "shortcut_delete",
            "today": "shortcut_today",
            "export": "shortcut_export",
            "search": "shortcut_search",
        }
        for action_key, setting_key in mapping.items():
            shortcut = self.settings.get(setting_key, "")
            self.actions[action_key].setShortcut(QKeySequence(shortcut))

    def _apply_theme(self) -> None:
        """Применяет единую светлую (белую) или тёмную тему ко всему приложению."""
        dark = self.settings.get("theme", "Светлая") == "Тёмная"
        if dark:
            colors = {
                "window": "#17191F",
                "panel": "#22252D",
                "surface": "#2B2F39",
                "surface_alt": "#252933",
                "text": "#F3F4F6",
                "muted": "#A3AAB8",
                "border": "#3B414D",
                "input": "#1D2028",
                "selection": "#75401F",
                "selection_text": "#FFFFFF",
                "accent": "#F97316",
                "accent_hover": "#EA580C",
            }
        else:
            # Светлая тема намеренно белая, а не системно-серая.
            colors = {
                "window": "#F4F6FA",
                "panel": "#FFFFFF",
                "surface": "#FFFFFF",
                "surface_alt": "#F8FAFC",
                "text": "#202938",
                "muted": "#697586",
                "border": "#E2E8F0",
                "input": "#FFFFFF",
                "selection": "#FFEDD5",
                "selection_text": "#9A3412",
                "accent": "#F97316",
                "accent_hover": "#EA580C",
            }

        stylesheet = f"""
            QMainWindow, QDialog {{
                background-color: {colors['window']};
                color: {colors['text']};
            }}
            QWidget {{ color: {colors['text']}; }}
            QWidget#centralWidget {{ background-color: {colors['window']}; }}
            QWidget#panel {{
                background-color: {colors['panel']};
                border: 1px solid {colors['border']};
                border-radius: 14px;
            }}
            QLabel {{ background: transparent; }}
            QLabel#appTitle {{
                font-size: 24px;
                font-weight: 700;
                color: {colors['text']};
            }}
            QLabel#appSubtitle {{ font-size: 12px; color: {colors['muted']}; }}
            QLabel#sectionTitle {{ font-size: 16px; font-weight: 650; }}
            QLabel#monthLabel {{ font-size: 14px; font-weight: 650; }}
            QPushButton {{
                background-color: {colors['surface']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
                padding: 7px 12px;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background-color: {colors['surface_alt']};
                border-color: {colors['muted']};
            }}
            QPushButton:pressed {{ background-color: {colors['selection']}; }}
            QPushButton:disabled {{ color: {colors['muted']}; }}
            QPushButton#primaryButton {{
                background-color: {colors['accent']};
                color: #FFFFFF;
                border: 1px solid {colors['accent']};
                font-weight: 650;
                padding-left: 15px;
                padding-right: 15px;
            }}
            QPushButton#primaryButton:hover {{
                background-color: {colors['accent_hover']};
                border-color: {colors['accent_hover']};
            }}
            QPushButton#quietButton {{
                background-color: transparent;
                border-color: transparent;
                color: {colors['accent']};
                padding-left: 8px;
                padding-right: 8px;
            }}
            QPushButton#calendarNavButton {{
                min-width: 34px;
                max-width: 34px;
                min-height: 32px;
                max-height: 32px;
                padding: 0px;
                font-size: 23px;
                font-weight: 500;
            }}
            QLineEdit, QPlainTextEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox {{
                background-color: {colors['input']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
                padding: 7px 9px;
                selection-background-color: {colors['accent']};
                selection-color: #FFFFFF;
            }}
            QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus,
            QDateEdit:focus, QTimeEdit:focus, QSpinBox:focus {{
                border: 1px solid {colors['accent']};
            }}
            QComboBox QAbstractItemView {{
                background-color: {colors['panel']};
                color: {colors['text']};
                selection-background-color: {colors['selection']};
                selection-color: {colors['selection_text']};
                border: 1px solid {colors['border']};
            }}
            QCalendarWidget {{
                background-color: {colors['panel']};
                border: none;
            }}
            QCalendarWidget QWidget {{
                background-color: {colors['panel']};
                color: {colors['text']};
            }}
            QCalendarWidget QAbstractItemView {{
                background-color: {colors['panel']};
                color: {colors['text']};
                selection-background-color: {colors['accent']};
                selection-color: #FFFFFF;
                outline: 0;
                border: none;
                gridline-color: {colors['border']};
            }}
            QCalendarWidget QAbstractItemView:disabled {{ color: {colors['muted']}; }}
            QTableWidget {{
                background-color: {colors['panel']};
                alternate-background-color: {colors['surface_alt']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: 9px;
                selection-background-color: {colors['selection']};
                selection-color: {colors['selection_text']};
                outline: 0;
            }}
            QHeaderView::section {{
                background-color: {colors['surface_alt']};
                color: {colors['muted']};
                border: none;
                border-bottom: 1px solid {colors['border']};
                padding: 10px 8px;
                font-weight: 650;
            }}
            QTableWidget::item {{ padding: 7px; border: none; }}
            QLabel#detailsPanel {{
                background-color: {colors['surface_alt']};
                border: 1px solid {colors['border']};
                border-radius: 9px;
                padding: 10px 12px;
            }}
            QMenuBar, QMenu {{
                background-color: {colors['panel']};
                color: {colors['text']};
            }}
            QMenu::item {{ padding: 6px 24px 6px 10px; }}
            QMenu::item:selected {{
                background-color: {colors['selection']};
                color: {colors['selection_text']};
            }}
            QStatusBar {{
                background-color: {colors['panel']};
                color: {colors['muted']};
                border-top: 1px solid {colors['border']};
            }}
            QCheckBox {{ spacing: 8px; }}
            QScrollBar:vertical {{
                background: {colors['surface_alt']};
                width: 10px;
                margin: 2px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: {colors['border']};
                min-height: 24px;
                border-radius: 5px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """
        application = QApplication.instance()
        if application is not None:
            application.setStyleSheet(stylesheet)
        else:
            self.setStyleSheet(stylesheet)

    def selected_date_text(self) -> str:
        return self.calendar.selectedDate().toString("yyyy-MM-dd")

    def display_time(self, time_text: str) -> str:
        time_value = QTime.fromString(time_text, "HH:mm")
        if not time_value.isValid():
            return time_text
        format_text = "h:mm AP" if self.settings.get("time_format") == "12 часов" else "HH:mm"
        return time_value.toString(format_text)

    def refresh_meetings(self) -> None:
        """Обновляет список встреч для выбранного дня."""
        date = self.calendar.selectedDate()
        self.day_label.setText(f"Встречи на {date.toString('dd.MM.yyyy')}")
        meetings = self.database.get_meetings_for_date(self.selected_date_text())
        self._fill_table(meetings)
        self._refresh_calendar_markers()

    def _fill_table(self, meetings: list[dict]) -> None:
        self.meetings_table.setRowCount(0)
        self.selected_meeting_id = None
        for meeting in meetings:
            row = self.meetings_table.rowCount()
            self.meetings_table.insertRow(row)
            start = self.display_time(meeting["start_time"])
            end = self.display_time(meeting["end_time"])
            values = [
                f"{start} – {end}",
                meeting["title"],
                meeting["place"],
                meeting["description"],
                str(meeting["id"]),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, meeting["id"])
                self.meetings_table.setItem(row, column, item)
        self.details_label.setText("Выберите встречу, чтобы посмотреть подробности.")
        self.statusBar().showMessage(f"Встреч: {len(meetings)}")

    def current_meeting_id(self) -> int | None:
        row = self.meetings_table.currentRow()
        if row < 0:
            return None
        item = self.meetings_table.item(row, 4)
        if item is None:
            return None
        return int(item.text())

    def show_details(self) -> None:
        meeting_id = self.current_meeting_id()
        if meeting_id is None:
            return
        meeting = self.database.get_meeting(meeting_id)
        if not meeting:
            return
        self.selected_meeting_id = meeting_id
        place = meeting.get("place") or "Не указано"
        description = meeting.get("description") or "Нет описания"
        notes = meeting.get("notes") or "Нет заметок"
        self.details_label.setText(
            f"<b>{meeting['title']}</b><br>"
            f"Место: {place}<br>Описание: {description}<br>Заметки: {notes}"
        )

    def add_meeting(self) -> None:
        dialog = MeetingDialog(
            self, time_format=self.settings.get("time_format", "24 часа")
        )
        dialog.date_edit.setDate(self.calendar.selectedDate())
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        data = dialog.get_data()
        if self.database.has_time_conflict(
            data["meeting_date"], data["start_time"], data["end_time"]
        ):
            answer = QMessageBox.question(
                self,
                "Возможное совпадение",
                "На это время уже есть встреча. Всё равно сохранить?",
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.database.add_meeting(data)
        self.calendar.setSelectedDate(QDate.fromString(data["meeting_date"], "yyyy-MM-dd"))
        self.refresh_meetings()
        self.statusBar().showMessage("Встреча добавлена", 4000)

    def edit_meeting(self) -> None:
        meeting_id = self.current_meeting_id()
        if meeting_id is None:
            QMessageBox.information(self, "Изменение", "Сначала выберите встречу.")
            return
        meeting = self.database.get_meeting(meeting_id)
        if not meeting:
            return
        dialog = MeetingDialog(
            self,
            meeting,
            self.settings.get("time_format", "24 часа"),
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        data = dialog.get_data()
        if self.database.has_time_conflict(
            data["meeting_date"], data["start_time"], data["end_time"], meeting_id
        ):
            answer = QMessageBox.question(
                self,
                "Возможное совпадение",
                "На это время уже есть встреча. Всё равно сохранить изменения?",
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.database.update_meeting(meeting_id, data)
        self.calendar.setSelectedDate(QDate.fromString(data["meeting_date"], "yyyy-MM-dd"))
        self.refresh_meetings()
        self.statusBar().showMessage("Изменения сохранены", 4000)

    def delete_meeting(self) -> None:
        meeting_id = self.current_meeting_id()
        if meeting_id is None:
            QMessageBox.information(self, "Удаление", "Сначала выберите встречу.")
            return
        answer = QMessageBox.question(
            self,
            "Удаление встречи",
            "Вы действительно хотите удалить выбранную встречу?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.database.delete_meeting(meeting_id)
        self.refresh_meetings()
        self.statusBar().showMessage("Встреча удалена", 4000)

    def go_to_today(self) -> None:
        self.calendar.setSelectedDate(QDate.currentDate())
        self.calendar.showToday()
        self.search_edit.clear()
        self.refresh_meetings()

    def focus_search(self) -> None:
        self.search_edit.setFocus()
        self.search_edit.selectAll()

    def search_meetings(self, text: str) -> None:
        if not text.strip():
            self.refresh_meetings()
            return
        results = self.database.search_meetings(text)
        self.day_label.setText(f"Результаты поиска: {len(results)}")
        self._fill_table(results)

    def export_calendar(self) -> None:
        """Экспортирует все записи в CSV или TXT."""
        meetings = self.database.get_all_meetings()
        if not meetings:
            QMessageBox.information(self, "Экспорт", "В календаре пока нет встреч.")
            return
        path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Экспорт календаря",
            str(Path.home() / "meetings.csv"),
            "CSV (*.csv);;Текстовый файл (*.txt)",
        )
        if not path:
            return
        if selected_filter.startswith("CSV") and not path.lower().endswith(".csv"):
            path += ".csv"
        elif selected_filter.startswith("Текст") and not path.lower().endswith(".txt"):
            path += ".txt"
        try:
            if path.lower().endswith(".txt"):
                self._export_txt(path, meetings)
            else:
                self._export_csv(path, meetings)
        except OSError as error:
            QMessageBox.critical(self, "Ошибка экспорта", str(error))
            return
        QMessageBox.information(self, "Экспорт", f"Календарь сохранён:\n{path}")

    @staticmethod
    def _export_csv(path: str, meetings: list[dict]) -> None:
        with open(path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file, delimiter=";")
            writer.writerow(
                ["Название", "Дата", "Начало", "Окончание", "Место", "Описание", "Заметки"]
            )
            for meeting in meetings:
                writer.writerow(
                    [
                        meeting["title"],
                        meeting["meeting_date"],
                        meeting["start_time"],
                        meeting["end_time"],
                        meeting["place"],
                        meeting["description"],
                        meeting["notes"],
                    ]
                )

    @staticmethod
    def _export_txt(path: str, meetings: list[dict]) -> None:
        with open(path, "w", encoding="utf-8") as file:
            file.write("MEET TO MEET — СПИСОК ВСТРЕЧ\n")
            file.write("=" * 60 + "\n\n")
            for meeting in meetings:
                file.write(
                    f"{meeting['meeting_date']} | {meeting['start_time']}–"
                    f"{meeting['end_time']} | {meeting['title']}\n"
                )
                file.write(f"Место: {meeting['place'] or 'Не указано'}\n")
                file.write(f"Описание: {meeting['description'] or 'Нет описания'}\n")
                if meeting["notes"]:
                    file.write(f"Заметки: {meeting['notes']}\n")
                file.write("-" * 60 + "\n")

    def open_settings(self) -> None:
        dialog = SettingsDialog(self, self.settings)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        new_settings = dialog.get_settings()
        if self._validate_shortcuts(new_settings):
            return
        self.database.save_settings(new_settings)
        self.settings = self.database.get_settings()
        self.notification_manager.update_settings(self.settings)
        self.update_shortcuts()
        self._apply_theme()
        self.refresh_meetings()
        QMessageBox.information(self, "Настройки", "Настройки сохранены.")

    def _validate_shortcuts(self, settings: dict[str, str]) -> bool:
        """Проверяет, что сочетания корректны и не повторяются."""
        used: dict[str, str] = {}
        for key, value in settings.items():
            if not key.startswith("shortcut_") or not value:
                continue
            sequence = QKeySequence(value)
            if sequence.isEmpty():
                QMessageBox.warning(self, "Горячие клавиши", f"Некорректное сочетание: {value}")
                return True
            normalized = sequence.toString()
            if normalized in used:
                QMessageBox.warning(
                    self,
                    "Горячие клавиши",
                    f"Сочетание {normalized} используется дважды.",
                )
                return True
            used[normalized] = key
        return False


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

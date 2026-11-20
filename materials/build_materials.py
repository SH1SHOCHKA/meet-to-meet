from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_BREAK
from docx.enum.table import WD_ROW_HEIGHT_RULE
from pathlib import Path

OUT = Path(__file__).resolve().parent / 'Meet_to_meet_guide_for_defense.docx'
NAVY = '17253E'
BLUE = '24466A'
ORANGE = 'F97316'
PALE = 'F3F6FA'
PALE_ORANGE = 'FFF2E8'
LIGHT_BLUE = 'EAF1F8'
TEXT = '243247'
MUTED = '66758A'
BORDER = 'D9E1EA'
WHITE = 'FFFFFF'
GREEN = '247A55'


def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = tcPr.find(qn('w:shd'))
    if shd is None:
        shd = OxmlElement('w:shd')
        tcPr.append(shd)
    shd.set(qn('w:fill'), fill)


def set_cell_border(cell, **kwargs):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    borders = tcPr.first_child_found_in('w:tcBorders')
    if borders is None:
        borders = OxmlElement('w:tcBorders')
        tcPr.append(borders)
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        if edge in kwargs:
            tag = 'w:{}'.format(edge)
            element = borders.find(qn(tag))
            if element is None:
                element = OxmlElement(tag)
                borders.append(element)
            for key in ['val', 'sz', 'space', 'color']:
                if key in kwargs[edge]:
                    element.set(qn('w:{}'.format(key)), str(kwargs[edge][key]))


def set_cell_margins(cell, top=90, start=110, bottom=90, end=110):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcMar = tcPr.first_child_found_in('w:tcMar')
    if tcMar is None:
        tcMar = OxmlElement('w:tcMar')
        tcPr.append(tcMar)
    for m, v in [('top', top), ('start', start), ('bottom', bottom), ('end', end)]:
        node = tcMar.find(qn('w:' + m))
        if node is None:
            node = OxmlElement('w:' + m)
            tcMar.append(node)
        node.set(qn('w:w'), str(v))
        node.set(qn('w:type'), 'dxa')


def set_repeat_table_header(row):
    trPr = row._tr.get_or_add_trPr()
    tblHeader = OxmlElement('w:tblHeader')
    tblHeader.set(qn('w:val'), 'true')
    trPr.append(tblHeader)


def prevent_row_split(row):
    trPr = row._tr.get_or_add_trPr()
    cant = OxmlElement('w:cantSplit')
    trPr.append(cant)


def set_run_font(run, name='Arial', size=10.5, color=TEXT, bold=None, italic=None):
    run.font.name = name
    run._element.rPr.rFonts.set(qn('w:eastAsia'), name)
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor.from_string(color)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    return run


def add_text(p, text, bold=False, italic=False, color=TEXT, size=10.5):
    return set_run_font(p.add_run(text), size=size, color=color, bold=bold, italic=italic)


def set_keep(p, keep_next=False, keep_lines=False):
    p.paragraph_format.keep_with_next = keep_next
    p.paragraph_format.keep_together = keep_lines


def add_p(doc, text='', style=None, before=0, after=5, line=1.12, color=TEXT,
          bold_prefix=None, italic=False, align=None, keep=False):
    p = doc.add_paragraph(style=style)
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = line
    if align is not None:
        p.alignment = align
    if bold_prefix and text.startswith(bold_prefix):
        add_text(p, bold_prefix, bold=True, color=color)
        add_text(p, text[len(bold_prefix):], italic=italic, color=color)
    else:
        add_text(p, text, italic=italic, color=color)
    if keep:
        set_keep(p, keep_lines=True)
    return p


def heading(doc, text, level=1):
    p = doc.add_paragraph(style=f'Heading {level}')
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(11 if level == 1 else 7)
    p.paragraph_format.space_after = Pt(5)
    add_text(p, text, bold=True,
             color=NAVY if level == 1 else BLUE,
             size=16 if level == 1 else 12.5 if level == 2 else 11)
    return p


def bullet(doc, text, level=0, bold_prefix=None):
    style = 'List Bullet' if level == 0 else 'List Bullet 2'
    p = doc.add_paragraph(style=style)
    p.paragraph_format.space_after = Pt(2.5)
    p.paragraph_format.line_spacing = 1.08
    if bold_prefix and text.startswith(bold_prefix):
        add_text(p, bold_prefix, bold=True)
        add_text(p, text[len(bold_prefix):])
    else:
        add_text(p, text)
    return p


_numbered_counter = 0

def reset_numbered():
    global _numbered_counter
    _numbered_counter = 0

def numbered(doc, text):
    global _numbered_counter
    _numbered_counter += 1
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.48)
    p.paragraph_format.first_line_indent = Cm(-0.48)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.08
    add_text(p, f'{_numbered_counter}. ', bold=True, color=ORANGE)
    add_text(p, text)
    return p


def callout(doc, title, body, fill=PALE_ORANGE, accent=ORANGE):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    cell = table.cell(0, 0)
    shade(cell, fill)
    set_cell_margins(cell, top=140, start=180, bottom=140, end=180)
    set_cell_border(cell,
                    left={'val':'single','sz':'20','color':accent},
                    top={'val':'nil'}, bottom={'val':'nil'}, right={'val':'nil'})
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(4)
    add_text(p, title, bold=True, color=NAVY, size=10.5)
    p2 = cell.add_paragraph()
    p2.paragraph_format.space_after = Pt(0)
    p2.paragraph_format.line_spacing = 1.08
    add_text(p2, body, color=TEXT, size=9.8)
    return table


def table(doc, headers, rows, widths=None, font_size=9.1):
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False if widths else True
    t.style = 'Table Grid'
    hdr = t.rows[0]
    set_repeat_table_header(hdr)
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        shade(cell, NAVY)
        set_cell_margins(cell, top=100, start=110, bottom=100, end=110)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        if widths:
            cell.width = Cm(widths[i])
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        add_text(p, h, bold=True, color=WHITE, size=font_size)
    for ridx, row in enumerate(rows):
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cell = cells[i]
            if ridx % 2 == 1:
                shade(cell, 'F5F7FA')
            set_cell_margins(cell, top=80, start=105, bottom=80, end=105)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if widths:
                cell.width = Cm(widths[i])
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.04
            add_text(p, str(val), size=font_size)
        prevent_row_split(t.rows[-1])
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return t


def codebox(doc, code):
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = t.cell(0,0)
    shade(cell, 'F1F4F8')
    set_cell_margins(cell, top=120, start=160, bottom=120, end=160)
    set_cell_border(cell,
                    left={'val':'single','sz':'12','color':BLUE},
                    top={'val':'single','sz':'4','color':BORDER},
                    bottom={'val':'single','sz':'4','color':BORDER},
                    right={'val':'single','sz':'4','color':BORDER})
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run(code)
    r.font.name = 'Consolas'
    r._element.rPr.rFonts.set(qn('w:eastAsia'), 'Consolas')
    r.font.size = Pt(8.7)
    r.font.color.rgb = RGBColor.from_string('26364A')
    doc.add_paragraph().paragraph_format.space_after = Pt(1)


_page_break_count = 0

def page_break(doc):
    global _page_break_count
    _page_break_count += 1
    # Keep the cover separate; let the remaining chapters flow naturally
    # so a short spillover does not create an almost empty page.
    if _page_break_count == 1:
        doc.add_page_break()


def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = paragraph.add_run('Стр. ')
    set_run_font(r, size=8, color=MUTED)
    fldChar1 = OxmlElement('w:fldChar')
    fldChar1.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = ' PAGE '
    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'end')
    r2 = paragraph.add_run()
    r2._r.append(fldChar1)
    r2._r.append(instrText)
    r2._r.append(fldChar2)
    set_run_font(r2, size=8, color=MUTED)


doc = Document()
sec = doc.sections[0]
sec.page_width = Cm(21.0)
sec.page_height = Cm(29.7)
sec.top_margin = Cm(1.75)
sec.bottom_margin = Cm(1.65)
sec.left_margin = Cm(1.9)
sec.right_margin = Cm(1.8)
sec.header_distance = Cm(0.75)
sec.footer_distance = Cm(0.75)

# Default and heading styles
styles = doc.styles
normal = styles['Normal']
normal.font.name = 'Arial'
normal._element.rPr.rFonts.set(qn('w:eastAsia'), 'Arial')
normal.font.size = Pt(10.5)
normal.font.color.rgb = RGBColor.from_string(TEXT)
normal.paragraph_format.space_after = Pt(5)
normal.paragraph_format.line_spacing = 1.12
for stylename, size, col in [('Heading 1',16,NAVY),('Heading 2',12.5,BLUE),('Heading 3',11,ORANGE)]:
    st = styles[stylename]
    st.font.name = 'Arial'
    st._element.rPr.rFonts.set(qn('w:eastAsia'), 'Arial')
    st.font.size = Pt(size)
    st.font.bold = True
    st.font.color.rgb = RGBColor.from_string(col)
    st.paragraph_format.keep_with_next = True

# Header and footer
header = sec.header.paragraphs[0]
header.alignment = WD_ALIGN_PARAGRAPH.LEFT
add_text(header, 'MEET TO MEET', bold=True, color=NAVY, size=8.5)
add_text(header, '   |   ПАМЯТКА К ЗАЩИТЕ ПРОЕКТА', color=MUTED, size=8)
footer = sec.footer.paragraphs[0]
add_page_number(footer)

# Cover
p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(95)
p.paragraph_format.space_after = Pt(10)
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_text(p, 'MEET TO MEET', bold=True, color=NAVY, size=30)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(22)
add_text(p, 'Руководство для защиты учебного проекта', color=ORANGE, size=16, bold=True)

callout(doc, 'Для чего этот документ',
        'Здесь собраны готовый текст выступления, понятное объяснение архитектуры, интерфейса, всех основных функций, базы данных SQLite, уведомлений и тестов, а также ответы на вопросы преподавателя.',
        fill=LIGHT_BLUE, accent=BLUE)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(35)
add_text(p, 'Автор проекта', color=MUTED, size=10)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(5)
add_text(p, 'Саша Шишкин', bold=True, color=NAVY, size=19)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(65)
add_text(p, 'Python  •  PyQt6  •  SQLite', color=MUTED, size=11)
add_p(doc, 'Версия документа соответствует структуре репозитория на GitHub на 20 ноября 2026 года.',
      before=18, align=WD_ALIGN_PARAGRAPH.CENTER, color=MUTED)

page_break(doc)

heading(doc, 'Как пользоваться руководством', 1)
add_p(doc, 'Документ состоит из трёх частей. Первая — готовая речь, которую можно рассказывать во время презентации. Вторая — подробное техническое объяснение: что находится в каждом файле, откуда берутся данные и как проходит выполнение операций. Третья — ответы на вероятные вопросы преподавателя.')
callout(doc, 'Как лучше готовиться',
        'Сначала прочитай речь целиком, затем разберись с разделами про Database, MainWindow и NotificationManager. Перед защитой отдельно повтори схему прохождения данных: форма → MainWindow → Database → SQLite → обновление интерфейса.',
        fill=PALE_ORANGE)
heading(doc, 'Маршрут по документу', 2)
table(doc, ['Раздел', 'Что в нём'], [
    ('1. Готовая речь', 'Текст выступления по логическим частям презентации.'),
    ('2. Структура проекта', 'Файлы, классы и обязанности каждого компонента.'),
    ('3. Интерфейс и события', 'Календарь, таблица, формы, кнопки, сигналы Qt.'),
    ('4. База данных SQLite', 'Расположение, перенос старой базы, таблицы, поля, SQL и методы.'),
    ('5. Алгоритмы функций', 'Создание, изменение, удаление, пересечения, поиск, экспорт.'),
    ('6. Уведомления и настройки', 'QTimer, QSystemTrayIcon, параметры и горячие клавиши.'),
    ('7. Технологии и тесты', 'Стек разработки, проверки и ограничения текущей версии.'),
    ('8. Вопросы преподавателя', 'Готовые ответы и короткая памятка перед выступлением.'),
], widths=[4.2,12.4])

heading(doc, 'Самая короткая схема архитектуры', 2)
codebox(doc, 'Пользователь\n    ↓\nMainWindow (main.py)  ←→  MeetingDialog / SettingsDialog\n    ↓                         ↓\nDatabase (database.py)   NotificationManager (notifications.py)\n    ↓                         ↑\nSQLite: meetings, settings   QTimer → системный трей Qt')
add_p(doc, 'Главное: MainWindow управляет пользовательскими действиями, Database отвечает за сохранение информации, а NotificationManager периодически проверяет расписание и показывает напоминания.')

page_break(doc)
heading(doc, 'Часть 1. Готовый текст выступления', 1)
add_p(doc, 'Ниже речь, которую можно использовать вместе со слайдами. Не обязательно читать дословно: лучше пересказывать своими словами, сохраняя порядок и смысл.', color=MUTED, italic=True)

heading(doc, 'Титульный слайд', 2)
add_p(doc, '«Здравствуйте! Я представляю учебный проект Meet to meet. Это настольное приложение для планирования встреч, созвонов и онлайн-конференций. Автор проекта — Саша Шишкин. Приложение позволяет хранить расписание в одном месте: создавать встречи, редактировать их, искать нужные записи, экспортировать календарь и получать напоминания. Для разработки я использовал Python, PyQt6 для графического интерфейса и SQLite для хранения данных.»', italic=True)

heading(doc, 'Введение: идея и задача проекта', 2)
add_p(doc, '«Проблема, которую решает проект, заключается в том, что информация о встречах часто разбросана по разным приложениям и перепискам. Можно забыть время, потерять ссылку на созвон или назначить две встречи на один интервал. Я решил объединить основные действия с расписанием в одной программе. Пользователь выбирает дату, добавляет событие, указывает время, место или ссылку, описание и заметки. Данные сохраняются локально на компьютере, поэтому для основной работы не нужен отдельный сервер.»', italic=True)

heading(doc, 'Основные возможности', 2)
add_p(doc, '«В программе есть календарь с выбором даты и список встреч на выбранный день. Можно добавить, посмотреть, изменить или удалить запись. Для каждой встречи хранятся название, дата, время начала и окончания, место, описание и заметки. Программа проверяет корректность времени и предупреждает о пересечении с другими встречами. Есть поиск по названию, месту и описанию, экспорт всего календаря в CSV или TXT, системные уведомления, настройки темы и формата времени, а также горячие клавиши.»', italic=True)

heading(doc, 'Как работает создание встречи', 2)
add_p(doc, '«При создании встречи открывается MeetingDialog. Пользователь заполняет поля формы. Метод get_data собирает их в словарь Python. Метод accept проверяет, что название не пустое, а время окончания позже времени начала. После подтверждения MainWindow получает словарь, вызывает Database.has_time_conflict и проверяет пересечения в выбранную дату. Если конфликт найден, появляется предупреждение: можно отменить сохранение или подтвердить его. Затем вызывается Database.add_meeting, запись сохраняется в SQLite, после чего календарь и таблица обновляются.»', italic=True)

heading(doc, 'Архитектура и устройство кода', 2)
add_p(doc, '«Я разделил приложение на отдельные модули. В main.py расположены интерфейс и основная логика: классы MainWindow, MeetingDialog и SettingsDialog. В database.py находится класс Database, который выполняет SQL-запросы и управляет таблицами. В notifications.py расположен NotificationManager, который проверяет ближайшие встречи и отвечает за системные сообщения. Такое разделение нужно, чтобы интерфейс, хранение данных и уведомления не были смешаны в одном большом блоке кода.»', italic=True)

heading(doc, 'База данных', 2)
add_p(doc, '«Для хранения данных используется SQLite. Это встраиваемая реляционная база данных: она хранится в файле meet_to_meet.db и не требует отдельного сервера MySQL. Файл создаётся рядом с исходными файлами проекта. В таблице meetings находятся записи календаря, а в settings — настройки приложения. У каждой встречи есть уникальный ID. Даты хранятся в формате год-месяц-день, а время — в формате часы:минуты. Это позволяет удобно сортировать записи по дате и времени.»', italic=True)

heading(doc, 'Поиск, экспорт и настройки', 2)
add_p(doc, '«Поиск запускается при изменении текста в поле ввода. MainWindow вызывает Database.search_meetings, а SQL-запрос ищет совпадения в названии, месте и описании. Экспорт сначала получает все записи из базы, а затем сохраняет их в выбранный файл: CSV записывается через модуль csv с разделителем точка с запятой, TXT — обычным текстом. В настройках пользователь выбирает светлую или тёмную тему, формат времени, интервал напоминания, включает или отключает уведомления и меняет горячие клавиши. Настройки сохраняются в SQLite и применяются после повторного запуска.»', italic=True)

heading(doc, 'Уведомления', 2)
add_p(doc, '«За уведомления отвечает NotificationManager. Он использует QTimer, который запускает проверку раз в 30 секунд. Компонент получает текущее время, добавляет заданный интервал напоминания, запрашивает подходящие встречи в Database и проверяет, не наступило ли время уведомить пользователя. Если системный трей доступен, сообщение выводится через QSystemTrayIcon. Идентификаторы уже обработанных встреч сохраняются в наборе sent_ids, чтобы одно и то же напоминание не повторялось в рамках текущего запуска.»', italic=True)

heading(doc, 'Технологии, тестирование и заключение', 2)
add_p(doc, '«Основной язык — Python. Для окон, календаря, таблиц, кнопок и сигналов использован PyQt6. Для хранения данных используется SQLite через модуль sqlite3, который входит в стандартную библиотеку Python. Для экспорта используются csv и pathlib, для уведомлений — QTimer и QSystemTrayIcon, для тестов — unittest. Тесты проверяют добавление и чтение встречи, изменение, удаление, пересечение интервалов, сохранение настроек, расположение базы и перенос старого файла базы. В дальнейшем можно добавить повторяющиеся встречи, резервное копирование и синхронизацию между устройствами. Спасибо за внимание!»', italic=True)

page_break(doc)
heading(doc, 'Часть 2. Структура проекта и роли компонентов', 1)
heading(doc, 'Файлы проекта', 2)
table(doc, ['Файл', 'Назначение', 'Что важно объяснить'], [
    ('main.py', 'Главное окно, диалоги, обработчики действий, поиск, экспорт, тема.', 'Здесь находится пользовательская логика, но SQL-запросы вынесены в Database.'),
    ('database.py', 'Класс Database и весь доступ к SQLite.', 'Один слой отвечает за создание таблиц, чтение, запись и настройки.'),
    ('notifications.py', 'Класс NotificationManager.', 'QTimer проверяет расписание, QSystemTrayIcon выводит сообщение.'),
    ('tests/test_database.py', 'Автоматические тесты слоя данных.', 'Каждый тест работает с временной БД, а не с основной базой пользователя.'),
    ('requirements.txt', 'Список внешних зависимостей.', 'В проекте указан PyQt6; sqlite3, csv, pathlib, unittest входят в Python.'),
    ('run.bat', 'Установка зависимости и запуск на Windows.', 'Сначала pip install -r requirements.txt, затем python main.py.'),
    ('README.md', 'Описание, установка, запуск и пояснение хранения данных.', 'Это инструкция для пользователя или проверяющего.'),
    ('.gitignore', 'Исключает временные файлы и локальные базы из Git.', 'Файлы .db, -wal и -shm не должны попадать в репозиторий.'),
], widths=[3.2,6.0,7.4], font_size=8.7)

heading(doc, 'Классы и их ответственность', 2)
table(doc, ['Класс', 'Роль', 'Типичные методы / обязанности'], [
    ('MeetingDialog', 'Форма создания или изменения встречи.', '_build_ui, _fill_values, get_data, accept.'),
    ('SettingsDialog', 'Форма параметров приложения.', '_build_ui, _fill_values, get_settings.'),
    ('MainWindow', 'Центральный координатор интерфейса.', 'Показывает календарь, получает данные форм, вызывает Database и обновляет экран.'),
    ('Database', 'Слой доступа к данным.', 'initialize, add_meeting, update_meeting, delete_meeting, search_meetings, get_settings.'),
    ('NotificationManager', 'Планировщик напоминаний внутри приложения.', 'Инициализирует QTimer, проверяет встречи и отображает системные сообщения.'),
], widths=[3.3,5.0,8.3], font_size=8.8)
callout(doc, 'Важный честный ответ',
        'В этой версии проекта нет отдельного класса Meeting. Сама встреча передаётся между формой, главным окном и базой как словарь Python с полями title, meeting_date, start_time, end_time, place, description и notes. Не нужно говорить преподавателю, что класс Meeting существует.',
        fill=PALE_ORANGE)

heading(doc, 'Как запускается программа', 2)
reset_numbered()
numbered(doc, 'Функция main создаёт QApplication(sys.argv). Это объект приложения Qt, который запускает обработку событий интерфейса.')
numbered(doc, 'Создаётся MainWindow. В его конструкторе создаётся Database, поэтому база при необходимости появляется и выполняется инициализация таблиц.')
numbered(doc, 'Из базы считываются пользовательские настройки.')
numbered(doc, 'Создаются элементы интерфейса и действия меню, назначаются сигналы и горячие клавиши.')
numbered(doc, 'Создаётся NotificationManager, которому передаётся тот же объект Database. Запускается таймер проверки встреч.')
numbered(doc, 'Применяется тема, загружаются встречи выбранной даты, отображается главное окно.')
numbered(doc, 'В конце main вызывается app.exec(). Это цикл событий Qt: он позволяет обрабатывать нажатия, сигналы, перерисовку и срабатывания QTimer.')

heading(doc, 'Почему используется разделение ответственности', 2)
add_p(doc, 'MainWindow знает, когда пользователь нажал кнопку, но не должен собирать SQL вручную. Он вызывает метод Database. Database не знает, как выглядит таблица или кнопка, — он только возвращает данные. NotificationManager тоже не меняет интерфейс календаря: он получает расписание и показывает системные сообщения. Такое разделение упрощает проверку и дальнейшее развитие кода.')

page_break(doc)
heading(doc, 'Часть 3. Интерфейс: что показать и как объяснить', 1)
heading(doc, 'Главное окно MainWindow', 2)
table(doc, ['Область интерфейса', 'Что видит пользователь', 'Как это связано с кодом'], [
    ('Верхняя строка', 'Название, кнопки «Новая встреча», «Изменить», «Удалить», «Экспорт», «Настройки».', 'Кнопки подключены к методам MainWindow через clicked.connect(...).'),
    ('Панель календаря', 'Месяц, стрелки назад/вперёд, кнопка «Сегодня», сетка календаря.', 'QCalendarWidget; currentPageChanged обновляет заголовок месяца, selectionChanged обновляет встречи.'),
    ('Поиск', 'Поле поиска и кнопка сброса.', 'textChanged вызывает search_meetings; clear очищает текст и возвращает список выбранного дня.'),
    ('Таблица', 'Время, название, место, описание, скрытая колонка ID.', 'QTableWidget заполняется методом _fill_table; ID хранится в строке для последующего выбора записи.'),
    ('Панель подробностей', 'Полное название, место, описание и заметки выбранной встречи.', 'itemSelectionChanged вызывает show_details; по ID запись повторно читается из базы.'),
    ('Меню и статусная строка', 'Меню «Файл», «Встречи», «Вид» и короткие сообщения о результате действий.', 'QAction вызывает методы окна; statusBar().showMessage показывает состояние.'),
], widths=[3.0,6.0,7.6], font_size=8.5)

heading(doc, 'Календарь и навигация', 2)
add_p(doc, 'Календарь построен на QCalendarWidget. Встроенная панель навигации скрыта через setNavigationBarVisible(False), потому что у календаря сделана собственная строка: две отдельные кнопки одинакового размера и центральная подпись месяца. Нажатие на стрелки вызывает showPreviousMonth или showNextMonth. Сигнал currentPageChanged передаёт год и месяц в _update_month_label, который формирует название месяца с помощью QLocale("ru_RU").')
add_p(doc, 'Первым днём недели установлен понедельник. Вертикальная нумерация недель отключена. При обновлении списка встреч метод _refresh_calendar_markers получает все встречи и подсвечивает даты, для которых есть записи. Перед повторной подсветкой старые форматы снимаются, чтобы маркеры не оставались на датах после удаления встреч.')

heading(doc, 'Таблица и выбор записи', 2)
add_p(doc, 'Таблица QTableWidget содержит пять колонок: время, название, место, описание и ID. Последняя колонка скрыта для пользователя, но нужна программе. В ней хранится идентификатор записи. Из таблицы нельзя редактировать текст напрямую: изменения выполняются через MeetingDialog. Так программа контролирует проверку данных и запись в БД. Таблица поддерживает выбор одной строки, двойное нажатие запускает редактирование.')

heading(doc, 'Окно MeetingDialog', 2)
add_p(doc, 'В форме встречи есть QLineEdit для названия, места и описания; QDateEdit для даты; QTimeEdit для начала и окончания; QPlainTextEdit для заметок. При редактировании _fill_values заполняет поля значениями существующей встречи. При создании дата изначально берётся из выбранной ячейки календаря. get_data возвращает словарь, а accept проверяет, что название непустое и конец позже начала. Формат отображения времени может быть 12- или 24-часовым, но get_data всё равно сохраняет нормализованное время в формате HH:mm.')

heading(doc, 'Окно SettingsDialog', 2)
add_p(doc, 'Форма настроек содержит выпадающий список темы, формат отображения времени, интервал напоминания от 0 до 1440 минут, переключатель уведомлений и шесть полей горячих клавиш. get_settings собирает настройки в словарь строк. После нажатия «Сохранить» MainWindow проверяет комбинации методом _validate_shortcuts: QKeySequence должна распознаваться, а одинаковые нормализованные комбинации не должны повторяться. Затем параметры записываются в SQLite и применяются к окну.')

heading(doc, 'Сигналы и слоты Qt', 2)
add_p(doc, 'В PyQt6 сигнал — это событие от элемента интерфейса, а слот — метод, который вызывается в ответ. Например, add_button.clicked.connect(self.add_meeting) означает: когда нажата кнопка, вызвать add_meeting. У календаря selectionChanged связан с refresh_meetings. У строки поиска textChanged связан с search_meetings. У таблицы itemSelectionChanged связан с show_details. Это событийная модель: приложение реагирует на действия пользователя, а не выполняет линейный набор команд один раз.')

page_break(doc)
heading(doc, 'Часть 4. База данных SQLite — подробно', 1)
heading(doc, 'Что такое SQLite и почему она выбрана', 2)
add_p(doc, 'SQLite — реляционная СУБД, работающая непосредственно с файлом. Отдельный процесс сервера не нужен: приложение открывает файл базы через стандартный модуль Python sqlite3. Для небольшого локального планировщика одного пользователя это упрощает установку и перенос. SQLite поддерживает таблицы, первичные ключи, SQL-запросы, индексы и транзакции.')
callout(doc, 'Важно различать',
        'SQLite — не «SQLite Server». Для открытия файла используется программа просмотра, например DB Browser for SQLite или SQLiteStudio. Само приложение подключается к файлу через sqlite3.',
        fill=LIGHT_BLUE, accent=BLUE)

heading(doc, 'Где находится файл базы данных', 2)
codebox(doc, 'meet_to_meet/\n├── main.py\n├── database.py\n├── notifications.py\n├── meet_to_meet.db   ← файл базы появляется здесь\n└── README.md')
add_p(doc, 'Путь в коде задаётся методом Database.default_db_path():')
codebox(doc, 'return Path(__file__).resolve().parent / "meet_to_meet.db"')
add_p(doc, 'Path(__file__).resolve() определяет абсолютный путь к самому файлу database.py, а parent берёт его родительскую папку. Поэтому база создаётся рядом с исходным кодом Database, а не зависит от того, из какой текущей директории пользователь вызвал команду запуска.')

heading(doc, 'Перенос старой базы', 2)
add_p(doc, 'В предыдущей версии база хранилась по пути Path.home() / ".meet_to_meet" / "meet_to_meet.db". Метод _migrate_legacy_database проверяет этот путь. Если новая база ещё не существует и старый файл найден, shutil.copy2 копирует его в папку проекта. Старый файл не удаляется. Если база в папке проекта уже есть, копирование не выполняется, поэтому существующая рабочая база не перезаписывается.')
add_p(doc, 'Если пользователь передаёт Database собственный параметр db_path, тесты могут создавать временную базу в отдельной папке. В таком режиме стандартная миграция не запускается. Это удобно для изолированного тестирования.')

heading(doc, 'Как открывается соединение: метод connect', 2)
reset_numbered()
numbered(doc, 'sqlite3.connect(self.db_path) открывает соединение с файлом SQLite. Если файла ещё нет, SQLite создаёт его.')
numbered(doc, 'connection.row_factory = sqlite3.Row позволяет обращаться к колонкам по имени: row["title"], а не только по числовому индексу.')
numbered(doc, 'PRAGMA foreign_keys = ON включает поддержку проверки внешних ключей в SQLite. В текущей схеме явные связи FOREIGN KEY не объявлены, поэтому это настройка на будущее и безопасное поведение соединения.')
numbered(doc, 'Контекстный менеджер передаёт соединение вызывающему коду. Если операция закончилась без исключения, выполняется commit. Если возникла ошибка, выполняется rollback. В блоке finally соединение закрывается.')
callout(doc, 'Что сказать преподавателю',
        'Транзакция — это группа операций, которые фиксируются вместе. commit подтверждает изменения, rollback отменяет незавершённые изменения при ошибке. Контекстный менеджер в connect гарантирует закрытие соединения.',
        fill=PALE_ORANGE)

heading(doc, 'Таблица meetings: поля и назначение', 2)
table(doc, ['Поле', 'Тип / ограничение', 'Значение'], [
    ('id', 'INTEGER PRIMARY KEY AUTOINCREMENT', 'Уникальный автоматически растущий ID встречи.'),
    ('title', 'TEXT NOT NULL', 'Обязательное название.'),
    ('meeting_date', 'TEXT NOT NULL', 'Дата в формате yyyy-MM-dd, например 2026-11-20.'),
    ('start_time', 'TEXT NOT NULL', 'Время начала в формате HH:mm.'),
    ('end_time', 'TEXT NOT NULL', 'Время окончания в формате HH:mm.'),
    ('place', 'TEXT DEFAULT \'\'', 'Место, сервис или ссылка; по умолчанию пустая строка.'),
    ('description', 'TEXT DEFAULT \'\'', 'Краткое описание цели встречи.'),
    ('notes', 'TEXT DEFAULT \'\'', 'Дополнительные заметки.'),
    ('created_at', 'TEXT DEFAULT CURRENT_TIMESTAMP', 'Дата и время создания записи.'),
    ('updated_at', 'TEXT DEFAULT CURRENT_TIMESTAMP', 'Дата и время последнего изменения; обновляется при UPDATE.'),
], widths=[3.0,5.2,8.4], font_size=8.6)

heading(doc, 'Таблица settings и настройки по умолчанию', 2)
add_p(doc, 'Настройки хранятся в таблице ключ-значение. setting_key — первичный ключ, setting_value — текстовое значение. В DEFAULT_SETTINGS предусмотрены: тема «Светлая», формат «24 часа», шесть горячих клавиш, интервал напоминания 10 минут и включённые уведомления. Цифровые параметры тоже сохраняются строками, а при использовании преобразуются в нужный тип.')
table(doc, ['Ключ', 'Значение по умолчанию', 'Назначение'], [
    ('theme', 'Светлая', 'Вариант оформления: Светлая или Тёмная.'),
    ('time_format', '24 часа', 'Формат показа времени в окнах и таблице.'),
    ('shortcut_add / edit / delete', 'Ctrl+N / Ctrl+E / Delete', 'Добавление, изменение и удаление.'),
    ('shortcut_today / export / search', 'Ctrl+T / Ctrl+Shift+E / Ctrl+F', 'Сегодня, экспорт и поиск.'),
    ('reminder_minutes', '10', 'За сколько минут до встречи напоминать.'),
    ('notifications_enabled', '1', '1 — уведомления включены; 0 — отключены.'),
], widths=[4.5,4.5,7.6], font_size=8.5)

heading(doc, 'Индекс', 2)
codebox(doc, 'CREATE INDEX IF NOT EXISTS idx_meetings_date\nON meetings(meeting_date, start_time);')
add_p(doc, 'Индекс строится по дате и времени начала. Он помогает ускорять операции, где нужно искать и упорядочивать встречи по этим колонкам. Индекс не содержит копию всех данных встречи и не заменяет таблицу: он является дополнительной структурой для поиска.')

page_break(doc)
heading(doc, 'Часть 5. SQL и методы Database', 1)
heading(doc, 'Добавление встречи — INSERT', 2)
add_p(doc, 'Метод add_meeting получает словарь и передаёт значения в INSERT. Поля title, meeting_date, start_time, end_time, place, description и notes записываются в одну строку таблицы. Значения передаются отдельно от SQL-текста через заполнители ?, что уменьшает риск SQL-инъекций. Метод возвращает cursor.lastrowid — ID только что добавленной записи.')
codebox(doc, 'INSERT INTO meetings\n(title, meeting_date, start_time, end_time, place, description, notes)\nVALUES (?, ?, ?, ?, ?, ?, ?);')

heading(doc, 'Изменение встречи — UPDATE', 2)
add_p(doc, 'Метод update_meeting обновляет семь основных полей существующей встречи. В WHERE id = ? выбирается нужная запись по уникальному идентификатору. Дополнительно updated_at устанавливается в CURRENT_TIMESTAMP. При редактировании сама запись не создаётся заново и её ID сохраняется.')
codebox(doc, 'UPDATE meetings SET title = ?, meeting_date = ?, start_time = ?,\n    end_time = ?, place = ?, description = ?, notes = ?,\n    updated_at = CURRENT_TIMESTAMP\nWHERE id = ?;')

heading(doc, 'Удаление — DELETE', 2)
add_p(doc, 'delete_meeting удаляет строку с выбранным ID. Перед вызовом SQL интерфейс показывает диалог подтверждения, чтобы пользователь не удалил встречу случайно. После удаления MainWindow обновляет таблицу.')
codebox(doc, 'DELETE FROM meetings WHERE id = ?;')

heading(doc, 'Чтение — SELECT', 2)
table(doc, ['Метод', 'Запрос / фильтр', 'Где используется'], [
    ('get_meeting', 'WHERE id = ?', 'Открытие выбранной записи для подробностей или редактирования.'),
    ('get_meetings_for_date', 'WHERE meeting_date = ?', 'Загрузка встреч выбранного дня.'),
    ('get_all_meetings', 'Все записи, сортировка по дате и времени.', 'Подсветка дат и экспорт.'),
    ('get_meetings_between', 'BETWEEN start_date AND end_date.', 'Получение календарного диапазона.'),
    ('get_upcoming_meetings', 'Дата + время начала не позже указанного момента; LIMIT 50.', 'Получение кандидатов для проверки напоминаний.'),
], widths=[4.0,6.3,6.3], font_size=8.5)

heading(doc, 'Поиск — LIKE', 2)
add_p(doc, 'search_meetings формирует шаблон вида %текст%. Процент означает любое количество любых символов до или после введённого текста. SQL проверяет title, place или description. Заметки в текущей реализации в поиск не включены. Результаты сортируются по дате и времени.')
codebox(doc, 'SELECT * FROM meetings\nWHERE title LIKE ? OR place LIKE ? OR description LIKE ?\nORDER BY meeting_date, start_time;')

heading(doc, 'Настройки — INSERT ... ON CONFLICT', 2)
add_p(doc, 'save_settings использует executemany, чтобы сохранить сразу несколько пар «ключ — значение». Если ключа ещё нет, INSERT создаёт строку. Если setting_key уже существует, срабатывает ON CONFLICT и выполняется DO UPDATE. Это называется upsert: вставка новой записи или обновление существующей.')
codebox(doc, 'INSERT INTO settings(setting_key, setting_value) VALUES (?, ?)\nON CONFLICT(setting_key)\nDO UPDATE SET setting_value = excluded.setting_value;')

heading(doc, 'Подготовка значений и словари', 2)
add_p(doc, '_meeting_values централизованно собирает поля словаря в кортеж в правильном порядке и очищает пробелы в текстовых полях. Строки, возвращённые sqlite3.Row, преобразуются в обычные словари через dict(row). Это упрощает обмен между базой и интерфейсом.')

page_break(doc)
heading(doc, 'Часть 6. Как работают ключевые пользовательские сценарии', 1)
heading(doc, '1. Добавление встречи', 2)
reset_numbered()
numbered(doc, 'Пользователь выбирает дату и нажимает «Новая встреча» или сочетание Ctrl+N.')
numbered(doc, 'MainWindow создаёт MeetingDialog и передаёт выбранный формат времени. В поле даты подставляется выбранный день календаря.')
numbered(doc, 'Пользователь заполняет поля и нажимает «Сохранить».')
numbered(doc, 'MeetingDialog.accept проверяет обязательное название и сравнивает QTime начала и окончания.')
numbered(doc, 'get_data возвращает словарь со строками. Дата нормализована до yyyy-MM-dd, время — до HH:mm.')
numbered(doc, 'MainWindow вызывает Database.has_time_conflict. Если конфликт найден, показывает предупреждение и спрашивает подтверждение.')
numbered(doc, 'Если пользователь подтверждает действие, Database.add_meeting выполняет INSERT и возвращает ID.')
numbered(doc, 'Календарь выбирает дату записи, refresh_meetings заново заполняет таблицу и подсвечивает даты с встречами.')

heading(doc, '2. Проверка пересечения времени', 2)
add_p(doc, 'Проверка выполняется в рамках одной даты. SQL считает записи, для которых существующая встреча начинается раньше окончания новой и заканчивается позже начала новой. Если количество таких строк больше нуля, метод возвращает True.')
codebox(doc, 'WHERE meeting_date = ?\n  AND start_time < new_end_time\n  AND end_time > new_start_time')
add_p(doc, 'Пример: существующая встреча длится 10:00–11:00, новая — 10:30–11:30. Условия выполняются, значит, есть пересечение. Если новая начинается ровно в 11:00, существующая заканчивается в 11:00, условие end_time > new_start_time ложно — соседние встречи не считаются пересечением. При редактировании параметр exclude_id исключает саму редактируемую запись из проверки, чтобы она не конфликтовала сама с собой.')
callout(doc, 'Формулировка для защиты',
        'Программа использует проверку пересечения полуоткрытых временных интервалов: начало одной записи должно быть раньше конца другой, а конец другой — позже начала первой. Поэтому встречи, которые соприкасаются ровно по границе времени, допустимы.',
        fill=LIGHT_BLUE, accent=BLUE)

heading(doc, '3. Редактирование и удаление', 2)
add_p(doc, 'Для редактирования MainWindow получает ID выбранной строки, загружает запись через get_meeting и передаёт её в MeetingDialog. Форма заполняется существующими значениями. После проверки MainWindow снова проверяет конфликты, но передаёт exclude_id текущей записи. При подтверждении вызывается update_meeting. Для удаления сначала показывается вопрос подтверждения, затем вызывается delete_meeting и обновляется список.')

heading(doc, '4. Просмотр дня и подсветка календаря', 2)
add_p(doc, 'Когда пользователь выбирает день, сигнал selectionChanged запускает refresh_meetings. Метод обновляет заголовок выбранной даты, получает записи через get_meetings_for_date и передаёт их в _fill_table. Для подсветки всех дат с встречами метод получает общий список через get_all_meetings. Тема определяет цвета текста и фона маркера.')

heading(doc, '5. Поиск', 2)
add_p(doc, 'Изменение текста в QLineEdit вызывает search_meetings практически сразу. Если поле пустое, программа возвращает список встреч выбранного дня. Если текст есть, база ищет по названию, месту и описанию по всему календарю. В заголовке справа отображается количество найденных записей. Очистка поля также запускает обработчик и восстанавливает дневной список.')

heading(doc, '6. Экспорт CSV и TXT', 2)
add_p(doc, 'export_calendar получает все встречи через get_all_meetings, показывает диалог выбора имени и типа файла. CSV открывается с encoding="utf-8-sig" и записывается стандартным модулем csv с разделителем «;». В него попадают название, дата, начало, окончание, место, описание и заметки. TXT формируется обычными строками, где каждая встреча отделена линией. Если пользователь отменяет диалог, экспорт не выполняется. Ошибки записи OSError показываются пользователю в отдельном диалоге.')

heading(doc, '7. Переключение темы и формата времени', 2)
add_p(doc, 'SettingsDialog собирает новые параметры. MainWindow проверяет горячие клавиши и затем сохраняет словарь через save_settings. После сохранения настройки заново читаются из базы. NotificationManager получает обновлённые параметры через update_settings, горячие клавиши применяются через update_shortcuts, тема — через _apply_theme, а список встреч обновляется. При отображении время преобразуется методом display_time, но в базе оно остаётся в едином формате HH:mm.')

page_break(doc)
heading(doc, 'Часть 7. Уведомления и горячие клавиши', 1)
heading(doc, 'NotificationManager: последовательность проверки', 2)
reset_numbered()
numbered(doc, 'При создании NotificationManager он получает объект Database и загружает настройки.')
numbered(doc, 'Создаётся набор sent_ids, в котором хранятся ID уже обработанных уведомлений в рамках текущего запуска программы.')
numbered(doc, 'Создаётся QTimer. Интервал задан как 30 000 миллисекунд, то есть 30 секунд.')
numbered(doc, 'Таймер подключается к методу check_meetings и запускается.')
numbered(doc, 'Если notifications_enabled не равно "1", проверка сразу завершается.')
numbered(doc, 'Получается текущее время QDateTime.currentDateTime. К нему добавляется reminder_minutes, получается целевой момент.')
numbered(doc, 'Метод get_upcoming_meetings передаёт SQL запросу строку целевого времени и возвращает не более 50 записей, которые начинаются не позже этого момента.')
numbered(doc, 'Для каждой записи проверяются корректность даты/времени, попадание в интервал от текущего времени до целевого и отсутствие ID в sent_ids.')
numbered(doc, 'Вызывается show_notification. Если системный трей создан, QSystemTrayIcon.showMessage отображает заголовок, название встречи, время и место.')
numbered(doc, 'ID добавляется в sent_ids, а сигнал notification_sent испускается с этим ID.')

heading(doc, 'Что нужно знать о QTimer и системном трее', 2)
add_p(doc, 'QTimer работает внутри event loop Qt. Он не создаёт отдельный фоновый процесс и не запускает уведомления после закрытия приложения. QSystemTrayIcon.isSystemTrayAvailable проверяет, доступен ли системный трей на текущей платформе. Если он недоступен, объект трея не создаётся и системное сообщение не показывается. Внешний вид и разрешения системных уведомлений могут зависеть от операционной системы.')
callout(doc, 'Ограничение текущей реализации',
        'Уведомления работают, пока приложение запущено. sent_ids хранится в оперативной памяти и очищается при новом запуске, поэтому это защита от повторов только в пределах одной сессии. Для уведомлений после закрытия программы понадобится отдельный системный планировщик или фоновый сервис.',
        fill=PALE_ORANGE)

heading(doc, 'Горячие клавиши', 2)
table(doc, ['Сочетание по умолчанию', 'Действие', 'Метод'], [
    ('Ctrl+N', 'Новая встреча', 'add_meeting'),
    ('Ctrl+E', 'Редактировать выбранную', 'edit_meeting'),
    ('Delete', 'Удалить выбранную', 'delete_meeting'),
    ('Ctrl+T', 'Перейти к сегодняшней дате', 'go_to_today'),
    ('Ctrl+Shift+E', 'Экспортировать календарь', 'export_calendar'),
    ('Ctrl+F', 'Перейти в поле поиска', 'focus_search'),
], widths=[4.0,6.0,6.8], font_size=8.8)
add_p(doc, 'Горячие клавиши реализованы через QAction и QKeySequence. update_shortcuts связывает ключи настроек с действиями меню. Если сочетание не распознаётся QKeySequence или повторяется у другого действия, _validate_shortcuts показывает предупреждение и не сохраняет настройки.')

page_break(doc)
heading(doc, 'Часть 8. Использованные технологии и тестирование', 1)
table(doc, ['Технология', 'Где используется', 'Как объяснить'], [
    ('Python 3.10+', 'Логика всего проекта.', 'Основной язык: классы, методы, обработка данных и запуск.'),
    ('PyQt6', 'Графический интерфейс.', 'Окна, формы, календарь, таблица, меню и система событий.'),
    ('SQLite / sqlite3', 'Файл meet_to_meet.db.', 'Локальная реляционная БД; отдельный сервер не нужен.'),
    ('QTimer / QDateTime', 'notifications.py.', 'Периодический запуск проверки и операции с датой/временем.'),
    ('QSystemTrayIcon', 'notifications.py.', 'Показ системных уведомлений в трее.'),
    ('csv', 'Экспорт CSV.', 'Стандартный модуль Python для табличного текста.'),
    ('pathlib / shutil', 'Пути и перенос базы.', 'Кроссплатформенная работа с путями и копирование старого файла.'),
    ('unittest / tempfile / mock', 'tests/test_database.py.', 'Тесты, временные каталоги и подмена путей для проверки миграции.'),
], widths=[3.4,4.4,9.0], font_size=8.5)

heading(doc, 'Семь тестов, которые есть в репозитории', 2)
table(doc, ['Тест', 'Что проверяется'], [
    ('test_add_and_read_meeting', 'После добавления запись находится по возвращённому ID, название совпадает.'),
    ('test_update_meeting', 'После UPDATE у записи появляется новое название.'),
    ('test_delete_meeting', 'После DELETE get_meeting возвращает None.'),
    ('test_time_conflict', 'Встреча 10:30–11:30 пересекается с 10:00–11:00, а 11:00–12:00 — нет.'),
    ('test_settings_are_saved', 'Тема сохраняется и считывается как «Тёмная».'),
    ('test_default_database_path_is_inside_project', 'Путь по умолчанию равен папке проекта плюс meet_to_meet.db.'),
    ('test_legacy_database_is_copied_to_project_location', 'Старый файл копируется, оригинал остаётся, данные в копии доступны.'),
], widths=[6.2,10.6], font_size=8.5)

heading(doc, 'Как запустить тесты', 2)
codebox(doc, 'python -m unittest discover -s tests -v')
add_p(doc, 'В тестах используется временная база внутри TemporaryDirectory. Поэтому тесты не портят рабочий файл meet_to_meet.db пользователя. Отдельно для миграции подменяются Database.default_db_path и Path.home, чтобы не обращаться к реальным личным папкам.')

heading(doc, 'Что тесты не доказывают', 2)
add_p(doc, 'Текущие тесты проверяют Database и логику хранения данных. Они не являются полным автоматическим тестом интерфейса PyQt6, внешнего вида календаря, реального системного трея или отображения уведомлений в конкретной операционной системе. Эти части нужно дополнительно проверять вручную в графической среде.')

page_break(doc)
heading(doc, 'Часть 9. Вопросы преподавателя и готовые ответы', 1)
qa = [
('Почему ты выбрал SQLite?', 'Приложение локальное и рассчитано на одного пользователя. SQLite хранит всё в файле, не требует отдельного сервера и подключается через стандартный модуль sqlite3.'),
('Где лежит файл базы?', 'Рядом с файлом database.py, в корневой папке проекта. Путь строится через Path(__file__).resolve().parent / "meet_to_meet.db".'),
('Что происходит при первом запуске?', 'Database вызывает initialize. Создаются таблицы meetings и settings, индекс по дате и времени, а отсутствующие настройки добавляются со значениями по умолчанию.'),
('Как не потерять старую базу?', 'Перед инициализацией программа проверяет старый путь в домашней директории. Если новая база ещё не существует, старый файл копируется через shutil.copy2. Старый файл не удаляется.'),
('Что такое PRIMARY KEY?', 'Это поле, которое уникально идентифицирует каждую строку. В meetings таким полем является id.'),
('Зачем AUTOINCREMENT?', 'Чтобы SQLite автоматически выдавала новый числовой ID для новой встречи.'),
('Зачем индекс?', 'Индекс по meeting_date и start_time помогает ускорять выборки и сортировки расписания по дате и времени.'),
('Что такое параметризированный запрос?', 'Это запрос с заполнителями ?, в который значения передаются отдельно. Так пользовательский текст не склеивается с SQL-командой.'),
('Что такое commit и rollback?', 'commit фиксирует изменения в базе. rollback отменяет изменения текущей транзакции, если операция завершилась ошибкой.'),
('Как работает поиск?', 'Поле поиска реагирует на textChanged. SQL использует LIKE и ищет подстроку в названии, месте и описании.'),
('Почему соседние встречи не считаются конфликтом?', 'Условие пересечения использует start_time < end_time второй записи и end_time > start_time второй записи. Равенство границе не считается пересечением.'),
('Как исключается конфликт с самой собой при редактировании?', 'В has_time_conflict передаётся exclude_id, и запрос добавляет условие id != текущий ID.'),
('Как работает экспорт?', 'Все записи считываются из БД. CSV формируется модулем csv с разделителем ; и кодировкой utf-8-sig; TXT записывается обычным текстом UTF-8.'),
('Почему нет отдельного класса Meeting?', 'В текущей версии поля встречи передаются в виде словаря Python. Это проще для данного небольшого проекта; отдельную модель можно добавить при дальнейшем развитии.'),
('Как работает смена темы?', 'Тема хранится в settings. После сохранения MainWindow перечитывает настройки и применяет общий Qt Style Sheet через _apply_theme.'),
('Почему формат времени не влияет на базу?', 'Для хранения используется единый формат HH:mm. Настройка 12/24 часа влияет только на отображение в форме и таблице.'),
('Как работают уведомления?', 'QTimer каждые 30 секунд вызывает check_meetings. Текущий момент сравнивается с началом встречи и заданным интервалом напоминания, а сообщение показывается через QSystemTrayIcon.'),
('Будут ли уведомления после закрытия приложения?', 'Нет. Таймер работает внутри цикла событий Qt, который прекращается после закрытия приложения. Нужен отдельный фоновый сервис или системный планировщик.'),
('Что такое сигнал и слот?', 'Сигнал сообщает о событии интерфейса, например нажатии кнопки. Слот — метод, который вызывается при этом событии. В PyQt связь создаётся через connect.'),
('Что делает app.exec()?', 'Запускает цикл событий Qt, который обрабатывает действия пользователя, сигналы, перерисовку окон и таймеры.'),
('Что проверяют тесты?', 'Пять операций с данными и настройками, а ещё новый путь базы и перенос старой базы. GUI-тестирование в эти семь тестов не входит.'),
('Какие слабые места и планы развития?', 'Пока нет синхронизации между устройствами, повторяющихся событий, резервного копирования и уведомлений после закрытия. Это возможные следующие функции.'),
]
for q, a in qa:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(5)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    add_text(p, 'Вопрос: ' + q, bold=True, color=BLUE, size=10)
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.35)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.line_spacing = 1.08
    add_text(p, 'Ответ: ' + a, color=TEXT, size=9.6)

page_break(doc)
heading(doc, 'Часть 10. План живой демонстрации и шпаргалка', 1)
heading(doc, 'Что показать на компьютере', 2)
reset_numbered()
numbered(doc, 'Открой главное окно и покажи календарь, заголовок месяца и переход между месяцами.')
numbered(doc, 'Выбери день и добавь демонстрационную встречу: название, дату, начало/окончание, место, описание, заметки.')
numbered(doc, 'Попробуй указать некорректное время окончания. Покажи, что форма предупреждает и не принимает такой интервал.')
numbered(doc, 'Создай вторую встречу, пересекающуюся по времени. Покажи предупреждение о совпадении и объясни, что пользователь может принять решение.')
numbered(doc, 'Выбери встречу в таблице. Покажи панель подробностей, затем открой редактирование и измени название.')
numbered(doc, 'Покажи поиск по слову из названия или места, затем очисти поле и вернись к списку выбранного дня.')
numbered(doc, 'Открой настройки, переключи тему, формат времени и покажи поля горячих клавиш.')
numbered(doc, 'Экспортируй календарь в CSV или TXT и покажи созданный файл.')
numbered(doc, 'Открой папку проекта и покажи meet_to_meet.db. При необходимости открой его через DB Browser for SQLite и покажи таблицы meetings и settings.')
numbered(doc, 'В терминале запусти команду тестов и объясни, какие операции они проверяют.')

heading(doc, 'Пять фраз, которые нужно помнить', 2)
callout(doc, '1. Про архитектуру', '«MainWindow управляет интерфейсом, Database — хранением данных, NotificationManager — напоминаниями».', fill=LIGHT_BLUE, accent=BLUE)
callout(doc, '2. Про базу', '«SQLite хранится в файле meet_to_meet.db рядом с исходным кодом; отдельный сервер не нужен».', fill=LIGHT_BLUE, accent=BLUE)
callout(doc, '3. Про данные', '«Встреча передаётся как словарь, а её уникальный ID нужен для чтения, изменения и удаления».', fill=LIGHT_BLUE, accent=BLUE)
callout(doc, '4. Про пересечения', '«Два сравнения интервалов определяют конфликт; при редактировании текущий ID исключается из проверки».', fill=LIGHT_BLUE, accent=BLUE)
callout(doc, '5. Про уведомления', '«QTimer проверяет расписание каждые 30 секунд; уведомления показываются, пока приложение запущено и доступен системный трей».', fill=LIGHT_BLUE, accent=BLUE)

heading(doc, 'Команды запуска и проверки', 2)
codebox(doc, 'python -m pip install -r requirements.txt\npython main.py\n\n# В отдельном терминале для тестирования\npython -m unittest discover -s tests -v')

page_break(doc)
heading(doc, 'Перед защитой: что не перепутать', 1)
add_p(doc, 'Эта последняя страница — короткая проверка формулировок. Она помогает не приписать программе функции, которых пока нет, и уверенно назвать реальные механизмы проекта.')
heading(doc, 'Чего не нужно утверждать на защите', 2)
bullet(doc, 'Не говори, что используется MySQL или SQLite Server. Используется SQLite — локальная файловая база.')
bullet(doc, 'Не говори, что уведомления продолжают работать после закрытия программы. В этой версии это не реализовано.')
bullet(doc, 'Не говори, что тестируется весь GUI. Семь тестов проверяют Database и миграцию базы.')
bullet(doc, 'Не говори, что в коде есть отдельный класс Meeting. Данные встречи сейчас передаются словарём.')
bullet(doc, 'Не говори, что поиск ищет по заметкам. Сейчас он проверяет название, место и описание.')

heading(doc, 'Шесть фактов, которые стоит назвать точно', 2)
table(doc, ['Факт', 'Точное описание'], [
    ('Файл БД', 'meet_to_meet.db рядом с database.py.'),
    ('Таблицы', 'meetings и settings.'),
    ('Доступ к БД', 'Стандартный sqlite3; отдельный сервер не нужен.'),
    ('Формат хранения', 'Дата yyyy-MM-dd, время HH:mm.'),
    ('Проверка напоминаний', 'QTimer с интервалом 30 секунд.'),
    ('Автотесты', '7 тестов слоя данных и переноса старой базы; не GUI-тесты.'),
], widths=[4.2,12.4], font_size=8.8)

callout(doc, 'Финальное напоминание',
        'На защите важнее понимание связей, чем заучивание имён всех функций. Умей объяснить путь одной встречи: пользователь вводит её в MeetingDialog → MainWindow получает словарь → Database выполняет INSERT → SQLite сохраняет строку → MainWindow перечитывает встречи и обновляет таблицу.',
        fill=PALE_ORANGE)

# Document properties
props = doc.core_properties
props.title = 'Meet to meet — руководство для защиты проекта'
props.subject = 'Текст выступления и техническое объяснение проекта'
props.author = 'Саша Шишкин'
props.keywords = 'Meet to meet, Python, PyQt6, SQLite, защита проекта'
props.comments = 'Подготовлено по структуре репозитория SH1SHOCHKA/meet-to-meet на 20.11.2026.'

doc.save(OUT)
print(OUT)
print('size', OUT.stat().st_size)


# ----------------------------- Minimal presentation -----------------------------

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.text import MSO_AUTO_SIZE
from pathlib import Path

OUT = Path(__file__).resolve().parent / 'Meet_to_meet_presentation_minimal.pptx'
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLK = RGBColor(20, 22, 25)
DARK = RGBColor(39, 42, 47)
MID = RGBColor(93, 99, 108)
GRAY = RGBColor(135, 141, 149)
LIGHT = RGBColor(235, 237, 240)
PALE = RGBColor(246, 247, 249)
WHITE = RGBColor(255,255,255)
FONT = 'Aptos'


def rect(slide, x, y, w, h, fill=PALE, line=None, radius=False):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h)
    )
    shape.fill.solid(); shape.fill.fore_color.rgb = fill
    shape.line.fill.background() if line is None else None
    if line is not None:
        shape.line.color.rgb = line
        shape.line.width = Pt(0.8)
    if radius:
        try: shape.adjustments[0] = 0.08
        except Exception: pass
    return shape


def text(slide, txt, x, y, w, h, size=16, color=BLK, bold=False,
         align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.TOP, margin=0.02,
         font=FONT, fit=True, italic=False):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear(); tf.word_wrap = True
    tf.margin_left = Inches(margin); tf.margin_right = Inches(margin)
    tf.margin_top = Inches(margin); tf.margin_bottom = Inches(margin)
    tf.vertical_anchor = valign
    if fit:
        tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    p = tf.paragraphs[0]
    p.alignment = align
    p.space_before = Pt(0); p.space_after = Pt(0)
    r = p.add_run(); r.text = txt
    r.font.name = font; r.font.size = Pt(size); r.font.bold = bold
    r.font.italic = italic; r.font.color.rgb = color
    return box


def line(slide, x1, y1, x2, y2, color=LIGHT, width=1.0, dash=None):
    s = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,
        Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    s.line.color.rgb = color; s.line.width = Pt(width)
    if dash is not None: s.line.dash_style = dash
    return s


def base(title, section, num, dark=False):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg = BLK if dark else WHITE
    slide.background.fill.solid(); slide.background.fill.fore_color.rgb = bg
    primary = WHITE if dark else BLK
    muted = RGBColor(175,179,185) if dark else MID
    text(slide, section.upper(), 0.62, 0.38, 6.5, 0.22, 9, muted, True)
    text(slide, title, 0.62, 0.78, 12.0, 0.52, 26, primary, True)
    line(slide, 0.62, 1.43, 12.72, 1.43, DARK if dark else LIGHT, 1.0)
    line(slide, 0.62, 7.05, 12.72, 7.05, DARK if dark else LIGHT, 0.8)
    text(slide, 'MEET TO MEET', 0.62, 7.13, 3.0, 0.18, 8, muted, True)
    text(slide, f'{num:02d} / 10', 11.55, 7.13, 1.15, 0.18, 8, muted, True, PP_ALIGN.RIGHT)
    return slide


def card(slide, x, y, w, h, title_, body, dark=False, index=None, body_size=14):
    fill = DARK if dark else PALE
    edge = RGBColor(73,77,84) if dark else LIGHT
    rect(slide,x,y,w,h,fill,line=edge,radius=True)
    tx = x+0.22
    if index is not None:
        text(slide, index, tx, y+0.18, 0.42, 0.28, 11, GRAY if not dark else RGBColor(170,175,181), True)
        tx += 0.48
    text(slide,title_,tx,y+0.18,w-(tx-x)-0.20,0.35,15,WHITE if dark else BLK,True)
    text(slide,body,x+0.22,y+0.68,w-0.44,h-0.84,body_size,RGBColor(220,223,227) if dark else DARK)


def bullet_list(slide, items, x, y, w, h, size=15, color=DARK, gap=0.11,
                bullet_color=GRAY):
    n=len(items)
    each=(h-gap*(n-1))/n
    for i,item in enumerate(items):
        yy=y+i*(each+gap)
        rect(slide,x,yy+0.07,0.09,0.09,bullet_color)
        text(slide,item,x+0.25,yy,w-0.25,each,size,color)

# 1 — title
s=prs.slides.add_slide(prs.slide_layouts[6])
s.background.fill.solid(); s.background.fill.fore_color.rgb=BLK
rect(s,0.75,0.72,0.10,5.95,RGBColor(145,150,157))
text(s,'УЧЕБНЫЙ ПРОЕКТ',1.18,1.22,4.0,0.28,10,RGBColor(177,182,189),True)
text(s,'MEET TO MEET',1.15,2.05,10.8,1.05,42,WHITE,True)
text(s,'Настольное приложение\nдля планирования встреч',1.18,3.27,8.8,1.05,24,RGBColor(218,221,225),False)
line(s,1.18,5.35,5.6,5.35,RGBColor(92,97,104),1.1)
text(s,'Автор проекта',1.18,5.65,2.1,0.22,10,RGBColor(165,170,177),True)
text(s,'Саша Шишкин',1.18,5.96,4.4,0.42,19,WHITE,True)
text(s,'PYTHON  /  PYQT6  /  SQLITE',8.1,6.45,4.4,0.22,9,RGBColor(165,170,177),True,PP_ALIGN.RIGHT)

# 2 — introduction
s=base('Идея и задача проекта','01 — введение',2)
card(s,0.7,1.78,3.85,2.0,'Проблема','Встречи, ссылки, время и заметки часто разбросаны по перепискам и разным приложениям.')
card(s,4.75,1.78,3.85,2.0,'Идея','Собрать календарь, список событий и напоминания в одном простом настольном приложении.')
card(s,8.8,1.78,3.85,2.0,'Цель','Упростить планирование и снизить вероятность забыть встречу или назначить два события одновременно.')
text(s,'Задачи, которые решает приложение',0.72,4.25,5.4,0.35,17,BLK,True)
bullet_list(s,[
    'создавать, просматривать, изменять и удалять встречи;',
    'хранить дату, время, место, описание и заметки;',
    'находить записи, экспортировать календарь и получать напоминания;',
    'сохранять настройки пользователя между запусками.'
],0.78,4.78,11.6,1.75,14)

# 3 — architecture
s=base('Архитектура и разделение ответственности','02 — реализация',3)
# central app layer diagram
rect(s,4.55,1.82,4.2,0.74,BLK,radius=True)
text(s,'MainWindow  ·  координация приложения',4.75,2.03,3.8,0.28,15,WHITE,True,PP_ALIGN.CENTER)
line(s,6.65,2.56,2.8,3.18,MID,1.1); line(s,6.65,2.56,6.65,3.18,MID,1.1); line(s,6.65,2.56,10.5,3.18,MID,1.1)
card(s,0.75,3.18,3.8,1.65,'Формы интерфейса','MeetingDialog — данные встречи.\nSettingsDialog — параметры пользователя.',body_size=13)
card(s,4.75,3.18,3.8,1.65,'Database','Создание таблиц, SQL-запросы, сохранение и получение данных SQLite.',body_size=13)
card(s,8.75,3.18,3.8,1.65,'NotificationManager','QTimer проверяет расписание, QSystemTrayIcon показывает системное сообщение.',body_size=13)
line(s,6.65,4.85,6.65,5.35,MID,1.1)
rect(s,4.75,5.35,3.8,0.88,RGBColor(225,228,232),radius=True)
text(s,'SQLite  ·  meet_to_meet.db',4.95,5.62,3.4,0.28,15,BLK,True,PP_ALIGN.CENTER)
text(s,'Интерфейс не содержит SQL-запросы напрямую: он обращается к методам Database.',0.9,6.48,11.5,0.30,12,MID,False,PP_ALIGN.CENTER)

# 4 — interface
s=base('Интерфейс и основные классы','02 — реализация',4)
card(s,0.72,1.78,5.85,1.95,'Главное окно — MainWindow','Календарь, список встреч, подробности выбранной записи, поиск, меню, кнопки, горячие клавиши и обновление данных.')
card(s,6.75,1.78,5.85,1.95,'Форма встречи — MeetingDialog','Поля: название, дата, время начала и окончания, место/ссылка, описание и заметки. Возвращает данные словарём.')
card(s,0.72,3.98,5.85,1.95,'Форма настроек — SettingsDialog','Тема, формат времени, уведомления, интервал напоминания и шесть настраиваемых горячих клавиш.')
card(s,6.75,3.98,5.85,1.95,'Как интерфейс реагирует на действия','Сигналы Qt: clicked, selectionChanged, textChanged, itemSelectionChanged. Они вызывают методы MainWindow.')
text(s,'Важно: отдельного класса Meeting в этой версии нет — запись представлена словарём Python.',0.9,6.35,11.5,0.35,12,MID,True,PP_ALIGN.CENTER)

# 5 — meeting workflow
s=base('Жизненный цикл встречи','02 — реализация',5)
steps=[('01','Ввод','Пользователь заполняет MeetingDialog.'),('02','Проверка формы','Название обязательно; время окончания позже начала.'),('03','Проверка конфликта','Database.has_time_conflict ищет пересечение в этот день.'),('04','Сохранение','Database.add_meeting или update_meeting выполняет INSERT / UPDATE.'),('05','Обновление','MainWindow перечитывает встречи и перерисовывает таблицу и маркеры.')]
for i,(n,t,b) in enumerate(steps):
    y=1.8+i*0.94
    rect(s,0.82,y,0.55,0.55,BLK,radius=True)
    text(s,n,0.83,y+0.14,0.53,0.2,11,WHITE,True,PP_ALIGN.CENTER)
    text(s,t,1.65,y+0.02,2.45,0.27,15,BLK,True)
    text(s,b,4.05,y+0.03,8.25,0.42,14,DARK)
    if i<4: line(s,1.1,y+0.57,1.1,y+0.92,LIGHT,1.1)
rect(s,0.82,6.55,11.7,0.28,LIGHT)
text(s,'Пересечение не запрещает запись автоматически: пользователь видит предупреждение и принимает решение.',1.0,6.57,11.3,0.20,10,BLK,True,PP_ALIGN.CENTER)

# 6 — database schema
s=base('База данных: таблицы и поля','03 — хранение данных',6)
text(s,'SQLite хранит данные в локальном файле meet_to_meet.db рядом с файлами проекта.',0.75,1.72,11.7,0.35,14,DARK)
# table headings and row details
rect(s,0.75,2.28,7.55,0.48,BLK,radius=True)
text(s,'meetings  ·  календарные записи',0.98,2.40,7.1,0.20,13,WHITE,True)
leftrows=[
('id','INTEGER PRIMARY KEY AUTOINCREMENT','Уникальный ID'),
('title','TEXT NOT NULL','Название встречи'),
('meeting_date','TEXT NOT NULL','Дата: YYYY-MM-DD'),
('start_time / end_time','TEXT NOT NULL','Время: HH:MM'),
('place / description / notes','TEXT DEFAULT empty','Место, описание, заметки'),
('created_at / updated_at','TEXT DEFAULT CURRENT_TIMESTAMP','Время создания и изменения')]
for i,row in enumerate(leftrows):
    y=2.86+i*0.52
    fill=PALE if i%2==0 else WHITE
    rect(s,0.75,y,7.55,0.45,fill,line=LIGHT)
    text(s,row[0],0.91,y+0.08,1.8,0.23,11,BLK,True)
    text(s,row[1],2.78,y+0.08,2.65,0.23,10,DARK)
    text(s,row[2],5.48,y+0.08,2.62,0.23,10,MID)
rect(s,8.65,2.28,3.93,0.48,BLK,radius=True)
text(s,'settings  ·  настройки',8.87,2.40,3.5,0.20,13,WHITE,True)
card(s,8.65,2.86,3.93,2.12,'Структура «ключ — значение»','setting_key — имя параметра.\nsetting_value — значение в виде текста.\n\nПримеры: theme, time_format, reminder_minutes, shortcut_add.',body_size=12)
card(s,8.65,5.18,3.93,1.23,'Индекс','idx_meetings_date по meeting_date и start_time ускоряет выборки расписания.',body_size=11)

# 7 — database operation and migration
s=base('Как программа работает с SQLite','03 — хранение данных',7)
card(s,0.75,1.82,3.85,1.7,'Подключение','sqlite3.connect открывает файл. row_factory = sqlite3.Row позволяет обращаться к полям по имени.',body_size=12)
card(s,4.75,1.82,3.85,1.7,'Транзакции','Контекстный менеджер connect выполняет commit при успехе, rollback при ошибке и закрывает соединение.',body_size=12)
card(s,8.75,1.82,3.85,1.7,'Безопасность запросов','Значения передаются через заполнители ?, отдельно от SQL-команды. Это защищает от некорректной подстановки данных.',body_size=12)
text(s,'Основные операции',0.82,4.0,3.0,0.32,17,BLK,True)
ops=[('INSERT','Добавление новой встречи'),('SELECT','Чтение одной / списка встреч'),('UPDATE','Изменение существующей записи'),('DELETE','Удаление по ID'),('LIKE','Поиск по части текста'),('ON CONFLICT','Обновление настроек по ключу')]
for i,(sql,desc) in enumerate(ops):
    col=i%3; row=i//3
    x=0.82+col*4.1; y=4.48+row*0.82
    rect(s,x,y,3.82,0.65,PALE,line=LIGHT,radius=True)
    text(s,sql,x+0.14,y+0.10,1.25,0.22,12,BLK,True)
    text(s,desc,x+1.38,y+0.09,2.28,0.36,10,DARK)
text(s,'При обновлении проекта старая база из домашней папки копируется в каталог проекта; исходный файл не удаляется.',0.85,6.35,11.6,0.34,11,MID,False,PP_ALIGN.CENTER)

# 8 — search, export, settings
s=base('Поиск, экспорт и пользовательские настройки','04 — функции',8)
card(s,0.75,1.82,3.85,2.0,'Поиск','Поле textChanged вызывает MainWindow.search_meetings. Database использует LIKE по названию, месту и описанию.',body_size=12)
card(s,4.75,1.82,3.85,2.0,'Экспорт','Все встречи считываются из базы. CSV формируется модулем csv с разделителем «;», TXT — обычной записью текста.',body_size=12)
card(s,8.75,1.82,3.85,2.0,'Настройки','Тема, 12/24-часовой формат, уведомления, интервал 0–1440 минут и горячие клавиши сохраняются в settings.',body_size=12)
text(s,'Горячие клавиши по умолчанию',0.82,4.32,5.0,0.35,17,BLK,True)
shortcuts=[('Ctrl + N','Новая встреча'),('Ctrl + E','Изменить выбранную'),('Delete','Удалить'),('Ctrl + T','Сегодня'),('Ctrl + Shift + E','Экспорт'),('Ctrl + F','Поиск')]
for i,(key,action) in enumerate(shortcuts):
    col=i%3; row=i//3
    x=0.82+col*4.08; y=4.87+row*0.76
    rect(s,x,y,3.8,0.56,LIGHT,radius=True)
    text(s,key,x+0.13,y+0.16,1.65,0.18,11,BLK,True)
    text(s,action,x+1.82,y+0.15,1.78,0.2,11,DARK)

# 9 — notifications, stack and tests
s=base('Уведомления, технологии и тестирование','05 — реализация',9)
card(s,0.75,1.82,5.85,2.05,'Механизм уведомлений','NotificationManager использует QTimer с интервалом 30 000 мс. При проверке вычисляется момент напоминания, выбираются ближайшие встречи, затем QSystemTrayIcon показывает сообщение. sent_ids не допускает повтор в рамках одного запуска.',body_size=12)
card(s,6.75,1.82,5.85,2.05,'Ограничение текущей версии','Уведомления работают, пока приложение запущено и системный трей доступен. Набор sent_ids хранится в оперативной памяти и очищается при новом запуске.',body_size=12)
text(s,'Стек технологий',0.82,4.18,3.5,0.32,17,BLK,True)
tech=[('Python 3.10+','основная логика'),('PyQt6','окна и события'),('SQLite / sqlite3','локальное хранение'),('QTimer / QDateTime','проверка времени'),('QSystemTrayIcon','системные уведомления'),('csv / pathlib / shutil','экспорт и файлы'),('unittest / tempfile / mock','автоматические тесты')]
for i,(name,desc) in enumerate(tech):
    row=i//4; col=i%4
    x=0.82+col*3.06; y=4.68+row*0.74
    w=2.82
    rect(s,x,y,w,0.58,PALE,line=LIGHT,radius=True)
    text(s,name,x+0.12,y+0.07,w-0.24,0.19,10,BLK,True)
    text(s,desc,x+0.12,y+0.31,w-0.24,0.18,9,MID)
text(s,'7 тестов проверяют CRUD, поиск конфликтов по времени, настройки, путь базы и перенос старой базы.',0.85,6.42,11.6,0.28,11,MID,True,PP_ALIGN.CENTER)

# 10 — conclusion
s=base('Результат и дальнейшее развитие','06 — заключение',10, dark=True)
card(s,0.78,1.85,3.78,1.72,'Что реализовано','Рабочая структура настольного планировщика: календарь, CRUD встреч, поиск, экспорт, настройки и уведомления.',dark=True,body_size=12)
card(s,4.78,1.85,3.78,1.72,'Что освоено','Разделение кода на модули, классы, сигналы и слоты Qt, SQL, работа с файлами и автоматические тесты.',dark=True,body_size=12)
card(s,8.78,1.85,3.78,1.72,'Что можно улучшить','Повторяющиеся события, резервные копии, синхронизация, фоновые уведомления и дополнительные фильтры.',dark=True,body_size=12)
text(s,'ИТОГ',0.9,4.45,1.0,0.25,10,RGBColor(168,173,180),True)
text(s,'Meet to meet объединяет основные действия с расписанием в одном локальном приложении.',0.9,4.92,11.4,0.78,25,WHITE,True)
text(s,'Спасибо за внимание',0.9,6.12,4.2,0.36,16,RGBColor(203,207,212),False)

# Presentation metadata
prs.core_properties.title = 'Meet to meet — защита проекта'
prs.core_properties.subject = '10-слайдовая презентация учебного проекта'
prs.core_properties.author = 'Саша Шишкин'
prs.core_properties.keywords = 'Meet to meet, Python, PyQt6, SQLite'
prs.save(OUT)
print(OUT)
print('slides',len(prs.slides),'bytes',OUT.stat().st_size)

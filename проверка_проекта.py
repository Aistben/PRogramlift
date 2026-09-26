#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Проверка целостности тренировочного проекта.

Запуск из корня репозитория:  python3 проверка_проекта.py
Код выхода: 0 — всё целостно, 1 — найдены ошибки.

Проверки:
  1. Наличие всех файлов проекта.
  2. CJK-дрейф (символы дальневосточных диапазонов) во всех текстовых файлах.
  3. Журнал: оглавление против заголовков, якоря по правилу GitHub.
  4. HTML: баланс тегов обеих программ.
  5. Недели: идентификаторы 1–8 (цикл 1) и 1–9 (цикл 2), nav-ссылки,
     ровно один маркер «Сейчас», «Пройдено» идут подряд до него.
  6. Цикл 2: у всех плашек навигации есть даты.
  7. Стоп-слово «в паузах»: в цикле 2 — ноль вхождений; в цикле 1 — только
     в пройденных неделях; в правилах и базе знаний — только с оговоркой.
  8. Инварианты цикла 2: суперсеты ×8 и ×8, строки суперсета ×16,
     темповый присед «вверх обычно» ×8, ширина страницы 1440px.
  9. README: все упомянутые файлы существуют.

При намеренном изменении инвариантов (разметка суперсетов, темповый присед,
ширина страницы, состав файлов) — обнови константы в этом скрипте.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

FILES = [
    '00_Профиль_спортсмена.md',
    '01_Программа_8_недель.html',
    '02_Журнал_тренировок.md',
    '03_Анализ_программы.md',
    '05_Правила_программы.md',
    '06_Мертвые_точки_жима.md',
    '07_База_знаний.md',
    'README.md',
    'Цикл_2_Объём/Программа_8_недель.html',
    'Цикл_2_Объём/Правила_цикла.md',
    'проверка_проекта.py',
]
C1 = '01_Программа_8_недель.html'
C2 = 'Цикл_2_Объём/Программа_8_недель.html'
JOURNAL = '02_Журнал_тренировок.md'

TAGS = ['section', 'article', 'div', 'details', 'summary', 'ol', 'ul',
        'li', 'span', 'b', 'i', 'a', 'h3', 'table', 'tr', 'td']

INVARIANTS = [
    ('Суперсет рук', 8),
    ('Суперсет ног', 8),
    ('Темповый присед · 3 с опускания, вверх обычно', 8),
    ('class="ss-row"', 32),  # 16 суперсетов x 2 строки
    ('max-width:1440px', 1),
]


def read(name):
    return (ROOT / name).read_text(encoding='utf-8')


def gh_slug(header):
    s = header.lower()
    s = ''.join(ch for ch in s if ch.isalnum() or ch in ' -')
    return s.replace(' ', '-')


def check_files():
    errs = []
    for f in FILES:
        if not (ROOT / f).is_file():
            errs.append(f'отсутствует файл {f}')
    return errs


def check_cjk():
    errs = []
    for f in FILES:
        t = read(f)
        bad = sorted({ch for ch in t
                      if '\u3040' <= ch <= '\u30ff'
                      or '\u4e00' <= ch <= '\u9fff'
                      or '\uff00' <= ch <= '\uffef'})
        if bad:
            errs.append(f'{f}: CJK-символы {bad}')
    return errs


def check_toc():
    errs = []
    j = read(JOURNAL)
    toc = re.findall(r'^- \[([^\]]+)\]\(#([^)]+)\)$', j, re.M)
    headers = re.findall(r'^## (.+)$', j, re.M)
    entries = [h for h in headers if h != 'Содержание']
    if len(headers) != len(set(headers)):
        errs.append('дубликаты заголовков ##')
    if len(toc) != len(entries):
        errs.append(f'строк оглавления {len(toc)}, записей {len(entries)}')
    slug_set = {gh_slug(h) for h in headers}
    for title, anchor in toc:
        if gh_slug(title) != anchor:
            errs.append(f'якорь не по правилу GitHub: [{title}](#{anchor})')
        if anchor not in slug_set:
            errs.append(f'нет заголовка под оглавлением: [{title}]')
    return errs


def check_html():
    errs = []
    for f in (C1, C2):
        t = read(f)
        for tag in TAGS:
            n_open = len(re.findall(fr'<{tag}\b', t))
            n_close = len(re.findall(fr'</{tag}>', t))
            if n_open != n_close:
                errs.append(f'{f}: <{tag}> открытий {n_open}, закрытий {n_close}')
    return errs


def check_weeks():
    errs = []
    for f, total in ((C1, 8), (C2, 9)):
        t = read(f)
        ids = sorted(int(m) for m in re.findall(r'id="week-(\d+)"', t))
        if ids != list(range(1, total + 1)):
            errs.append(f'{f}: идентификаторы недель {ids}, ожидалось 1..{total}')
        nav = re.findall(r'href="#week-(\d+)"([^>]*)>', t)
        nums = sorted({int(n) for n, _ in nav})
        if nums != list(range(1, total + 1)):
            errs.append(f'{f}: nav-ссылки {nums}')
        cur = [int(n) for n, attrs in nav if 'current' in attrs]
        done = sorted(int(n) for n, attrs in nav if 'done' in attrs)
        if len(cur) != 1:
            errs.append(f'{f}: маркеров «Сейчас» {len(cur)}, должен быть ровно 1')
        elif done != list(range(1, len(done) + 1)) or cur[0] != len(done) + 1:
            errs.append(f'{f}: «Пройдено» не подряд или не впритык к «Сейчас»: {done}, сейчас {cur[0]}')
    return errs


def check_dates():
    errs = []
    plates = re.findall(r'href="#week-\d+"[^>]*>Н\d+<small>([^<]+)</small>', read(C2))
    if len(plates) != 9:
        errs.append(f'цикл 2: плашек навигации с датами {len(plates)}, ожидалось 9')
    return errs


def week_segment(t, n, total):
    i = t.find(f'id="week-{n}"')
    if i < 0:
        return ''
    j = t.find(f'id="week-{n + 1}"') if n < total else len(t)
    return t[i:j]


def check_stopwords():
    errs = []
    warns = []
    if 'в паузах' in read(C2):
        errs.append(f'цикл 2: «в паузах» ×{read(C2).count("в паузах")} — ролик отдельным упражнением')
    t1 = read(C1)
    nav = re.findall(r'href="#week-(\d+)"([^>]*)>', t1)
    done = {int(n) for n, attrs in nav if 'done' in attrs}
    for n in range(1, 9):
        if n in done:
            continue
        if 'в паузах' in week_segment(t1, n, 8):
            errs.append(f'цикл 1, неделя {n}: «в паузах» в непройденной неделе')
    for f in ('Цикл_2_Объём/Правила_цикла.md', '07_База_знаний.md', '05_Правила_программы.md'):
        t = read(f)
        for m in re.finditer('в паузах', t):
            ctx = t[max(0, m.start() - 80):m.end() + 140]
            if not re.search(r'не делать|должна отдыхать|его не|отдыхает|вне пауз', ctx):
                warns.append(f'{f}: «в паузах» без оговорки рядом: …{ctx.strip()[:80]}…')
    return errs, warns


def check_invariants():
    errs = []
    t = read(C2)
    for needle, want in INVARIANTS:
        got = t.count(needle)
        if got != want:
            errs.append(f'цикл 2: «{needle}» ×{got}, ожидалось ×{want}')
    return errs


def check_readme():
    errs = []
    r = read('README.md')
    for m in re.findall(r'`([^`\n]+\.(?:md|html|py))`', r):
        candidate = m.split()[-1]  # «python3 проверка_проекта.py» → имя файла
        # короткие имена из таблицы папки цикла 2 ищутся и в Цикл_2_Объём/
        found = (ROOT / candidate).is_file() or (ROOT / 'Цикл_2_Объём' / candidate).is_file()
        if not found:
            errs.append(f'README упоминает несуществующий файл: {candidate}')
    return errs


def main():
    simple = [
        ('Файлы проекта', check_files),
        ('Кодировка (CJK)', check_cjk),
        ('Оглавление журнала', check_toc),
        ('Баланс HTML-тегов', check_html),
        ('Недели и маркеры', check_weeks),
        ('Даты навигации цикла 2', check_dates),
        ('Инварианты цикла 2', check_invariants),
        ('Файлы из README', check_readme),
    ]
    total_err, total_warn = 0, 0
    for name, fn in simple:
        errs = fn()
        total_err += len(errs)
        print(('OK  ' if not errs else 'FAIL') + ' ' + name)
        for e in errs:
            print('     - ' + e)
    errs, warns = check_stopwords()
    total_err += len(errs)
    total_warn += len(warns)
    print(('OK  ' if not errs else 'FAIL') + ' Стоп-слова «в паузах»')
    for e in errs:
        print('     - ' + e)
    for w in warns:
        print('     ! ' + w)
    total_warn += len(warns)
    print()
    if total_err:
        print(f'ИТОГ: ошибок {total_err}, предупреждений {total_warn}.')
        sys.exit(1)
    print(f'ИТОГ: проект целостен. Предупреждений: {total_warn}.')


if __name__ == '__main__':
    main()

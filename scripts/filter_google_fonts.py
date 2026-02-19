# -*- coding: utf-8 -*-
"""
Оставляет в static/fonts-list.json только шрифты, которые есть в каталоге Google Fonts.
Список Google Fonts берётся из github.com/jonathantneal/google-fonts-complete.
"""
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIST_PATH = os.path.join(ROOT, 'static', 'fonts-list.json')
GOOGLE_FONTS_JSON_URL = 'https://raw.githubusercontent.com/jonathantneal/google-fonts-complete/master/google-fonts.json'


def fetch_google_font_names():
    """Скачивает JSON и возвращает set точных названий семейств."""
    print('Загрузка списка Google Fonts...', flush=True)
    req = urllib.request.Request(GOOGLE_FONTS_JSON_URL, headers={'User-Agent': 'TipTyp/1'})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode('utf-8', errors='ignore'))
    if isinstance(data, dict):
        return set(data.keys())
    print('Неожиданная структура JSON', file=sys.stderr)
    return set()


def main():
    with open(LIST_PATH, 'r', encoding='utf-8') as f:
        fonts = json.load(f)
    if not isinstance(fonts, list):
        print('Ожидается JSON-массив строк', file=sys.stderr)
        sys.exit(1)
    valid_set = fetch_google_font_names()
    if not valid_set:
        sys.exit(1)
    valid = [name for name in fonts if name in valid_set]
    removed = [name for name in fonts if name not in valid_set]
    with open(LIST_PATH, 'w', encoding='utf-8') as f:
        json.dump(valid, f, ensure_ascii=False, indent=0)
    print('Готово. Оставлено: {}, убрано: {}'.format(len(valid), len(removed)))
    if removed:
        print('Удалённые (нет в Google Fonts):', ', '.join(sorted(removed)[:40]) + (' ...' if len(removed) > 40 else ''))


if __name__ == '__main__':
    main()

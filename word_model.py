# -*- coding: utf-8 -*-
"""
Локальная модель для генерации русских слов.
Обучается на списке слов (n-граммы по символам), затем генерирует новые слова
по обученному распределению. Работает без внешних API и тяжёлых зависимостей.
"""
import os
import random
import pickle

# Специальные токены для границ слова
START = '\x00'
END = '\x01'

# Ограничения длины сгенерированного слова
MIN_WORD_LEN = 2
MAX_WORD_LEN = 14


def _normalize_word(w):
    """Оставляем только буквы в нижнем регистре (кириллица и латиница)."""
    return ''.join(c for c in w.lower() if c.isalpha())


def train(words, smoothing=0.5):
    """
    Обучает модель на списке слов.
    Строит распределение P(c_next | c_prev, c_prev2) — триграммы по символам.
    Возвращает структуру для генерации: (c1, c2) -> { c3: вероятность }.
    """
    # (c1, c2) -> { c3: count }
    counts = {}
    for w in words:
        w = _normalize_word(w)
        if len(w) < 1:
            continue
        seq = [START, START] + list(w) + [END]
        for i in range(len(seq) - 2):
            c1, c2, c3 = seq[i], seq[i + 1], seq[i + 2]
            key = (c1, c2)
            if key not in counts:
                counts[key] = {}
            counts[key][c3] = counts[key].get(c3, 0) + 1

    # Сглаживание (add-smoothing) и перевод в вероятности
    probs = {}
    for key, next_counts in counts.items():
        total = sum(next_counts.values()) + smoothing * (len(next_counts) + 1)
        probs[key] = {
            c: (cnt + smoothing) / total
            for c, cnt in next_counts.items()
        }
    return probs


def generate_one_word(probs, max_attempts=50):
    """
    Генерирует одно слово сэмплированием из модели.
    """
    for _ in range(max_attempts):
        word_chars = []
        c1, c2 = START, START
        while True:
            key = (c1, c2)
            if key not in probs:
                break
            choices = list(probs[key].keys())
            weights = [probs[key][c] for c in choices]
            c3 = random.choices(choices, weights=weights, k=1)[0]
            if c3 == END:
                break
            word_chars.append(c3)
            if len(word_chars) >= MAX_WORD_LEN:
                break
            c1, c2 = c2, c3
        word = ''.join(word_chars)
        if MIN_WORD_LEN <= len(word) <= MAX_WORD_LEN:
            return word
    return None


def generate_words_from_model(probs, count=45):
    """Генерирует count слов. Повторяет попытки, если слово не подошло или дубликат."""
    result = []
    seen = set()
    attempts = 0
    max_total_attempts = count * 20
    while len(result) < count and attempts < max_total_attempts:
        w = generate_one_word(probs)
        attempts += 1
        if w and w not in seen:
            seen.add(w)
            result.append(w)
    return result


def get_model_path(lang='ru'):
    """Путь к файлу сохранённой модели. lang: 'ru' | 'en'. TIPTYP_DATA — каталог данных (Docker)."""
    base = os.environ.get('TIPTYP_DATA') or os.path.dirname(os.path.abspath(__file__))
    instance = os.path.join(base, 'instance')
    if not os.path.isdir(instance):
        instance = base
    name = 'word_gen_model_en.pkl' if lang == 'en' else 'word_gen_model.pkl'
    return os.path.join(instance, name)


def save_model(probs, path=None):
    path = path or get_model_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        pickle.dump(probs, f, protocol=pickle.HIGHEST_PROTOCOL)


def load_model(path=None):
    path = path or get_model_path()
    if not os.path.isfile(path):
        return None
    with open(path, 'rb') as f:
        return pickle.load(f)

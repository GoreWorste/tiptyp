# -*- coding: utf-8 -*-
"""
Обучение локальной модели генерации слов.
Запуск: python train_word_model.py
Модель обучается на встроенном списке слов и сохраняется в instance/word_gen_model.pkl.
Можно передать файл со словами (одно слово на строку):
  python train_word_model.py words.txt
"""
import sys
from word_model import train, save_model, get_model_path
from word_generator import REAL_WORDS


def main():
    if len(sys.argv) > 1:
        path = sys.argv[1]
        words = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                w = line.strip().lower()
                if w and w.isalpha():
                    words.append(w)
        print(f'Загружено {len(words)} слов из {path}')
    else:
        words = list(REAL_WORDS)
        print(f'Используется встроенный список: {len(words)} слов')

    if not words:
        print('Нет слов для обучения.')
        return 1

    probs = train(words)
    out = get_model_path()
    save_model(probs, out)
    print(f'Модель сохранена: {out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())

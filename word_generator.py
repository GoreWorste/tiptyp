# -*- coding: utf-8 -*-
"""
Генерация слов для теста набора.
- words: осмысленные русские слова из словаря (по умолчанию).
- model: наша локальная модель (n-граммы), обучается на словах и сама генерирует новые.
- syllable: псевдослова из русских слогов.
"""
import os
import random

from word_model import (
    train as model_train,
    load_model,
    save_model,
    generate_words_from_model,
    get_model_path,
)


# Осмысленные русские слова для режима "слова" 
REAL_WORDS = [
    'новый', 'стать', 'более', 'уж', 'куда', 'показаться', 'пойти', 'выйти', 'через', 'ряд',
    'по', 'машина', 'много', 'перед', 'мой', 'со', 'как', 'можно', 'значить', 'на', 'один',
    'когда', 'первый', 'смотреть', 'ещё', 'себя', 'другой', 'тогда', 'говорить', 'такой',
    'очень', 'сегодня', 'жизнь', 'быть', 'год', 'человек', 'время', 'дело', 'рука', 'раз',
    'глаз', 'день', 'ночь', 'мир', 'голова', 'друг', 'дом', 'слово', 'место', 'конец',
    'вопрос', 'лицо', 'дверь', 'сторона', 'страна', 'земля', 'вода', 'огонь', 'небо', 'солнце',
    'луна', 'город', 'улица', 'дорога', 'путь', 'час', 'минута', 'неделя', 'месяц', 'вечер',
    'утро', 'зима', 'весна', 'лето', 'осень', 'холод', 'тепло', 'свет', 'тень', 'звук',
    'голос', 'музыка', 'книга', 'страница', 'письмо', 'язык', 'речь', 'мысль', 'душа', 'сердце',
    'сила', 'власть', 'право', 'закон', 'порядок', 'война', 'мир', 'правда', 'ложь', 'добро',
    'зло', 'любовь', 'дружба', 'работа', 'труд', 'дело', 'цель', 'смысл', 'ответ', 'вопрос',
    'начало', 'конец', 'результат', 'способ', 'средство', 'условие', 'возможность', 'шанс',
    'причина', 'следствие', 'вывод', 'решение', 'выбор', 'мнение', 'знание', 'опыт', 'ум',
    'память', 'внимание', 'желание', 'надежда', 'страх', 'радость', 'грусть', 'счастье',
    'отец', 'мать', 'сын', 'дочь', 'брат', 'сестра', 'муж', 'жена', 'ребёнок', 'семья',
    'друг', 'враг', 'гость', 'хозяин', 'учитель', 'ученик', 'врач', 'больной', 'писатель',
    'читатель', 'художник', 'музыкант', 'учёный', 'инженер', 'рабочий', 'крестьянин',
    'поле', 'лес', 'река', 'море', 'гора', 'долина', 'остров', 'берег', 'небо', 'звезда',
    'птица', 'зверь', 'рыба', 'дерево', 'цветок', 'трава', 'камень', 'песок', 'металл',
    'хлеб', 'вода', 'молоко', 'мясо', 'фрукт', 'овощ', 'чай', 'кофе', 'сахар', 'соль',
    'стол', 'стул', 'кровать', 'окно', 'комната', 'кухня', 'ванна', 'двор', 'сад',
    'школа', 'университет', 'больница', 'магазин', 'банк', 'офис', 'завод', 'фабрика',
    'идти', 'бежать', 'сидеть', 'стоять', 'лежать', 'спать', 'есть', 'пить', 'читать',
    'писать', 'думать', 'знать', 'видеть', 'слышать', 'говорить', 'понимать', 'помнить',
    'хотеть', 'мочь', 'должен', 'нужно', 'можно', 'нельзя', 'надо', 'пора', 'пора',
    'здесь', 'там', 'тут', 'везде', 'нигде', 'иногда', 'всегда', 'часто', 'редко', 'скоро',
    'потом', 'сначала', 'теперь', 'уже', 'ещё', 'только', 'даже', 'лишь', 'просто', 'точно',
    'почти', 'совсем', 'полностью', 'частично', 'много', 'мало', 'несколько', 'больше', 'меньше',
    'хороший', 'плохой', 'новый', 'старый', 'большой', 'маленький', 'длинный', 'короткий',
    'высокий', 'низкий', 'широкий', 'узкий', 'толстый', 'тонкий', 'тяжёлый', 'лёгкий',
    'быстрый', 'медленный', 'горячий', 'холодный', 'тёплый', 'светлый', 'тёмный', 'яркий',
    'тихий', 'громкий', 'мягкий', 'твёрдый', 'острый', 'тупой', 'гладкий', 'шершавый',
    'красивый', 'уродливый', 'умный', 'глупый', 'добрый', 'злой', 'честный', 'лживый',
    'богатый', 'бедный', 'сильный', 'слабый', 'здоровый', 'больной', 'молодой', 'старый',
    'живой', 'мёртвый', 'свободный', 'занятой', 'готовый', 'пустой', 'полный', 'открытый',
    'закрытый', 'правый', 'левый', 'верхний', 'нижний', 'внешний', 'внутренний', 'передний',
    'задний', 'последний', 'следующий', 'текущий', 'прошлый', 'будущий', 'настоящий',
]

# English words for typing test
REAL_WORDS_EN = [
    'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it', 'for', 'not', 'on', 'with',
    'he', 'as', 'you', 'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
    'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what', 'so', 'up', 'out', 'if',
    'about', 'who', 'get', 'which', 'go', 'me', 'when', 'make', 'can', 'like', 'time', 'no', 'just',
    'him', 'know', 'take', 'people', 'into', 'year', 'your', 'good', 'some', 'could', 'them', 'see',
    'other', 'than', 'then', 'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also', 'back',
    'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well', 'way', 'even', 'new', 'want', 'because',
    'any', 'these', 'give', 'day', 'most', 'us', 'is', 'was', 'are', 'were', 'been', 'has', 'had', 'did',
    'word', 'world', 'right', 'find', 'long', 'down', 'own', 'part', 'place', 'same', 'number', 'live',
    'where', 'before', 'mean', 'old', 'high', 'such', 'follow', 'change', 'light', 'kind', 'need', 'house',
    'picture', 'try', 'again', 'line', 'different', 'turn', 'cause', 'same', 'show', 'every', 'small',
    'three', 'set', 'put', 'end', 'does', 'another', 'well', 'large', 'must', 'big', 'through', 'here',
    'while', 'where', 'much', 'before', 'right', 'means', 'still', 'last', 'never', 'left', 'call',
    'each', 'thing', 'may', 'many', 'after', 'water', 'life', 'hand', 'sound', 'point', 'letter', 'form',
]

# Russian syllables for procedural generation
SYLLABLES = [
    'ба', 'бе', 'би', 'бо', 'бу', 'бы', 'ва', 'ве', 'ви', 'во', 'ву', 'вы',
    'га', 'ге', 'ги', 'го', 'гу', 'да', 'де', 'ди', 'до', 'ду', 'ды',
    'жа', 'же', 'жи', 'жо', 'жу', 'за', 'зе', 'зи', 'зо', 'зу', 'зы',
    'ка', 'ке', 'ки', 'ко', 'ку', 'ла', 'ле', 'ли', 'ло', 'лу', 'лы',
    'ма', 'ме', 'ми', 'мо', 'му', 'мы', 'на', 'не', 'ни', 'но', 'ну', 'ны',
    'па', 'пе', 'пи', 'по', 'пу', 'пы', 'ра', 'ре', 'ри', 'ро', 'ру', 'ры',
    'са', 'се', 'си', 'со', 'су', 'сы', 'та', 'те', 'ти', 'то', 'ту', 'ты',
    'фа', 'фе', 'фи', 'фо', 'ху', 'ца', 'це', 'ча', 'че', 'чи', 'чу',
    'ша', 'ше', 'ши', 'шо', 'шу', 'ща', 'ще', 'щи', 'ща', 'это', 'я',
]

SYLLABLES_EN = [
    'ba', 'be', 'bi', 'bo', 'bu', 'ca', 'ce', 'ci', 'co', 'cu', 'da', 'de', 'di', 'do', 'du',
    'fa', 'fe', 'fi', 'fo', 'fu', 'ga', 'ge', 'gi', 'go', 'gu', 'ha', 'he', 'hi', 'ho', 'hu',
    'ka', 'ke', 'ki', 'ko', 'ku', 'la', 'le', 'li', 'lo', 'lu', 'ma', 'me', 'mi', 'mo', 'mu',
    'na', 'ne', 'ni', 'no', 'nu', 'pa', 'pe', 'pi', 'po', 'pu', 'ra', 're', 'ri', 'ro', 'ru',
    'sa', 'se', 'si', 'so', 'su', 'ta', 'te', 'ti', 'to', 'tu', 'wa', 'we', 'wi', 'wo', 'za', 'ze', 'zi', 'zo', 'zu',
]


def generate_real_words(count=45, lang='ru'):
    """Осмысленные слова (ru или en)."""
    word_list = REAL_WORDS_EN if lang == 'en' else REAL_WORDS
    count = min(count, len(word_list)) if count <= len(word_list) else count
    if count <= len(word_list):
        return random.sample(word_list, count)
    return random.choices(word_list, k=count)


def generate_via_model(count=45, train_words=None, lang='ru'):
    """Генерация слов локальной моделью. lang: 'ru' | 'en'."""
    path = get_model_path(lang)
    probs = load_model(path)
    if probs is None:
        words_for_train = train_words or (REAL_WORDS_EN if lang == 'en' else REAL_WORDS)
        probs = model_train(words_for_train)
        save_model(probs, path)
    result = generate_words_from_model(probs, count)
    if len(result) < count:
        result.extend(generate_real_words(count - len(result), lang))
    return result[:count]


def generate_syllable_words(count=45, min_syllables=2, max_syllables=4, lang='ru'):
    """Псевдослова из слогов (ru или en)."""
    syll = SYLLABLES_EN if lang == 'en' else SYLLABLES
    words = []
    for _ in range(count):
        n = random.randint(min_syllables, max_syllables)
        words.append(''.join(random.choices(syll, k=n)))
    return words


def generate_words(count=45, generator='words', lang='ru'):
    """Единая точка входа. lang: 'ru' | 'en'."""
    count = max(10, min(100, int(count)))
    if generator == 'words':
        return generate_real_words(count, lang)
    if generator == 'model':
        return generate_via_model(count, lang=lang)
    return generate_syllable_words(count, lang=lang)


def ensure_model_trained():
    """Обучает модели при старте, если файлы ещё не созданы."""
    for lang in ('ru', 'en'):
        if load_model(get_model_path(lang)) is None:
            generate_via_model(1, lang=lang)

# -*- coding: utf-8 -*-
import os
from datetime import datetime
from urllib.parse import urlencode
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from word_generator import generate_words, ensure_model_trained

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')

# БД: TIPTYP_DATA для Docker (volume), иначе — папка проекта
_basedir = os.path.abspath(os.path.dirname(__file__))
_data_dir = os.environ.get('TIPTYP_DATA', _basedir)
_db_path = os.path.join(_data_dir, 'tiptyp.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + _db_path.replace('\\', '/')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Хеширование паролей: только хеш хранится в БД, пароль в открытом виде нигде не сохраняется
PASSWORD_HASH_METHOD = 'pbkdf2:sha256:600000'
PASSWORD_SALT_LENGTH = 16

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Войдите, чтобы видеть эту страницу.'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)  # только хеш, не пароль
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    results = db.relationship('TypingResult', backref='user', lazy='dynamic')

    def set_password(self, password):
        """Сохраняет только хеш пароля. Пароль в открытом виде в БД не попадает."""
        self.password_hash = generate_password_hash(
            password,
            method=PASSWORD_HASH_METHOD,
            salt_length=PASSWORD_SALT_LENGTH,
        )

    def check_password(self, password):
        """Проверка пароля по сохранённому хешу."""
        return check_password_hash(self.password_hash, password)


class TypingResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # null = гость
    wpm = db.Column(db.Float, nullable=False)           # слов в минуту
    accuracy = db.Column(db.Float, nullable=False)      # точность %
    time_seconds = db.Column(db.Integer, nullable=False)
    chars_typed = db.Column(db.Integer, nullable=False)
    chars_correct = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.context_processor
def inject_lang():
    lang = request.args.get('lang', 'ru') if request else 'ru'
    if not request:
        return {'lang': lang, 'url_lang_ru': '/?lang=ru', 'url_lang_en': '/?lang=en'}
    args = request.args.to_dict(flat=True)
    args_ru = {**args, 'lang': 'ru'}
    args_en = {**args, 'lang': 'en'}
    url_lang_ru = request.path + '?' + urlencode(args_ru)
    url_lang_en = request.path + '?' + urlencode(args_en)
    return {'lang': lang, 'url_lang_ru': url_lang_ru, 'url_lang_en': url_lang_en}


@app.route('/')
def index():
    return render_template('index.html')


def _redirect_with_lang(target=None):
    """Редирект на target или на главную с сохранением текущего языка."""
    lang = request.args.get('lang', 'ru')
    if not target or target in ('/', url_for('index')):
        return redirect(url_for('index', lang=lang))
    sep = '&' if '?' in target else '?'
    return redirect(target + sep + urlencode({'lang': lang}))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return _redirect_with_lang(url_for('index'))
    lang = request.args.get('lang', 'ru')
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('You are logged in.' if lang == 'en' else 'Вы вошли в систему.', 'success')
            next_page = request.args.get('next') or url_for('index')
            return _redirect_with_lang(next_page)
        flash('Invalid username or password.' if lang == 'en' else 'Неверный логин или пароль.', 'error')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return _redirect_with_lang(url_for('index'))
    lang = request.args.get('lang', 'ru')
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not username or len(username) < 2:
            flash('Username must be at least 2 characters.' if lang == 'en' else 'Логин должен быть не короче 2 символов.', 'error')
            return render_template('register.html')
        if not password or len(password) < 4:
            flash('Password must be at least 4 characters.' if lang == 'en' else 'Пароль должен быть не короче 4 символов.', 'error')
            return render_template('register.html')
        if User.query.filter_by(username=username).first():
            flash('This username is already taken.' if lang == 'en' else 'Такой пользователь уже есть.', 'error')
            return render_template('register.html')
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Registration successful.' if lang == 'en' else 'Регистрация прошла успешно.', 'success')
        return _redirect_with_lang(url_for('index'))
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    lang = request.args.get('lang', 'ru')
    flash('You have been logged out.' if lang == 'en' else 'Вы вышли из системы.', 'info')
    return _redirect_with_lang(url_for('index'))


@app.route('/stats')
@login_required
def stats():
    return render_template('stats.html')


@app.route('/themes')
def themes():
    return render_template('themes.html')


@app.route('/api/save_result', methods=['POST'])
def save_result():
    data = request.get_json() or {}
    wpm = data.get('wpm')
    accuracy = data.get('accuracy')
    time_seconds = data.get('time_seconds')
    chars_typed = data.get('chars_typed')
    chars_correct = data.get('chars_correct')
    if wpm is None or accuracy is None or time_seconds is None:
        return jsonify({'ok': False, 'error': 'Не хватает данных'}), 400
    r = TypingResult(
        user_id=current_user.id if current_user.is_authenticated else None,
        wpm=float(wpm),
        accuracy=float(accuracy),
        time_seconds=int(time_seconds),
        chars_typed=int(chars_typed or 0),
        chars_correct=int(chars_correct or 0),
    )
    db.session.add(r)
    db.session.commit()
    return jsonify({'ok': True, 'id': r.id})


@app.route('/api/words')
def api_words():
    """Генерация слов для теста. ?count=45&generator=words|model|syllable&lang=ru|en"""
    count = request.args.get('count', 45, type=int)
    generator = request.args.get('generator', 'words')
    lang = request.args.get('lang', 'ru')
    if generator not in ('words', 'model', 'syllable'):
        generator = 'words'
    if lang not in ('ru', 'en'):
        lang = 'ru'
    try:
        words = generate_words(count=count, generator=generator, lang=lang)
        return jsonify({'words': words, 'generator': generator, 'lang': lang})
    except Exception as e:
        return jsonify({'error': str(e), 'words': []}), 503


@app.route('/api/my_stats')
def my_stats():
    if not current_user.is_authenticated:
        return jsonify({'results': [], 'best_wpm': None, 'avg_wpm': None, 'total_tests': 0})
    results = TypingResult.query.filter_by(user_id=current_user.id).order_by(TypingResult.created_at.desc()).limit(50).all()
    arr = [{
        'id': r.id,
        'wpm': r.wpm,
        'accuracy': r.accuracy,
        'time_seconds': r.time_seconds,
        'created_at': r.created_at.isoformat() if r.created_at else None,
    } for r in results]
    wpm_list = [r.wpm for r in results]
    return jsonify({
        'results': arr,
        'best_wpm': max(wpm_list) if wpm_list else None,
        'avg_wpm': round(sum(wpm_list) / len(wpm_list), 1) if wpm_list else None,
        'total_tests': TypingResult.query.filter_by(user_id=current_user.id).count(),
    })


with app.app_context():
    db.create_all()
    ensure_model_trained()


if __name__ == '__main__':
    app.run(debug=True, port=5000)

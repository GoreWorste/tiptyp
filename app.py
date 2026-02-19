# -*- coding: utf-8 -*-
import os
import logging
from datetime import datetime
from urllib.parse import urlencode
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import re

from word_generator import generate_words, ensure_model_trained
from sqlalchemy import text, func
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')

# Логи: одна строка на событие, понятный формат для отслеживания
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
)
log = logging.getLogger(__name__)
# Убираем дублирующий вывод запросов от Werkzeug
logging.getLogger('werkzeug').setLevel(logging.WARNING)


def _log_time():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def _client_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr or '?').split(',')[0].strip()

# БД: TIPTYP_DATA для Docker (volume), иначе — папка проекта
_basedir = os.path.abspath(os.path.dirname(__file__))
_data_dir = os.environ.get('TIPTYP_DATA', _basedir)
_db_path = os.path.join(_data_dir, 'tiptyp.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + _db_path.replace('\\', '/')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Загрузки: аватарки в data/avatars
_avatars_dir = os.path.join(_data_dir, 'avatars')
os.makedirs(_avatars_dir, exist_ok=True)
app.config['UPLOAD_FOLDER'] = _avatars_dir
app.config['MAX_AVATAR_SIZE'] = 2 * 1024 * 1024  # 2 MB
ALLOWED_AVATAR_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Хеширование паролей: только хеш хранится в БД, пароль в открытом виде нигде не сохраняется
PASSWORD_HASH_METHOD = 'pbkdf2:sha256:600000'
PASSWORD_SALT_LENGTH = 16

db = SQLAlchemy(app)
login_manager = LoginManager(app)


@app.after_request
def log_request(response):
    """Один понятный лог на запрос: тип, метод, путь, статус, IP. Статика — только при DEBUG."""
    ip = _client_ip()
    path = request.path or '/'
    if path.startswith('/static/'):
        kind = 'static'
    elif path.startswith('/api/'):
        kind = 'api'
    elif request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        kind = 'xhr'
    else:
        kind = 'page'
    msg = '%s | %-6s | %s %s %s | %s' % (_log_time(), kind.upper(), request.method, path, response.status_code, ip)
    if kind == 'static':
        log.debug(msg)
    else:
        log.info(msg)
    return response


login_manager.login_view = 'login'
login_manager.login_message = 'Войдите, чтобы видеть эту страницу.'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)  # только хеш, не пароль
    display_name = db.Column(db.String(80), nullable=True)   # никнейм для отображения
    avatar = db.Column(db.String(120), nullable=True)         # имя файла аватарки в uploads
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    results = db.relationship('TypingResult', backref='user', lazy='dynamic')

    @property
    def display(self):
        """Имя для отображения: никнейм или логин."""
        return (self.display_name or self.username or '').strip() or self.username

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


# Метка сборки: при обновлении кода на хосте меняется — по ней видно, что отдаётся новая версия
BUILD_ID = os.environ.get('TIPTYP_BUILD_ID', 'dev')


def _static_version():
    """Версия статики по времени изменения app.js — браузер не кэширует старые файлы после обновления."""
    try:
        path = os.path.join(app.root_path, 'static', 'app.js')
        return str(int(os.path.getmtime(path))) if os.path.isfile(path) else '0'
    except Exception:
        return '0'


@app.context_processor
def inject_lang():
    lang = request.args.get('lang', 'ru') if request else 'ru'
    if not request:
        return {'lang': lang, 'url_lang_ru': '/?lang=ru', 'url_lang_en': '/?lang=en', 'static_version': _static_version(), 'build_id': BUILD_ID}
    args = request.args.to_dict(flat=True)
    args_ru = {**args, 'lang': 'ru'}
    args_en = {**args, 'lang': 'en'}
    url_lang_ru = request.path + '?' + urlencode(args_ru)
    url_lang_en = request.path + '?' + urlencode(args_en)
    return {'lang': lang, 'url_lang_ru': url_lang_ru, 'url_lang_en': url_lang_en, 'static_version': _static_version(), 'build_id': BUILD_ID}


@app.after_request
def disable_html_cache(response):
    """Отключаем кэш HTML, чтобы по туннелю (localhost.run и т.п.) всегда отдавалась свежая версия."""
    if response.content_type and 'text/html' in response.content_type:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
    return response


@app.route('/')
def index():
    return render_template('index.html')


def _normalize_username_for_check(name):
    """Нормализация логина для проверки уникальности (без учёта регистра)."""
    return (name or '').strip().lower()


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return _redirect_with_lang(url_for('index'))
    lang = request.args.get('lang', 'ru')
    if request.method == 'POST':
        username_raw = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        canonical = _normalize_username_for_check(username_raw)
        user = User.query.filter(func.lower(User.username) == canonical).first() if canonical else None
        if user and user.check_password(password):
            login_user(user)
            log.info('%s | %-6s | LOGIN ok user=%s | %s', _log_time(), 'AUTH', user.username, _client_ip())
            flash('You are logged in.' if lang == 'en' else 'Вы вошли в систему.', 'success')
            next_page = request.args.get('next') or url_for('index')
            return _redirect_with_lang(next_page)
        log.info('%s | %-6s | LOGIN fail user=%s | %s', _log_time(), 'AUTH', username_raw or '(empty)', _client_ip())
        flash('Invalid username or password.' if lang == 'en' else 'Неверный логин или пароль.', 'error')
    return render_template('login.html')


def _redirect_with_lang(target=None):
    """Редирект на target или на главную с сохранением текущего языка."""
    lang = request.args.get('lang', 'ru')
    if not target or target in ('/', url_for('index')):
        return redirect(url_for('index', lang=lang))
    sep = '&' if '?' in target else '?'
    return redirect(target + sep + urlencode({'lang': lang}))


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
        if len(username) > 80:
            flash('Username is too long.' if lang == 'en' else 'Логин слишком длинный.', 'error')
            return render_template('register.html')
        if not password or len(password) < 4:
            flash('Password must be at least 4 characters.' if lang == 'en' else 'Пароль должен быть не короче 4 символов.', 'error')
            return render_template('register.html')
        canonical = _normalize_username_for_check(username)
        if User.query.filter(func.lower(User.username) == canonical).first():
            log.info('%s | %-6s | REGISTER fail user=%s (taken) | %s', _log_time(), 'AUTH', username, _client_ip())
            flash('This username is already taken.' if lang == 'en' else 'Такой логин уже занят.', 'error')
            return render_template('register.html')
        user = User(username=username[:80])
        user.set_password(password)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            log.info('%s | %-6s | REGISTER fail user=%s (integrity) | %s', _log_time(), 'AUTH', username, _client_ip())
            flash('This username is already taken.' if lang == 'en' else 'Такой логин уже занят.', 'error')
            return render_template('register.html')
        login_user(user)
        log.info('%s | %-6s | REGISTER ok user=%s | %s', _log_time(), 'AUTH', user.username, _client_ip())
        flash('Registration successful.' if lang == 'en' else 'Регистрация прошла успешно.', 'success')
        return _redirect_with_lang(url_for('index'))
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    who = current_user.username
    logout_user()
    log.info('%s | %-6s | LOGOUT user=%s | %s', _log_time(), 'AUTH', who, _client_ip())
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


def _allowed_avatar(filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return ext in ALLOWED_AVATAR_EXTENSIONS


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    lang = request.args.get('lang', 'ru')
    if request.method == 'POST':
        # Обновление никнейма
        new_name = request.form.get('display_name', '').strip()
        if len(new_name) > 80:
            flash('Display name is too long.' if lang == 'en' else 'Никнейм слишком длинный.', 'error')
        else:
            current_user.display_name = new_name if new_name else None
        # Загрузка аватарки
        if 'avatar' in request.files:
            f = request.files['avatar']
            if f and f.filename and _allowed_avatar(f.filename):
                if f.content_length and f.content_length > app.config['MAX_AVATAR_SIZE']:
                    flash('File is too large.' if lang == 'en' else 'Файл слишком большой.', 'error')
                else:
                    ext = f.filename.rsplit('.', 1)[-1].lower()
                    safe_name = 'user_%s_%s.%s' % (current_user.id, int(datetime.utcnow().timestamp()), ext)
                    path = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
                    try:
                        f.save(path)
                        if os.path.getsize(path) > app.config['MAX_AVATAR_SIZE']:
                            os.remove(path)
                            flash('File is too large.' if lang == 'en' else 'Файл слишком большой.', 'error')
                        else:
                            if current_user.avatar:
                                old_path = os.path.join(app.config['UPLOAD_FOLDER'], current_user.avatar)
                                if os.path.isfile(old_path):
                                    try:
                                        os.remove(old_path)
                                    except OSError:
                                        pass
                            current_user.avatar = safe_name
                            flash('Avatar updated.' if lang == 'en' else 'Аватар обновлён.', 'success')
                    except Exception:
                        if os.path.isfile(path):
                            try:
                                os.remove(path)
                            except OSError:
                                pass
                        flash('Failed to save avatar.' if lang == 'en' else 'Не удалось сохранить аватар.', 'error')
            elif f and f.filename:
                flash('Allowed formats: PNG, JPG, GIF, WebP.' if lang == 'en' else 'Разрешены форматы: PNG, JPG, GIF, WebP.', 'error')
        db.session.commit()
        if current_user.is_authenticated:
            log.info('%s | %-6s | PROFILE saved user=%s | %s', _log_time(), 'USER', current_user.username, _client_ip())
        return redirect(url_for('profile', lang=lang))
    return render_template('profile.html')


@app.route('/avatar/<path:filename>')
def avatar_file(filename):
    """Раздача аватарок только из нашей папки и только безопасное имя."""
    if not filename or not re.match(r'^user_\d+_\d+\.(png|jpg|jpeg|gif|webp)$', filename):
        return '', 404
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


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
    user_id = current_user.id if current_user.is_authenticated else None
    log.info('%s | %-6s | RESULT saved id=%s user_id=%s wpm=%s acc=%s%% | %s',
             _log_time(), 'USER', r.id, user_id, r.wpm, round(r.accuracy, 1), _client_ip())
    return jsonify({'ok': True, 'id': r.id})


@app.route('/api/words')
def api_words():
    """Генерация слов для теста. ?count=45&generator=words|model|syllable&lang=ru|en, count 1–10000"""
    count = request.args.get('count', 45, type=int)
    count = max(1, min(10000, count))
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


def _ensure_profile_columns():
    """Добавить колонки профиля в существующую таблицу user, если их ещё нет."""
    with db.engine.connect() as conn:
        try:
            conn.execute(text('ALTER TABLE user ADD COLUMN display_name VARCHAR(80)'))
            conn.commit()
        except Exception:
            conn.rollback()
        try:
            conn.execute(text('ALTER TABLE user ADD COLUMN avatar VARCHAR(120)'))
            conn.commit()
        except Exception:
            conn.rollback()


with app.app_context():
    db.create_all()
    _ensure_profile_columns()
    ensure_model_trained()


if __name__ == '__main__':
    log.info('%s | %-6s | TipTyp starting on http://127.0.0.1:5000', _log_time(), 'APP')
    app.run(debug=True, port=5000)

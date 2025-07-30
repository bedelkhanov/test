"""
Flask‑сервер для Telegram Mini App.

Этот сервер реализует три основные части:

* **Мини‑приложение** (`/mini-app`): HTML‑страница с интерфейсом для пользователей.
  С помощью Telegram Web App SDK страница загружает список рубрик и роликов через
  API (`/api/categories` и `/api/videos/<id>`) и отображает контент. По клику
  на ролик показывается видеоплеер и текстовый разбор.

* **Админ‑панель** (`/admin`): защищённый паролем раздел, где администратор
  может добавлять категории и загружать ролики. Файлы сохраняются в папку
  `static/uploads`, а информация записывается в базу данных.

* **API** (`/api/...`): маршруты, возвращающие JSON с данными для мини‑приложения.

Чтобы запустить сервер, убедитесь, что установлены зависимости из
`requirements.txt`. Перед запуском создайте файл `.env` со следующими
переменными:

```
TELEGRAM_BOT_TOKEN=<ваш токен бота>
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<пароль для админки>
WEB_APP_URL=https://example.com
SECRET_KEY=<случайная строка>
```

Компонент бота (`bot.py`) использует `WEB_APP_URL` для формирования кнопки,
открывающей мини‑приложение в Телеграме.
"""
from __future__ import annotations

import os
from pathlib import Path
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    send_from_directory,
    abort,
)
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from models import db, Category, VideoContent

# Загружаем переменные из .env, если файл существует
load_dotenv()

# Создаём приложение Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = str(Path(__file__).parent / 'static' / 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 500  # максимальный размер файла 500 МБ

# Секретный ключ для сессий
app.secret_key = os.environ.get('SECRET_KEY', 'changeme')

# Инициализируем базу данных
db.init_app(app)


def ensure_upload_folder() -> None:
    """Создаёт каталог для загрузок, если его нет."""
    upload_dir = Path(app.config['UPLOAD_FOLDER'])
    upload_dir.mkdir(parents=True, exist_ok=True)


@app.before_first_request
def _setup_db() -> None:
    """Создаём таблицы, если они ещё не созданы."""
    ensure_upload_folder()
    db.create_all()


# ------------------------ Админка ------------------------

def check_auth(username: str, password: str) -> bool:
    """Проверяет, соответствует ли введённая пара логин/пароль переменным окружения."""
    return (
        username == os.environ.get('ADMIN_USERNAME', 'admin')
        and password == os.environ.get('ADMIN_PASSWORD', 'admin')
    )


def login_required(func):  # type: ignore[override]
    """Декоратор для маршрутов, требующих авторизации."""

    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('admin_login'))
        return func(*args, **kwargs)

    return wrapper


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Страница входа в админку."""
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if check_auth(username, password):
            session['logged_in'] = True
            return redirect(url_for('admin_index'))
        error = 'Неверный логин или пароль'
    return render_template('login.html', error=error)


@app.route('/admin/logout')
def admin_logout():
    """Выход из админки."""
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_index():
    """Главная страница админки: отображает список рубрик и роликов, предоставляет формы для создания."""
    categories = Category.query.order_by(Category.name).all()
    videos = VideoContent.query.order_by(VideoContent.id.desc()).all()
    return render_template('admin.html', categories=categories, videos=videos)


@app.route('/admin/add_category', methods=['POST'])
@login_required
def admin_add_category():
    """Обработчик создания новой рубрики."""
    name = request.form.get('name', '').strip()
    if not name:
        return redirect(url_for('admin_index'))
    # Проверяем, что такая рубрика ещё не существует
    if Category.query.filter_by(name=name).first() is None:
        category = Category(name=name)
        db.session.add(category)
        db.session.commit()
    return redirect(url_for('admin_index'))


@app.route('/admin/add_video', methods=['POST'])
@login_required
def admin_add_video():
    """Обработчик загрузки нового видеоролика."""
    title = request.form.get('title', '').strip()
    analysis = request.form.get('analysis', '').strip()
    category_id = request.form.get('category_id')
    file = request.files.get('video_file')
    if not title or not file or not category_id:
        return redirect(url_for('admin_index'))
    # Проверяем существование рубрики
    try:
        category_id_int = int(category_id)
    except (TypeError, ValueError):
        return redirect(url_for('admin_index'))
    category = Category.query.get(category_id_int)
    if category is None:
        return redirect(url_for('admin_index'))
    # Сохраняем файл
    filename = secure_filename(file.filename)
    save_path = Path(app.config['UPLOAD_FOLDER']) / filename
    # Если файл с таким именем уже существует, дополняем имя
    counter = 1
    original_name = filename.rsplit('.', 1)
    while save_path.exists():
        name_part = original_name[0]
        ext = original_name[1] if len(original_name) > 1 else ''
        filename = f"{name_part}_{counter}.{ext}" if ext else f"{name_part}_{counter}"
        save_path = Path(app.config['UPLOAD_FOLDER']) / filename
        counter += 1
    file.save(save_path)
    # Создаём запись в базе
    video = VideoContent(
        title=title,
        video_filename=filename,
        analysis=analysis,
        category=category,
    )
    db.session.add(video)
    db.session.commit()
    return redirect(url_for('admin_index'))


@app.route('/uploads/<path:filename>')
def uploaded_file(filename: str):
    """Маршрут для отдачи загруженных файлов."""
    upload_dir = Path(app.config['UPLOAD_FOLDER'])
    return send_from_directory(upload_dir, filename, as_attachment=False)


# ------------------------ API ------------------------

@app.route('/api/categories')
def api_categories():
    """Возвращает список рубрик в JSON."""
    categories = Category.query.order_by(Category.name).all()
    data = [
        {
            'id': c.id,
            'name': c.name,
        }
        for c in categories
    ]
    return jsonify(data)


@app.route('/api/videos/<int:category_id>')
def api_videos_by_category(category_id: int):
    """Возвращает список видеороликов для указанной рубрики."""
    category = Category.query.get_or_404(category_id)
    videos = VideoContent.query.filter_by(category_id=category.id).order_by(VideoContent.id.desc()).all()
    data = [
        {
            'id': v.id,
            'title': v.title,
        }
        for v in videos
    ]
    return jsonify(data)


@app.route('/api/video/<int:video_id>')
def api_video_details(video_id: int):
    """Возвращает подробности ролика: имя файла, заголовок, анализ."""
    video = VideoContent.query.get_or_404(video_id)
    # Формируем полный URL к видео
    base_url = request.host_url.rstrip('/')
    video_url = url_for('uploaded_file', filename=video.video_filename, _external=True)
    return jsonify(
        {
            'id': video.id,
            'title': video.title,
            'video_url': video_url,
            'analysis': video.analysis or '',
        }
    )


# ------------------------ Мини‑приложение ------------------------

@app.route('/mini-app')
def mini_app():
    """Отдаёт HTML‑страницу мини‑приложения."""
    return render_template('mini_app.html')


# Главная страница может перенаправлять на документацию или мини‑приложение
@app.route('/')
def index():
    return redirect(url_for('mini_app'))


if __name__ == '__main__':
    # Запускаем сервер для разработки
    # В production рекомендуется использовать Gunicorn или Uvicorn
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
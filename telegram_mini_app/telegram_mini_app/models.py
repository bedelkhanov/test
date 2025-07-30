"""
Модели базы данных для мини‑приложения.

Используется SQLAlchemy, подключённый в приложении Flask. Определены две
основные таблицы:

* `Category` — справочник рубрик. Имеет уникальное имя.
* `VideoContent` — информация о видеороликах: название, имя файла,
  текстовый анализ и внешние ключ к рубрике.

При необходимости можно расширить модели: добавить дату публикации, статус
видимости и т.д.
"""
from __future__ import annotations

from flask_sqlalchemy import SQLAlchemy

# Инициализируем объект базы без привязки к приложению.
db = SQLAlchemy()


class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Category id={self.id} name={self.name}>"


class VideoContent(db.Model):
    __tablename__ = 'video_content'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    video_filename = db.Column(db.String(200), nullable=False)
    analysis = db.Column(db.Text, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)

    # Отношение с Category. Через backref можно получить список videos.
    category = db.relationship('Category', backref=db.backref('videos', lazy=True))

    def __repr__(self) -> str:
        return f"<VideoContent id={self.id} title={self.title}>"
from app.database import db
from datetime import datetime


class TelegramUser(db.Model):
    __tablename__ = 'telegram_user'

    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.BigInteger, unique=True, nullable=False)
    username = db.Column(db.Text)
    full_name = db.Column(db.Text)
    is_authorized = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Task(db.Model):
    __tablename__ = 'task'

    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.Text, nullable=False)
    time = db.Column(db.DateTime, nullable=False)
    deadline = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.Text, default='Не выполнено')


class Birthday(db.Model):
    __tablename__ = 'birthday'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    day = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=True)
    group = db.Column(db.Text, nullable=True)


class Holiday(db.Model):
    __tablename__ = 'holiday'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    day = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=True)
    group = db.Column(db.Text, nullable=True)


class Purchase(db.Model):
    __tablename__ = 'purchase'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    size = db.Column(db.Text, nullable=True)
    quantity = db.Column(db.Integer, nullable=True)

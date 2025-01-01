from app.database import db


class Task(db.Model):
    __tablename__ = 'task'

    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.Text, nullable=False)
    time = db.Column(db.Text, nullable=False)
    status = db.Column(db.Text, default='Не выполнено')


class Birthday(db.Model):
    __tablename__ = 'birthday'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    day = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=True)


class Holiday(db.Model):
    __tablename__ = 'holiday'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    day = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=True)

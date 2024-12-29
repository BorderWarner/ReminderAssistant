from flask import Flask, render_template
from .database import db
from config import Config
from app.holAndBirth.routes import holAndBirth_bp
from app.weather.routes import weather_bp, get_weather
from app.toDo.routes import toDo_bp
from app.shoppList.routes import shoppList_bp
from datetime import datetime, date
from app.models import Task, Birthday, Holiday
from app.base_socket import socketio


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    socketio.init_app(app)

    db.init_app(app)
    with app.app_context():
        db.create_all()

    app.register_blueprint(holAndBirth_bp)
    app.register_blueprint(weather_bp)
    app.register_blueprint(toDo_bp)
    app.register_blueprint(shoppList_bp)

    @app.route('/')
    def index():
        weather = get_weather()
        current_time = datetime.now().strftime('%H:%M:%S')
        tasks = Task.query.order_by(Task.time).all()
        current_date = date.today()
        nearest_birthdays = Birthday.query.filter(
            db.extract('month', Birthday.month) == current_date.month
        ).all()

        nearest_holidays = Holiday.query.filter(
            db.extract('month', Holiday.month) == current_date.month
        ).all()
        return render_template(
            'index.html',
            weather=weather,
            time=current_time,
            tasks=tasks,
            birthdays=nearest_birthdays,
            holidays=nearest_holidays
        )

    return app

from flask import Flask, render_template
from .database import db
from config import Config
from app.holAndBirth.routes import holAndBirth_bp, init_socketio_hab
from app.weather.routes import weather_bp, init_socketio_weather
from app.toDo.routes import toDo_bp, init_socketio_todo
from app.shoppList.routes import shoppList_bp, init_socketio_shopplist
from app.models import Task, Birthday, Holiday
from flask_socketio import SocketIO
from app.base_socket import init_socketio_base
from flask_apscheduler import APScheduler


socketio = SocketIO()
scheduler = APScheduler()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    socketio.init_app(app)

    scheduler.init_app(app)

    db.init_app(app)
    with app.app_context():
        db.create_all()

    init_socketio_hab(app)
    init_socketio_weather(app)
    init_socketio_todo(app)
    init_socketio_shopplist(app)
    init_socketio_base(app)

    app.register_blueprint(holAndBirth_bp)
    app.register_blueprint(weather_bp)
    app.register_blueprint(toDo_bp)
    app.register_blueprint(shoppList_bp)

    @app.route('/')
    def index():
        return render_template('index.html')

    return app

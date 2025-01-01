from flask import Blueprint
from flask import (
    render_template,
    jsonify,
    request,
    redirect,
    url_for,
)
from app.database import db
from config import ConfigOWM
from app.weather.func import get_forecast_weather, get_current_weather

weather_bp = Blueprint('weather', __name__)


@weather_bp.route('/weather')
def weather():
    return render_template('1.html')


def init_socketio_weather(app):
    from app import socketio

    @socketio.on('get_weather')
    def get_weather():
        try:
            weather_data = {
                'hourly': get_forecast_weather(),
                'current': get_current_weather()
            }
            socketio.emit('weather_update', weather_data)
        except Exception as e:
            socketio.emit('error', f"Ошибка: {e}")

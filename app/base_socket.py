from datetime import datetime
from app.weather.func import get_current_weather, get_forecast_weather
from babel.dates import format_datetime


def init_socketio_base(app):
    from app import socketio

    @socketio.on('connect')
    def handle_connect():
        print("Client connected")

    @socketio.on('disconnect')
    def handle_disconnect():
        print("Client disconnected")

    @socketio.on('get_time')
    def get_time():
        try:
            now = datetime.now()
            current_time = now.strftime('%H:%M:%S')
            formatted_date = format_datetime(now, "EEEE, d MMMM", locale="ru")
            result = {'current_time': current_time,
                      'formatted_date': formatted_date}
            socketio.emit('time_update', result)
        except Exception as e:
            socketio.emit('error', f"Ошибка: {e}")

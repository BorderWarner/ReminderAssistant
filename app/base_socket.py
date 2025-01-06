from datetime import datetime
from app.weather.func import get_current_weather, get_forecast_weather
from babel.dates import format_datetime
from flask import send_from_directory
import os


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

    TEMP_FOLDER = "temp_audio"
    os.makedirs(TEMP_FOLDER, exist_ok=True)

    @app.route('/temp_audio/<filename>')
    def serve_audio(filename):
        print(filename)
        return send_from_directory(TEMP_FOLDER, filename)

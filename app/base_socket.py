from datetime import datetime
from app.weather.func import get_current_weather, get_forecast_weather


def init_socketio_base(app):
    from app import socketio
    from app import scheduler

    def background_time_update():
        current_time = datetime.now().strftime('%H:%M:%S')
        socketio.emit('time_update', current_time)

    @socketio.on('connect')
    def handle_connect():
        scheduler.add_job(
            id='update_time',
            func=background_time_update,
            trigger='interval',
            seconds=1,
            replace_existing=True
        )

        def update_weather_task():
            try:
                weather_data = {
                    'hourly': get_forecast_weather(),
                    'current': get_current_weather()
                }
                socketio.emit('weather_update', weather_data)
            except Exception as e:
                socketio.emit('error', f"Ошибка обновления погоды: {e}")
        scheduler.add_job(
            id='update_weather',
            func=update_weather_task,
            trigger='interval',
            hours=1,
            replace_existing=True
        )
        print("Client connected")

    @socketio.on('disconnect')
    def handle_disconnect():
        print("Client disconnected")

    @socketio.on('get_time')
    def get_time():
        try:
            current_time = datetime.now().strftime('%H:%M:%S')
            socketio.emit('time_update', current_time)
        except Exception as e:
            socketio.emit('error', f"Ошибка: {e}")

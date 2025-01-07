from datetime import datetime
from app.weather.func import get_current_weather, get_forecast_weather
from babel.dates import format_datetime
from app.holAndBirth.func import get_birthdays_for, get_holidays_for


def start_scheduler_task(app, socketio, scheduler):

    def background_time_update():
        try:
            with app.app_context():
                now = datetime.now()
                current_time = now.strftime('%H:%M:%S')
                formatted_date = format_datetime(now, "EEEE, d MMMM", locale="ru")
                result = {'current_time': current_time,
                          'formatted_date': formatted_date}
                socketio.emit('time_update', result)
        except Exception as e:
            print(f'Error scheduler time_update: {e}')

    scheduler.add_job(
        id='update_time',
        func=background_time_update,
        trigger='interval',
        seconds=1,
        replace_existing=True
    )

    def update_weather_task():
        try:
            with app.app_context():
                weather_data = {
                    'hourly': get_forecast_weather(),
                    'current': get_current_weather()
                }
                socketio.emit('weather_update', weather_data)
        except Exception as e:
            print(f'Error scheduler weather_update: {e}')

    scheduler.add_job(
        id='update_weather',
        func=update_weather_task,
        trigger='interval',
        hours=1,
        replace_existing=True
    )

    def update_birthdays_task():
        try:
            with app.app_context():
                print(f'birthdays_update_at_{datetime.now()}')
                socketio.emit('birthdays_update', get_birthdays_for(days=30, limit=10))
        except Exception as e:
            print(f'Error scheduler birthdays_update: {e}')

    scheduler.add_job(
        id='update_birthdays',
        func=update_birthdays_task,
        trigger='cron',
        hour=0,
        minute=0,
        second=1,
        replace_existing=True
    )

    def update_holidays_task():
        try:
            with app.app_context():
                print(f'holidays_update_at_{datetime.now()}')
                socketio.emit('holidays_update', get_holidays_for(days=30, limit=10))
        except Exception as e:
            print(f'Error scheduler holidays_update: {e}')

    scheduler.add_job(
        id='update_holidays',
        func=update_holidays_task,
        trigger='cron',
        hour=0,
        minute=0,
        second=2,
        replace_existing=True
    )

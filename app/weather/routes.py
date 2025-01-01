from flask import Blueprint
from flask import (
    render_template,
    jsonify,
    request,
    redirect,
    url_for,
)
from app.database import db
import requests
from config import ConfigOWM
from datetime import date, time, datetime
from app.base_socket import socketio

weather_bp = Blueprint('weather', __name__)


def get_weather_owm():
    try:
        url = f"http://api.openweathermap.org/data/2.5/forecast?" \
              f"q={ConfigOWM.CITY}&" \
              f"appid={ConfigOWM.WEATHER_API_KEY}&" \
              f"units=metric&lang=ru"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        if response.status_code == 200:
            data = response.json()
            forecast = {"current": None, "hourly": []}
            now = datetime.utcnow()
            today = now.date()

            for entry in data['list']:
                date_time = datetime.strptime(entry['dt_txt'], "%Y-%m-%d %H:%M:%S")
                temp = entry['main']['temp']
                description = entry['weather'][0]['description']
                icon = entry['weather'][0]['icon']
                wind_speed = entry['wind']['speed']
                humidity = entry['main']['humidity']

                forecast_entry = {
                    'time': date_time.time().strftime('%H:%M'),
                    'temp': temp,
                    'description': description,
                    'icon': f"http://openweathermap.org/img/wn/{icon}.png",
                    'wind_speed': wind_speed,
                    'humidity': humidity
                }

                if date_time.date() == today:
                    if date_time > now and forecast["current"] is None:
                        forecast["current"] = forecast_entry
                    forecast["hourly"].append(forecast_entry)

            return forecast
        return {"current": None, "hourly": []}
    except requests.exceptions.RequestException:
        return {"current": None, "hourly": []}



@weather_bp.route('/weather')
def weather():
    return render_template('1.html')


@socketio.on('get_weather')
def get_weather():
    try:
        weather = get_weather_owm()
        socketio.emit('weather_update', weather)
    except Exception as e:
        socketio.emit('error', f"Ошибка: {e}")

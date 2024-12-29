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
from datetime import datetime, date, timedelta

weather_bp = Blueprint('weather', __name__)


def get_weather():
    try:
        url = f"http://api.openweathermap.org/data/2.5/forecast?" \
              f"q={ConfigOWM.CITY}&" \
              f"appid={ConfigOWM.WEATHER_API_KEY}&" \
              f"units=metric&lang=ru"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        if response.status_code == 200:
            data = response.json()
            forecast = {"today": [], "tomorrow": []}
            today = date.today()
            tomorrow = today + timedelta(days=1)
            for entry in data['list']:
                date_time = datetime.strptime(entry['dt_txt'], "%Y-%m-%d %H:%M:%S")
                day = date_time.date()
                time = date_time.time().strftime('%H:%M')
                temp = entry['main']['temp']
                description = entry['weather'][0]['description']
                icon = entry['weather'][0]['icon']
                humidity = entry['main']['humidity']
                forecast_entry = {
                    'time': time,
                    'temp': temp,
                    'description': description,
                    'icon': f"http://openweathermap.org/img/wn/{icon}.png",
                    'humidity': humidity
                }
                if day == today:
                    forecast['today'].append(forecast_entry)
                elif day == tomorrow:
                    forecast['tomorrow'].append(forecast_entry)
            return forecast
        return {"today": [], "tomorrow": []}
    except requests.exceptions.RequestException:
        return {"today": [], "tomorrow": []}


@weather_bp.route('/weather')
def weather():
    return render_template('1.html')

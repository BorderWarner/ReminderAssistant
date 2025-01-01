from datetime import date, time, datetime
import requests
from config import ConfigOWM


def get_forecast_weather():
    try:
        url = f"https://api.openweathermap.org/data/2.5/forecast?" \
              f"q={ConfigOWM.CITY}&" \
              f"appid={ConfigOWM.WEATHER_API_KEY}&" \
              f"units=metric&lang=ru"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        if response.status_code == 200:
            data = response.json()
            forecast = []
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
                    'icon': f"https://openweathermap.org/img/wn/{icon}.png",
                    'wind_speed': wind_speed,
                    'humidity': humidity
                }

                if len(forecast) < 8:
                    forecast.append(forecast_entry)

                # if date_time.date() == today:
                #     forecast.append(forecast_entry)

            return forecast
        return []
    except requests.exceptions.RequestException:
        return []


def get_current_weather():
    url = f"https://api.openweathermap.org/data/2.5/weather?" \
          f"q={ConfigOWM.CITY}&" \
          f"appid={ConfigOWM.WEATHER_API_KEY}&" \
          f"units=metric&lang=ru"
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    if response.status_code == 200:
        data = response.json()

        temp = data['main']['temp']
        description = data['weather'][0]['description']
        icon = data['weather'][0]['icon']
        wind_speed = data['wind']['speed']
        humidity = data['main']['humidity']

        current_weather = {
            'temp': temp,
            'description': description,
            'icon': f"https://openweathermap.org/img/wn/{icon}.png",
            'wind_speed': wind_speed,
            'humidity': humidity
        }

        return current_weather
    return None
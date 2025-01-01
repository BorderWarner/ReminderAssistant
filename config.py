from datetime import timedelta
from dotenv import load_dotenv
import os


load_dotenv()


class Config:
    DEBUG = False
    CSRF_ENABLED = True
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REMEMBER_COOKIE_DURATION = timedelta(days=120)


class ConfigTelBot:
    BOT_TOKEN = os.getenv('BOT_TOKEN')


class ConfigOWM:
    WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
    CITY = os.getenv('CITY')
    COORDINATES = os.getenv('COORDINATES')

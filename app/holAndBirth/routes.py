from flask import Blueprint
from flask import (
    render_template,
    jsonify,
    request,
    redirect,
    url_for,
)
from app.database import db
from app.models import Birthday, Holiday
from sqlalchemy import or_, and_
from datetime import date, timedelta
from app.holAndBirth.func import get_holidays_for, get_birthdays_for

holAndBirth_bp = Blueprint('holAndBirth', __name__)


@holAndBirth_bp.route('/holAndBirth')
def hol_and_birth():
    return render_template('1.html')


def init_socketio_hab(app):
    from app import socketio
    from app import scheduler

    @socketio.on('get_birthdays')
    def get_birthdays():
        print(111111)
        try:
            socketio.emit('birthdays_update', get_birthdays_for(days=30, limit=10))
        except Exception as e:
            socketio.emit('error', f"Ошибка: {e}")

    @socketio.on('get_holidays')
    def get_holidays():
        print(222222)
        try:
            socketio.emit('holidays_update', get_holidays_for(days=30, limit=10))
        except Exception as e:
            socketio.emit('error', f"Ошибка: {e}")

    @socketio.on('get_bAndH_details')
    def get_bAndH_details():
        try:
            print(33333)
            birthdays = get_birthdays_for(limit=23)
            print(333366, len(birthdays))
            socketio.emit('holidays_and_birthdays_details_update',
                          {'holidays': get_holidays_for(limit=23), 'birthdays': get_birthdays_for(limit=23)})
        except Exception as e:
            socketio.emit('error', f"Ошибка: {e}")

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
        try:
            socketio.emit('birthdays_update', get_birthdays_for(30))
        except Exception as e:
            socketio.emit('error', f"Ошибка: {e}")

    @socketio.on('get_holidays')
    def get_holidays():
        try:
            socketio.emit('holidays_update', get_holidays_for(30))
        except Exception as e:
            socketio.emit('error', f"Ошибка: {e}")

    @socketio.on('get_bAndH_details')
    def get_bAndH_details():
        try:
            socketio.emit('holidays_and_birthdays_details_update',
                          {'holidays': get_holidays_for(90), 'birthdays': get_birthdays_for(90)})
        except Exception as e:
            socketio.emit('error', f"Ошибка: {e}")

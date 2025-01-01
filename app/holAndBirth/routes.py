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

holAndBirth_bp = Blueprint('holAndBirth', __name__)


@holAndBirth_bp.route('/holAndBirth')
def hol_and_birth():
    return render_template('1.html')


def init_socketio_hab(app):
    from app import socketio

    @socketio.on('get_birthdays')
    def get_birthdays():
        try:
            all_birthdays = db.session.query(Birthday).all()
            birthdays = []
            for birthday in all_birthdays:
                birthdays.append({'date': f'{birthday.day}.'
                                          f'{birthday.month}.'
                                          f'{birthday.year}',
                                  'name': birthday.name})
            socketio.emit('birthdays_update', birthdays)
        except Exception as e:
            socketio.emit('error', f"Ошибка: {e}")

    @socketio.on('get_holidays')
    def get_holidays():
        try:
            all_holidays = db.session.query(Holiday).all()
            holidays = []
            for holiday in all_holidays:
                holidays.append({'date': f'{holiday.day}.'
                                         f'{holiday.month}.'
                                         f'{holiday.year}',
                                 'name': holiday.name})
            socketio.emit('holidays_update', holidays)
        except Exception as e:
            socketio.emit('error', f"Ошибка: {e}")

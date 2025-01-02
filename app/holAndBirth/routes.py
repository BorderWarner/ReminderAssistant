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

holAndBirth_bp = Blueprint('holAndBirth', __name__)

MONTHS_RU = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
}


def get_year_suffix(age):
    if 11 <= age % 100 <= 14:
        return "лет"
    last_digit = age % 10
    if last_digit == 1:
        return "год"
    elif 2 <= last_digit <= 4:
        return "года"
    else:
        return "лет"


@holAndBirth_bp.route('/holAndBirth')
def hol_and_birth():
    return render_template('1.html')


def init_socketio_hab(app):
    from app import socketio

    @socketio.on('get_birthdays')
    def get_birthdays():
        try:
            today = date.today()
            current_day = today.day
            current_month = today.month

            future_date = today + timedelta(days=30)
            future_day = future_date.day
            future_month = future_date.month

            if future_month >= current_month:
                birthdays_query = db.session.query(Birthday).filter(
                    or_(
                        and_(
                            Birthday.month == current_month,
                            Birthday.day >= current_day
                        ),
                        and_(
                            Birthday.month > current_month,
                            Birthday.month < future_month
                        ),
                        and_(
                            Birthday.month == future_month,
                            Birthday.day <= future_day
                        )
                    )
                )
            else:
                birthdays_query = db.session.query(Birthday).filter(
                    or_(
                        and_(
                            Birthday.month == current_month,
                            Birthday.day >= current_day
                        ),
                        Birthday.month > current_month,
                        and_(
                            Birthday.month == future_month,
                            Birthday.day <= future_day
                        ),
                        Birthday.month < future_month
                    )
                )

            birthdays = []
            for birthday in birthdays_query.all():
                age = None
                if birthday.year:
                    age = today.year - birthday.year
                date_str = f"{birthday.day} {MONTHS_RU[birthday.month]}"
                if age:
                    suffix = get_year_suffix(age)
                    date_str += f" ({age} {suffix})"
                birthdays.append({
                    'date': date_str,
                    'name': birthday.name
                })

            socketio.emit('birthdays_update', birthdays)
        except Exception as e:
            socketio.emit('error', f"Ошибка: {e}")

    @socketio.on('get_holidays')
    def get_holidays():
        try:
            today = date.today()
            current_day = today.day
            current_month = today.month

            future_date = today + timedelta(days=30)
            future_day = future_date.day
            future_month = future_date.month

            if future_month >= current_month:
                holidays_query = db.session.query(Holiday).filter(
                    or_(
                        and_(
                            Holiday.month == current_month,
                            Holiday.day >= current_day
                        ),
                        and_(
                            Holiday.month > current_month,
                            Holiday.month < future_month
                        ),
                        and_(
                            Holiday.month == future_month,
                            Holiday.day <= future_day
                        )
                    )
                )
            else:
                holidays_query = db.session.query(Holiday).filter(
                    or_(
                        and_(
                            Holiday.month == current_month,
                            Holiday.day >= current_day
                        ),
                        Holiday.month > current_month,
                        and_(
                            Holiday.month == future_month,
                            Holiday.day <= future_day
                        ),
                        Holiday.month < future_month
                    )
                )

            holidays = []
            for holiday in holidays_query.all():
                age = None
                if holiday.year:
                    age = today.year - holiday.year
                date_str = f"{holiday.day} {MONTHS_RU[holiday.month]}"
                if age:
                    suffix = get_year_suffix(age)
                    date_str += f" ({age} {suffix})"
                holidays.append({
                    'date': date_str,
                    'name': holiday.name
                })

            socketio.emit('holidays_update', holidays)
        except Exception as e:
            socketio.emit('error', f"Ошибка: {e}")

    @socketio.on('get_bAndH_details')
    def get_bAndH_details():
        try:
            today = date.today()
            current_day = today.day
            current_month = today.month

            future_date = today + timedelta(days=90)
            future_day = future_date.day
            future_month = future_date.month

            if future_month >= current_month:
                birthdays_query = db.session.query(Birthday).filter(
                    or_(
                        and_(
                            Birthday.month == current_month,
                            Birthday.day >= current_day
                        ),
                        and_(
                            Birthday.month > current_month,
                            Birthday.month < future_month
                        ),
                        and_(
                            Birthday.month == future_month,
                            Birthday.day <= future_day
                        )
                    )
                )
            else:
                birthdays_query = db.session.query(Birthday).filter(
                    or_(
                        and_(
                            Birthday.month == current_month,
                            Birthday.day >= current_day
                        ),
                        Birthday.month > current_month,
                        and_(
                            Birthday.month == future_month,
                            Birthday.day <= future_day
                        ),
                        Birthday.month < future_month
                    )
                )

            if future_month >= current_month:
                holidays_query = db.session.query(Holiday).filter(
                    or_(
                        and_(
                            Holiday.month == current_month,
                            Holiday.day >= current_day
                        ),
                        and_(
                            Holiday.month > current_month,
                            Holiday.month < future_month
                        ),
                        and_(
                            Holiday.month == future_month,
                            Holiday.day <= future_day
                        )
                    )
                )
            else:
                holidays_query = db.session.query(Holiday).filter(
                    or_(
                        and_(
                            Holiday.month == current_month,
                            Holiday.day >= current_day
                        ),
                        Holiday.month > current_month,
                        and_(
                            Holiday.month == future_month,
                            Holiday.day <= future_day
                        ),
                        Holiday.month < future_month
                    )
                )

            birthdays = []
            for birthday in birthdays_query.all():
                age = None
                if birthday.year:
                    age = today.year - birthday.year
                date_str = f"{birthday.day} {MONTHS_RU[birthday.month]}"
                if age:
                    suffix = get_year_suffix(age)
                    date_str += f" ({age} {suffix})"
                birthdays.append({
                    'date': date_str,
                    'name': birthday.name
                })

            holidays = []
            for holiday in holidays_query.all():
                age = None
                if holiday.year:
                    age = today.year - holiday.year
                date_str = f"{holiday.day} {MONTHS_RU[holiday.month]}"
                if age:
                    suffix = get_year_suffix(age)
                    date_str += f" ({age} {suffix})"
                holidays.append({
                    'date': date_str,
                    'name': holiday.name
                })

            socketio.emit('holidays_and_birthdays_details_update', {'holidays': holidays, 'birthdays': birthdays})
        except Exception as e:
            socketio.emit('error', f"Ошибка: {e}")

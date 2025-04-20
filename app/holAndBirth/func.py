from app.database import db
from app.models import Birthday, Holiday
from sqlalchemy import or_, and_
from datetime import date, timedelta


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


def get_holidays_for(days=None, limit=None):
    today = date.today()
    current_day = today.day
    current_month = today.month

    if days:
        future_date = today + timedelta(days=days)
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
            if limit:
                result_query = holidays_query.limit(limit)
            else:
                result_query = holidays_query.all()
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
            if limit:
                result_query = holidays_query.limit(limit)
            else:
                result_query = holidays_query.all()
    else:
        if limit:
            holidays_query = db.session.query(Holiday).order_by(Holiday.month, Holiday.day).filter(
                or_(
                    and_(
                        Holiday.month == current_month,
                        Holiday.day >= current_day
                    ),
                    and_(
                        Holiday.month > current_month,
                    )
                ))
            result_query = holidays_query.limit(limit)
            if len(result_query) < limit:
                holidays_query = db.session.query(Holiday) \
                    .order_by(Holiday.month, Holiday.day).limit(limit - len(result_query))
                dop_result_query = holidays_query.limit(limit)
                result_query += dop_result_query
        else:
            holidays_query = db.session.query(Holiday).order_by(Holiday.month, Holiday.day)
            result_query = holidays_query.all()

    holidays = []

    for holiday in result_query:
        holiday_date_this_year = date(today.year, holiday.month, holiday.day)
        if holiday_date_this_year < today:
            holiday_date_this_year = date(today.year + 1, holiday.month, holiday.day)
        age = None
        if holiday.year:
            age = today.year - holiday.year
        date_str = f"{holiday.day} {MONTHS_RU[holiday.month]}"
        if age:
            suffix = get_year_suffix(age)
            date_str += f" ({age} {suffix})"
        flag_today = 1 if [holiday.day, holiday.month] == [today.day, today.month] else 0
        holidays.append({
            'date': date_str,
            'name': holiday.name,
            'flag_today': flag_today,
            'days_to_holiday': (holiday_date_this_year - today).days
        })
    sorted_holidays = sorted(
        holidays,
        key=lambda x: x['days_to_holiday']
    )
    return sorted_holidays


def get_birthdays_for(days=None, limit=None):
    today = date.today()
    current_day = today.day
    current_month = today.month
    print('CCCCCCC')
    if days:
        future_date = today + timedelta(days=days)
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
            if limit:
                result_query = birthdays_query.limit(limit).all()
            else:
                result_query = birthdays_query.all()
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
            if limit:
                result_query = birthdays_query.limit(limit).all()
            else:
                result_query = birthdays_query.all()
    else:
        print('CHECK')
        if limit:
            birthdays_query = db.session.query(Birthday).order_by(Birthday.month, Birthday.day).filter(
                or_(
                    and_(
                        Birthday.month == current_month,
                        Birthday.day >= current_day
                    ),
                    and_(
                        Birthday.month > current_month,
                    )
                ))
            result_query = birthdays_query.limit(limit).all()
            print('result_query: ', len(result_query))
            if len(result_query) < limit:
                dop_birthdays_query = db.session.query(Birthday) \
                    .order_by(Birthday.month, Birthday.day)
                dop_result_query = dop_birthdays_query.limit(limit - len(result_query))
                print('dop_result_query: ', len(dop_result_query))
                result_query = [*result_query, *dop_result_query]
        else:
            print('CHECK33')
            birthdays_query = db.session.query(Birthday).order_by(Birthday.month, Birthday.day)
            result_query = birthdays_query.all()

    print('result_query: ', len(result_query))

    birthdays = []

    for birthday in result_query:
        birthday_date_this_year = date(today.year, birthday.month, birthday.day)
        if birthday_date_this_year < today:
            birthday_date_this_year = date(today.year + 1, birthday.month, birthday.day)
        age = None
        if birthday.year:
            age = today.year - birthday.year
        date_str = f"{birthday.day} {MONTHS_RU[birthday.month]}"
        if age:
            suffix = get_year_suffix(age)
            date_str += f" ({age} {suffix})"
        flag_today = 1 if [birthday.day, birthday.month] == [today.day, today.month] else 0
        birthdays.append({
            'date': date_str,
            'name': birthday.name,
            'flag_today': flag_today,
            'days_to_birthday': (birthday_date_this_year - today).days
        })
    sorted_birthdays = sorted(
        birthdays,
        key=lambda x: x['days_to_birthday']
    )
    return sorted_birthdays

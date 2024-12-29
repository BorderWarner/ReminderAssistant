import telebot
from config import ConfigTelBot
from app.database import db
from app.models import Task, Birthday, Holiday
from datetime import datetime
from app import socketio

bot = telebot.TeleBot(ConfigTelBot.BOT_TOKEN)


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Используй меню для управления задачами, днями рождения и праздниками.")


@bot.message_handler(commands=['addtask'])
def add_task_prompt(message):
    bot.reply_to(message, "Отправь текст задачи.")
    bot.register_next_step_handler(message, save_task)


def save_task(message):
    try:
        task = message.text
        new_task = Task(task=task, time=datetime.now().strftime('%H:%M:%S'))
        db.session.add(new_task)
        db.session.commit()
        socketio.emit('new_task', task, broadcast=True)
        bot.reply_to(message, f'Задача "{task}" добавлена!')
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")


@bot.message_handler(commands=['addbirthday'])
def add_birthday_prompt(message):
    bot.reply_to(message, "Отправь день рождения в формате: Имя, ДД.ММ.ГГГГ (ГГГГ опционально)")
    bot.register_next_step_handler(message, save_birthday)


def save_birthday(message):
    try:
        name, date = [x.strip() for x in message.text.split(',')]
        day, month, *year = map(int, date.split('.'))
        new_birthday = Birthday(name=name, day=day, month=month, year=year[0] if year else None)
        db.session.add(new_birthday)
        db.session.commit()
        bot.reply_to(message, f'День рождения {name} на {day}.{month}{f".{year[0]}" if year else ""} добавлен!')
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")


@bot.message_handler(commands=['addholiday'])
def add_holiday_prompt(message):
    bot.reply_to(message, "Отправь праздник в формате: Имя праздника, ДД.ММ.ГГГГ (ГГГГ опционально)")
    bot.register_next_step_handler(message, save_holiday)


def save_holiday(message):
    try:
        name, date = [x.strip() for x in message.text.split(',')]
        day, month, *year = map(int, date.split('.'))
        new_holiday = Holiday(name=name, day=day, month=month, year=year[0] if year else None)
        db.session.add(new_holiday)
        db.session.commit()
        bot.reply_to(message, f'Праздник "{name}" на {day}.{month}{f".{year[0]}" if year else ""} добавлен!')
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")


def run_telegram_bot():
    while True:
        try:
            bot.polling(non_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Ошибка телеграм-бота: {e}")
            continue

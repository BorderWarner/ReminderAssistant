import telebot
from telebot.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from config import ConfigTelBot
from app.database import db
from app.models import Task, Birthday, Holiday
from datetime import datetime
from app import socketio, create_app

bot = telebot.TeleBot(ConfigTelBot.BOT_TOKEN)
app = create_app()

commands = [
    ("help", "Показать справку с доступными командами"),
    ("addtask", "Добавить задачу"),
    ("addbirthday", "Добавить день рождения"),
    ("addholiday", "Добавить праздник")
]


def generate_commands_keyboard(comms):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for command, description in comms:
        markup.add(KeyboardButton(f'/{command} - {description}'))
    return markup


def cancel_button():
    cancel_button = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, is_persistent=True)
    cancel_button.add(KeyboardButton("Отмена"))
    return cancel_button


@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def handle_unknown_message(message):
    comms = [("help", "Показать справку с доступными командами")]
    response = (
        "Извините, я не понимаю это сообщение. Нажмите кнопку ниже для получения справки."
    )
    bot.send_message(message.chat.id, response, reply_markup=generate_commands_keyboard(comms))


@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_message = (
        "Привет! Я могу помочь вам с задачами, днями рождения и праздниками. "
        "Нажмите на кнопку ниже для получения подробной информации."
    )
    comms = [
        ("help", "Показать справку с доступными командами")
    ]
    bot.send_message(message.chat.id, welcome_message, reply_markup=generate_commands_keyboard(comms))


@bot.message_handler(commands=['help'])
def send_help(message):
    help_message = "Вот список всех доступных команд и их описание:"
    for command, description in commands:
        help_message += f"\n/{command} - {description}"
    comms = [
        ("addtask", "Добавить задачу"),
        ("addbirthday", "Добавить день рождения"),
        ("addholiday", "Добавить праздник")
    ]

    bot.send_message(message.chat.id, help_message, reply_markup=generate_commands_keyboard(comms))


@bot.message_handler(commands=['addtask'])
def add_task_prompt(message):
    bot.reply_to(
        message,
        "Введите текст задачи или нажмите 'Отмена' для выхода.",
        reply_markup=cancel_button()
    )
    bot.register_next_step_handler(message, validate_task)


def validate_task(message):
    if message.text.strip().lower() == "отмена":
        cancel_process(message)
        return
    if not message.text.strip():
        bot.reply_to(message, "Задача не может быть пустой. Попробуйте ещё раз.", reply_markup=cancel_button())
        bot.register_next_step_handler(message, validate_task)
        return

    save_task(message)


def save_task(message):
    try:
        task = message.text
        with app.app_context():
            new_task = Task(task=task, time=datetime.now().strftime('%H:%M:%S'))
            db.session.add(new_task)
            db.session.commit()
            socketio.emit('new_task', {'time': new_task.time,
                                       'task': new_task.task})
            bot.reply_to(
                message,
                f'Задача "{task}" успешно добавлена!',
                reply_markup=ReplyKeyboardRemove()
            )
    except Exception as e:
        bot.reply_to(
            message,
            f"Ошибка: {e}",
            reply_markup=ReplyKeyboardRemove()
        )


@bot.message_handler(commands=['addbirthday'])
def add_birthday_prompt(message):
    bot.reply_to(
        message,
        "Введите день рождения в формате: Имя, ДД.ММ.ГГГГ (или нажмите 'Отмена').",
        reply_markup=cancel_button()
    )
    bot.register_next_step_handler(message, validate_birthday)


def validate_birthday(message):
    if message.text.strip().lower() == "отмена":
        cancel_process(message)
        return
    try:
        name, date = [x.strip() for x in message.text.split(',')]
        day, month, *year = map(int, date.split('.'))
        if year:
            datetime(year[0], month, day)
        else:
            datetime(1900, month, day)

        save_birthday(name, day, month, year[0] if year else None, message)
    except (ValueError, IndexError):
        bot.reply_to(
            message,
            "Неверный формат данных. Попробуйте снова. Пример: Имя, 25.12.1990",
            reply_markup=cancel_button()
        )
        bot.register_next_step_handler(message, validate_birthday)


def save_birthday(name, day, month, year, message):
    try:
        with app.app_context():
            new_birthday = Birthday(name=name, day=day, month=month, year=year)
            db.session.add(new_birthday)
            db.session.commit()
            bot.reply_to(
                message,
                f'День рождения {name} на {day}.{month}{f".{year}" if year else ""} успешно добавлен!',
                reply_markup=ReplyKeyboardRemove()
            )
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")


@bot.message_handler(commands=['addholiday'])
def add_holiday_prompt(message):
    bot.reply_to(
        message,
        "Введите праздник в формате: Название, ДД.ММ.ГГГГ (или нажмите 'Отмена').",
        reply_markup=cancel_button()
    )
    bot.register_next_step_handler(message, validate_holiday)


def validate_holiday(message):
    if message.text.strip().lower() == "отмена":
        cancel_process(message)
        return
    try:
        name, date = [x.strip() for x in message.text.split(',')]
        day, month, *year = map(int, date.split('.'))
        if year:
            datetime(year[0], month, day)
        else:
            datetime(1900, month, day)

        save_holiday(name, day, month, year[0] if year else None, message)
    except (ValueError, IndexError):
        bot.reply_to(
            message,
            "Неверный формат данных. Попробуйте снова. Пример: Название, 31.12.2023",
            reply_markup=cancel_button()
        )
        bot.register_next_step_handler(message, validate_holiday)


def save_holiday(name, day, month, year, message):
    try:
        with app.app_context():
            new_holiday = Holiday(name=name, day=day, month=month, year=year)
            db.session.add(new_holiday)
            db.session.commit()
            bot.reply_to(
                message,
                f'Праздник "{name}" на {day}.{month}{f".{year}" if year else ""} успешно добавлен!',
                reply_markup=ReplyKeyboardRemove()
            )
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")


# Выход из функционала
def cancel_process(message):
    bot.reply_to(
        message,
        "Операция отменена.",
        reply_markup=ReplyKeyboardRemove()
    )


def run_telegram_bot():
    while True:
        try:
            bot.polling(non_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Ошибка телеграм-бота: {e}")
            continue

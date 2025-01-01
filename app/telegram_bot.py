import telebot
from telebot.types import KeyboardButton, \
    ReplyKeyboardMarkup, ReplyKeyboardRemove, \
    InlineKeyboardMarkup, InlineKeyboardButton
from config import ConfigTelBot
from app.database import db
from app.models import Task, Birthday, Holiday, TelegramUser
from datetime import datetime
from app import socketio
import threading

bot = telebot.TeleBot(ConfigTelBot.BOT_TOKEN)

bot_stop_event = threading.Event()


def stop_telegram_bot():
    bot_stop_event.set()
    bot.stop_polling()


def run_telegram_bot(app):
    with app.app_context():
        while not bot_stop_event.is_set():
            try:
                bot.polling(non_stop=True, interval=0, timeout=20)
            except Exception as e:
                print(f"Ошибка телеграм-бота: {e}")
                continue


def init_telebot(app):
    def authorized_users_only(handler):
        def wrapper(message):
            try:
                with app.app_context():
                    user = db.session.query(TelegramUser).filter_by(telegram_id=message.from_user.id).first()
                    if not user:
                        new_user = TelegramUser(
                            telegram_id=message.from_user.id,
                            username=message.from_user.username,
                            full_name=f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
                        )
                        db.session.add(new_user)
                        db.session.commit()
                        bot.reply_to(message, "У вас нет доступа к этому боту, ожидайте подтверждения.")
                        return
                    return handler(message)
            except Exception as e:
                bot.send_message(message.chat.id, f"Ошибка: {e}")

        return wrapper

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
        if message.text.strip().lower() == "отмена":
            cancel_process(message)
            return
        comms = [("help", "Показать справку с доступными командами")]
        response = (
            "Извините, я не понимаю это сообщение. Нажмите кнопку ниже для получения справки."
        )
        bot.send_message(message.chat.id, response, reply_markup=generate_commands_keyboard(comms))

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        try:
            with app.app_context():
                user = db.session.query(TelegramUser).filter_by(telegram_id=message.from_user.id).first()
                if not user:
                    new_user = TelegramUser(
                        telegram_id=message.from_user.id,
                        username=message.from_user.username,
                        full_name=f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
                    )
                    db.session.add(new_user)
                    db.session.commit()
                    bot.send_message(
                        message.chat.id,
                        "Вы успешно зарегистрированы! Ожидайте подтверждения от администратора."
                    )
                else:
                    welcome_message = (
                        "Привет! Я могу помочь вам с задачами, днями рождения, праздниками и списком покупок. "
                        "Нажмите на кнопку ниже для получения подробной информации."
                    )
                    comms = [
                        ("help", "Показать справку с доступными командами")
                    ]
                    bot.send_message(message.chat.id, welcome_message, reply_markup=generate_commands_keyboard(comms))
        except Exception as e:
            bot.send_message(message.chat.id, f"Ошибка: {e}")

    @bot.message_handler(commands=['help'])
    @authorized_users_only
    def send_help(message):
        help_message = "Вот список всех доступных команд и их описание:"
        comms = [
            ("addtask", "Добавить задачу"),
            ("addbirthday", "Добавить день рождения"),
            ("addholiday", "Добавить праздник"),
            ("tasks", "Показать список задач"),
            ("perform_task", "Выполнить задачу")
        ]
        for command, description in comms:
            help_message += f"\n/{command} - {description}"

        bot.send_message(message.chat.id, help_message, reply_markup=generate_commands_keyboard(comms))

    @bot.message_handler(commands=['addtask'])
    @authorized_users_only
    def add_task_start(message):
        bot.reply_to(
            message,
            "С помощью этой команды можно добавить задачу. Укажите, нужна ли задача с дедлайном.",
            reply_markup=task_type_buttons()
        )
        bot.send_message(
            message.chat.id,
            "Для выхода нажмите 'Отмена'.",
            reply_markup=cancel_button()
        )

    def task_type_buttons():
        """Кнопки для выбора типа задачи."""
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("С дедлайном", callback_data="task_with_deadline"),
            InlineKeyboardButton("Без дедлайна", callback_data="task_without_deadline")
        )
        return keyboard

    @bot.callback_query_handler(func=lambda call: call.data in ["task_with_deadline", "task_without_deadline"])
    def handle_task_type(call):
        if call.data == "task_with_deadline":
            bot.send_message(
                call.message.chat.id,
                "Введите дедлайн задачи в формате ДД.ММ.ГГГГ ЧЧ:ММ или нажмите 'Отмена'.",
                reply_markup=cancel_button()
            )
            bot.register_next_step_handler(call.message, validate_deadline)
        elif call.data == "task_without_deadline":
            bot.send_message(
                call.message.chat.id,
                "Введите текст задачи или нажмите 'Отмена'.",
                reply_markup=cancel_button()
            )
            bot.register_next_step_handler(call.message, validate_task)

    def validate_deadline(message):
        if message.text.strip().lower() == "отмена":
            cancel_process(message)
            return

        try:
            deadline = datetime.strptime(message.text.strip(), '%d.%m.%Y %H:%M')
            bot.reply_to(
                message,
                "Введите текст задачи или нажмите 'Отмена'.",
                reply_markup=cancel_button()
            )
            bot.register_next_step_handler(message, validate_task, deadline)
        except ValueError:
            bot.reply_to(
                message,
                "Неверный формат даты. Попробуйте ещё раз в формате ДД.ММ.ГГГГ ЧЧ:ММ.",
                reply_markup=cancel_button()
            )
            bot.register_next_step_handler(message, validate_deadline)

    def validate_task(message, deadline=None):
        if message.text.strip().lower() == "отмена":
            cancel_process(message)
            return

        if not message.text.strip():
            bot.reply_to(
                message,
                "Текст задачи не может быть пустым. Попробуйте снова.",
                reply_markup=cancel_button()
            )
            bot.register_next_step_handler(message, validate_task, deadline)
            return

        save_task(message, message.text.strip(), deadline)

    def save_task(message, task_text, deadline):
        try:
            with app.app_context():
                new_task = Task(
                    task=task_text,
                    time=datetime.now(),
                    deadline=deadline,
                    status="Не выполнено"
                )
                db.session.add(new_task)
                db.session.commit()
                db.session.refresh(new_task)

                socketio.emit('new_task', {'id': new_task.id,
                                           'deadline': new_task.deadline.strftime('%d.%m.%Y %H:%M') if
                                           new_task.deadline else None,
                                           'task': new_task.task})

                deadline_str = f" с дедлайном {deadline.strftime('%d.%m.%Y %H:%M')}" if deadline else ""
                bot.reply_to(
                    message,
                    f'Задача "{task_text}" успешно добавлена {deadline_str}!',
                    reply_markup=ReplyKeyboardRemove()
                )
        except Exception as e:
            bot.reply_to(
                message,
                f"Ошибка: {e}",
                reply_markup=ReplyKeyboardRemove()
            )

    @bot.message_handler(commands=['tasks'])
    @authorized_users_only
    def list_all_tasks(message):
        try:
            with app.app_context():
                tasks = db.session.query(Task).filter(Task.status == 'Не выполнено').all()
                if not tasks:
                    bot.reply_to(message, "Нет задач.")
                    return

                tasks_list = "\n".join([f"{task.id}. {task.task}" for task in tasks])

                bot.send_message(
                    message.chat.id,
                    f"Вот список всех невыполненных задач:\n{tasks_list}",
                )

        except Exception as e:
            bot.reply_to(message, f"Ошибка: {e}")

    @bot.message_handler(commands=['perform_task'])
    @authorized_users_only
    def list_tasks_with_buttons(message):
        try:
            with app.app_context():
                tasks = db.session.query(Task).filter(Task.status != 'Выполнено').all()
                if not tasks:
                    bot.reply_to(message, "Нет невыполненных задач.")
                    return

                keyboard = []
                for task in tasks:
                    button = InlineKeyboardButton(task.task,
                                                  callback_data=f'perform_{task.id}')
                    keyboard.append([button])

                reply_markup = InlineKeyboardMarkup(keyboard)
                bot.reply_to(message, "Выберите задачу для выполнения:", reply_markup=reply_markup)

        except Exception as e:
            bot.reply_to(message, f"Ошибка: {e}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith('perform_'))
    @authorized_users_only
    def perform_task_callback(call):
        try:
            task_id = int(call.data.split('_')[1])
            with app.app_context():
                task = Task.query.get(task_id)
                if not task:
                    bot.answer_callback_query(call.id, "Задача не найдена.")
                    return

                if task.status == 'Выполнено':
                    bot.answer_callback_query(call.id, "Эта задача уже выполнена.")
                    return

                task.status = 'Выполнено'
                db.session.commit()

                socketio.emit('delete_task', {'task_id': task.id})

                bot.answer_callback_query(call.id, f'Задача {task.task} выполнена!')

                bot.edit_message_text(
                    text=f'Задача {task.task} выполнена!',
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )

        except Exception as e:
            bot.answer_callback_query(call.id, f"Ошибка при выполнении задачи: {e}")

    @bot.message_handler(commands=['addbirthday'])
    @authorized_users_only
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
    @authorized_users_only
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

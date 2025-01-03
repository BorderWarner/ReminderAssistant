import telebot
from telebot.types import KeyboardButton, \
    ReplyKeyboardMarkup, ReplyKeyboardRemove, \
    InlineKeyboardMarkup, InlineKeyboardButton
from config import ConfigTelBot
from app.database import db
from app.models import Task, Birthday, Holiday, TelegramUser, Purchase
from datetime import datetime
from app import socketio
import threading
from sqlalchemy import func

bot = telebot.TeleBot(ConfigTelBot.BOT_TOKEN)

bot_stop_event = threading.Event()


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
                    if user.is_authorized:
                        return handler(message)
                    bot.reply_to(message, "У вас нет доступа к этому боту, ожидайте подтверждения.")
                    return None
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
            ("manageScr", "Управление экраном"),
            ("task", "Управление задачами"),
            ("purchases", "Управление списком покупок"),
            ("bAndHol", "Управление праздниками и др")
        ]
        for command, description in comms:
            help_message += f"\n/{command} - {description}"

        bot.send_message(message.chat.id, help_message, reply_markup=generate_commands_keyboard(comms))

    @bot.message_handler(commands=['task'])
    @authorized_users_only
    def task_start(message):
        bot.reply_to(
            message,
            "Вы попали в меню управления задачами, выберите нужно действие.",
            reply_markup=task_actions_buttons()
        )

    def task_actions_buttons():
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("Добавить", callback_data="add_task")
        )
        keyboard.add(
            InlineKeyboardButton("Выполнить", callback_data="perform_task")
        )
        keyboard.add(
            InlineKeyboardButton("Показать все", callback_data="show_tasks")
        )
        return keyboard

    @bot.callback_query_handler(func=lambda call: call.data in ["add_task", "perform_task", "show_tasks"])
    def handle_task_type(call):
        if call.data == "add_task":
            bot.reply_to(
                call.message,
                "С помощью этой команды можно добавить задачу. Укажите, нужна ли задача с дедлайном.",
                reply_markup=task_type_buttons()
            )
            bot.send_message(
                call.message.chat.id,
                "Для выхода нажмите 'Отмена'.",
                reply_markup=cancel_button()
            )
        elif call.data == "perform_task":
            try:
                with app.app_context():
                    tasks = db.session.query(Task).filter(Task.status != 'Выполнено').all()
                    if not tasks:
                        bot.reply_to(call.message, "Нет невыполненных задач.")
                        return

                    keyboard = []
                    for task in tasks:
                        button = InlineKeyboardButton(task.task,
                                                      callback_data=f'perform_task_{task.id}')
                        keyboard.append([button])

                    reply_markup = InlineKeyboardMarkup(keyboard)
                    bot.reply_to(call.message, "Выберите задачу для выполнения:", reply_markup=reply_markup)
            except Exception as e:
                bot.reply_to(call.message, f"Ошибка: {e}")
        elif call.data == "show_tasks":
            try:
                with app.app_context():
                    tasks = db.session.query(Task).filter(Task.status != 'Выполнено').all()
                    if not tasks:
                        bot.reply_to(call.message, "Нет задач.")
                        return

                    tasks_list = "\n".join([f"- {task.task}" for task in tasks])

                    bot.send_message(
                        call.message.chat.id,
                        f"Вот список всех невыполненных задач:\n{tasks_list}",
                    )
            except Exception as e:
                bot.reply_to(call.message, f"Ошибка: {e}")

    def task_type_buttons():
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("С дедлайном", callback_data="task_with_deadline")
        )
        keyboard.add(
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

                today = datetime.now()
                flag_today = 0
                if new_task.deadline:
                    if today.strftime('%d.%m.%Y') >= new_task.deadline.strftime('%d.%m.%Y'):
                        flag_today = 1

                socketio.emit('new_task', {'id': new_task.id,
                                           'deadline': new_task.deadline.strftime('%d.%m.%Y %H:%M') if
                                           new_task.deadline else None,
                                           'task': new_task.task,
                                           'flag_today': flag_today})

                deadline_str = f" с дедлайном {deadline.strftime('%d.%m.%Y %H:%M')}" if deadline else ""
                bot.reply_to(
                    message,
                    f'Задача "{task_text}" успешно добавлена{deadline_str}!',
                    reply_markup=ReplyKeyboardRemove()
                )
        except Exception as e:
            bot.reply_to(
                message,
                f"Ошибка: {e}",
                reply_markup=ReplyKeyboardRemove()
            )

    @bot.callback_query_handler(func=lambda call: call.data.startswith('perform_task_'))
    @authorized_users_only
    def perform_task_callback(call):
        try:
            task_id = int(call.data.split('_')[2])
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

    @bot.message_handler(commands=['purchases'])
    @authorized_users_only
    def purchases_start(message):
        bot.reply_to(
            message,
            "Вы попали в меню управления списком покупок, выберите нужно действие.",
            reply_markup=purchases_actions_buttons()
        )

    def purchases_actions_buttons():
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("Добавить", callback_data="add_purchase")
        )
        keyboard.add(
            InlineKeyboardButton("Удалить", callback_data="delete_purchase")
        )
        keyboard.add(
            InlineKeyboardButton("Показать все", callback_data="show_purchases")
        )
        return keyboard

    @bot.callback_query_handler(func=lambda call: call.data in ["add_purchase", "delete_purchase", "show_purchases"])
    def handle_purchase_type(call):
        if call.data == "add_purchase":
            bot.reply_to(
                call.message,
                "С помощью этой команды можно добавить товар в список покупок. Укажите, нужен ли объема/размер товара.",
                reply_markup=purchase_type_buttons()
            )
            bot.send_message(
                call.message.chat.id,
                "Для выхода нажмите 'Отмена'.",
                reply_markup=cancel_button()
            )
        elif call.data == "delete_purchase":
            try:
                with app.app_context():
                    purchases = db.session.query(Purchase).filter(Purchase.status != 'Куплено').all()
                    if not purchases:
                        bot.reply_to(call.message, "Список покупок пуст.")
                        return

                    keyboard = []
                    for purchase in purchases:
                        button = InlineKeyboardButton(purchase.name, callback_data=f'delete_purchase_{purchase.id}')
                        keyboard.append([button])

                    reply_markup = InlineKeyboardMarkup(keyboard)
                    bot.reply_to(call.message, "Выберите товар для удаления:", reply_markup=reply_markup)

            except Exception as e:
                bot.reply_to(call.message, f"Ошибка: {e}")
        elif call.data == "show_purchases":
            try:
                with app.app_context():
                    purchases = db.session.query(Purchase).filter(Purchase.status != 'Куплено').all()
                    if not purchases:
                        bot.reply_to(call.message, "Список покупок пуст.")
                        return

                    purchase_list = "\n".join([
                        f" ◦ {purchase.name} {'(' + purchase.size + ') ' if purchase.size else ''}- {purchase.quantity} шт."
                        for purchase in purchases
                    ])

                    bot.send_message(
                        call.message.chat.id,
                        f"Список покупок:\n{purchase_list}",
                    )
            except Exception as e:
                bot.reply_to(call.message, f"Ошибка: {e}")

    def purchase_type_buttons():
        """Кнопки для выбора типа покупки."""
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("С указанием объема", callback_data="purchase_with_size")
        )
        keyboard.add(
            InlineKeyboardButton("Без указания объема", callback_data="purchase_without_size")
        )
        return keyboard

    @bot.callback_query_handler(func=lambda call: call.data in ["purchase_with_size", "purchase_without_size"])
    @authorized_users_only
    def handle_purchase_type(call):
        if call.data == "purchase_with_size":
            bot.send_message(
                call.message.chat.id,
                "Введите объем/размер товара или нажмите 'Отмена'.",
                reply_markup=cancel_button()
            )
            bot.register_next_step_handler(call.message, validate_size)
        elif call.data == "purchase_without_size":
            bot.send_message(
                call.message.chat.id,
                "Введите название товара или нажмите 'Отмена'.",
                reply_markup=cancel_button()
            )
            bot.register_next_step_handler(call.message, validate_purchase)

    def validate_size(message):
        """Проверяет введённый размер и переходит к названию покупки."""
        if message.text.strip().lower() == "отмена":
            cancel_process(message)
            return

        size = message.text.strip()
        bot.reply_to(
            message,
            "Введите название товара.",
            reply_markup=cancel_button()
        )
        bot.register_next_step_handler(message, lambda msg: validate_purchase(msg, size=size))

    def validate_purchase(message, size=None):
        """Проверяет название покупки и запрашивает количество."""
        if message.text.strip().lower() == "отмена":
            cancel_process(message)
            return

        if not message.text.strip():
            bot.reply_to(
                message,
                "Название товара не может быть пустым. Попробуйте снова.",
                reply_markup=cancel_button()
            )
            bot.register_next_step_handler(message, lambda msg: validate_purchase(msg, size=size))
            return

        name = message.text.strip()
        bot.reply_to(
            message,
            "Введите количество товара.",
            reply_markup=cancel_button()
        )
        bot.register_next_step_handler(message, lambda msg: validate_quantity(msg, name=name, size=size))

    def validate_quantity(message, name, size=None):
        """Проверяет введённое количество и сохраняет покупку."""
        if message.text.strip().lower() == "отмена":
            cancel_process(message)
            return

        try:
            quantity = int(message.text.strip())
            if quantity <= 0:
                raise ValueError("Количество должно быть положительным числом.")

            save_purchase(message, name, size, quantity)
        except ValueError:
            bot.reply_to(
                message,
                "Количество должно быть положительным целым числом. Попробуйте снова.",
                reply_markup=cancel_button()
            )
            bot.register_next_step_handler(message, lambda msg: validate_quantity(msg, name=name, size=size))

    def save_purchase(message, name, size, quantity):
        """Сохраняет покупку в базе данных."""
        try:
            with app.app_context():
                new_purchase = Purchase(
                    name=name,
                    size=size,
                    quantity=quantity,
                    status="Не куплено",
                    time=datetime.now()
                )
                db.session.add(new_purchase)
                db.session.commit()
                db.session.refresh(new_purchase)

                socketio.emit('new_purchase', {'id': new_purchase.id,
                                               'name': new_purchase.name,
                                               'size': new_purchase.size,
                                               'quantity': new_purchase.quantity})

                size_str = f" с объемом/размером {size}" if size else " без указания объема/размера"
                bot.reply_to(
                    message,
                    f'Товар "{name}" ({quantity} шт.) успешно добавлен{size_str}.',
                    reply_markup=ReplyKeyboardRemove()
                )
        except Exception as e:
            bot.reply_to(
                message,
                f"Ошибка: {e}",
                reply_markup=ReplyKeyboardRemove()
            )

    @bot.callback_query_handler(func=lambda call: call.data.startswith('delete_purchase_'))
    @authorized_users_only
    def delete_purchase_callback(call):
        try:
            purchase_id = int(call.data.split('_')[2])
            with app.app_context():
                purchase = Purchase.query.get(purchase_id)
                if not purchase:
                    bot.answer_callback_query(call.id, "Товар не найден.")
                    return

                if purchase.status == 'Куплено':
                    bot.answer_callback_query(call.id, "Этот товар уже удален.")
                    return

                purchase.status = 'Куплено'
                db.session.commit()

                socketio.emit('delete_purchase', {'purchase_id': purchase.id})

                bot.answer_callback_query(call.id, f'Товар {purchase.name} удален!')

                bot.edit_message_text(
                    text=f'Товар {purchase.name} успешно удален!',
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )
        except Exception as e:
            bot.answer_callback_query(call.id, f"Ошибка при удалении: {e}")

    @bot.message_handler(commands=['bAndHol'])
    @authorized_users_only
    def bAndHol_start(message):
        bot.reply_to(
            message,
            "Вы попали в меню управления праздниками и днями рождений, выберите нужно действие.",
            reply_markup=bAndHol_actions_buttons()
        )

    def bAndHol_actions_buttons():
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("Добавить др", callback_data="add_birthday")
        )
        keyboard.add(
            InlineKeyboardButton("Удалить др", callback_data="delete_birthday")
        )
        keyboard.add(
            InlineKeyboardButton("Добавить праздник", callback_data="add_holiday")
        )
        keyboard.add(
            InlineKeyboardButton("Удалить праздник", callback_data="delete_holiday")
        )
        return keyboard

    @bot.callback_query_handler(func=lambda call: call.data in ["add_birthday", "delete_birthday",
                                                                "add_holiday", "delete_holiday"])
    def handle_bAndHol_type(call):
        if call.data == "add_birthday":
            bot.reply_to(
                call.message,
                "Введите день рождения в формате: Имя, ДД.ММ.ГГГГ (или нажмите 'Отмена').",
                reply_markup=cancel_button()
            )
            bot.register_next_step_handler(call.message, validate_birthday)
        elif call.data == "delete_birthday":
            # TODO: удаление др
            bot.reply_to(
                call.message,
                "Введите имя человека для удаления ДР или нажмите 'Отмена').",
                reply_markup=cancel_button()
            )
            bot.register_next_step_handler(call.message, delete_birthday)
        elif call.data == "add_holiday":
            bot.reply_to(
                call.message,
                "Введите праздник в формате: Название, ДД.ММ.ГГГГ (или нажмите 'Отмена').",
                reply_markup=cancel_button()
            )
            bot.register_next_step_handler(call.message, validate_holiday)
        elif call.data == "delete_holiday":
            # TODO: удаление праздника
            bot.reply_to(
                call.message,
                "Введите название праздника для удаления или нажмите 'Отмена').",
                reply_markup=cancel_button()
            )
            bot.register_next_step_handler(call.message, delete_holiday)

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

    def delete_birthday(message):
        if message.text.strip().lower() == "отмена":
            cancel_process(message)
            return
        try:
            with app.app_context():
                birthday = db.session.query(Birthday).filter(Birthday.name == message.text.strip()).first()
                if birthday:
                    name = birthday.name
                    db.session.delete(birthday)
                    db.session.commit()
                    bot.reply_to(
                        message,
                        f'День рождения "{name}" успешно удален!',
                        reply_markup=ReplyKeyboardRemove()
                    )
                else:
                    bot.reply_to(
                        message,
                        "Такого имени нет, попробуйте ввести снова.",
                        reply_markup=cancel_button()
                    )
                    bot.register_next_step_handler(message, delete_birthday)
        except Exception as e:
            bot.reply_to(message, f"Ошибка: {e}")

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

    def delete_holiday(message):
        if message.text.strip().lower() == "отмена":
            cancel_process(message)
            return
        try:
            with app.app_context():
                holiday = db.session.query(Holiday).filter(Holiday.name == message.text.strip()).first()
                if holiday:
                    name = holiday.name
                    db.session.delete(holiday)
                    db.session.commit()
                    bot.reply_to(
                        message,
                        f'Праздник "{name}" успешно удален!',
                        reply_markup=ReplyKeyboardRemove()
                    )
                else:
                    bot.reply_to(
                        message,
                        "Праздника с таким названием нет, попробуйте ввести снова",
                        reply_markup=cancel_button()
                    )
                    bot.register_next_step_handler(message, delete_holiday)
        except Exception as e:
            bot.reply_to(message, f"Ошибка: {e}")

    @bot.message_handler(commands=['manageScr'])
    @authorized_users_only
    def manageScr_start(message):
        bot.reply_to(
            message,
            "Вы попали в меню управления экраном, выберите нужно действие.",
            reply_markup=manageScr_actions_buttons()
        )

    def manageScr_actions_buttons():
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("Вернуться на главную", callback_data="main")
        )
        keyboard.add(
            InlineKeyboardButton("Погода на неделю", callback_data="weather_details")
        )
        keyboard.add(
            InlineKeyboardButton("ДР и праздники", callback_data="bAndHol_details")
        )
        return keyboard

    @bot.callback_query_handler(func=lambda call: call.data in ["main", "weather_details",
                                                                "bAndHol_details"])
    def handle_manageScr_type(call):
        if call.data == "main":
            socketio.emit('manageScr', {'command': 'openMain'})
            bot.answer_callback_query(call.id, f'Главная страница открыта!')
        elif call.data == "weather_details":
            socketio.emit('manageScr', {'command': 'openWeatherDetails'})
            bot.answer_callback_query(call.id, f'Страница погоды открыта!')
        elif call.data == "bAndHol_details":
            socketio.emit('manageScr', {'command': 'openBirthdaysAndHolidaysDetails'})
            bot.answer_callback_query(call.id, f'Страница ДР и праздников открыта!')

    # Выход из функционала
    def cancel_process(message):
        bot.reply_to(
            message,
            "Операция отменена.",
            reply_markup=ReplyKeyboardRemove()
        )

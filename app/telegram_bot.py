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

bot = telebot.TeleBot(ConfigTelBot.BOT_TOKEN)

bot_stop_event = threading.Event()

user_states = {}


def set_user_state(user_id, state):
    user_states[user_id] = state


def get_user_state(user_id):
    return user_states.get(user_id)


def clear_user_state(user_id):
    user_states.pop(user_id, None)


def run_telegram_bot(app):
    with app.app_context():
        while not bot_stop_event.is_set():
            try:
                bot.polling(non_stop=True, interval=0, timeout=20)
            except Exception as e:
                print(f"Ошибка телеграм-бота: {e}")
                bot_stop_event.wait(5)


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

    # Выход из функционала
    def cancel_process(message):
        user_id = message.from_user.id
        clear_user_state(user_id)
        bot.reply_to(
            message,
            "Операция отменена.",
            reply_markup=ReplyKeyboardRemove()
        )

    def cancel_button():
        cancel_button = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, is_persistent=True)
        cancel_button.add(KeyboardButton("Отмена"))
        return cancel_button

    @bot.message_handler(func=lambda message: not message.text.startswith('/'))
    def handle_unknown_message(message):
        if message.text.strip().lower() == "отмена":
            cancel_process(message)
            return
        clear_user_state(message.from_user.id)
        comms = [("help", "Показать справку с доступными командами")]
        response = (
            "Извините, я не понимаю это сообщение. Нажмите кнопку ниже для получения справки."
        )
        bot.send_message(message.chat.id, response, reply_markup=generate_commands_keyboard(comms))

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        try:
            with app.app_context():
                clear_user_state(message.from_user.id)
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
        clear_user_state(message.from_user.id)
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
        clear_user_state(message.from_user.id)
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
        user_id = call.from_user.id
        current_state = get_user_state(user_id)

        if current_state:
            bot.reply_to(call.message, "Завершите текущую операцию перед началом новой.")
            return

        if call.data == "add_task":
            set_user_state(user_id, "add_task")
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
            set_user_state(user_id, "perform_task")
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
            clear_user_state(user_id)
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

    @bot.callback_query_handler(func=lambda call: (call.data in ["task_with_deadline", "task_without_deadline"]) and (get_user_state(call.from_user.id) == "add_task"))
    def handle_task_type(call):
        if call.data == "task_with_deadline":
            set_user_state(call.from_user.id, "task_with_deadline")
            bot.send_message(
                call.message.chat.id,
                "Введите дедлайн задачи в формате ДД.ММ.ГГГГ ЧЧ:ММ или нажмите 'Отмена'.",
                reply_markup=cancel_button()
            )
            bot.register_next_step_handler(call.message, validate_deadline)
        elif call.data == "task_without_deadline":
            set_user_state(call.from_user.id, "task_without_deadline")
            bot.send_message(
                call.message.chat.id,
                "Введите текст задачи или нажмите 'Отмена'.",
                reply_markup=cancel_button()
            )
            bot.register_next_step_handler(call.message, validate_task)

    def validate_deadline(message):
        user_id = message.from_user.id
        current_state = get_user_state(user_id)

        if current_state != 'task_with_deadline':
            bot.reply_to(message, "Завершите текущую операцию перед началом новой.")
            return

        if message.text.strip().lower() == "отмена":
            cancel_process(message)
            return

        try:
            set_user_state(message.from_user.id, "task_without_deadline")
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
        user_id = message.from_user.id
        current_state = get_user_state(user_id)

        if current_state != 'task_without_deadline':
            bot.reply_to(message, "Завершите текущую операцию перед началом новой.")
            return

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

        clear_user_state(message.from_user.id)
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

    @bot.callback_query_handler(func=lambda call: (call.data.startswith('perform_task_')) and (get_user_state(call.from_user.id) == "perform_task"))
    @authorized_users_only
    def perform_task_callback(call):
        try:
            clear_user_state(call.from_user.id)

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
        clear_user_state(message.from_user.id)
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
        user_id = call.from_user.id
        current_state = get_user_state(user_id)

        if current_state:
            bot.reply_to(call.message, "Завершите текущую операцию перед началом новой.")
            return

        if call.data == "add_purchase":
            set_user_state(user_id, "add_purchase")
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
            set_user_state(user_id, "delete_purchase")
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
            set_user_state(user_id, "delete_purchase")
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
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("С указанием объема", callback_data="purchase_with_size")
        )
        keyboard.add(
            InlineKeyboardButton("Без указания объема", callback_data="purchase_without_size")
        )
        return keyboard

    @bot.callback_query_handler(func=lambda call: call.data in ["purchase_with_size", "purchase_without_size"] and (get_user_state(call.from_user.id) == "add_purchase"))
    @authorized_users_only
    def handle_purchase_type(call):
        if call.data == "purchase_with_size":
            set_user_state(call.from_user.id, "purchase_with_size")
            bot.send_message(
                call.message.chat.id,
                "Введите объем/размер товара или нажмите 'Отмена'.",
                reply_markup=cancel_button()
            )
            bot.register_next_step_handler(call.message, validate_size)
        elif call.data == "purchase_without_size":
            set_user_state(call.from_user.id, "purchase_without_size")
            bot.send_message(
                call.message.chat.id,
                "Введите название товара или нажмите 'Отмена'.",
                reply_markup=cancel_button()
            )
            bot.register_next_step_handler(call.message, validate_purchase)

    def validate_size(message):
        user_id = message.from_user.id
        current_state = get_user_state(user_id)

        if current_state != 'purchase_with_size':
            bot.reply_to(message, "Завершите текущую операцию перед началом новой.")
            return

        if message.text.strip().lower() == "отмена":
            cancel_process(message)
            return

        set_user_state(message.from_user.id, "purchase_without_size")
        size = message.text.strip()
        bot.reply_to(
            message,
            "Введите название товара.",
            reply_markup=cancel_button()
        )
        bot.register_next_step_handler(message, lambda msg: validate_purchase(msg, size=size))

    def validate_purchase(message, size=None):
        user_id = message.from_user.id
        current_state = get_user_state(user_id)

        if current_state != 'purchase_without_size':
            bot.reply_to(message, "Завершите текущую операцию перед началом новой.")
            return

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

        set_user_state(message.from_user.id, "purchase_quantity")
        name = message.text.strip()
        bot.reply_to(
            message,
            "Введите количество товара.",
            reply_markup=cancel_button()
        )
        bot.register_next_step_handler(message, lambda msg: validate_quantity(msg, name=name, size=size))

    def validate_quantity(message, name, size=None):
        user_id = message.from_user.id
        current_state = get_user_state(user_id)

        if current_state != 'purchase_quantity':
            bot.reply_to(message, "Завершите текущую операцию перед началом новой.")
            return

        if message.text.strip().lower() == "отмена":
            cancel_process(message)
            return

        try:
            quantity = int(message.text.strip())
            if quantity <= 0:
                raise ValueError("Количество должно быть положительным числом.")

            save_purchase(message, name, size, quantity)
            clear_user_state(message.from_user.id)
        except ValueError:
            bot.reply_to(
                message,
                "Количество должно быть положительным целым числом. Попробуйте снова.",
                reply_markup=cancel_button()
            )
            bot.register_next_step_handler(message, lambda msg: validate_quantity(msg, name=name, size=size))

    def save_purchase(message, name, size, quantity):
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

    @bot.callback_query_handler(func=lambda call: call.data.startswith('delete_purchase_') and (get_user_state(call.from_user.id) == "delete_purchase"))
    @authorized_users_only
    def delete_purchase_callback(call):
        try:
            clear_user_state(call.from_user.id)

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
        clear_user_state(message.from_user.id)
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
        user_id = call.from_user.id
        current_state = get_user_state(user_id)

        if current_state:
            bot.reply_to(call.message, "Завершите текущую операцию перед началом новой.")
            return

        if call.data == "add_birthday":
            set_user_state(user_id, "add_birthday")
            bot.reply_to(
                call.message,
                "Введите день рождения в формате: Имя, ДД.ММ.ГГГГ (или нажмите 'Отмена').",
                reply_markup=cancel_button()
            )
            bot.register_next_step_handler(call.message, validate_birthday)
        elif call.data == "delete_birthday":
            set_user_state(user_id, "delete_birthday")
            bot.reply_to(
                call.message,
                "Введите имя человека для удаления ДР или нажмите 'Отмена').",
                reply_markup=cancel_button()
            )
            bot.register_next_step_handler(call.message, delete_birthday)
        elif call.data == "add_holiday":
            set_user_state(user_id, "add_holiday")
            bot.reply_to(
                call.message,
                "Введите праздник в формате: Название, ДД.ММ.ГГГГ (или нажмите 'Отмена').",
                reply_markup=cancel_button()
            )
            bot.register_next_step_handler(call.message, validate_holiday)
        elif call.data == "delete_holiday":
            set_user_state(user_id, "delete_holiday")
            bot.reply_to(
                call.message,
                "Введите название праздника для удаления или нажмите 'Отмена').",
                reply_markup=cancel_button()
            )
            bot.register_next_step_handler(call.message, delete_holiday)

    def validate_birthday(message):
        user_id = message.from_user.id
        current_state = get_user_state(user_id)

        if current_state != 'add_birthday':
            bot.reply_to(message, "Завершите текущую операцию перед началом новой.")
            return

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
            clear_user_state(message.from_user.id)
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
        user_id = message.from_user.id
        current_state = get_user_state(user_id)

        if current_state != 'delete_birthday':
            bot.reply_to(message, "Завершите текущую операцию перед началом новой.")
            return

        if message.text.strip().lower() == "отмена":
            cancel_process(message)
            return

        search_query = message.text.strip()

        if len(search_query) < 3:
            bot.reply_to(message, "Введите не менее 3 символов.", reply_markup=cancel_button())
            bot.register_next_step_handler(message, delete_birthday)
            return

        try:
            with app.app_context():
                birthdays = db.session.query(Birthday).filter(Birthday.name.ilike(f"%{search_query}%")).all()

                if not birthdays:
                    bot.reply_to(message, "Совпадений не найдено. Попробуйте снова.", reply_markup=cancel_button())
                    bot.register_next_step_handler(message, delete_birthday)
                    return

                if len(birthdays) == 1:
                    birthday = birthdays[0]
                    name = birthday.name
                    db.session.delete(birthday)
                    db.session.commit()
                    clear_user_state(user_id)
                    bot.reply_to(message, f'День рождения "{name}" успешно удален!', reply_markup=ReplyKeyboardRemove())
                    return

                keyboard = InlineKeyboardMarkup()
                for birthday in birthdays:
                    button_text = f"{birthday.name} ({birthday.day}.{birthday.month}.{birthday.year if birthday.year else ''})"
                    keyboard.add(InlineKeyboardButton(button_text, callback_data=f"delete_birthday_{birthday.id}"))

                response_text = "Найдено несколько совпадений, выберите один:\n\n"
                for idx, birthday in enumerate(birthdays, start=1):
                    response_text += f"{idx}. {birthday.name} - {birthday.day}.{birthday.month}.{birthday.year or ''}\n"

                bot.reply_to(message, response_text.strip(), reply_markup=keyboard)
                set_user_state(user_id, "delete_birthday_cont")
        except Exception as e:
            bot.reply_to(message, f"Ошибка: {e}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("delete_birthday_") and (get_user_state(call.from_user.id) == "delete_birthday_cont"))
    def handle_delete_birthday_choice(call):
        try:
            birthday_id = int(call.data.split("_")[-1])
            with app.app_context():
                birthday = db.session.query(Birthday).filter(Birthday.id == birthday_id).first()

                if not birthday:
                    bot.edit_message_text("День рождения не найден.", chat_id=call.message.chat.id,
                                          message_id=call.message.message_id)
                    return

                name = birthday.name
                db.session.delete(birthday)
                db.session.commit()
                clear_user_state(call.from_user.id)

                bot.edit_message_text(
                    f'День рождения "{name}" успешно удален!',
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )
        except Exception as e:
            bot.edit_message_text(f"Ошибка: {e}", chat_id=call.message.chat.id, message_id=call.message.message_id)

    def validate_holiday(message):
        user_id = message.from_user.id
        current_state = get_user_state(user_id)

        if current_state != 'add_holiday':
            bot.reply_to(message, "Завершите текущую операцию перед началом новой.")
            return

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
            clear_user_state(message.from_user.id)
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
        user_id = message.from_user.id
        current_state = get_user_state(user_id)

        if current_state != 'delete_holiday':
            bot.reply_to(message, "Завершите текущую операцию перед началом новой.")
            return

        if message.text.strip().lower() == "отмена":
            cancel_process(message)
            return

        search_query = message.text.strip()

        if len(search_query) < 3:
            bot.reply_to(message, "Введите не менее 3 символов.", reply_markup=cancel_button())
            bot.register_next_step_handler(message, delete_holiday)
            return

        try:
            with app.app_context():
                holidays = db.session.query(Holiday).filter(
                    db.func.lower(Holiday.name).contains(search_query.lower())
                ).all()

                if not holidays:
                    bot.reply_to(message, "Совпадений не найдено. Попробуйте снова.", reply_markup=cancel_button())
                    bot.register_next_step_handler(message, delete_holiday)
                    return

                if len(holidays) == 1:
                    holiday = holidays[0]
                    name = holiday.name
                    db.session.delete(holiday)
                    db.session.commit()
                    clear_user_state(user_id)
                    bot.reply_to(message, f'Праздник "{name}" успешно удален!', reply_markup=ReplyKeyboardRemove())
                    return

                keyboard = InlineKeyboardMarkup()
                for holiday in holidays:
                    button_text = f"{holiday.name} ({holiday.day}.{holiday.month}.{holiday.year if holiday.year else ''})"
                    keyboard.add(InlineKeyboardButton(button_text, callback_data=f"delete_holiday_{holiday.id}"))

                response_text = "Найдено несколько совпадений, выберите один:\n\n"
                for idx, holiday in enumerate(holidays, start=1):
                    response_text += f"{idx}. {holiday.name} - {holiday.day}.{holiday.month}.{holiday.year or ''}\n"

                bot.reply_to(message, response_text.strip(), reply_markup=keyboard)
                set_user_state(user_id, "delete_holiday_cont")
        except Exception as e:
            bot.reply_to(message, f"Ошибка: {e}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("delete_holiday_") and (
            get_user_state(call.from_user.id) == "delete_holiday_cont"))
    def handle_delete_holiday_choice(call):
        try:
            holiday_id = int(call.data.split("_")[-1])
            with app.app_context():
                holiday = db.session.query(Holiday).filter(Holiday.id == holiday_id).first()

                if not holiday:
                    bot.edit_message_text("Праздник не найден.", chat_id=call.message.chat.id,
                                          message_id=call.message.message_id)
                    return

                name = holiday.name
                db.session.delete(holiday)
                db.session.commit()
                clear_user_state(call.from_user.id)

                bot.edit_message_text(
                    f'Праздник "{name}" успешно удален!',
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )
        except Exception as e:
            bot.edit_message_text(f"Ошибка: {e}", chat_id=call.message.chat.id, message_id=call.message.message_id)

    @bot.message_handler(commands=['manageScr'])
    @authorized_users_only
    def manageScr_start(message):
        clear_user_state(message.from_user.id)
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
        user_id = call.from_user.id
        current_state = get_user_state(user_id)

        if current_state:
            bot.reply_to(call.message, "Завершите текущую операцию перед началом новой.")
            return

        if call.data == "main":
            socketio.emit('manageScr', {'command': 'openMain'})
            bot.answer_callback_query(call.id, f'Главная страница открыта!')
        elif call.data == "weather_details":
            socketio.emit('manageScr', {'command': 'openWeatherDetails'})
            bot.answer_callback_query(call.id, f'Страница погоды открыта!')
        elif call.data == "bAndHol_details":
            socketio.emit('manageScr', {'command': 'openBirthdaysAndHolidaysDetails'})
            bot.answer_callback_query(call.id, f'Страница ДР и праздников открыта!')

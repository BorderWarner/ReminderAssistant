from app import create_app
from app import socketio, scheduler
import threading
from app.telegram_bot import run_telegram_bot, init_telebot
from app.scheduler_func import start_scheduler_task


def run():
    app = create_app()

    init_telebot(app)
    bot_thread = threading.Thread(target=run_telegram_bot, args=(app,), daemon=True)
    bot_thread.start()

    scheduler.start()

    start_scheduler_task(app, socketio, scheduler)

    try:
        socketio.run(app, host='0.0.0.0', port=5000)
    finally:
        print("Получен сигнал завершения. Ожидаем завершения потоков и планировщика...")
        scheduler.shutdown()
        print("Процесс завершен")


if __name__ == "__main__":
    run()

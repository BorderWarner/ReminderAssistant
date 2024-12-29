from app import create_app
from app.base_socket import socketio
import threading
from app.telegram_bot import run_telegram_bot

app = create_app()

if __name__ == "__main__":
    threading.Thread(target=run_telegram_bot).start()
    socketio.run(app, host='0.0.0.0', port=5000)
    # socketio.run(app, host='localhost', port=5000)

from datetime import datetime
from threading import Lock
from flask_socketio import SocketIO

socketio = SocketIO()
thread = None
thread_lock = Lock()


def background_time_update():
    while True:
        socketio.sleep(1)
        current_time = datetime.now().strftime('%H:%M:%S')
        socketio.emit('time_update', current_time)


@socketio.on('connect')
def handle_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_time_update)
    print("Client connected")


@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")


@socketio.on('get_time')
def get_time():
    try:
        current_time = datetime.now().strftime('%H:%M:%S')
        socketio.emit('time_update', current_time)
    except Exception as e:
        socketio.emit('error', f"Ошибка: {e}")

from flask import Blueprint
from flask import (
    render_template,
    jsonify,
    request,
    redirect,
    url_for,
)
from app.database import db
from app.base_socket import socketio
from app.models import Task

toDo_bp = Blueprint('toDo', __name__)


@toDo_bp.route('/toDo')
def toDo():
    return render_template('1.html')


@socketio.on('get_toDo')
def get_toDo():
    try:
        all_toDo = db.session.query(Task).all()
        toDo = []
        for do in all_toDo:
            toDo.append({'time': do.time,
                         'task': do.task})
        socketio.emit('toDo_received', toDo)
    except Exception as e:
        socketio.emit('error', f"Ошибка: {e}")


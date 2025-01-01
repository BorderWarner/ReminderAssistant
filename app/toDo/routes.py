from flask import Blueprint
from flask import (
    render_template,
    jsonify,
    request,
    redirect,
    url_for,
)
from app.database import db
from app.models import Task

toDo_bp = Blueprint('toDo', __name__)


@toDo_bp.route('/toDo')
def toDo():
    return render_template('1.html')


def init_socketio_todo(app):
    from app import socketio

    @socketio.on('get_todo')
    def get_todo():
        try:
            all_todo = db.session.query(Task).all()
            todo = []
            for do in all_todo:
                todo.append({'time': do.time,
                             'task': do.task})
            socketio.emit('todo_update', todo)
        except Exception as e:
            socketio.emit('error', f"Ошибка: {e}")

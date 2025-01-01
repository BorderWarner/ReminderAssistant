from flask import Blueprint
from flask import (
    render_template,
    jsonify,
    request,
    redirect,
    url_for,
)
from app.database import db

shoppList_bp = Blueprint('shoppList', __name__)


@shoppList_bp.route('/shoppList')
def shoppList():
    return render_template('1.html')


def init_socketio_shopplist(app):
    from app import socketio

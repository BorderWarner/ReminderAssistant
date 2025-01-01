from flask import Blueprint
from flask import (
    render_template,
    jsonify,
    request,
    redirect,
    url_for,
)
from app.database import db
from app.models import Purchase

shoppList_bp = Blueprint('shoppList', __name__)


@shoppList_bp.route('/shoppList')
def shoppList():
    return render_template('1.html')


def init_socketio_shopplist(app):
    from app import socketio

    @socketio.on('get_shopp_list')
    def get_shopp_list():
        try:
            all_purchases = db.session.query(Purchase).all()
            shopp_list = []
            for purchase in all_purchases:
                shopp_list.append({'id': purchase.id,
                                   'name': purchase.name,
                                   'size': purchase.size,
                                   'quantity': purchase.quantity})
            socketio.emit('shopp_list_update', shopp_list)
        except Exception as e:
            socketio.emit('error', f"Ошибка: {e}")

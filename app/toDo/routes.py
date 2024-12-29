from flask import Blueprint
from flask import (
    render_template,
    jsonify,
    request,
    redirect,
    url_for,
)
from app.database import db

toDo_bp = Blueprint('toDo', __name__)


@toDo_bp.route('/toDo')
def toDo():
    return render_template('1.html')


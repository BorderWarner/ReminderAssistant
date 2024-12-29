from flask import Blueprint
from flask import (
    render_template,
    jsonify,
    request,
    redirect,
    url_for,
)
from app.database import db

holAndBirth_bp = Blueprint('holAndBirth', __name__)


@holAndBirth_bp.route('/holAndBirth')
def holAndBirth():
    return render_template('1.html')


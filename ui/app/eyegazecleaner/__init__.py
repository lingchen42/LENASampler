from flask import Blueprint

bp = Blueprint('eyegazecleaner', __name__)

from app.eyegazecleaner import routes
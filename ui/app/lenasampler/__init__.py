from flask import Blueprint

bp = Blueprint('lenasampler', __name__)

from app.lenasampler import routes
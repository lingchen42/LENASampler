import os
import numpy as np
from flask import Flask
from config import Config
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_session import Session

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bootstrap = Bootstrap(app)
Session(app)
db.init_app(app)

from app.lenasampler import bp as lenasampler_bp
from app.eyegazecleaner import bp as eyegazecleaner_bp
app.register_blueprint(lenasampler_bp, url_prefix='/lenasampler')
app.register_blueprint(eyegazecleaner_bp, url_prefix='/eyegazecleaner')

from app import routes, models
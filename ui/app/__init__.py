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

from app.data import bp as data_bp
app.register_blueprint(data_bp, url_prefix='/data')

from app import routes, models
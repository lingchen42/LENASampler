import os
from datetime import timedelta
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    name = "LILAC Tool Suite"
    SECRET_KEY = 'you-would-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SESSION_TYPE = "filesystem"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    ITS_FILENAME_COL = "ITS_File_Name"
    START_TIME_COL = "StartTime"
    DURATION_COL = "Duration_Secs"
    DEFAULT_FILTER_NUM_COLUMNS = ["Duration_Secs", "Silence"]
    SAMPLING_CRITERIA_COLS = ["CT_COUNT"]
    #SESSION_PERMANENT = False
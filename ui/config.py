import os
from datetime import timedelta
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    name = "LILAC Tool Suite"
    SECRET_KEY = 'you-would-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SESSION_TYPE = "filesystem"
    #SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

    # lenasampler settings
    ITS_FILENAME_COL = "ITS_File_Name"
    START_TIME_COL = "StartTime"
    DURATION_COL = "Duration_Secs"
    DEFAULT_FILTER_NUM_COLUMNS = ["Duration_Secs", "Silence"]
    SAMPLING_CRITERIA_COLS = ["CT_COUNT"]

    # eyegazecleaner settings
    CODE_COL = "code"
    ONSET_COL = "onset"
    OFFSET_COL = "offset"
    TRIAL_ID_COL = "trial_id"
    BEGIN_CODE = "B"
    END_CODE = "S"
    CODE_MEANING_DICT = {
        "L": "left",
        "R": "right",
        "C": "center"
    }
    DEFAULT_CODES = ["B", "S", "L", "R", "C"]
    DISCRENPANCY_THRESHOLD_MILISECOND = 500
    DISCRENPANCY_THRESHOLD_FRAME = DISCRENPANCY_THRESHOLD_MILISECOND * 0.03
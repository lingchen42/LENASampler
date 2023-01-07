from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, BooleanField, \
                    IntegerField
from flask_wtf.file import FileField, FileAllowed
from app import app
from app.eyegazecleaner.utils import rearrange_codes


class DataInput(FlaskForm):
    fn = FileField("Add an Eyegaze Coding csv/xlsx file",
                    validators=[FileAllowed(['csv', 'xlsx'],
                                 "Only csv/xlsx file is accepted")])
    timestamp_unit = SelectField("Is the timestamp unit milisecond or frame?",
                          choices=["milisecond", "frame"],
                          default="frame")
    submit = SubmitField('Upload')


class QualityCheckInput(FlaskForm):
    expected_num_trials = IntegerField("How many trials should be there?")
    begin_code = SelectField("Which code is the begining code?",
                        default="", choices=[])
    end_code = SelectField("Which code is the end code?",
                        default="", choices=[])
    eligible_code_okay = BooleanField("Does the eligible codes in "\
                                      "the above list look correct?")
    submit = SubmitField('Run Quality Check')
    
    def __init__(self, codes=[], expected_num_trials=0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if len(codes):
            self.begin_code.choices = rearrange_codes(codes)
            self.end_code.choices = rearrange_codes(codes)
        if expected_num_trials:
            self.expected_num_trials.data = expected_num_trials
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, BooleanField, \
                    IntegerField, MultipleFileField
from flask_wtf.file import FileField, FileAllowed
from app import app
from app.eyegazecleaner.utils import rearrange_codes


class DataInput(FlaskForm):
    fn = FileField("Add an Eyegaze Coding csv/xlsx file",
                    validators=[FileAllowed(['csv', 'xlsx'],
                                 "Only csv/xlsx file is accepted")])
    original_timestamp_unit = SelectField("Select original timestamp unit",
                          choices=["milisecond", "frame"],
                          default="milisecond")
    target_timestamp_unit = SelectField("Select target timestamp unit",
                          choices=["milisecond", "frame"],
                          default="milisecond")
    submit = SubmitField('Upload')


class BatchInput(FlaskForm):
    folder_path = StringField("Enter the absolute folder path that "\
                                    "contain Eyegaze Coding csv/xlsx files")
    original_timestamp_unit = SelectField("Select original timestamp unit",
                          choices=["milisecond", "frame"],
                          default="milisecond")
    target_timestamp_unit = SelectField("Select target timestamp unit",
                          choices=["milisecond", "frame"],
                          default="milisecond")
    expected_num_trials = IntegerField("How many trials are you expecting?")
    begin_code = StringField("Which code is the begining code?",
                        default=app.config["BEGIN_CODE"])
    end_code = StringField("Which code is the end code?",
                        default=app.config["END_CODE"])
    eligible_codes = StringField("Enter eligible codes, seperate by ,",
                        default=",".join(app.config["DEFAULT_CODES"]))
    submit = SubmitField('Upload and run batch quality check')


class QualityCheckInput(FlaskForm):
    expected_num_trials = IntegerField("How many trials are you expecting")
    begin_code = SelectField("Which code is the begining code?",
                        default=app.config["BEGIN_CODE"], choices=[])
    end_code = SelectField("Which code is the end code?",
                        default=app.config["END_CODE"], choices=[])
    eligible_codes = StringField("Enter eligible codes, seperate by ,",
                        default=",".join(app.config["DEFAULT_CODES"]))
    submit = SubmitField('Run Quality Check')
    
    def __init__(self, codes=[], expected_num_trials=0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if len(codes):
            self.begin_code.choices = rearrange_codes(codes)
            self.end_code.choices = rearrange_codes(codes)
            self.eligible_codes.default = ",".join(rearrange_codes(codes))
        if expected_num_trials:
            self.expected_num_trials.default = expected_num_trials


class CompareTwoInput(FlaskForm):
    coder1 = SelectField("Select coder 1 file", choices=[])
    coder1_id = StringField("Code 1 File ID", 
                             render_kw={"readonly": True})
    coder2 = SelectField("Select coder 2 file", choices=[])
    coder2_id = StringField("Code 2 File ID", 
                             render_kw={"readonly": True})
    submit = SubmitField('Run Comparison')
    
    def __init__(self, files=[], *args, **kwargs):
        super().__init__(*args, **kwargs)
        if len(files):
            self.coder1.choices = files
            self.coder2.choices = files


class CompareThreeInput(FlaskForm):
    coder1 = SelectField("Select coder 1 file", choices=[], 
                         render_kw={"readonly": True})
    coder1_id = StringField("Code 1 File ID", 
                             render_kw={"readonly": True})
    coder2 = SelectField("Select coder 2 file", choices=[],
                        render_kw={"readonly": True})
    coder2_id = StringField("Code 2 File ID", 
                             render_kw={"readonly": True})
    coder3 = SelectField("Select coder 3 file", choices=[])
    coder3_id = StringField("Code 3 File ID", 
                             render_kw={"readonly": True})
    submit = SubmitField('Run Comparison')
    
    def __init__(self, files=[], *args, **kwargs):
        super().__init__(*args, **kwargs)
        if len(files):
            self.coder1.choices = files
            self.coder2.choices = files
            self.coder3.choices = files
import uuid
import traceback
import tempfile
import pandas as pd
from werkzeug.utils import secure_filename
from flask import redirect, render_template, url_for, request, session
from app import app
from app.eyegazecleaner import bp
from app.eyegazecleaner.forms import *
from app.eyegazecleaner.utils import *


@bp.route('/input', methods=['GET', 'POST'])
def input():
    form = DataInput()
    status_records = session.get("eyegazecleaner_records", [])
    status_columns = session.get("eyegazecleaner_columns",
                                ["Filename", 
                                "Timestamp Unit", 
                                 "Quality Check Status", 
                                 "Run Quality Check"
                                 "Delete",
                                 "View", 
                                 "ID" ])

    if form.validate_on_submit():
        fn = form.fn.data
        if fn:
            filename = secure_filename(fn.filename)
            timestamp_unit = form.timestamp_unit.data
            file_id = str(uuid.uuid4())
            session["%s_filename"%file_id] = filename 
            session["%s_timestamp_unit"%file_id] = timestamp_unit
            with tempfile.NamedTemporaryFile() as tmp:
                fn.save(tmp.name)
                try:
                    dft, error_message = read_data(filename, tmp.name, 
                                                   timestamp_unit) 
                    if error_message:
                        return render_template("error.html", 
                                            message=error_message)
                    dft = dft.reset_index(drop=True)
                    columns = list(dft.columns)
                    records = dft.to_dict("records")
                    session['%s_columns'%file_id] = columns
                    session['%s_records'%file_id] = records
                    status_records.append({"Filename":filename, 
                        "Original timestamp Unit":timestamp_unit, 
                        "Quality": session.get("%s_quality"%file_id, "Not checked"),
                        "Run Quality Check": "<a href='%seyegazecleaner/quality_check/%s'>check</a>"%(request.host_url, file_id),
                        "Delete": "<a href='%seyegazecleaner/delete/%s'>delete</a>"%(request.host_url, file_id),
                        "View": "<a href='%seyegazecleaner/view_data/%s'>view</a>"%(request.host_url, file_id), 
                        "ID": file_id }) 
                    session["eyegazecleaner_records"] = status_records
                except Exception as e:
                    return render_template("error.html", 
                                            message=traceback.format_exc())

    status_df = pd.DataFrame.from_dict(status_records)
    status_df = status_df.reset_index()
    status_records = status_df.to_dict("records")
    status_columns = status_df.columns
    return render_template("eyegazecleaner/input.html",
                            form=form,
                            columns=status_columns,
                            records=status_records)


@bp.route('/delete/<file_id>', methods=['GET'])
def delete(file_id):
    status_records = session.get("eyegazecleaner_records", [])
    status_df = pd.DataFrame.from_dict(status_records)
    status_df = status_df[status_df["ID"] != file_id]
    status_records = status_df.to_dict("records")
    session["eyegazecleaner_records"] = status_records
    return redirect(url_for("eyegazecleaner.input"))


def update_status_df(file_id, column, value):
    status_records = session.get("eyegazecleaner_records", [])
    status_df = pd.DataFrame.from_dict(status_records)
    status_record_ind = status_df[status_df["ID"] == file_id].index
    status_df.loc[status_record_ind, column] = value
    status_records = status_df.to_dict("records")
    session["eyegazecleaner_records"] = status_records


@bp.route('/quality_check', methods=['GET', 'POST'])
@bp.route('/quality_check/<file_id>', methods=['GET', 'POST'])
def quality_check(file_id):
    records = session.get('%s_records'%file_id, [])
    dft = pd.DataFrame.from_dict(records)
    codes = list(dft["code"].value_counts().index)
    b_counts = list(dft["code"].values).count("B") # B usually stands for begining
    form = QualityCheckInput(codes=codes, expected_num_trials=b_counts)

    if request.method == "GET":
        begin_code = session.get('%s_begin_code'%file_id)
        if begin_code is not None: 
            setattr(getattr(form, "begin_code"), "data", begin_code)
        end_code = session.get('%s_end_code'%file_id)
        if end_code is not None:
            setattr(getattr(form, "end_code"), "data", end_code)
        eligible_code_okay = session.get("%s_eligible_codes"%file_id)
        if eligible_code_okay is not None:
            setattr(getattr(form, "eligible_code_okay"), "data", eligible_code_okay)
        expected_num_trials = session.get("%s_expected_num_trials"%file_id) 
        if expected_num_trials is not None:
            setattr(getattr(form, "expected_num_trials"), "data", expected_num_trials)
    
    if form.validate_on_submit():
        session['%s_begin_code'%file_id] = form.begin_code.data
        session['%s_end_code'%file_id] = form.end_code.data
        session["%s_eligible_codes"%file_id] = form.eligible_code_okay.data
        session["%s_expected_num_trials"%file_id] = form.expected_num_trials.data

        paired_begin_and_end, num_trials\
            = check_trial_begin_and_end_are_paired(dft, 
                    code_col="code",
                    begining_code=form.begin_code.data, 
                    ending_code=form.end_code.data)
        session['%s_paired_begin_and_end'%file_id] = paired_begin_and_end
        session['%s_num_trials'%file_id] = num_trials
        session['%s_num_trials_match_expectation'%file_id] \
            = (num_trials == form.expected_num_trials.data)

        onset_offset_check = check_non_begining_nor_end_code_has_on_off_set(dft, 
                    code_col="code",
                    begining_code=form.begin_code.data, 
                    ending_code=form.end_code.data)
        session['%s_onset_offset_check'%file_id] = onset_offset_check

    eligible_codes = session.get("%s_eligible_codes"%file_id, 'Not checked')
    if eligible_codes == "Not checked":
        bool_eligible_codes = False
    else:
        bool_eligible_codes = bool(eligible_codes)
    paired_begin_and_end = session.get("%s_paired_begin_and_end"%file_id, 'Not checked')
    if paired_begin_and_end == "Not checked":
        bool_paired_begin_and_end = False
    else:
        bool_paired_begin_and_end = bool(paired_begin_and_end)
    onset_offset_check = session.get("%s_onset_offset_check"%file_id, 'Not checked')
    if onset_offset_check == "Not checked":
        bool_onset_offset_check = False
    else:
        bool_onset_offset_check = bool(onset_offset_check)
    num_trials = session.get('%s_num_trials'%file_id, 'Not checked')
    num_trials_match_expectation \
        = session.get('%s_num_trials_match_expectation'%file_id, 'Not checked')
    if num_trials_match_expectation == "Not checked":
        bool_num_trials_match_expectation = False
    else:
        bool_num_trials_match_expectation = num_trials_match_expectation
    overall_quality =  bool_eligible_codes \
                       & bool_paired_begin_and_end \
                       & bool_onset_offset_check \
                       & bool_num_trials_match_expectation
    session["%s_quality"%file_id] = overall_quality
    update_status_df(file_id, "Quality", overall_quality)
    quality_df = pd.DataFrame({
        "Item": ["Overall Quality Pass",
                 "Eligible Codes are correct", 
                 "Trial has paired begining and end", 
                 "Detected Num of Trials",
                 "Num of Trials match expectation",
                 "All non begining or ending code has onset and offset"],
        "Result": [overall_quality, 
                   eligible_codes, 
                   paired_begin_and_end,
                   num_trials,
                   num_trials_match_expectation,
                   onset_offset_check],
        })
    quality_df =  quality_df.reset_index()
    quality_records = quality_df.to_dict("records")
    quality_columns = quality_df.columns

    return render_template("eyegazecleaner/quality_check.html",
                            form=form,
                            columns=quality_columns,
                            records=quality_records)


@bp.route('/view_data', methods=['GET'])
@bp.route('/view_data/<file_id>', methods=['GET'])
def view_data(file_id=None):
    if file_id:
        filename = session.get("%s_filename"%file_id, "Unknown")
        records = session.get('%s_records'%file_id, [])
        columns = session.get('%s_columns'%file_id, [])
        return render_template("eyegazecleaner/view_data.html",
                                filename=filename,
                                file_id=file_id,
                                columns=columns,
                                records=records)
    

@bp.route("/reset_session", methods=["GET", "POST"])
def reset_session():
    session.clear()
    return render_template("eyegazecleaner/reset_session.html") 
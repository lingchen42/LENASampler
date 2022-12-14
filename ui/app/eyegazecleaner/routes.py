import os
import uuid
import traceback
import tempfile
import pandas as pd
from glob import glob
from io import BytesIO
from werkzeug.utils import secure_filename
from flask import redirect, render_template, url_for, request, session, \
                  send_file, Response
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
            original_timestamp_unit = form.original_timestamp_unit.data
            target_timestamp_unit = form.target_timestamp_unit.data
            file_id = str(uuid.uuid4())
            session["%s_filename"%file_id] = filename 
            session["%s_original_timestamp_unit"%file_id] = original_timestamp_unit
            session["%s_target_timestamp_unit"%file_id] = target_timestamp_unit
            with tempfile.NamedTemporaryFile() as tmp:
                fn.save(tmp.name)
                try:
                    dft, error_message = read_data(filename, tmp.name, 
                                                   original_timestamp_unit,
                                                   target_timestamp_unit) 
                    if error_message:
                        return render_template("error.html", 
                                            message=error_message)
                    dft = dft.reset_index(drop=True)
                    columns = list(dft.columns)
                    records = dft.to_dict("records")
                    session['%s_columns'%file_id] = columns
                    session['%s_records'%file_id] = records
                    status_records.append({"Filename":filename, 
                        "Original timestamp Unit":original_timestamp_unit, 
                        "Target timestamp Unit":target_timestamp_unit, 
                        "Quality": session.get("%s_quality"%file_id, "Not checked"),
                        "Run Quality Check": "<a href='%seyegazecleaner/quality_check/%s'>check</a>"%(request.host_url, file_id),
                        "View": "<a href='%seyegazecleaner/view_data/%s'>view</a>"%(request.host_url, file_id), 
                        "Trial Level Summary": "<a href='%seyegazecleaner/trial_summary/%s'>summary</a>"%(request.host_url, file_id), 
                        "Delete": "<a href='%seyegazecleaner/delete/%s'>delete</a>"%(request.host_url, file_id),
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


@bp.route('/batch_input', methods=['GET', 'POST'])
def batch_input():
    form = BatchInput()
    status_records = session.get("eyegazecleaner_records", [])
    status_columns = session.get("eyegazecleaner_batch_columns",
                                ["Filename", 
                                "Timestamp Unit", 
                                 "Quality Check Status", 
                                 "Run Quality Check"
                                 "Delete",
                                 "View", 
                                 "ID" ])

    if request.method == "GET":
        original_timestamp_unit = session.get('batch_original_timestamp_unit')
        if original_timestamp_unit is not None:
            setattr(getattr(form, "original_timestamp_unit"), "data", 
                    original_timestamp_unit)
        target_timestamp_unit = session.get('batch_target_timestamp_unit')
        if target_timestamp_unit is not None:
            setattr(getattr(form, "target_timestamp_unit"), "data", 
                    target_timestamp_unit)
        begin_code = session.get('batch_begin_code')
        if begin_code is not None: 
            setattr(getattr(form, "begin_code"), "data", begin_code)
        end_code = session.get('batch_end_code')
        if end_code is not None:
            setattr(getattr(form, "end_code"), "data", end_code)
        eligible_codes = session.get("batch_eligible_codes")
        if eligible_codes is not None:
            setattr(getattr(form, "eligible_codes"), "data", eligible_codes)
        expected_num_trials = session.get("batch_expected_num_trials") 
        if expected_num_trials is not None:
            setattr(getattr(form, "expected_num_trials"), "data", expected_num_trials)

    if form.validate_on_submit():
        folder_path = form.folder_path.data
        if os.path.exists(folder_path):
            fns = glob(os.path.join(folder_path, "*csv"))
            fns.extend(glob(os.path.join(folder_path, "*xlsx")))
        session["batch_original_timestamp_unit"] = form.original_timestamp_unit.data
        session["batch_target_timestamp_unit"] = form.target_timestamp_unit.data
        session["batch_begin_code"] = form.begin_code.data
        session["batch_end_code"] = form.end_code.data
        session["batch_eligible_codes"] = form.eligible_codes.data
        session["batch_expected_num_trials"] = form.expected_num_trials.data
        if fns:
            for fn in fns:
                filename = os.path.basename(fn)
                original_timestamp_unit = form.original_timestamp_unit.data
                target_timestamp_unit = form.target_timestamp_unit.data
                file_id = str(uuid.uuid4())
                session["%s_filename"%file_id] = filename 
                session["%s_original_timestamp_unit"%file_id] = original_timestamp_unit
                session["%s_target_timestamp_unit"%file_id] = target_timestamp_unit
                session["%s_begin_code"%file_id] = form.begin_code.data
                session["%s_end_code"%file_id] = form.end_code.data
                session["%s_eligible_codes"%file_id] = form.eligible_codes.data
                session["%s_expected_num_trials"%file_id] = form.expected_num_trials.data
                try:
                    dft, error_message = read_data(filename, fn, 
                                                original_timestamp_unit,
                                                target_timestamp_unit) 
                    if error_message:
                        return render_template("error.html", 
                                            message=error_message)
                    dft = dft.reset_index(drop=True)
                    columns = list(dft.columns)
                    records = dft.to_dict("records")
                    session['%s_columns'%file_id] = columns
                    session['%s_records'%file_id] = records
                except Exception as e:
                    status_records.append({"Filename":filename, 
                        "Original timestamp Unit":original_timestamp_unit, 
                        "Target timestamp Unit":target_timestamp_unit, 
                        "Quality": "Data Loading Failed",
                        "Run Quality Check": "Not Available",
                        "View":  "Not Available", 
                        "Trial Level Summary": "Not Available",
                        "Delete": "Not Available",
                        "ID": file_id }) 
                    session["eyegazecleaner_records"] = status_records
                    traceback.print_exc()
                    continue

                # run quality check automatically
                try:
                    overall_quality = \
                        run_quality_check(dft, file_id, session,
                                      eligible_codes=form.eligible_codes.data, 
                                      expected_num_trials=form.expected_num_trials.data,
                                      begin_code=form.begin_code.data, 
                                      end_code=form.end_code.data)
                    status_records.append({"Filename":filename, 
                        "Original timestamp Unit":original_timestamp_unit, 
                        "Target timestamp Unit":target_timestamp_unit, 
                        "Quality": overall_quality,
                        "Run Quality Check": "<a href='%seyegazecleaner/quality_check/%s'>check</a>"%(request.host_url, file_id),
                        "View": "<a href='%seyegazecleaner/view_data/%s'>view</a>"%(request.host_url, file_id), 
                        "Trial Level Summary": "<a href='%seyegazecleaner/trial_summary/%s'>summary</a>"%(request.host_url, file_id), 
                        "Delete": "<a href='%seyegazecleaner/delete/%s'>delete</a>"%(request.host_url, file_id),
                        "ID": file_id }) 
                    session["eyegazecleaner_records"] = status_records
                except Exception as e:
                    status_records.append({"Filename":filename, 
                        "Original timestamp Unit":original_timestamp_unit, 
                        "Target timestamp Unit":target_timestamp_unit, 
                        "Quality": "Quality check run with errors",
                        "Run Quality Check": "<a href='%seyegazecleaner/quality_check/%s'>check</a>"%(request.host_url, file_id),
                        "View": "<a href='%seyegazecleaner/view_data/%s'>view</a>"%(request.host_url, file_id), 
                        "Trial Level Summary": "<a href='%seyegazecleaner/trial_summary/%s'>summary</a>"%(request.host_url, file_id), 
                        "Delete": "<a href='%seyegazecleaner/delete/%s'>delete</a>"%(request.host_url, file_id),
                        "ID": file_id })  
                    session["eyegazecleaner_records"] = status_records
                    traceback.print_exc()

    status_df = pd.DataFrame.from_dict(status_records)
    status_df = status_df.reset_index()
    status_records = status_df.to_dict("records")
    status_columns = status_df.columns
    return render_template("eyegazecleaner/batch_input.html",
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


@bp.route('/quality_check', methods=['GET', 'POST'])
@bp.route('/quality_check/<file_id>', methods=['GET', 'POST'])
@bp.route('/quality_check/<file_id>/<auto_check>', methods=['GET', 'POST'])
def quality_check(file_id, auto_check=0):
    auto_check = int(auto_check)
    if file_id:
        records = session.get('%s_records'%file_id, [])
        dft = pd.DataFrame.from_dict(records)
        codes = list(dft[app.config["CODE_COL"]].value_counts().index)
        # count default begin code
        b_counts = list(dft[app.config["CODE_COL"]].values)\
                            .count(app.config["BEGIN_CODE"]) 
        form = QualityCheckInput(codes=codes, expected_num_trials=b_counts)

        if request.method == "GET":
            begin_code = session.get('%s_begin_code'%file_id)
            if begin_code is not None: 
                setattr(getattr(form, "begin_code"), "data", begin_code)
            end_code = session.get('%s_end_code'%file_id)
            if end_code is not None:
                setattr(getattr(form, "end_code"), "data", end_code)
            eligible_codes = session.get("%s_eligible_codes"%file_id)
            if eligible_codes is not None:
                setattr(getattr(form, "eligible_codes"), "data", eligible_codes)
            expected_num_trials = session.get("%s_expected_num_trials"%file_id) 
            if expected_num_trials is not None:
                setattr(getattr(form, "expected_num_trials"), "data", expected_num_trials)
        
        if form.validate_on_submit() or auto_check:
            session["%s_eligible_codes"%file_id] = form.eligible_codes.data
            session["%s_expected_num_trials"%file_id] = form.expected_num_trials.data

            eligible_codes_okay = check_eligible_codes_match(codes, 
                form.eligible_codes.data)
            session["%s_eligible_codes_okay"%file_id] = eligible_codes_okay

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

        eligible_codes_okay = session.get("%s_eligible_codes_okay"%file_id, 'Not checked')
        if eligible_codes_okay == "Not checked":
            bool_eligible_codes_okay = False
        else:
            bool_eligible_codes_okay = bool(eligible_codes_okay)
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
        overall_quality =  bool_eligible_codes_okay \
                        & bool_paired_begin_and_end \
                        & bool_onset_offset_check \
                        & bool_num_trials_match_expectation
        session["%s_quality"%file_id] = overall_quality
        update_status_df(file_id, "Quality", overall_quality, session)
        quality_df = pd.DataFrame({
            "Item": ["Overall Quality Pass",
                    "Eligible Codes are correct", 
                    "Trial has paired begining and end", 
                    "Detected Num of Trials",
                    "Num of Trials match expectation",
                    "All non begining or ending code has onset and offset"],
            "Result": [overall_quality, 
                    eligible_codes_okay, 
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
    else:
        return render_template("error.html", 
                message="Please initiate this page from the EyegazeClenaer's "\
                    "Input page's table entry: %s/eyegazecleaner/input"%(request.host_url))


@bp.route('/trial_summary', methods=['GET'])
@bp.route('/trial_summary/<file_id>', methods=['GET'])
def trial_summary(file_id=None):
    if file_id:
        summary_records = session.get("%s_summary_records"%file_id, None)
        summary_columns = session.get("%s_summary_records"%file_id, None)
        if summary_records is None:
            filename = session.get("%s_filename"%file_id, "Unknown")
            records = session.get('%s_records'%file_id, [])
            begin_code = session.get('%s_begin_code'%file_id, app.config["BEGIN_CODE"])
            end_code = session.get('%s_end_code'%file_id, app.config["END_CODE"])
            df = pd.DataFrame.from_dict(records)
            summary_df = get_trial_summary(df, 
                        code_col=app.config["CODE_COL"],
                        begin_code=begin_code,
                        end_code=end_code)
            summary_columns = summary_df.columns
            summary_records = summary_df.to_dict("records")
            session["%s_summary_records"%file_id] = summary_records
            session["%s_summary_columns"%file_id] = summary_columns
        return render_template("eyegazecleaner/view_data.html",
                                title="Trial Level Summary Data",
                                filename=filename,
                                file_id=file_id,
                                columns=summary_columns,
                                records=summary_records)
    else:
        return render_template("error.html", 
                message="Please initiate this page from the EyegazeClenaer's "\
                    "Input page's table entry: %s/eyegazecleaner/input"%(request.host_url))


@bp.route('/view_data', methods=['GET'])
@bp.route('/view_data/<file_id>', methods=['GET'])
def view_data(file_id=None):
    if file_id:
        filename = session.get("%s_filename"%file_id, "Unknown")
        records = session.get('%s_records'%file_id, [])
        columns = session.get('%s_columns'%file_id, [])
        return render_template("eyegazecleaner/view_data.html",
                                title="Input Coding Data",
                                filename=filename,
                                file_id=file_id,
                                columns=columns,
                                records=records)
    else:
        return render_template("error.html", 
                message="Please initiate this page from the EyegazeClenaer's "\
                    "Input page's table entry: %s/eyegazecleaner/input"%(request.host_url))
    

@bp.route("/reset_session", methods=["GET", "POST"])
def reset_session():
    session.clear()
    return render_template("eyegazecleaner/reset_session.html") 


@bp.route("/compare_two", methods=["GET", "POST"])
def compare_two():
    status_records = session.get("eyegazecleaner_records", [])
    status_df = pd.DataFrame.from_dict(status_records)
    files = list(status_df["Filename"].values)
    form = CompareTwoInput(files=files)
    columns = []
    records = []
    coder1 = session.get('eyegazercleaner_code1')
    coder1_id = session.get('eyegazercleaner_code1_id')
    coder2 = session.get('eyegazercleaner_code2')
    coder2_id = session.get('eyegazercleaner_code2_id')

    if request.method == "GET":
        if coder1 is not None: 
            setattr(getattr(form, "coder1"), "data", coder1)
        if coder1_id is not None: 
            setattr(getattr(form, "coder1_id"), "data", coder1_id)
        if coder2 is not None: 
            setattr(getattr(form, "coder2"), "data", coder2)
        if coder2_id is not None: 
            setattr(getattr(form, "coder2_id"), "data", coder2_id)

    if form.validate_on_submit():
        coder1 = form.coder1.data
        coder2 = form.coder2.data
        if coder1 == coder2:
            return render_template("error.html", 
                        message="Coder 1 and Coder2 must be different files!")
        coder1_id = status_df[status_df["Filename"] == coder1]["ID"].values[0]
        form.coder1_id.data = coder1_id
        coder2_id = status_df[status_df["Filename"] == coder2]["ID"].values[0]
        form.coder2_id.data = coder2_id
        session['eyegazercleaner_code1'] = coder1
        session['eyegazercleaner_code1_id'] = coder1_id
        session['eyegazercleaner_code2'] = coder2
        session['eyegazercleaner_code2_id'] = coder2_id
        coder_file_id_dict = session.get("eyegaze_file_id_dict", {})
        coder_file_id_dict[coder1_id] = coder1
        coder_file_id_dict[coder2_id] = coder2
        session["eyegaze_file_id_dict"] = coder_file_id_dict

    if coder1 and coder2:
        coder1_timestsamp_unit = session.get("%s_target_timestamp_unit"%coder1_id)
        coder2_timestsamp_unit = session.get("%s_target_timestamp_unit"%coder2_id)
        if coder1_timestsamp_unit == "milisecond":
            timestamp_unit = "milisecond"
            diff_threshold = app.config["DISCRENPANCY_THRESHOLD_MILISECOND"]
        else:
            timestamp_unit = "frame"
            diff_threshold = app.config["DISCRENPANCY_THRESHOLD_FRAME"]
        session["compare_two_threshold_%s_%s"%(coder1_id, coder2_id)] \
            = diff_threshold

        # get precomputed records
        records = session.get("compare_two_records_%s_%s"%(coder1_id, coder2_id), [])
        columns = session.get("compare_two_columns_%s_%s"%(coder1_id, coder2_id), [])
        diff_col_indices = session.get("compare_two_diffindies_%s_%s"%(coder1_id, coder2_id), [])
        if not (len(records) and len(columns) and len(diff_col_indices)):
            coder1_summary_records = session.get("%s_summary_records"%coder1_id, [])
            coder2_summary_records = session.get("%s_summary_records"%coder2_id, [])
            if not len(coder1_summary_records):
                records = session.get('%s_records'%coder1_id, [])
                begin_code = session.get('%s_begin_code'%coder1_id, 
                                            app.config["BEGIN_CODE"])
                end_code = session.get('%s_end_code'%coder1_id,
                                            app.config["END_CODE"])
                df = pd.DataFrame.from_dict(records)
                coder1_summary_df = get_trial_summary(df, 
                            begin_code=begin_code,
                            end_code=end_code)
                coder1_summary_records = coder1_summary_df.to_dict("records")
                session["%s_summary_records"%coder1_id] = coder1_summary_records

            if not len(coder2_summary_records):
                records = session.get('%s_records'%coder2_id, [])
                begin_code = session.get('%s_begin_code'%coder2_id, 
                                            app.config["BEGIN_CODE"])
                end_code = session.get('%s_end_code'%coder2_id, 
                                        app.config["END_CODE"])
                df = pd.DataFrame.from_dict(records)
                coder2_summary_df = get_trial_summary(df, 
                            begin_code=begin_code,
                            end_code=end_code)
                coder2_summary_records = coder2_summary_df.to_dict("records")
                session["%s_summary_records"%coder2_id] = coder2_summary_records

            records, columns, diff_col_indices = \
                run_trial_summary_comparison_two(coder1_summary_records, 
                                                coder1_timestsamp_unit,
                                                coder2_summary_records,
                                                coder2_timestsamp_unit,
                                                )
            session["compare_two_records_%s_%s"%(coder1_id, coder2_id)] = records
            session["compare_two_columns_%s_%s"%(coder1_id, coder2_id)] = columns
            session["compare_two_diffindies_%s_%s"%(coder1_id, coder2_id)] = diff_col_indices

    else:
        records = columns = []
        timestamp_unit = "milisecond"
        diff_threshold = app.config["DISCRENPANCY_THRESHOLD_MILISECOND"]
        diff_col_indices = []
        coder1_id = None
        coder2_id = None
    
    return render_template("eyegazecleaner/compare.html",
                            form=form,
                            columns=columns,
                            records=records,
                            coder1_id=coder1_id,
                            coder2_id=coder2_id,
                            timestamp_unit=timestamp_unit,
                            diff_col_indices=diff_col_indices,
                            diff_threshhold=diff_threshold)


@bp.route("/export_compare_two", methods=["GET"])
@bp.route("/export_compare_two/<coder1_id>/<coder2_id>", methods=["GET"])
def export_compare_two(coder1_id=None, coder2_id=None):
    records = session.get("compare_two_records_%s_%s"%(coder1_id, coder2_id), [])
    if len(records):
        df = pd.DataFrame.from_records(records)
        # format it
        threshold= session.get("compare_two_threshold_%s_%s"\
                               %(coder1_id, coder2_id),
                               app.config["DISCRENPANCY_THRESHOLD_MILISECOND"])
        df = highlight_compare_two_discrepancy(df, threshold)
        buffer = BytesIO()
        df.to_excel(buffer, sheet_name = "ComparisonResult", index=False)
        coder_file_id_dict = session.get("eyegaze_file_id_dict", {})
        coder1_filename = coder_file_id_dict.get(coder1_id, coder1_id)
        coder2_filename = coder_file_id_dict.get(coder2_id, coder2_id)
        outfn = "PairCompare_%s-%s.xlsx"%(os.path.splitext(coder1_filename)[0],
                                          os.path.splitext(coder2_filename)[0])

        headers = {
                'Content-Disposition': 'attachment; filename=%s'%outfn,
                'Content-type': 'application/vnd.ms-excel'
            }
        return Response(buffer.getvalue(), mimetype='application/vnd.ms-excel', 
                        headers=headers)
    else:
        # no prev records found
        return render_template("error.html", 
                    message="No comparison results found for the requested "\
                            "coders, please Run Comparison for the requested "\
                            "coders first")


@bp.route("/compare_three", methods=["GET", "POST"])
def compare_three():
    status_records = session.get("eyegazecleaner_records", [])
    status_df = pd.DataFrame.from_dict(status_records)
    files = list(status_df["Filename"].values)
    form = CompareThreeInput(files=files)
    columns = []
    records = []
    coder1 = session.get('eyegazercleaner_code1')
    coder1_id = session.get('eyegazercleaner_code1_id')
    coder2 = session.get('eyegazercleaner_code2')
    coder2_id = session.get('eyegazercleaner_code2_id')
    if not (coder1 and coder2 and coder1_id and coder2_id):
        return render_template("error.html",
                message="Please run Pair Compare for Coder 1 and Coder 2 first")
    
    if request.method == "GET":
        setattr(getattr(form, "coder1"), "data", coder1)
        setattr(getattr(form, "coder1_id"), "data", coder1_id)
        setattr(getattr(form, "coder2"), "data", coder2)
        setattr(getattr(form, "coder2_id"), "data", coder2_id)

    if form.validate_on_submit():
        coder3 = form.coder3.data
        if coder3 in [coder1, coder2]:
            return render_template("error.html", 
                                    message="Coder 3 must be different from "\
                                            "Coder1 and Coder2's files")

    
    return render_template("eyegazecleaner/compare.html",
                            form=form,
                            columns=columns,
                            records=records,
                            coder1_id=coder1_id,
                            coder2_id=coder2_id,
                            timestamp_unit="milisecond",
                            diff_col_indices=[],
                            diff_threshhold=500)
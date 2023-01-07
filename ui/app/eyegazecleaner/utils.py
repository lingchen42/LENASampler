import traceback
import pandas as pd


def convert_milisecond_to_frame(df, scale=0.03):
    ''' 30 frame in 1000 miliseconds; 1 miliseconds = 0.03 frame.

    Note that we are rounding the results not just taking the integer portion
    '''
    df["onset"] = round(df["onset"] * scale)
    df["offset"] = round(df["offset"] * scale)
    df["onset"] = df["onset"].astype(int)
    df["offset"] = df["offset"].astype(int)
    return df


def read_data(fn, filepath, timestamp_unit):
    '''read csv/excel files'''
    error_message = ""
    if fn.endswith("csv"):
        df = pd.read_csv(filepath)
        cols = list(df.columns)
        cols[:4] = ["index", "onset", "offset", "code"]
        df.columns = cols
        df = df[["index", "code", "onset", "offset"]]
    else:
        try:
            # xlsx file coded using frame as time unit doesn't have header
            df = pd.read_excel(filepath, header=None)
            df.columns = ["code", "onset", "offset"]
            df = df.reset_index()
        except:
            df = None
            error_message = "%s cannot be openned,"\
                            " please make sure it is csv/xlsx file format\n"\
                            "%s"%(fn, traceback.format_exc())
    if df is not None :
        df = df.fillna(0)
        if timestamp_unit == "milisecond":
            df = convert_milisecond_to_frame(df)
    return df, error_message


def check_eligible_codes(df, code_col="code"):
    return list(df[code_col].value_counts().index)


def check_trial_begin_and_end_are_paired(df, code_col="code",
    begining_code="B", ending_code="S"):
    dft = df[df[code_col].isin([begining_code, ending_code])]
    codes = list(dft["code"].values)
    code_stack = []
    try:
        for code in codes:
            if code == begining_code:
                # everytime a new trial begins,
                # we must found previous trial has a paired begining and end
                assert len(code_stack) == 0, "Trial has unpaired begining and end"
                code_stack.append(code)
            if code == ending_code:
                code_stack.pop()
                # everytime a trail ends
                # it must pop up its begining, leave the code stack empty
                assert len(code_stack) == 0, "Trial has unpaired begining and end"
        # at the end, there should not be any unpaired beginings
        assert len(code_stack) == 0, "Trial has unpaired begining and end"
    except:
        return False, codes.count(begining_code)
    return True, codes.count(begining_code)


def check_non_begining_nor_end_code_has_on_off_set(df, code_col="code",
    begining_code="B", ending_code="S"):
    dft = df[(df[code_col] != begining_code) & (df[code_col] != ending_code)]
    no_onset_value_rows = dft[dft["onset"] == 0]
    no_offset_value_rows = dft[dft["offset"] == 0]
    if (len(no_onset_value_rows) == 0) and (len(no_offset_value_rows) == 0):
        return True
    else:
        return False


def rearrange_codes(codes, default_begin_code="B", default_end_code="S"):
    codes = sorted(codes)
    if default_end_code in codes:
        codes.remove(default_end_code)
        codes.insert(0, default_end_code)
    if default_begin_code in codes:
        codes.remove(default_begin_code)
        codes.insert(0, default_begin_code)
    return codes
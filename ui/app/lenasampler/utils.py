import os
import shutil
import pandas as pd
import zipfile
from zipfile import ZipFile
from tqdm import tqdm
from moviepy.editor import *


def remove_audio_fn_prefix(fn):
    """ M001_20210311_135447_010263_2.wav to 20210311_135447_010263_2.wav
    """
    return "_".join(fn.split("_")[1:])


def its_wav_match_quality_check(its_file_names, audio_dir, idprefix):
    audio_files = [ fn for fn in os.listdir(audio_dir) \
                    if (fn.endswith("wav") and not fn.startswith("._"))]
    its_to_wav_files = ["%s_%s"%(idprefix, fn.replace(".its", ".wav")) \
        for fn in its_file_names]
    missing_files = sorted(list(set(its_to_wav_files) - set(audio_files)))
    missing_files = [remove_audio_fn_prefix(fn.replace(".wav", ".its"))\
                     for fn in missing_files]
    extra_files = sorted(list(set(audio_files) - set(its_to_wav_files)))
    matched_files = sorted(list(set(audio_files) & set(its_to_wav_files)))
    if (len(missing_files) == 0) and (len(extra_files) == 0):
        is_perfect_match = True
    else:
        is_perfect_match = False
    return missing_files, extra_files, matched_files, is_perfect_match


def get_audio_duration(fn):
    ''' Measure the duration of a wav file
    '''
    a = AudioFileClip(fn)
    return int(a.duration)


def check_audio_duration_match(df, audio_dir, matched_files,
                       missing_files, extra_files,
                       itsfile_col, duration_col):
    '''
        :params df: dataframe, should contain the its file name
                    column and duration column
    '''
    records = []
    for fn in matched_files:
        itsfilename = fn.replace(".wav", ".its")
        itsfilename = remove_audio_fn_prefix(itsfilename)
        dft = df[df[itsfile_col] == itsfilename]
        its_duration = dft[duration_col].sum()
        audio_filepath = os.path.join(audio_dir, fn)
        audio_duration = get_audio_duration(audio_filepath)
        diff = audio_duration - its_duration
        if diff == 0:
            note = "Perfect match"
        else:
            note = "The duration of its file and wav is not the same."
        t_record = {"Filename": itsfilename,
                    "Type": "Matched",
                    "its duration (s)": its_duration,
                    "wav duration (s)": audio_duration,
                    "note": note}
        records.append(t_record)

    for fn in missing_files:
        dft = df[df[itsfile_col] == fn]
        its_duration = dft[duration_col].sum()
        t_record = {"Filename": fn,
                    "Type": "No matching wav file",
                    "its duration (s)": its_duration,
                    "wav duration (s)": "NA",
                    "note": "No matching wav file found for this its file"}
        records.append(t_record)

    for fn in extra_files:
        audio_filepath = os.path.join(audio_dir, fn)
        audio_duration = get_audio_duration(audio_filepath)
        t_record = {"Filename": fn,
                    "Type": "No matching its file",
                    "its duration (s)": "NA",
                    "wav duration (s)": audio_duration,
                    "note": "No matching its file found for this wav file"}
        records.append(t_record)

    return records


def run_quality_check(records, audio_dir, itsfile_col, duration_col, idprefix):
    df = pd.DataFrame(records)
    its_file_names = df[itsfile_col].values
    # does the its file column correspond to the audio wav file?
    missing_files, extra_files, matched_files, is_perfect_match \
        = its_wav_match_quality_check(its_file_names, audio_dir, idprefix)
    quality_records = [
        {"Item": "ITS files perfect match WAV files",
         "Value": is_perfect_match, "Notes": ''},
        {"Item": "ITS files without corresponding WAV files",
         "Value": ", ".join(missing_files), "Notes": ''},
        {"Item": "WAV files without corresponding ITS files",
         "Value": ", ".join(extra_files), "Notes": ''},
        {"Item": "Matched ITS and WAV files",
         "Value": ", ".join(matched_files), "Notes": ''}
    ]
    dft_summary = pd.DataFrame(quality_records)
    dft_summary = dft_summary.reset_index()

    # Does the length of a wav file correspond to
    # the sum of the length of the segments?
    duration_match_records = check_audio_duration_match(df, audio_dir,
        matched_files, missing_files, extra_files, itsfile_col, duration_col)
    dft_per_file = pd.DataFrame(duration_match_records)
    dft_per_file = dft_per_file.reset_index()
    matched_itsfiles = [remove_audio_fn_prefix(fn.replace(".wav", ".its"))\
                     for fn in matched_files]

    return dft_summary, dft_per_file, matched_itsfiles, is_perfect_match


def parse_time(time_str):
    time_str = time_str.split("(")[0].strip()
    ts = pd.to_datetime(time_str)
    return ts


def extract_from_audio_file(its_file, audiodir, idprefix, start, duration,
                            abs_ts, outdir):
    audio_file = "%s_%s"%(idprefix, its_file.replace(".its", ".wav"))
    audio_filepath = os.path.join(audiodir, audio_file)
    # Colon is not allowed in windows paths and causes unhandled error
    modified_timestamp = str(abs_ts).replace(":", "-")
    outfn = os.path.join(outdir,
        audio_file.replace(".wav", "_AbsStart_%s_RelStart_%s_Duration_%s.wav"\
                                    %(modified_timestamp, start, duration)))
    a = AudioFileClip(audio_filepath)
    segment = a.subclip(start, start+duration)
    segment.write_audiofile(outfn)
    return outfn


def prepare_audio_files(df, df_ori, audiodir, outdir, idprefix,
                        itsfilecol, starttimecol, durationcol):
    if os.path.exists(outdir):  # remove existing outdir if there is one
        shutil.rmtree(outdir, ignore_errors=True)
    else:
        os.makedirs(outdir)

    relative_start_time = []
    outfns = []
    for ind, row in df.iterrows():
        its_file = row[itsfilecol]
        its_file_start = df_ori[df_ori[itsfilecol]==its_file][starttimecol].values[0]
        its_file_start = parse_time(its_file_start)
        segment_start = row[starttimecol]
        segment_start = parse_time(segment_start)
        segment_relative_start = (segment_start - its_file_start).seconds
        duration = row[durationcol]
        relative_start_time.append(segment_relative_start)
        outfn = extract_from_audio_file(its_file, audiodir, idprefix,
                                segment_relative_start, duration,
                                str(segment_start), outdir)
        outfns.append(os.path.basename(outfn))
    df["segment_relative_start_time"] = relative_start_time
    df["segment_filename"] = outfns
    df.to_csv(os.path.join(outdir, "%s_SampledAudioSegmentsMetadata.csv"%idprefix))
    return df


def zipdir(path, ziph):
    print("\nZipping files ...")
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        if len(files):
            for file in tqdm(files):
                ziph.write(os.path.join(root, file))
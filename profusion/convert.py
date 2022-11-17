"""Parse Profusion export data and write to sleeplab format."""
import argparse
import logging
import re
import xmltodict

from dataset_generation import edf, writer
from dataset_generation.models import *
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any, Callable


logger = logging.getLogger(__name__)


def str_to_time(time_str):
    hour, minute, _second = time_str.split(sep=':')
    hour = int(hour)
    minute = int(minute)
    _second = float(_second)
    second = int(_second)
    microsecond = int(_second % 1 * 1e6)

    return time(hour=hour, minute=minute, second=second, microsecond=microsecond)


def resolve_datetime(start_ts, _time):
    """Convert time of the day to datetime based on start_ts datetime.
    
    This function assumes that time_str presents a time of the day within
    24 hours from start_ts.
    """
    _date = start_ts.date()
    if _time < start_ts.time():
        # If the time is smaller, it belongs to next day
        _date = _date + timedelta(days=1)

    return datetime(
        year=_date.year,
        month=_date.month,
        day=_date.day,
        hour=_time.hour,
        minute=_time.minute,
        second=_time.second,
        microsecond=_time.microsecond    
    )
    
    
def resolve_log_start_ts(start_ts, _time):
    """
    Start_ts represents the start of recording, and there may be
    logging before that, so create a log_start_ts to be used in
    resolve_datetime().
    """
    # If start_ts is after midnight, and there are logs before midnight,
    # those logs actually happened during the previous date
    if start_ts.hour < 12 and _time.hour > 12:
        _date = start_ts.date() - timedelta(days=1)

    # If both are before midnight or after midnight, they belong to same date.
    else:
        _date = start_ts.date()

    return datetime(
        year=_date.year,
        month=_date.month,
        day=_date.day,
        hour=_time.hour,
        minute=_time.minute,
        second=_time.second,
        microsecond=_time.microsecond
    )


def parse_study_logs(log_file_path: Path, start_ts: datetime) -> list[LogEntry]:
    """Parse txt study logs so that the time will be converted to datetime.
    
    Resolving the datetime relies on the heuristic that logs are for a duration
    shorter than 24h.

    TODO: Add validation for the 24h assumption.
    """
    def _parse_line(l):
        time_str, _, _, text = l.split(sep=',', maxsplit=3)
        _time = str_to_time(time_str)
        ts = resolve_datetime(log_start_ts, _time)
        return LogEntry(ts=ts, text=text)
    
    res = []
    with open(log_file_path, 'r') as f:
        lines = f.readlines()
        
    first_log_time_str = lines[0].split(',', maxsplit=1)[0].strip()
    log_start_ts = resolve_log_start_ts(start_ts, str_to_time(first_log_time_str))

    for line in lines:
        res.append(_parse_line(line.strip()))

    return res


def parse_annotation(d: dict[str, Any], start_ts: datetime) -> Annotation:
    name = d.pop('Name')
    start_sec = float(d.pop('Start'))
    duration = float(d.pop('Duration'))
    _start_ts = start_ts + timedelta(seconds=start_sec)
    input_channel = d.pop('Input')
    
    # Parse the rest as extra_attributes
    if len(d) > 0:
        extra_attributes = d
    else:
        extra_attributes = None

    return Annotation(
        name=name,
        start_ts=_start_ts,
        start_sec=start_sec,
        duration=duration,
        input_channel=input_channel,
        extra_attributes=extra_attributes
    )


def parse_xml(
        xml_path: Path,
        start_ts: datetime) -> tuple[dict[str, list[Annotation]], list[int], int]:
    """Read the events and hypnogram from the xml event file."""
    with open(xml_path, 'rb') as f:
        xml_parsed = xmltodict.parse(f)

    xml_events = xml_parsed['CMPStudyConfig']['ScoredEvents']['ScoredEvent']
    annotations = {'events': []}
    for e in xml_events:
        annotations['events'].append(parse_annotation(e, start_ts))
    
    hypnogram = xml_parsed['CMPStudyConfig']['SleepStages']['SleepStage']
    hypnogram = [int(stage) for stage in hypnogram]

    epoch_sec = int(xml_parsed['CMPStudyConfig']['EpochLength'])

    return annotations, hypnogram, epoch_sec


def parse_edf(edf_path: Path) -> tuple[datetime, dict[str, SampleArray]]:
    """Read the start_ts and SampleArrays from the EDF."""
    def _parse_samplearray(
            _load_func: Callable[[], np.array],
            _header: dict[str, Any]) -> SampleArray:
        array_attributes = ArrayAttributes(
            # Replace '/' with '_' to avoid errors in filepaths
            name=_header['label'].replace('/', '_'),
            sampling_rate=_header['sample_rate'],
            unit=_header['dimension']
        )
        return SampleArray(attributes=array_attributes, values_func=_load_func)

    s_load_funcs, s_headers, header = edf.read_edf_export(edf_path)

    start_ts = header['startdate']
    sample_arrays = {}
    for s_load_func, s_header in zip(s_load_funcs, s_headers):
        sample_array = _parse_samplearray(s_load_func, s_header)
        sample_arrays[sample_array.attributes.name] = sample_array

    return start_ts, sample_arrays


def parse_subject_id(idinfo_path: Path) -> str:
    """Parse the profusion study id from txt_idinfo.txt.
    
    The study id is assumed to be contained in the idinfo generated from
    Profusion in the form 'Compumedics ProFusion PSG - [123456 1.1.1900]'.

    The study id is assumed to be a decimal integer.
    """
    with open(idinfo_path, 'r') as f:
        id_info = f.readlines()[0]

    # Match the decimal integer between '[' and space
    re_str = r'\[(\d+)\s'
    # This will raise AttributeError if no match
    subject_id = re.search(re_str, id_info).group(1)
    
    return str(subject_id)


def parse_hypnogram(hg_str_path: Path, hg_int: list[int], epoch_sec=30) -> SampleArray:
    with open(hg_str_path) as f:
        hg_str = f.readlines()
    hg_str = [l.strip() for l in hg_str]
    _msg = 'Hypnograms from xml and txt files have different lengths'
    assert len(hg_int) == len(hg_str), _msg
    hg_map = {int_stage: str_stage for int_stage, str_stage in zip(hg_int, hg_str)}
    
    return SampleArray(
        attributes=ArrayAttributes(
            name='hypnogram',
            sampling_interval=epoch_sec,
            value_map=hg_map
        ),
        values_func=lambda: hg_int
    )


def parse_subject(subject_dir: Path, file_names: dict[str, str]) -> Subject:
    subject_id = parse_subject_id(subject_dir / file_names['idinfo_file'])
    start_ts, sample_arrays = parse_edf(subject_dir / file_names['edf_file'])
    annotations, hg_int, epoch_sec = parse_xml(subject_dir / file_names['xml_file'],
        start_ts=start_ts)
    
    sample_arrays['hypnogram'] = parse_hypnogram(
        subject_dir / file_names['hg_file'],
        hg_int,
        epoch_sec=epoch_sec
    )

    study_logs = parse_study_logs(subject_dir / file_names['log_file'], start_ts)

    metadata = SubjectMetadata(
        subject_id=subject_id,
        recording_start_ts=start_ts
    )

    return Subject(
        metadata=metadata,
        sample_arrays=sample_arrays,
        annotations=annotations,
        study_logs=study_logs
    )


def read_data(
        src_dir: Path,
        ds_name: str,
        study_name: str,
        file_names: dict[str, str]) -> Dataset:
    """Read data from `basedir` and parse to sleeplab Dataset."""
    subjects = {}
    for subject_dir in src_dir.iterdir():
        subject = parse_subject(subject_dir, file_names=file_names)
        subjects[subject.metadata.subject_id] = subject

    studies = {study_name: Study(name=study_name, subjects=subjects)}
    dataset = Dataset(name=ds_name, studies=studies)
    
    return dataset


def convert_dataset(
        src_dir: Path,
        dst_dir: Path,
        ds_name: str,
        study_name: str,
        xml_file: str = 'edf_signals.edf.XML',
        log_file: str = 'txt_studylog.txt',
        edf_file: str = 'edf_signals.edf',
        idinfo_file: str = 'txt_idinfo.txt',
        hg_file: str = 'txt_hypnogram.txt') -> None:
    logger.info(f'Converting Profusion data from {src_dir} to {dst_dir}...')
    logger.info(f'Start reading the data from {src_dir}...')
    dataset = read_data(
        src_dir, ds_name, study_name,
        file_names={
            'xml_file': xml_file,
            'log_file': log_file,
            'edf_file': edf_file,
            'idinfo_file': idinfo_file,
            'hg_file': hg_file
        })

    logger.info(f'Start writing the data to {dst_dir}...')
    writer.write_dataset(dataset, dst_dir)
    logger.info(f'Done.')


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('--src_dir', type=Path, required=True)
    parser.add_argument('--dst_dir', type=Path, required=True)
    parser.add_argument('--ds_name', type=str, required=True)
    parser.add_argument('--study_name', type=str, required=True)
    parser.add_argument('--xml_file', type=str, default='edf_signals.edf.XML')
    parser.add_argument('--log_file', type=str, default='txt_studylog.txt')
    parser.add_argument('--edf_file', type=str, default='edf_signals.edf')
    parser.add_argument('--idinfo_file', type=str, default='txt_idinfo.txt')
    parser.add_argument('--hg_file', type=str, default='txt_hypnogram.txt')

    return parser


def cli_convert_dataset() -> None:
    parser = create_parser()
    args = parser.parse_args()
    logger.info(f'Profusion conversion args: {vars(args)}')
    convert_dataset(**vars(args))



if __name__ == '__main__':
    cli_convert_dataset()
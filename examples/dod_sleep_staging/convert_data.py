"""Convert DOD data from h5 files to sleeplab format."""
import argparse
import h5py
import logging
import numpy as np
import sleeplab_format as slf

from datetime import datetime as dt
from datetime import timedelta
from functools import partial
from pathlib import Path


logger = logging.getLogger(__name__)


def read_hypnogram(h5: h5py.File, start_ts: dt, epoch_sec=30.0):
    stage_map = {
        -1: slf.models.SleepStage.UNSCORED,
        0: slf.models.SleepStage.WAKE,
        1: slf.models.SleepStage.N1,
        2: slf.models.SleepStage.N2,
        3: slf.models.SleepStage.N3,
        4: slf.models.SleepStage.REM
    }
    h5_hg = h5['hypnogram'][:]
    #start_ts = dt.fromtimestamp(h5.attrs['start_time'])
    annotations = []

    for i, h5_stage in enumerate(h5_hg):
        start_delta = i * timedelta(seconds=epoch_sec)
        stage = slf.models.SleepStageAnnotation(
            name=stage_map[h5_stage],
            start_ts=start_ts + start_delta,
            start_sec=float(start_delta.seconds),
            duration=epoch_sec
        )
        annotations.append(stage)

    return slf.models.Hypnogram(annotations=annotations, scorer='manual_consensus')


def read_signal_from_h5_file(h5_path: Path, signal_type: str, signal_name: str):
    h5 = h5py.File(h5_path, 'r')
    s = h5['signals'][signal_type][signal_name][:].astype(np.float32)
    return s


def read_sample_arrays(h5: h5py.File, h5_path: Path, start_ts: dt):
    #start_ts = dt.fromtimestamp(h5.attrs['start_time'])
    sample_arrays = {}

    for signal_type in h5['signals']:
        fs = h5['signals'][signal_type].attrs['fs']
        unit = h5['signals'][signal_type].attrs['unit'].decode('utf-8')

        for signal_name in h5['signals'][signal_type]:
            # Use loading functions to avoid reading all data to memory
            s_load_func = partial(read_signal_from_h5_file,
                                  h5_path=h5_path,
                                  signal_type=signal_type,
                                  signal_name=signal_name)
            array_attributes = slf.models.ArrayAttributes(
                name=signal_name,
                start_ts=start_ts,
                sampling_rate=fs,
                unit=unit
            )
            sample_array = slf.models.SampleArray(
                attributes=array_attributes,
                values_func=s_load_func
            )

            sample_arrays[signal_name] = sample_array

    return sample_arrays


def read_subject(h5_path: Path):
    h5 = h5py.File(h5_path, 'r')

    # Presumably, there are no event annotations, so raise an error events are found
    assert len(h5['events']) == 0, f'There are events for {h5_path}'

    # Some recordings are missing start_time, substitute with zero
    try:
        start_ts = dt.fromtimestamp(h5.attrs['start_time'])
    except KeyError:
        start_ts = dt.utcfromtimestamp(0)

    sample_arrays = read_sample_arrays(h5, h5_path, start_ts)
    hg = read_hypnogram(h5, start_ts)

    metadata = slf.models.SubjectMetadata(
        subject_id=h5_path.stem,
        recording_start_ts=start_ts
    )

    return slf.models.Subject(
        metadata=metadata,
        sample_arrays=sample_arrays,
        annotations={'hypnogram': hg}
    )


def read_to_slf(h5_dir: Path):
    series = {}

    for subdir in h5_dir.iterdir():
        series_name = subdir.name
        subjects = {}
        h5_paths = [p for p in subdir.iterdir() if p.suffix == '.h5']

        for h5_path in h5_paths:
            logger.info(f'Parsing subject data from {h5_path.name}')
            subject = read_subject(h5_path)
            subjects[subject.metadata.subject_id] = subject

        series[series_name] = slf.models.Series(name=series_name, subjects=subjects)

    dataset = slf.models.Dataset(name=h5_dir.name, series=series)

    return dataset


def convert_data(h5_dir: Path, slf_dir: Path):
    logger.info(f'Reading data to slf Dataset from {h5_dir}')
    dataset = read_to_slf(h5_dir)

    logger.info(f'Writing the dataset to {slf_dir}')
    # Write annotations in parquet format, since sleeplab-tf-dataset supports it at the moment
    slf.writer.write_dataset(dataset, slf_dir, annotation_format='parquet')


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--src-dir', help='the h5 data dir')
    parser.add_argument('-d', '--dst-dir', help='the directory where the slf dataset is saved')

    return parser


if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()
    convert_data(Path(args.src_dir), Path(args.dst_dir))

"""Convert DOD data from h5 files to sleeplab format."""
import argparse
import h5py
import logging
import numpy as np
import sleeplab_format as slf

from datetime import datetime as dt
from datetime import timedelta
from datetime import timezone
from functools import partial
from pathlib import Path
from zoneinfo import ZoneInfo


logger = logging.getLogger(__name__)


def read_hypnogram(h5: h5py.File, start_ts: dt, epoch_sec: float = 30.0) -> slf.models.Hypnogram:
    """Read the hypnogram from .h5 file and parse to sleeplab format."""
    stage_map = {
        -1: slf.models.AASMSleepStage.UNSCORED,
        0: slf.models.AASMSleepStage.W,
        1: slf.models.AASMSleepStage.N1,
        2: slf.models.AASMSleepStage.N2,
        3: slf.models.AASMSleepStage.N3,
        4: slf.models.AASMSleepStage.R
    }
    h5_hg = h5['hypnogram'][:]
    annotations = []

    for i, h5_stage in enumerate(h5_hg):
        start_delta = i * timedelta(seconds=epoch_sec)
        stage = slf.models.Annotation[slf.models.AASMSleepStage](
            name=stage_map[h5_stage],
            start_ts=start_ts + start_delta,
            start_sec=float(start_delta.seconds),
            duration=epoch_sec
        )
        annotations.append(stage)

    return slf.models.Hypnogram(annotations=annotations, scorer='manual_consensus')


def read_signal_from_h5_file(h5_path: Path, signal_type: str, signal_name: str) -> np.ndarray:
    h5 = h5py.File(h5_path, 'r')
    s = h5['signals'][signal_type][signal_name][:].astype(np.float32)
    return s


def read_sample_arrays(
        h5: h5py.File,
        h5_path: Path,
        start_ts: dt) -> dict[str, slf.models.SampleArray]:
    """Read all signals from a .h5 file and parse to sleeplab format."""
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


def read_subject(h5_path: Path, tz: str) -> slf.models.Subject:
    """Read the signals and hypnogram from .h5 file and parse to sleeplab format Subject.

    Args:
        tz: The timezone as string. The original start_times are as UTC, and
            we want to convert them to correct local times ('US/Pacific' for DOD-O, 'CET' for DOD-H)
    """
    h5 = h5py.File(h5_path, 'r')

    # Presumably, there are no event annotations, so raise an error events are found
    assert len(h5['events']) == 0, f'There are events for {h5_path}'

    # Some recordings are missing start_time, substitute with zero
    try:
        start_ts = (dt
            .fromtimestamp(h5.attrs['start_time'], tz=timezone.utc)
            .astimezone(ZoneInfo(tz))  # Use aware timestamp to specify timezone
            .replace(tzinfo=None)  # Convert to naive timestamp
        )
    except KeyError:
        # If start_time is not found, just use Unix epoch 0
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
        annotations={f'{hg.scorer}_{hg.type}': hg}
    )


def read_to_slf(h5_dir: Path) -> slf.models.Dataset:
    """Parse the whole dataset to sleeplab format Dataset."""
    series = {}

    for subdir in h5_dir.iterdir():
        series_name = subdir.name
        subjects = {}
        h5_paths = [p for p in subdir.iterdir() if p.suffix == '.h5']

        if series_name == 'dodh':
            # DOD-H was recorded in Bretigny-Sur-Orge, France
            tz = 'CET'
        elif series_name == 'dodo':
            # DOD-O was recorded in Stanford, US
            tz = 'US/Pacific'

        for h5_path in h5_paths:
            logger.info(f'Parsing subject data from {h5_path.name}')
            subject = read_subject(h5_path, tz)
            subjects[subject.metadata.subject_id] = subject

        series[series_name] = slf.models.Series(name=series_name, subjects=subjects)

    dataset = slf.models.Dataset(name=h5_dir.name, series=series)

    return dataset


def convert_data(h5_dir: Path, slf_dir: Path, array_format: str = 'numpy', clevel: int = 9) -> None:
    """Run the conversion from .h5 files to sleeplab format."""
    logger.info(f'Reading data to slf Dataset from {h5_dir}')
    dataset = read_to_slf(h5_dir)

    logger.info(f'Writing the dataset to {slf_dir}')
    # The format for annotation files can be 'json' or 'parquet'.
    # array_format can be 'numpy' or 'parquet'. Parquet files will be smaller due to compression.
    slf.writer.write_dataset(dataset, slf_dir, annotation_format='json',
                             array_format=array_format, compression_level=clevel)


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--src-dir', help='the h5 data dir')
    parser.add_argument('-d', '--dst-dir', help='the directory where the slf dataset is saved')
    parser.add_argument('--array-format', default='numpy', help='Save format of the arrays; `numpy`, `parquet` or `zarr`')
    parser.add_argument('--clevel', type=int, default=9, help='Compression level used with zarr.')

    return parser


if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()
    convert_data(Path(args.src_dir), Path(args.dst_dir), args.array_format, args.clevel)

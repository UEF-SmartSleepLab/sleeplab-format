import argparse
import logging
import numpy as np
import pandas as pd
import sleeplab_format as slf

from datetime import datetime, timedelta
from functools import partial
from pathlib import Path
from pyedflib import highlevel
from typing import Any


logger = logging.getLogger(__name__)


def parse_hypnogram(ann_header: dict[str, Any], scorer: str) -> slf.models.RKHypnogram:
    """Parse the sleep stages according to Rechtschaffen and Kales."""
    stage_map = {
        'Sleep stage W': slf.models.RKSleepStage.W,
        'Sleep stage 1': slf.models.RKSleepStage.S1,
        'Sleep stage 2': slf.models.RKSleepStage.S2,
        'Sleep stage 3': slf.models.RKSleepStage.S3,
        'Sleep stage 4': slf.models.RKSleepStage.S4,
        'Sleep stage R': slf.models.RKSleepStage.R,
        'Movement time': slf.models.RKSleepStage.MOVEMENT,
        'Sleep stage ?': slf.models.RKSleepStage.UNSCORED,
    }
    annotations = [
        slf.models.Annotation[slf.models.RKSleepStage](
            name=stage_map[stage_str],
            start_ts=ann_header['startdate'] + timedelta(seconds=start_sec),
            start_sec=start_sec,
            duration=float(duration)
        )
        for start_sec, duration, stage_str in ann_header['annotations']
    ]

    return slf.models.RKHypnogram(scorer=scorer, annotations=annotations)


def read_signal_from_edf(edf_path: Path, ch_name, dtype=np.float32) -> np.array:
    """Read a single signal from an EDF file."""
    s, _, _ = highlevel.read_edf(str(edf_path), ch_names=ch_name)
    assert s.ndim == 2 and s.shape[0] == 1
    return s[0].astype(dtype)


def parse_sample_arrays(psg_path: Path) -> dict[str, slf.models.SampleArray]:
    """Parse all sample arrays from a PSG EDF file."""
    sample_arrays = {}
    headers = highlevel.read_edf_header(str(psg_path))
    for sig_header in headers['SignalHeaders']:
        # We define a function that loads and returns the signal
        # to avoid reading all signals of all subjects into memory at the same time
        s_load_func = partial(read_signal_from_edf, edf_path=psg_path, ch_name=sig_header['label'])
        array_attributes = slf.models.ArrayAttributes(
            name=sig_header['label'],
            start_ts=headers['startdate'],
            sampling_rate=sig_header['sample_frequency'],
            unit=sig_header['dimension'],
            sensor_info=sig_header['transducer'],
            amplifier_info=sig_header['prefilter']
        )
        sarr = slf.models.SampleArray(attributes=array_attributes, values_func=s_load_func)
        sample_arrays[sig_header['label']] = sarr

    return sample_arrays


def resolve_lightsoff(d, t):
    """Figure out if the date of lights off is the same as start_ts or the next."""
    if t >= d.time():
        return datetime.combine(d.date(), t)
    else:
        return datetime.combine((d + timedelta(days=1)).date(), t)


def parse_subject(src_dir: Path, meta: pd.Series) -> slf.models.Subject:
    """Parse the PSG recording and annotations for a single Subject."""
    # Parse recording
    sc_dir = src_dir / 'sleep-cassette'
    psg_path = next(sc_dir.glob(f'SC4{meta.subject:02d}{meta.night}*PSG.edf'))
    sample_arrays = parse_sample_arrays(psg_path)

    # Parse annotations
    # The eight letter of annotation file name is the scorer id
    ann_path = next(sc_dir.glob(f'SC4{meta.subject:02d}{meta.night}*Hypnogram.edf'))
    scorer = ann_path.name[7]
    ann_header = highlevel.read_edf_header(str(ann_path))
    hg = parse_hypnogram(ann_header, scorer)

    # Need to parse lights off using start_ts, since meta.LightsOff has only time, not date
    start_ts = ann_header['startdate']
    lights_off = resolve_lightsoff(start_ts, meta.LightsOff)

    metadata = slf.models.SubjectMetadata(
        subject_id=str(meta.subject),
        recording_start_ts=start_ts,
        lights_off=lights_off,
        age=meta.age,
        sex=slf.models.Sex.FEMALE if meta['sex (F=1)'] == 1 else slf.models.Sex.MALE
    )

    return slf.models.Subject(
        metadata=metadata,
        sample_arrays=sample_arrays,
        annotations={f'{hg.scorer}_{hg.type}': hg}
    )


def convert_data(
        src_dir: Path,
        dst_dir: Path,
        annotation_format: str,
        array_format: str,
        clevel: int) -> None:
    """Convert the sleep-cassette dataset to sleeplab format."""    
    # SC-subjects.xls contains ID, night, age, sex, and lights off time for each subject.
    excel_path = src_dir / 'SC-subjects.xls'
    meta_df = pd.read_excel(excel_path)

    # Sleep-cassette consists of two 20h PSGs recorded on consecutive days (1 and 2).
    all_subjects = {1: {}, 2: {}}
    for _, s in meta_df.iterrows():
        subject = parse_subject(src_dir, s)
        all_subjects[s.night][str(s.subject)] = subject
        
    night1_series = slf.models.Series(name='sc-night1', subjects=all_subjects[1])
    night2_series = slf.models.Series(name='sc-night2', subjects=all_subjects[2])
    ds = slf.models.Dataset(
        name='sleep-cassette',
        series={'sc-night1': night1_series, 'sc-night2': night2_series})

    slf.writer.write_dataset(ds, dst_dir, annotation_format=annotation_format,
                             array_format=array_format, compression_level=clevel)


def _create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-s', '--src-dir', help='Path to the sleep-edfx root folder, e.g. `sleep-edfx/1.0.0`')
    parser.add_argument(
        '-d', '--dst-dir', help='Path to the folder where the sleeplab-format dataset is saved.')
    parser.add_argument('--array-format', default='numpy', help='Array format, `numpy` or `zarr`')
    parser.add_argument('--annotation-format', default='json', help='Annotation format, `json` or `parquet`')
    parser.add_argument('--clevel', type=int, default=9, help='Compression level for the numerical arrays.')
    
    return parser


if __name__ == '__main__':
    parser = _create_parser()
    args = parser.parse_args()

    convert_data(
        src_dir=Path(args.src_dir).expanduser(),
        dst_dir=Path(args.dst_dir).expanduser(),
        annotation_format=args.annotation_format,
        array_format=args.array_format,
        clevel=args.clevel
    )

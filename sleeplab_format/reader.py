"""Read files into sleeplab format.

The data will be validated while parsing.
"""
import logging

from sleeplab_format.models import *
from pathlib import Path


logger = logging.getLogger(__name__)


ANNOTATION_SUFFIX = '_annotated.json'


def read_sample_arrays(subject_dir: Path) -> dict[str, SampleArray] | None:
    sarrs = {}
    for p in subject_dir.iterdir():
        if p.is_dir():
            attributes = ArrayAttributes.parse_file(p / 'attributes.json')

            val_path = [f for f in p.iterdir() if f.name == 'data.npy']
            assert len(val_path) == 1, 'exactly one .npy file required for array values'
            val_path = val_path[0]
            values_func = lazy_memmap_array(val_path)

            sarrs[p.name] = SampleArray(
                attributes=attributes, values_func=values_func)
    return sarrs


def read_annotations(subject_dir: Path) -> dict[str, list[Annotation]] | None:
    annotations = {}
    for p in subject_dir.iterdir():

        if p.is_file() and p.name.endswith(ANNOTATION_SUFFIX):            
            annotation_name = p.name.removesuffix(ANNOTATION_SUFFIX)
            annotations[annotation_name] = Annotations.parse_file(p)

    if len(annotations) == 0:
        return None
    return annotations


def read_study_logs(subject_dir: Path) -> list[LogEntry] | None:
    p = subject_dir / 'study_logs.json'
    if not p.exists():
        return None
    
    logs = Logs.parse_file(p)
    return logs


def read_subject(subject_dir: Path) -> Subject:
    metadata = SubjectMetadata.parse_file(subject_dir / 'metadata.json')
    
    sample_arrays = read_sample_arrays(subject_dir)

    annotations = read_annotations(subject_dir)

    study_logs = read_study_logs(subject_dir)

    return Subject(
        metadata=metadata,
        sample_arrays=sample_arrays,
        annotations=annotations,
        study_logs=study_logs
    )


def read_series(series_dir: Path) -> Series:
    return Series(
        name=series_dir.stem,
        subjects={subject_dir.stem: read_subject(subject_dir)
            for subject_dir in series_dir.iterdir()}
    )


def read_dataset(ds_dir: Path) -> Dataset:
    name = ds_dir.stem
    series = {series_dir.stem: read_series(series_dir)
        for series_dir in ds_dir.iterdir()}
    return Dataset(
        name=name,
        series=series
    )

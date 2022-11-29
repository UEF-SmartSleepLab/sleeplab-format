"""Write validated data into sleeplab format.

The data needs to conform to the types specified in
dataset_generation.data_types
"""
import logging
import numpy as np

from sleeplab_format.models import *
from pathlib import Path


logger = logging.getLogger(__name__)


JSON_INDENT = 2


def write_subject_metadata(
        subject: Subject,
        subject_path: Path) -> None:
    metadata_path = subject_path / 'metadata.json'
    metadata_path.write_text(
        subject.metadata.json(indent=JSON_INDENT, exclude_unset=True),
    )


def write_sample_arrays(
        subject: Subject,
        subject_path: Path) -> None:
    for name, sarr in subject.sample_arrays.items():
        sarr_path = subject_path / f'{sarr.attributes.name}'
        sarr_path.mkdir(exist_ok=True)
        
        # Write the attributes
        attr_path = sarr_path / 'attributes.json'
        attr_path.write_text(
            sarr.attributes.json(indent=JSON_INDENT, exclude_unset=True))

        # Write the array
        arr_fname = 'data.npy'
        np.save(sarr_path / arr_fname, sarr.values, allow_pickle=False)


def write_annotations(
        subject: Subject,
        subject_path: Path) -> None:
    for k, v in subject.annotations.items():
        # Write as JSON
        json_path = subject_path / f'{k}_annotated.json'
        json_path.write_text(
            v.json(exclude_unset=True, indent=JSON_INDENT)
        )


def write_study_logs(subject: Subject, subject_path: Path) -> None:
    json_path = subject_path / 'study_logs.json'
    json_path.write_text(
        subject.study_logs.json(indent=JSON_INDENT)
    )


def write_subject(
        subject: Subject,
        subject_path: Path) -> None:
    subject_path.mkdir(exist_ok=True)
    write_subject_metadata(subject, subject_path)
    
    write_sample_arrays(subject, subject_path)

    if subject.annotations is not None:
        write_annotations(subject, subject_path)

    if subject.study_logs is not None:
        write_study_logs(subject, subject_path)


def write_series(
        series: Series,
        series_path: Path) -> None:
    for sid, subject in series.subjects.items():
        logger.info(f'Writing subject ID {sid}...')
        subject_path = series_path / subject.metadata.subject_id
        write_subject(subject, subject_path)


def write_dataset(
        dataset: Dataset,
        basedir: str) -> None:
    # Create the folder
    dataset_path = Path(basedir) / dataset.name
    logger.info(f'Creating dataset dir {dataset_path}...')
    dataset_path.mkdir(parents=True, exist_ok=True)

    # Write the series
    for name, series in dataset.series.items():
        assert name == series.name
        logger.info(f'Writing data for series {series.name}...')
        series_path = dataset_path / series.name
        series_path.mkdir(exist_ok=True)

        write_series(series, series_path)
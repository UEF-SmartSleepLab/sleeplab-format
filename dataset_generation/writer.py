"""Write validated data into sleeplab format.

The data needs to conform to the types specified in
dataset_generation.data_types
"""
import json
import logging
import numpy as np

from dataset_generation.models import *
from pathlib import Path


logger = logging.getLogger(__name__)


JSON_INDENT = 2


def write_subject_metadata(
        subject: Subject,
        subject_path: Path) -> None:
    metadata_path = subject_path / 'metadata.json'
    metadata_path.write_text(subject.metadata.json(indent=JSON_INDENT))


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
        arr_fname = f'{subject.metadata.subject_id}_{sarr.attributes.name}.npy'
        np.save(sarr_path / arr_fname, sarr.values, allow_pickle=False)


def write_annotations(
        subject: Subject,
        subject_path: Path) -> None:
    for k, v in subject.annotations.items():
        # Write as JSON
        json_path = subject_path / f'{k}_annotated.json'
        json_path.write_text(
            # Use json.loads(a.json()) instead of a.dict()
            # to serialize datetimes properly...
            json.dumps([
                json.loads(a.json(exclude_unset=True)) for a in v],
                indent=JSON_INDENT)
        )


def write_study_logs(subject: Subject, subject_path: Path) -> None:
    json_path = subject_path / 'study_logs.json'
    json_path.write_text(
        # Use json.loads(entry.json()) instead of entry.dict()
        # to serialize datetimes properly...
        json.dumps([
            json.loads(entry.json(exclude_unset=True)) for entry in subject.study_logs],
            indent=JSON_INDENT)
    )


def write_subject(
        subject: Subject,
        subject_path: Path) -> None:
    subject_path.mkdir(exist_ok=True)
    write_subject_metadata(subject, subject_path)
    
    write_sample_arrays(subject, subject_path)

    write_annotations(subject, subject_path)

    write_study_logs(subject, subject_path)


def write_study(
        study: Study,
        study_path: Path) -> None:
    for sid, subject in study.subjects.items():
        logger.info(f'Writing subject ID {sid}...')
        subject_path = study_path / subject.metadata.subject_id
        write_subject(subject, subject_path)


def write_dataset(
        dataset: Dataset,
        basedir: str) -> None:
    # Create the folder
    dataset_path = Path(basedir) / dataset.name
    logger.info(f'Creating dataset dir {dataset_path}...')
    dataset_path.mkdir(parents=True, exist_ok=True)

    # Write the studies
    for name, study in dataset.studies.items():
        assert name == study.name
        logger.info(f'Writing data for study {study.name}...')
        study_path = dataset_path / study.name
        study_path.mkdir(exist_ok=True)

        write_study(study, study_path)
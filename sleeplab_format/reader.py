"""Read files into sleeplab format.

The data will be validated while parsing.
"""
import json
import logging
import pandas as pd

from sleeplab_format.models import *
from pathlib import Path


logger = logging.getLogger(__name__)


JSON_ANNOTATION_SUFFIX = '_annotated.json'
PARQUET_ANNOTATION_SUFFIX = '_annotated.parquet'
PARQUET_ANNOTATION_META_SUFFIX = '_annotated_metadata.json'


def read_sample_arrays(subject_dir: Path) -> dict[str, SampleArray] | None:
    sarrs = {}
    for p in subject_dir.iterdir():
        if p.is_dir():
            attributes = ArrayAttributes.parse_file(p / 'attributes.json')

            val_path = p / 'data.npy'
            values_func = lazy_memmap_array(val_path)

            sarrs[p.name] = SampleArray(
                attributes=attributes, values_func=values_func)
    return sarrs


def read_annotations(subject_dir: Path) -> dict[str, list[Annotation]] | None:
    annotations = {}
    for p in subject_dir.iterdir():

        if p.name.endswith(JSON_ANNOTATION_SUFFIX):            
            annotation_name = p.name.removesuffix(JSON_ANNOTATION_SUFFIX)
            annotations[annotation_name] = Annotations.parse_file(p)
        elif p.name.endswith(PARQUET_ANNOTATION_SUFFIX):
            annotation_name = p.name.removesuffix(PARQUET_ANNOTATION_SUFFIX)
            annotation_meta_path = subject_dir / f'{annotation_name}{PARQUET_ANNOTATION_META_SUFFIX}'

            with open(annotation_meta_path, 'r') as f:
                ann_dict = json.load(f)

            ann_df = pd.read_parquet(p)
            ann_dict['annotations'] = ann_df.to_dict('records')

            annotations[annotation_name] = Annotations.parse_obj(ann_dict)

    if len(annotations) == 0:
        return None
    return annotations


def read_study_logs(subject_dir: Path) -> list[LogEntry] | None:
    p_json = subject_dir / 'study_logs.json'
    if p_json.exists():
        logs = Logs.parse_file(p_json)
        return logs
    
    p_parquet = subject_dir / 'study_logs.parquet'
    if p_parquet.exists():
        logs = pd.read_parquet(p_parquet).to_dict('records')
        return Logs.parse_obj({'logs': logs})

    return None


def read_subject(
        subject_dir: Path,
        include_logs: bool = True,
        include_annotations: bool = True) -> Subject:
    metadata = SubjectMetadata.parse_file(subject_dir / 'metadata.json')
    
    sample_arrays = read_sample_arrays(subject_dir)

    if include_annotations:
        annotations = read_annotations(subject_dir)
    else:
        annotations = None

    if include_logs:
        study_logs = read_study_logs(subject_dir)
    else:
        study_logs = None

    return Subject(
        metadata=metadata,
        sample_arrays=sample_arrays,
        annotations=annotations,
        study_logs=study_logs
    )


def read_series(
        series_dir: Path,
        include_logs: bool = True,
        include_annotations: bool = True) -> Series:
    return Series(
        name=series_dir.stem,
        subjects={subject_dir.stem: read_subject(
                subject_dir, include_logs=include_logs, include_annotations=include_annotations)
            for subject_dir in series_dir.iterdir()}
    )


def read_dataset(
        ds_dir: Path,
        series_names: list[str] | None = None,
        include_logs: bool = True,
        include_annotations: bool = True) -> Dataset:
    name = ds_dir.stem
    if series_names is None:
        series = {series_dir.stem: read_series(
                series_dir, include_logs=include_logs, include_annotations=include_annotations)
            for series_dir in ds_dir.iterdir()}
    else:
        series = {series_name: read_series(
                ds_dir / series_name, include_logs=include_logs, include_annotations=include_annotations)
            for series_name in series_names}
    
    return Dataset(
        name=name,
        series=series
    )

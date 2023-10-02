"""Read files into sleeplab format.

The data will be validated while parsing.
"""
import json
import logging
import pandas as pd
import pyarrow.parquet as pq

from sleeplab_format.models import *
from pathlib import Path


logger = logging.getLogger(__name__)


JSON_ANNOTATION_SUFFIX = '.a.json'
PARQUET_ANNOTATION_SUFFIX = '.a.parquet'
PARQUET_ANNOTATION_META_SUFFIX = '.a_meta.json'


def read_sample_arrays(subject_dir: Path) -> dict[str, SampleArray] | None:
    sarrs = {}
    for p in subject_dir.iterdir():
        if p.is_dir() and not p.name.startswith('.'):
            with open(p / 'attributes.json', 'rb') as f:
                raw_data = f.read()
                attributes = ArrayAttributes.model_validate_json(raw_data)

            if (p / 'data.npy').exists():
                # Return a function that returns a memmapped numpy array
                values_func = lambda _p=p / 'data.npy': np.load(
                    _p, mmap_mode='r', allow_pickle=False)
            elif (p / 'data.parquet').exists():
                values_func = lambda _p=p / 'data.parquet': pq.read_table(
                    _p)['data'].to_numpy()
            else:
                raise FileNotFoundError(f'No data.npy or data.parquet in {p}')

            assert p.name == attributes.name
            sarrs[p.name] = SampleArray(
                attributes=attributes, values_func=values_func)
    return sarrs


def read_annotations(subject_dir: Path) -> dict[str, list[Annotation]] | None:
    annotations = {}
    for p in subject_dir.iterdir():

        if p.name.endswith(JSON_ANNOTATION_SUFFIX):            
            annotation_name = p.name.removesuffix(JSON_ANNOTATION_SUFFIX)
            with open(p, 'rb') as f:
                raw_data = f.read()
                annotations[annotation_name] = BaseAnnotations.model_validate_json(raw_data)
        elif p.name.endswith(PARQUET_ANNOTATION_SUFFIX):
            annotation_name = p.name.removesuffix(PARQUET_ANNOTATION_SUFFIX)
            annotation_meta_path = subject_dir / f'{annotation_name}{PARQUET_ANNOTATION_META_SUFFIX}'

            with open(annotation_meta_path, 'r') as f:
                ann_dict = json.load(f)

            ann_df = pd.read_parquet(p)
            ann_dict['annotations'] = ann_df.to_dict('records')

            annotations[annotation_name] = BaseAnnotations.model_validate(ann_dict)

    if len(annotations) == 0:
        return None
    return annotations


def read_subject(
        subject_dir: Path,
        include_annotations: bool = True) -> Subject:
    with open(subject_dir / 'metadata.json', 'rb') as f:
        raw_data = f.read()
        metadata = SubjectMetadata.model_validate_json(raw_data)
    
    sample_arrays = read_sample_arrays(subject_dir)

    if include_annotations:
        annotations = read_annotations(subject_dir)
    else:
        annotations = None

    return Subject(
        metadata=metadata,
        sample_arrays=sample_arrays,
        annotations=annotations,
    )


def read_series(
        series_dir: Path,
        include_annotations: bool = True) -> Series:
    return Series(
        name=series_dir.name,
        subjects={subject_dir.name: read_subject(
                subject_dir, include_annotations=include_annotations)
            for subject_dir in series_dir.iterdir()
            if not subject_dir.name.startswith('.')}  # Ignore hidden folders.
    )


def read_dataset(
        ds_dir: Path,
        series_names: list[str] | None = None,
        include_annotations: bool = True) -> Dataset:
    with open(ds_dir / 'metadata.json', 'r') as f:
        ds_meta = json.load(f)

    assert ds_meta['name'] == ds_dir.name
    if ds_meta['version'] != SLEEPLAB_FORMAT_VERSION:
        logger.warning(
            f'Reading dataset version {ds_meta["version"]} with sleeplab-format version {SLEEPLAB_FORMAT_VERSION}')

    if series_names is None:
        series = {series_dir.name: read_series(
                series_dir, include_annotations=include_annotations)
            for series_dir in ds_dir.iterdir()
            if series_dir.is_dir() and not series_dir.name.startswith('.')}  # Ignore hidden folders.
    else:
        series = {series_name: read_series(
                ds_dir / series_name, include_annotations=include_annotations)
            for series_name in series_names}
    
    return Dataset(
        series=series,
        **ds_meta
    )

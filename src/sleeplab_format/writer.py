"""Write validated data into sleeplab format.

The data needs to conform to the types specified in
dataset_generation.data_types
"""
import json
import logging
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from sleeplab_format.models import *
from sleeplab_format.reader import (
    JSON_ANNOTATION_SUFFIX,
    PARQUET_ANNOTATION_SUFFIX,
    PARQUET_ANNOTATION_META_SUFFIX
)
from pathlib import Path


logger = logging.getLogger(__name__)


JSON_INDENT = 2


def write_subject_metadata(
        subject: Subject,
        subject_path: Path) -> None:
    metadata_path = subject_path / 'metadata.json'
    metadata_path.write_text(
        subject.metadata.model_dump_json(indent=JSON_INDENT, exclude_none=True),
    )


def write_sample_arrays(
        subject: Subject,
        subject_path: Path,
        format: str = 'numpy') -> None:
    for name, sarr in subject.sample_arrays.items():
        assert name == sarr.attributes.name
        sarr_path = subject_path / f'{sarr.attributes.name}'
        sarr_path.mkdir(exist_ok=True)
        
        # Write the attributes
        attr_path = sarr_path / 'attributes.json'
        attr_path.write_text(
            sarr.attributes.model_dump_json(indent=JSON_INDENT, exclude_none=True))

        arr = sarr.values_func()
        if format == 'numpy':
            # Write the array
            arr_fname = 'data.npy'
            np.save(sarr_path / arr_fname, arr, allow_pickle=False)
        elif format == 'parquet':
            arr_fname = 'data.parquet'

            # Utilize Arrow to write the data to Parquet file
            arrow_table = pa.Table.from_arrays([arr], names=['data'])

            # Parquet uses Snappy as compression algorithm by default
            pq.write_table(arrow_table, sarr_path / arr_fname)
        else:
            raise AttributeError(f'Unsupported sample array format: {format}')


def write_annotations(
        subject: Subject,
        subject_path: Path,
        format: str = 'json') -> None:
    for k, v in subject.annotations.items():
        _msg = f'Annotation key should equal to "{v.scorer}_{v.type}", got "{k}"'
        assert k == f'{v.scorer}_{v.type}', _msg
        
        if format == 'json':
            json_path = subject_path / f'{k}{JSON_ANNOTATION_SUFFIX}'
            json_path.write_text(
                v.model_dump_json(exclude_none=True, indent=JSON_INDENT)
            )
        else:
            # Write the actual annotations in parquet, metadata in json
            metadata_path = subject_path / f'{k}{PARQUET_ANNOTATION_META_SUFFIX}'
            pq_path = subject_path / f'{k}{PARQUET_ANNOTATION_SUFFIX}'
            
            ann_dict = v.model_dump()
            ann_list = ann_dict.pop('annotations')
            
            with open(metadata_path, 'w') as f:
                json.dump(ann_dict, f)
            
            pd.DataFrame(ann_list).to_parquet(pq_path)


def write_subject(
        subject: Subject,
        subject_path: Path,
        annotation_format: str = 'json',
        array_format: str = 'numpy') -> None:
    subject_path.mkdir(exist_ok=True)
    write_subject_metadata(subject, subject_path)
    
    write_sample_arrays(subject, subject_path, format=array_format)

    if subject.annotations is not None:
        write_annotations(subject, subject_path, format=annotation_format)


def write_series(
        series: Series,
        series_path: Path,
        annotation_format: str = 'json',
        array_format: str = 'numpy') -> None:
    for sid, subject in series.subjects.items():
        logger.info(f'Writing subject ID {sid}...')
        subject_path = series_path / subject.metadata.subject_id
        write_subject(
            subject,
            subject_path,
            annotation_format=annotation_format,
            array_format=array_format)


def write_dataset(
        dataset: Dataset,
        basedir: str,
        annotation_format: str = 'json',
        array_format: str = 'numpy') -> None:
    assert annotation_format in ['json', 'parquet']
    assert array_format in ['numpy', 'parquet']

    # Create the folder
    dataset_path = Path(basedir) / dataset.name
    logger.info(f'Creating dataset dir {dataset_path}...')
    dataset_path.mkdir(parents=True, exist_ok=True)

    # Write the dataset metadata
    metadata_path = dataset_path / 'metadata.json'
    metadata_path.write_text(
        dataset.model_dump_json(exclude={'series'}, indent=JSON_INDENT))

    # Write the series
    for name, series in dataset.series.items():
        assert name == series.name
        logger.info(f'Writing data for series {series.name}...')
        series_path = dataset_path / series.name
        series_path.mkdir(exist_ok=True)

        write_series(
            series,
            series_path,
            annotation_format=annotation_format,
            array_format=array_format)

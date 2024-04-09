"""Write validated data into sleeplab format.

The data needs to conform to the types specified in
`sleeplab_format.models`.
"""
import json
import logging
import numcodecs
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import zarr

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
    """Write subject metadata to JSON file.
    
    Arguments:
        subject: The sleeplab_format.models.Subject whose metadata will be saved.
        subject_path: The path to the subject folder.
    """
    metadata_path = subject_path / 'metadata.json'
    metadata_path.write_text(
        subject.metadata.model_dump_json(indent=JSON_INDENT, exclude_none=True),
        encoding='utf-8'
    )


def write_sample_arrays(
        subject: Subject,
        subject_path: Path,
        format: str = 'numpy',
        zarr_chunksize: int | None = 5e6,
        zarr_compression_level: int = 9) -> None:
    """Write all sample arrays of the subject.
    
    Arguments:
        subject: The sleeplab.models.Subject instance.
        subject_path: Path to the folder where the sample arrays are saved.
        format: The save format for the numerical arrays; `numpy`, `parquet` or `zarr`.
        zarr_chunksize: The chunk size in bytes if `format='zarr'`.
        zarr_compression_level: The compression level used with the Zstandard compression.
    """
    for name, sarr in subject.sample_arrays.items():
        assert name == sarr.attributes.name
        sarr_path = subject_path / f'{sarr.attributes.name}'
        sarr_path.mkdir(exist_ok=True)
        
        # Write the attributes
        attr_path = sarr_path / 'attributes.json'
        attr_path.write_text(
            sarr.attributes.model_dump_json(indent=JSON_INDENT, exclude_none=True), encoding='utf-8')

        arr = sarr.values_func()
        if format == 'numpy':
            # Write the array
            arr_fname = 'data.npy'
            np.save(sarr_path / arr_fname, arr, allow_pickle=False)
        elif format == 'zarr':
            arr_fname = 'data.zarr'
            #shuffler = numcodecs.Shuffle(elementsize=4)
            #delta = numcodecs.Delta(dtype='i2')
            #compressor = numcodecs.Blosc(cname='zstd', clevel=5, shuffle=numcodecs.Blosc.NOSHUFFLE)
            #compressor = numcodecs.Blosc(cname='zstd', clevel=9, shuffle=numcodecs.Blosc.NOSHUFFLE)
            #compressor = numcodecs.Blosc(cname='lz4', clevel=5, shuffle=numcodecs.Blosc.NOSHUFFLE)
            #compressor = numcodecs.ZFPY(mode=4, tolerance=1e-3)
            #zarr.save_array(sarr_path / arr_fname, arr, filters=[shuffler, delta], compressor=compressor)
            if zarr_chunksize is not None:
                # Chunk size from bytes to samples
                chunks = (zarr_chunksize // arr.dtype.itemsize,)
                z = zarr.array(arr, chunks=chunks)

            #compressor = numcodecs.Blosc(cname='zstd', clevel=zarr_compression_level, shuffle=numcodecs.Blosc.NOSHUFFLE)
            compressor = numcodecs.Zstd(level=zarr_compression_level)
            zarr.save_array(sarr_path / arr_fname, z, compressor=compressor)
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
    """Write SLF annotations to disk.
    
    Arguments:
        subject: A sleeplab_format.models.Subject whose annotations will be written.
        subject_path: The path to the subject folder.
        format: The format of annotation files.
    """
    for k, v in subject.annotations.items():
        _msg = f'Annotation key should equal to "{v.scorer}_{v.type}", got "{k}"'
        assert k == f'{v.scorer}_{v.type}', _msg
        
        if format == 'json':
            json_path = subject_path / f'{k}{JSON_ANNOTATION_SUFFIX}'
            json_path.write_text(
                v.model_dump_json(exclude_none=True, indent=JSON_INDENT),
                encoding='utf-8'
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
        array_format: str = 'numpy',
        compression_level: int = 9) -> None:
    """Write a single Subject to disk.
    
    Arguments:
        subject: A sleeplab_format.models.Subject to save.
        subject_path: Path to the subject save folder.
        annotation_format: The format of annotation files.
        array_format: The format of the sample array data files.
        compression_level: The zstd compression level if `array_format` is `zarr`.
    """
    subject_path.mkdir(exist_ok=True)
    write_subject_metadata(subject, subject_path)
    
    if subject.sample_arrays is not None:
        write_sample_arrays(subject, subject_path, format=array_format,
                            zarr_compression_level=compression_level)

    if subject.annotations is not None:
        write_annotations(subject, subject_path, format=annotation_format)


def write_series(
        series: Series,
        series_path: Path,
        annotation_format: str = 'json',
        array_format: str = 'numpy',
        compression_level: int = 9) -> None:
    """Write a sleeplab_format.models.Series to disk.
    
    Arguments:
        series: The sleeplab_format.models.Series to save.
        series_path: The path to the folder where the series will be saved.
        annotation_format: The format of the annotation files.
        array_format: The format of the sample array data files.
        compression_level: The zstd compression level if `array_format` is `zarr`.
    """
    for sid, subject in series.subjects.items():
        logger.info(f'Writing subject ID {sid}...')
        subject_path = series_path / subject.metadata.subject_id
        write_subject(
            subject,
            subject_path,
            annotation_format=annotation_format,
            array_format=array_format,
            compression_level=compression_level)


def write_dataset(
        dataset: Dataset,
        basedir: str,
        annotation_format: str = 'json',
        array_format: str = 'numpy',
        compression_level: int = 9) -> None:
    """Write a SLF dataset to disk.
    
    Arguments:
        dataset: A sleeplab_format.models.Dataset.
        basedir: The folder where the dataset will be saved.
        annotation_format: The format of the annotation files.
        array_format: The format of the sample array data files.
        compression_level: The zstd compression level if `array_format` is `zarr`.
    """
    assert annotation_format in ['json', 'parquet']
    assert array_format in ['numpy', 'parquet', 'zarr']

    # Create the folder
    dataset_path = Path(basedir) / dataset.name
    logger.info(f'Creating dataset dir {dataset_path}...')
    dataset_path.mkdir(parents=True, exist_ok=True)

    # Write the dataset metadata
    dataset.version = SLEEPLAB_FORMAT_VERSION
    metadata_path = dataset_path / 'metadata.json'
    metadata_path.write_text(
        dataset.model_dump_json(exclude={'series'}, indent=JSON_INDENT),
        encoding='utf-8'
    )

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
            array_format=array_format,
            compression_level=compression_level)

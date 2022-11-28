import pytest
import shutil

from dataset_generation.models import *
from pathlib import Path

# Use the same functions in fixtures that were used to create test files
from .create_datasets import create_datasets, events, hypnogram, sample_arrays, \
    study_logs, subject_metadata


@pytest.fixture(scope='session', autouse=True)
def recreate_test_files() -> None:
    """Recreate the separate test data files at the beginning of tests."""
    # First remove the old files if existing
    ds_dir = Path(__file__).parent / 'datasets'
    shutil.rmtree(ds_dir, ignore_errors=True)

    # Then recreate them
    create_datasets(ds_dir)


@pytest.fixture(scope='session')
def subject_ids():
    return ['10001', '10002', '10003']


@pytest.fixture
def subjects(subject_ids):
    subjs = {}
    for sid in subject_ids:
        metadata = SubjectMetadata(**subject_metadata(sid))
        
        dict_arrays = sample_arrays()
        arrays = {
            k: SampleArray(
                attributes=ArrayAttributes(**v['attributes']),
                values_func=lambda v=v: v['values'])
            for k, v in dict_arrays.items()
        }

        annotations = {
            'events': events(),
            'hypnogram': hypnogram()   
        }

        _study_logs = study_logs()

        subjs[sid] = Subject(
            metadata=metadata,
            sample_arrays=arrays,
            annotations=annotations,
            study_logs=_study_logs)

    return subjs


@pytest.fixture
def series(subjects):
    series = Series(
        name='series1',
        subjects=subjects
    )
    return {'series1': series}


@pytest.fixture
def dataset(series):
    dataset = Dataset(
        name='dataset1',
        series=series
    )
    return dataset

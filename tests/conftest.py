import numpy as np
import pytest

from dataset_generation.models import *

# Use the same functions in fixtures that were used to create test files
from .create_datasets import events, sample_arrays, subject_metadata


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

        annotations = {'events': events()}

        subjs[sid] = Subject(
            metadata=metadata, sample_arrays=arrays, annotations=annotations)

    return subjs


@pytest.fixture
def studies(subjects):
    study = Study(
        name='study1',
        subjects=subjects
    )
    return {'study1': study}


@pytest.fixture
def dataset(studies):
    dataset = Dataset(
        name='dataset1',
        studies=studies
    )
    return dataset

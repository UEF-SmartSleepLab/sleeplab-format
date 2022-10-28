import numpy as np
import pytest

from dataset_generation.models import *
from pydantic import ValidationError


def test_samplearray_values(dataset):
    for _, subj in dataset.studies['study1'].subjects.items():
        for _, sarr in subj.sample_arrays.items():
            assert np.all(sarr.values_func() == sarr.values)


def test_extra_fields_forbidden(subjects, studies):
    with pytest.raises(ValidationError):
        s = Subject(
            metadata=SubjectMetadata(subject_id='123', extra_field='extra'),
            sample_arrays={},
            annotations={}
        )

    with pytest.raises(ValidationError):
        s = Study(name='study', subjects=subjects, extra_field='extra')

    with pytest.raises(ValidationError):
        ds = Dataset(name='ds', studies=studies, extra_field='extra')

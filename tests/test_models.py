import numpy as np
import pytest

from sleeplab_format.models import *
from pydantic import ValidationError


def test_samplearray_values(dataset):
    for _, subj in dataset.series['series1'].subjects.items():
        for _, sarr in subj.sample_arrays.items():
            assert np.all(sarr.values_func() == sarr.values)


def test_extra_fields_forbidden(subjects, series):
    with pytest.raises(ValidationError):
        s = Subject(
            metadata=SubjectMetadata(subject_id='123', extra_field='extra'),
            sample_arrays={},
            annotations={}
        )

    with pytest.raises(ValidationError):
        s = Series(name='series', subjects=subjects, extra_field='extra')

    with pytest.raises(ValidationError):
        ds = Dataset(name='ds', series=series, extra_field='extra')

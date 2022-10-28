import pytest

from dataset_generation.models import *


def test_parse_correct(dataset):
    for sid in ['10001', '10002', '10003']:
        assert isinstance(dataset.studies['study1'].subjects[sid], Subject)
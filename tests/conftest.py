import pytest
import shutil

from sleeplab_format.models import *
from pathlib import Path

from .create_datasets import create_datasets
from sleeplab_format.test_utils.fixtures import *


@pytest.fixture(scope='session', autouse=True)
def recreate_test_files() -> None:
    """Recreate the separate test data files at the beginning of tests."""
    # First remove the old files if existing
    ds_dir = Path(__file__).parent / 'datasets'
    shutil.rmtree(ds_dir, ignore_errors=True)

    # Then recreate them
    create_datasets(ds_dir)


@pytest.fixture(scope='session')
def example_extractor_config_path():
    data_dir = Path(__file__).parent / 'extractor' / 'data'
    return data_dir / 'example_config.yml'

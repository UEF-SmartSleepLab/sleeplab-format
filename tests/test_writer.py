import subprocess

from sleeplab_format import writer
from pathlib import Path


def test_write_dataset(dataset, tmp_path):
    ds_dir = tmp_path / 'datasets'
    writer.write_dataset(dataset, ds_dir)

    # Assert that the created dataset is equal to tests/datasets
    tests_ds_dir = Path(__file__).parent / 'datasets'
    p = subprocess.run(['diff', '-r',
        str(ds_dir.resolve()), str(tests_ds_dir.resolve())])
    assert p.returncode == 0


def test_overwrite_existing_dataset(dataset, tmp_path):
    ds_dir = tmp_path / 'datasets'
    writer.write_dataset(dataset, ds_dir)

    # Assert that the created dataset is equal to tests/datasets
    tests_ds_dir = Path(__file__).parent / 'datasets'
    p = subprocess.run(['diff', '-r',
        str(ds_dir.resolve()), str(tests_ds_dir.resolve())])
    assert p.returncode == 0

    # Write again and assert
    writer.write_dataset(dataset, ds_dir)

    p = subprocess.run(['diff', '-r',
        str(ds_dir.resolve()), str(tests_ds_dir.resolve())])
    assert p.returncode == 0

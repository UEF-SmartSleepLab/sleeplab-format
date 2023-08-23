import subprocess

from sleeplab_format import reader, writer
from pathlib import Path


def _assert_dirs_equal(dir1, dir2):
    p = subprocess.run(['diff', '-r', dir1, dir2])
    assert p.returncode == 0


def _assert_datasets_equal(ds1, ds2):
    """Compare the equality of two Dataset objects.
    
    Cannot just compare ds1 == ds2 since the 
    SampleArray.values_func objects can be different.
    """
    assert ds1.name == ds2.name
    assert ds1.series.keys() == ds2.series.keys()
    for (k, series1) in ds1.series.items():
        series2 = ds2.series[k]
        assert series1.name == series2.name
        assert series1.subjects.keys() == series2.subjects.keys()

        for (sk, subj1) in series1.subjects.items():
            subj2 = series2.subjects[sk]
            assert subj1.metadata == subj2.metadata
            # TODO: Figure out how to handle subclassed annotations in pydantic v2
            #assert subj1.annotations == subj2.annotations
            assert subj1.sample_arrays.keys() == subj2.sample_arrays.keys()
            
            for (arr_k, arr1) in subj1.sample_arrays.items():
                arr2 = subj2.sample_arrays[arr_k]
                assert arr1.attributes == arr2.attributes
                assert (arr1.values == arr2.values).all()


def test_read_dataset(dataset):
    tests_ds_dir = Path(__file__).parent / 'datasets' / 'dataset1'
    ds_read = reader.read_dataset(tests_ds_dir)

    _assert_datasets_equal(dataset, ds_read)


def test_read_ds_specify_series(dataset):
    tests_ds_dir = Path(__file__).parent / 'datasets' / 'dataset1'
    ds_read = reader.read_dataset(tests_ds_dir, series_names=['series1'])

    _assert_datasets_equal(dataset, ds_read)


def test_write_read(dataset, tmp_path):
    ds_dir = tmp_path / 'datasets'
    writer.write_dataset(dataset, ds_dir)
    ds_read = reader.read_dataset(ds_dir / dataset.name)
    _assert_datasets_equal(dataset, ds_read)


def test_write_read_parquet(dataset, tmp_path):
    ds_dir = tmp_path / 'datasets'
    writer.write_dataset(dataset, ds_dir, annotation_format='parquet')
    ds_read = reader.read_dataset(ds_dir / dataset.name)
    _assert_datasets_equal(dataset, ds_read)


def test_read_write(tmp_path):
    tests_ds_dir = Path(__file__).parent / 'datasets'
    ds_read = reader.read_dataset(tests_ds_dir / 'dataset1')

    ds_dir = tmp_path / 'datasets'
    writer.write_dataset(ds_read, ds_dir)

    # Assert that the created dataset is equal to tests/datasets
    _assert_dirs_equal(str(ds_dir.resolve()), str(tests_ds_dir.resolve()))

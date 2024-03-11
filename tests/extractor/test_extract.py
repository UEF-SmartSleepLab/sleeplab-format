import numpy as np

from sleeplab_format.extractor import config, cli
from sleeplab_format import reader


def test_extract_preprocess(ds_dir, tmp_path, example_extractor_config_path):
    orig_ds = reader.read_dataset(ds_dir)
    dst_dir = tmp_path / 'extracted_datasets'
    
    cfg = config.parse_config(example_extractor_config_path)
    
    cli.extract(ds_dir, dst_dir, cfg)

    extr_ds = reader.read_dataset(dst_dir / 'dataset1_extracted')

    assert extr_ds.name == cfg.new_dataset_name
    assert len(extr_ds.series['series1'].subjects) == 3

    old_subj = orig_ds.series['series1'].subjects['10001']
    new_subj = extr_ds.series['series1'].subjects['10001']

    assert new_subj.sample_arrays['s1_8Hz'].attributes.name == 's1_8Hz'

    old_shape = old_subj.sample_arrays['s1'].values_func().shape
    new_shape = new_subj.sample_arrays['s1_8Hz'].values_func().shape
 
    assert old_shape[0] == 4 * new_shape[0]


def test_extract_preprocess_filter(ds_dir, tmp_path, example_extractor_config_path):
    dst_dir = tmp_path / 'extracted_datasets'
    
    cfg = config.parse_config(example_extractor_config_path)

    # There's 30s of sleep for each example subject. Raise min_tst_sec to 31s,
    # and all subjects should be filtered out.
    fconds = cfg.series_configs[0].filter_conds
    fconds[0].kwargs['min_tst_sec'] = 31.0
    
    cli.extract(ds_dir, dst_dir, cfg)
    extr_ds = reader.read_dataset(dst_dir / 'dataset1_extracted')

    assert len(extr_ds.series['series1'].subjects) == 0


def test_extract_zarr_load(ds_dir, tmp_path, example_extractor_config_path):
    dst_dir = tmp_path / 'extracted_datasets'

    cfg = config.parse_config(example_extractor_config_path)
    cfg.array_format = 'zarr'
    cli.extract(ds_dir, dst_dir, cfg)

    extr_ds = reader.read_dataset(dst_dir / 'dataset1_extracted')
    subj = extr_ds.series['series1'].subjects['10001']
    assert type(subj.sample_arrays['s1_8Hz'].values_func()) == np.ndarray

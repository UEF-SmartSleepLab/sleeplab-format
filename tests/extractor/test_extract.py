import json
import numpy as np
import pytest

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


def test_required_result_array_names(ds_dir, tmp_path, example_extractor_config_path):
    dst_dir = tmp_path / 'extracted_datasets'

    cfg = config.parse_config(example_extractor_config_path)
    cfg.series_configs[0].required_result_array_names = ['doesnotexist']
    cli.extract(ds_dir, dst_dir, cfg)
    extr_ds = reader.read_dataset(dst_dir / 'dataset1_extracted')

    assert len(extr_ds.series['series1'].subjects) == 0


def test_alt_names(ds_dir, tmp_path, example_extractor_config_path):
    dst_dir = tmp_path / 'extracted_datasets'

    cfg = config.parse_config(example_extractor_config_path)

    cfg.series_configs[0].array_configs[2].name = 'doesnotexist'
    cfg.series_configs[0].array_configs[2].alt_names = ['doesnotexist2']
    cli.extract(ds_dir, dst_dir, cfg)
    extr_ds = reader.read_dataset(dst_dir / 'dataset1_extracted')
    for s in extr_ds.series['series1'].subjects.values():
        assert 's2s1_32Hz' not in s.sample_arrays.keys()

    cfg.series_configs[0].array_configs[2].alt_names = ['doesnotexist2', 's2']
    cli.extract(ds_dir, dst_dir, cfg)
    extr_ds = reader.read_dataset(dst_dir / 'dataset1_extracted')
    for s in extr_ds.series['series1'].subjects.values():
        assert 's2s1_32Hz' in s.sample_arrays.keys()

def test_alt_ref_names(ds_dir, tmp_path, example_extractor_config_path):
    dst_dir = tmp_path / 'extracted_datasets'

    cfg = config.parse_config(example_extractor_config_path)

    cfg.series_configs[0].array_configs[2].actions[1].ref_name = 'doesnotexist'
    cfg.series_configs[0].array_configs[2].actions[1].alt_ref_names = ['doesnotexist2']
    cli.extract(ds_dir, dst_dir, cfg)
    extr_ds = reader.read_dataset(dst_dir / 'dataset1_extracted')
    for s in extr_ds.series['series1'].subjects.values():
        assert 's2s1_32Hz' not in s.sample_arrays.keys()

    cfg.series_configs[0].array_configs[2].actions[1].alt_ref_names = ['doesnotexist2', 's1']
    cli.extract(ds_dir, dst_dir, cfg)
    extr_ds = reader.read_dataset(dst_dir / 'dataset1_extracted')
    for s in extr_ds.series['series1'].subjects.values():
        assert 's2s1_32Hz' in s.sample_arrays.keys()


def test_filter_cond_keyerror(ds_dir, tmp_path, example_extractor_config_path):
    dst_dir = tmp_path / 'extracted_datasets'
    cfg = config.parse_config(example_extractor_config_path)

    # Change the scorer to non-existing
    cfg.series_configs[0].filter_conds[0].kwargs = {'min_tst_sec': 30.0, 'hypnogram_key': 'doesntexist_hypnogram'}
    cli.extract(ds_dir, dst_dir, cfg)

    with open(dst_dir / cfg.new_dataset_name / '.extractor_skipped_subjects.json', 'r') as f:
        skipped = json.load(f)

    # Assert all subjects were skipped due to incorrect hypnogram_key
    assert len(skipped['series1']['unhandled']) == 3

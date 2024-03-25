"""Methods for reading and splitting sleeplab format data to tf.data.Dataset."""
import logging
import numpy as np
import sleeplab_format as slf
import sleeplab_tf_dataset as sds
import tensorflow as tf

from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


component_config = {
    'c3m2': {
        'src_name': 'C3_M2_64Hz',
        'ctype': 'sample_array',
        'fs': 64.0
    },
    'eog2': {
        'src_name': 'EOG2_64Hz',
        'ctype': 'sample_array',
        'fs': 64.0
    },
    'emg': {
        'src_name': 'EMG_64Hz',
        'ctype': 'sample_array',
        'fs': 64.0
    },
    'hypnogram': {
        'src_name': 'manual_consensus_hypnogram.a.json',
        'ctype': 'annotation',
        'sampling_interval': 30,
        'return_type': 'segmentation_combined',
        'value_map': {
            'W': 0,
            'N1': 1,
            'N2': 2,
            'N3': 3,
            'R': 4,
            '_default': 0  # Stages unspecified in value_map will be assigned as wake
        }
    }
}


dataset_config = {
    'dodh': {
        'ds_dir': '/tmp/slf/dod_extracted',
        'series_name': 'dodh',
        'roi_src_type': 'annotation',
        'roi_src_name': 'manual_consensus_hypnogram',
        'components': component_config,
        'splits': {
            # Total number of recordings = 25
            'train': {
                'n': 10,
                'config': {
                    'start_sec': -1.0,  # Randomly sample start_sec at each iteration
                    'duration': 60*60,  # Frame length in seconds
                }
            },
            'val': {
                'n': 5,
                'config': {
                    'start_sec': -1.0,
                    'duration': 60*60
                }
            },
            'test': {
                'n': 10,
                'config': {
                    # Use whole-night signals
                    'start_sec': 0.0,
                    'duration': -1.0
                }
            }
        }
    },
    'dodo': {
        'ds_dir': '/tmp/slf/dod_extracted',
        'series_name': 'dodo',
        'roi_src_type': 'annotation',
        'roi_src_name': 'manual_consensus_hypnogram',
        'components': component_config,
        'splits': {
            # Total number of recordings = 56
            'train': {
                'n': 40,
                'config': {
                    'start_sec': -1.0,  # Randomly sample start_sec at each iteration
                    'duration': 60*60,  # Frame length in seconds
                }
            },
            'val': {
                'n': 6,
                'config': {
                    'start_sec': -1.0,
                    'duration': 60*60
                }
            },
            'test': {
                'n': 10,
                'config': {
                    # Use whole-night signals
                    'start_sec': 0.0,
                    'duration': -1.0
                }
            }
        }
    }
}


def parse_dataset_configs(cfg: dict[str, Any]) -> dict[str, sds.config.DatasetConfig]:
    """Parse dict configs to sleeplab_tf_dataset.config.DatasetConfig items."""
    splits = cfg.pop('splits')
    res = {}
    for k, split in splits.items():
        _cfg_dict = cfg.copy()
        _cfg_dict.update(split['config'])
        _cfg = sds.config.DatasetConfig.parse_obj(_cfg_dict)
        res[k] = _cfg

    return res


def load_dataset(cfg: dict[str, Any], seed: int) -> dict[str, tf.data.Dataset]:
    """Load a single series to tf.data.Dataset."""
    logger.info(f"Reading the series {cfg['series_name']}...")
    slf_ds = slf.reader.read_dataset(
        ds_dir=Path(cfg['ds_dir']),
        series_names=[cfg['series_name']]
    )

    logger.info('Creating the splits...')
    # Read the subject IDs
    subj_ids = list(slf_ds.series[cfg['series_name']].subjects.keys())

    # Assert that the sum of split sizes matches the total number of subjects
    sum_split_sizes = sum([split['n'] for split in cfg['splits'].values()])
    _msg = f'Sum of split sizes does not match dataset size ({sum_split_sizes} != {len(subj_ids)})'
    assert sum_split_sizes == len(subj_ids), _msg

    # Randomly shuffle before splitting
    rng = np.random.default_rng(seed)
    permuted_subj_ids = rng.permutation(subj_ids)

    # Split the subject IDs
    split_subj_ids = {}
    curr_split_start = 0
    for k, split in cfg['splits'].items():
        curr_split_end = curr_split_start + split['n']
        split_subj_ids[k] = permuted_subj_ids[curr_split_start:curr_split_end]
        curr_split_start = curr_split_end

    # Parse config for each split
    split_cfgs = parse_dataset_configs(cfg)

    # Create the datasets for each split
    res = {}
    for k, cfg in split_cfgs.items():
        res[k] = sds.dataset.from_slf_dataset(
            slf_ds, cfg, subject_ids=split_subj_ids[k])

    return res


def load_datasets(cfgs: dict[str, Any], seed: int = 42) -> dict[str, tf.data.Dataset]:
    """Load and combine multiple series to tf.data.Dataset."""
    dodh_ds = load_dataset(cfgs['dodh'], seed=seed)
    dodo_ds = load_dataset(cfgs['dodo'], seed=seed)

    datasets = {
        'train': dodh_ds['train'].concatenate(dodo_ds['train']),
        'val': dodh_ds['val'].concatenate(dodo_ds['val']),
        'test': dodh_ds['test'].concatenate(dodo_ds['test']),
    }

    return datasets

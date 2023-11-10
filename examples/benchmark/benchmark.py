import argparse
import h5py
import json
import logging
import numpy as np
import pyedflib
import sleeplab_format as slf
import subprocess
import time

from pathlib import Path


logger = logging.getLogger(__name__)


def profile_time(f, *args, **kwargs):
    t1 = time.time()
    p1 = time.process_time()
    res = f(*args, **kwargs)
    t2 = time.time()
    p2 = time.process_time()
    
    return {
        'time': t2 - t1,
        'process_time': p2 - p1,
        'result': res
    }


def get_size(dir: Path):
    """Get folder size in bytes."""
    res = subprocess.run(['du', '-sb', str(dir)], capture_output=True, text=True)
    return res.stdout.split()[0]


def convert_dod(src_dir: Path, dst_dir: Path, array_format: str, clevel: str) -> None:
    subprocess.run(['nocache', 'python', '../dod_sleep_staging/convert_data.py',
                    '-s', src_dir,
                    '-d', dst_dir,
                    '--array-format', array_format,
                    '--clevel', clevel])


def iterate_dod(src_dir: Path) -> None:
    """Iterate over dodo and dodh h5 files and calculate mean.

    h5py.File with driver='core' loads the whole file into memory.
    """
    logger.info(f'Iterating {str(src_dir)}')
    for series in ['dodo', 'dodh']:
        for h5_path in (src_dir / series).glob('*.h5'):
            logger.info(f'Reading {str(h5_path)}')
            h5 = h5py.File(h5_path, 'r')
            for signal_type in h5['signals']:
                for signal_name in h5['signals'][signal_type]:
                    s = h5['signals'][signal_type][signal_name][:].astype(np.float32)
                    _ = np.mean(s)
            h5.close()


def convert_sc(src_dir: Path, dst_dir: Path, array_format: str, clevel: str) -> None:
    subprocess.run(['nocache', 'python', '../sleep_cassette_conversion/convert_data.py',
                    '-s', src_dir,
                    '-d', dst_dir,
                    '--array-format', array_format,
                    '--clevel', clevel])


def iterate_sc(src_dir: Path) -> None:
    logger.info(f'Iterating {str(src_dir)}')
    for edf_path in (src_dir / 'sleep-cassette').glob('*.edf'):
        sigs, sig_headers, header = pyedflib.highlevel.read_edf(str(edf_path))
        for s in sigs:
            _ = np.mean(s)


def iterate_slf_ds(ds_dir: Path) -> None:
    logger.info(f'Iterating {str(ds_dir)}')
    ds = slf.reader.read_dataset(ds_dir)
    for series in ds.series.values():
        for subject in series.subjects.values():
            for sarr in subject.sample_arrays.values():
                # Read SampleArray values to memory
                s = sarr.values_func()[:]
                _ = np.mean(s)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--slf-dir', help='Root folder where the converted datasets will be stored.')
    parser.add_argument('--output-path', help='Path to the benchmark result JSON file.')
    parser.add_argument('--dod-orig-dir', help='Path to the downloaded Dreem data')
    parser.add_argument('--sc-orig-dir', help='Path to the downloaded Sleep-Cassette data')
    args = parser.parse_args()
    slf_dir = Path(args.slf_dir)
    output_path = Path(args.output_path)

    res = {'dod': {}, 'sc': {}}

    ######################
    # Dreem open datasets
    ######################

    dod_orig_dir = Path(args.dod_orig_dir)
    dod_slf_numpy_dir = slf_dir / 'dod_slf_numpy'
    dod_slf_zarr_clevel_3_dir = slf_dir / 'dod_slf_clevel_3'
    dod_slf_zarr_clevel_9_dir = slf_dir / 'dod_slf_clevel_9'
    dod_slf_zarr_clevel_22_dir = slf_dir / 'dod_slf_clevel_22'

    # Original
    res['dod']['original'] = {}
    res['dod']['original']['size'] = int(get_size(dod_orig_dir)) / 1e9

    iterate_res = profile_time(iterate_dod, dod_orig_dir)
    res['dod']['original']['read_time'] = iterate_res['time']
    res['dod']['original']['read_process_time'] = iterate_res['process_time']

    # NumPy
    convert_res = profile_time(convert_dod, dod_orig_dir, dod_slf_numpy_dir, 'numpy', '-1')
    res['dod']['numpy'] = {}
    res['dod']['numpy']['size'] = int(get_size(dod_slf_numpy_dir)) / 1e9
    res['dod']['numpy']['write_time'] = convert_res['time']
    res['dod']['numpy']['write_process_time'] = convert_res['process_time']

    iterate_res = profile_time(iterate_slf_ds, dod_slf_numpy_dir / dod_orig_dir.name)
    res['dod']['numpy']['read_time'] = iterate_res['time']
    res['dod']['numpy']['read_process_time'] = iterate_res['process_time']

    # Zarr compression level 3
    convert_res = profile_time(convert_dod, dod_orig_dir, dod_slf_zarr_clevel_3_dir, 'zarr', '3')
    res['dod']['zarr_clevel_3'] = {}
    res['dod']['zarr_clevel_3']['size'] = int(get_size(dod_slf_zarr_clevel_3_dir)) / 1e9
    res['dod']['zarr_clevel_3']['write_time'] = convert_res['time']
    res['dod']['zarr_clevel_3']['write_process_time'] = convert_res['process_time']

    iterate_res = profile_time(iterate_slf_ds, dod_slf_zarr_clevel_3_dir / dod_orig_dir.name)
    res['dod']['zarr_clevel_3']['read_time'] = iterate_res['time']
    res['dod']['zarr_clevel_3']['read_process_time'] = iterate_res['process_time']
    
    # Zarr compression level 9
    convert_res = profile_time(convert_dod, dod_orig_dir, dod_slf_zarr_clevel_9_dir, 'zarr', '9')
    res['dod']['zarr_clevel_9'] = {}
    res['dod']['zarr_clevel_9']['size'] = int(get_size(dod_slf_zarr_clevel_9_dir)) / 1e9
    res['dod']['zarr_clevel_9']['write_time'] = convert_res['time']
    res['dod']['zarr_clevel_9']['write_process_time'] = convert_res['process_time']

    iterate_res = profile_time(iterate_slf_ds, dod_slf_zarr_clevel_9_dir / dod_orig_dir.name)
    res['dod']['zarr_clevel_9']['read_time'] = iterate_res['time']
    res['dod']['zarr_clevel_9']['read_process_time'] = iterate_res['process_time']

    # Zarr compression level 22
    convert_res = profile_time(convert_dod, dod_orig_dir, dod_slf_zarr_clevel_22_dir, 'zarr', '22')
    res['dod']['zarr_clevel_22'] = {}
    res['dod']['zarr_clevel_22']['size'] = int(get_size(dod_slf_zarr_clevel_22_dir)) / 1e9
    res['dod']['zarr_clevel_22']['write_time'] = convert_res['time']
    res['dod']['zarr_clevel_22']['write_process_time'] = convert_res['process_time']

    iterate_res = profile_time(iterate_slf_ds, dod_slf_zarr_clevel_22_dir / dod_orig_dir.name)
    res['dod']['zarr_clevel_22']['read_time'] = iterate_res['time']
    res['dod']['zarr_clevel_22']['read_process_time'] = iterate_res['process_time']

    #################
    # Sleep-Cassette
    #################

    sc_orig_dir = Path(args.sc_orig_dir)
    sc_slf_numpy_dir = slf_dir / 'sc_slf_numpy'
    sc_slf_zarr_clevel_3_dir = slf_dir / 'sc_slf_clevel_3'
    sc_slf_zarr_clevel_9_dir = slf_dir / 'sc_slf_clevel_9'
    sc_slf_zarr_clevel_22_dir = slf_dir / 'sc_slf_clevel_22'

    # Original
    res['sc']['original'] = {}
    res['sc']['original']['size'] = int(get_size(sc_orig_dir / 'sleep-cassette')) / 1e9

    iterate_res = profile_time(iterate_sc, sc_orig_dir)
    res['sc']['original']['read_time'] = iterate_res['time']
    res['sc']['original']['read_process_time'] = iterate_res['process_time']

    # NumPy
    convert_res = profile_time(convert_sc, sc_orig_dir, sc_slf_numpy_dir, 'numpy', '-1')
    res['sc']['numpy'] = {}
    res['sc']['numpy']['size'] = int(get_size(sc_slf_numpy_dir)) / 1e9
    res['sc']['numpy']['write_time'] = convert_res['time']
    res['sc']['numpy']['write_process_time'] = convert_res['process_time']

    iterate_res = profile_time(iterate_slf_ds, sc_slf_numpy_dir / 'sleep-cassette')
    res['sc']['numpy']['read_time'] = iterate_res['time']
    res['sc']['numpy']['read_process_time'] = iterate_res['process_time']

    # Zarr compression level 3
    convert_res = profile_time(convert_sc, sc_orig_dir, sc_slf_zarr_clevel_3_dir, 'zarr', '3')
    res['sc']['zarr_clevel_3'] = {}
    res['sc']['zarr_clevel_3']['size'] = int(get_size(sc_slf_zarr_clevel_3_dir)) / 1e9
    res['sc']['zarr_clevel_3']['write_time'] = convert_res['time']
    res['sc']['zarr_clevel_3']['write_process_time'] = convert_res['process_time']

    iterate_res = profile_time(iterate_slf_ds, sc_slf_zarr_clevel_3_dir / 'sleep-cassette')
    res['sc']['zarr_clevel_3']['read_time'] = iterate_res['time']
    res['sc']['zarr_clevel_3']['read_process_time'] = iterate_res['process_time']
    
    # Zarr compression level 9
    convert_res = profile_time(convert_sc, sc_orig_dir, sc_slf_zarr_clevel_9_dir, 'zarr', '9')
    res['sc']['zarr_clevel_9'] = {}
    res['sc']['zarr_clevel_9']['size'] = int(get_size(sc_slf_zarr_clevel_9_dir)) / 1e9
    res['sc']['zarr_clevel_9']['write_time'] = convert_res['time']
    res['sc']['zarr_clevel_9']['write_process_time'] = convert_res['process_time']

    iterate_res = profile_time(iterate_slf_ds, sc_slf_zarr_clevel_9_dir / 'sleep-cassette')
    res['sc']['zarr_clevel_9']['read_time'] = iterate_res['time']
    res['sc']['zarr_clevel_9']['read_process_time'] = iterate_res['process_time']

    # Zarr compression level 22
    convert_res = profile_time(convert_sc, sc_orig_dir, sc_slf_zarr_clevel_22_dir, 'zarr', '22')
    res['sc']['zarr_clevel_22'] = {}
    res['sc']['zarr_clevel_22']['size'] = int(get_size(sc_slf_zarr_clevel_22_dir)) / 1e9
    res['sc']['zarr_clevel_22']['write_time'] = convert_res['time']
    res['sc']['zarr_clevel_22']['write_process_time'] = convert_res['process_time']

    iterate_res = profile_time(iterate_slf_ds, sc_slf_zarr_clevel_22_dir / 'sleep-cassette')
    res['sc']['zarr_clevel_22']['read_time'] = iterate_res['time']
    res['sc']['zarr_clevel_22']['read_process_time'] = iterate_res['process_time']

    # Save results
    with open(args.output_path, 'w') as f:
        json.dump(res, f, indent=2)
    

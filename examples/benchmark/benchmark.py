import json
import sleeplab_format as slf
import subprocess
import time

from pathlib import Path


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


def convert_dod(src_dir: Path, dst_dir: Path,
                array_format: str, clevel: str) -> None:
    subprocess.run(['python', '../dod_sleep_staging/convert_data.py',
                    '-s', src_dir,
                    '-d', dst_dir,
                    '--array-format', array_format,
                    '--clevel', clevel])


def iterate_dod(src_dir: Path) -> None:
    ...


def convert_sc(src_dir: Path, dst_dir: Path) -> None:
    ...


def iterate_sc(src_dir: Path) -> None:
    ...


def iterate_slf_ds(ds_dir: Path) -> None:
    ...


if __name__ == '__main__':
    res = {'dod': {}, 'sc': {}}
    # Dreem conversion
    res['dod']['...'] = ...

    # Dreem reading

    # Sleep-Cassette conversion

    # Sleep-Cassette reading

    # Save results
    with open('./benchmark_out.json', 'w') as f:
        json.dump(res, f)
    
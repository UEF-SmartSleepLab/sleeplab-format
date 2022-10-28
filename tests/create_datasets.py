import json
import numpy as np

from pathlib import Path


def subject_metadata(sid):
    return {
        'subject_id': sid
    }


def sample_arrays():
    return {
        's1_1024Hz': {
            'attributes': {
                'name': 's1_1024Hz',
                'sampling_rate': 1024,
                'unit': 'V'
            },
            'values': 0.123 * np.ones(100),
        },
        's2_32.1Hz': {
            'attributes': {
                'name': 's2_32.1Hz',
                'sampling_rate': 32.1,
                'unit': 'mV'
            },
            'values': 1.23 * np.ones(100),
        },
        'hypnogram_30s': {
            'attributes': {
                'name': 'hypnogram_30s',
                'sampling_interval': 30,
                'value_map': {
                    0: 'wake',
                    1: 'n1',
                    2: 'n2',
                    3: 'n3',
                    4: 'rem'
                }
            },
            'values': np.array([0, 0, 1, 2, 2, 3, 2, 0, 0]),
        }
    }


def events():
    return [
        {'name': 'spo2_desat', 'start': 123.45, 'duration': 15.0},
        {'name': 'central_apnea', 'start': 321.45, 'duration': 11.2},
        {'name': 'hypopnea', 'start': 400.0, 'duration': 32.0},
    ]


def create_datasets():
    ds_name = 'dataset1'
    study_name = 'study1'
    subject_ids = ['10001', '10002', '10003']
    
    basedir = Path(__file__).parent / 'datasets'
    ds_dir = basedir / ds_name
    study_dir = ds_dir / study_name
    study_dir.mkdir(exist_ok=True, parents=True)

    for sid in subject_ids:
        subject_dir = study_dir / sid
        subject_dir.mkdir(exist_ok=True)

        subject_metadata_path = subject_dir / 'metadata.json'
        with open(subject_metadata_path, 'w') as f:
            json.dump(subject_metadata(sid), f, indent=2)

        for k, v in sample_arrays().items():
            sarr_path = subject_dir / k
            sarr_path.mkdir(exist_ok=True)

            attr_path = sarr_path / 'attributes.json'
            with open(attr_path, 'w') as f:
                json.dump(v['attributes'], f, indent=2)

            values_path = sarr_path / f'{sid}_{k}.npy'
            np.save(values_path, v['values'], allow_pickle=False)

        events_path = subject_dir / 'events_annotated.json'
        with open(events_path, 'w') as f:
            json.dump(events(), f, indent=2)


if __name__ == '__main__':
    create_datasets()
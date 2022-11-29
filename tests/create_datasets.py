import json
import numpy as np

from pathlib import Path


def subject_metadata(sid):
    return {
        'subject_id': sid,
        'recording_start_ts': '2018-01-01T23:10:04',
        'age': 24.0,
        'bmi': 25.56,
        'sex': 'MALE'
    }


def sample_arrays():
    return {
        's1_1024Hz': {
            'attributes': {
                'name': 's1_1024Hz',
                'start_ts': '2018-01-01T23:10:04',
                'sampling_rate': 1024,
                'unit': 'V'
            },
            'values': 0.123 * np.ones(100),
        },
        's2_32.1Hz': {
            'attributes': {
                'name': 's2_32.1Hz',
                'start_ts': '2018-01-01T23:10:04',
                'sampling_rate': 32.1,
                'unit': 'mV'
            },
            'values': 1.23 * np.ones(100),
        },
        # 'hypnogram_30s': {
        #     'attributes': {
        #         'name': 'hypnogram_30s',
        #         'start_ts': '2018-01-01T23:10:04',
        #         'sampling_interval': 30,
        #         'value_map': {
        #             0: 'wake',
        #             1: 'n1',
        #             2: 'n2',
        #             3: 'n3',
        #             4: 'rem'
        #         }
        #     },
        #     'values': np.array([0, 0, 1, 2, 2, 3, 2, 0, 0]),
        # }
    }


def events():
    return {
        'annotations': [
        {
            'name': 'spo2_desat',
            'start_ts': '2015-01-29T21:29:17.123000',
            'start_sec': 123.45,
            'duration': 15.0,
            'extra_attributes': {
                'LowestSpO2': 93,
                'Desaturation': 4
            }
        },
        {
            'name': 'central_apnea',
            'start_ts': '2018-01-01T23:10:04.432000',
            'start_sec': 321.45,
            'duration': 11.2
        },
        {
            'name': 'hypopnea',
            'start_ts': '2015-01-29T21:29:17',
            'start_sec': 400.0,
            'duration': 32.0,
        }],
        'scorer': 'automatic',
    }


def hypnogram():
    return {
        'annotations': [
        {
            'name': 'N1',
            'start_ts': '2015-01-29T21:29:17.123000',
            'start_sec': 0.0,
            'duration': 30.0,
        },
        {
            'name': 'WAKE',
            'start_ts': '2018-01-01T23:10:04.432000',
            'start_sec': 120.0,
            'duration': 30.0
        },
        {
            'name': 'REM',
            'start_ts': '2015-01-29T21:29:17',
            'start_sec': 300.0,
            'duration': 30.0,
        }],
        'scorer': 'scorer scorer',
    }



def study_logs():
    return {
        'logs': [
        {
            'ts': '2015-01-29T21:29:17',
            'text': 'F3 - Impedance 1,4k'
        },
        {
            'ts': '2015-01-29T21:29:17',
            'text': 'LIGHTS OUT'
        },
        {
            'ts': '2015-01-29T21:29:17',
            'text': 'LIGHTS ON'
        }
    ]}


def create_datasets(basedir: Path) -> None:
    ds_name = 'dataset1'
    series_name = 'series1'
    subject_ids = ['10001', '10002', '10003']
    
    ds_dir = basedir / ds_name
    series_dir = ds_dir / series_name
    series_dir.mkdir(exist_ok=True, parents=True)

    for sid in subject_ids:
        subject_dir = series_dir / sid
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

            values_path = sarr_path / f'data.npy'
            np.save(values_path, v['values'], allow_pickle=False)

        events_path = subject_dir / 'events_annotated.json'
        with open(events_path, 'w') as f:
            json.dump(events(), f, indent=2)

        hg_path = subject_dir / 'hypnogram_annotated.json'
        with open(hg_path, 'w') as f:
            json.dump(hypnogram(), f, indent=2)

        study_logs_path = subject_dir / 'study_logs.json'
        with open(study_logs_path, 'w') as f:
            json.dump(study_logs(), f, indent=2)


if __name__ == '__main__':
    basedir = Path(__file__).parent / 'datasets'
    create_datasets(basedir)
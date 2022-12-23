import pytest

from pathlib import Path
from sleeplab_format.models import *
from sleeplab_format import writer


@pytest.fixture(scope='session')
def example_config_path():
    data_dir = Path(__file__).parent / 'data'
    return data_dir / 'example_config.yml'


@pytest.fixture(scope='session')
def subject_ids():
    return ['10001', '10002', '10003']


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
        's1': {
            'attributes': {
                'name': 's1',
                'start_ts': '2018-01-01T23:10:04',
                'sampling_rate': 32,
                'unit': 'V'
            },
            'values': 0.123 * np.ones(60*32, dtype=np.float32),
        },
        's2': {
            'attributes': {
                'name': 's2',
                'start_ts': '2018-01-01T23:10:04',
                'sampling_rate': 64,
                'unit': 'mV'
            },
            'values': 1.23 * np.ones(60*64, dtype=np.float32),
        },
    }


def events():
    return {
        'annotations': [
        {
            'name': 'spo2_desat',
            'start_ts': '2018-01-01T23:10:04',
            'start_sec': 0.0,
            'duration': 15.0,
            'extra_attributes': {
                'LowestSpO2': 93,
                'Desaturation': 4
            }
        },
        {
            'name': 'central_apnea',
            'start_ts': '2018-01-01T23:10:24',
            'start_sec': 20.0,
            'duration': 10.0
        },
        {
            'name': 'hypopnea',
            'start_ts': '2018-01-01T23:10:34',
            'start_sec': 30.0,
            'duration': 10.0,
        }],
        'scorer': 'automatic',
    }


def hypnogram():
    return {
        'annotations': [
        {
            'name': 'N1',
            'start_ts': '2018-01-01T23:10:04',
            'start_sec': 0.0,
            'duration': 30.0,
        },
        {
            'name': 'WAKE',
            'start_ts': '2018-01-01T23:10:34',
            'start_sec': 30.0,
            'duration': 30.0
        },
        ],
        'scorer': 'scorer scorer',
    }


def study_logs():
    return {
        'logs': [
        {
            'ts': '2018-01-01T23:10:04',
            'text': 'F3 - Impedance 1,4k'
        },
        {
            'ts': '2018-01-01T23:10:04',
            'text': 'LIGHTS OUT'
        },
        {
            'ts': '2018-01-01T23:11:04',
            'text': 'LIGHTS ON'
        }
    ]}


@pytest.fixture
def subjects(subject_ids):
    subjs = {}
    for sid in subject_ids:
        metadata = SubjectMetadata(**subject_metadata(sid))
        
        dict_arrays = sample_arrays()
        arrays = {
            k: SampleArray(
                attributes=ArrayAttributes(**v['attributes']),
                values_func=lambda v=v: v['values'])
            for k, v in dict_arrays.items()
        }

        subjs[sid] = Subject(
            metadata=metadata,
            sample_arrays=arrays,
            annotations={
                'events': Annotations.parse_obj(events()),
                'hypnogram': Annotations.parse_obj(hypnogram())
            },
            study_logs=Logs.parse_obj(study_logs()))

    return subjs


@pytest.fixture
def series(subjects):
    series = Series(
        name='series1',
        subjects=subjects
    )
    return {'series1': series}


@pytest.fixture
def dataset(series):
    dataset = Dataset(
        name='dataset1',
        series=series
    )
    return dataset

@pytest.fixture
def ds_dir(dataset, tmp_path):
    basedir = tmp_path / 'datasets'
    writer.write_dataset(dataset, basedir)

    return basedir / dataset.name

import pytest

from sleeplab_format.models import *
from sleeplab_format import writer


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
                'sampling_rate': 32.0,
                'unit': 'V'
            },
            'values': 0.123 * np.ones(60*32, dtype=np.float32),
        },
        's2': {
            'attributes': {
                'name': 's2',
                'start_ts': '2018-01-01T23:10:04',
                'sampling_rate': 64.0,
                'unit': 'mV'
            },
            'values': 1.23 * np.ones(60*64, dtype=np.float32),
        },
    }


def events():
    return {
        'scorer': 'automatic',
        'type': 'aasmevents',
        'annotations': [
        {
            'name': 'SPO2_DESAT',
            'start_ts': '2018-01-01T23:10:04',
            'start_sec': 0.0,
            'duration': 15.0,
            'extra_attributes': {
                'min_spo2': 93,
                'desat_limit': 4
            }
        },
        {
            'name': 'APNEA_CENTRAL',
            'start_ts': '2018-01-01T23:10:24',
            'start_sec': 20.0,
            'duration': 10.0
        },
        {
            'name': 'HYPOPNEA',
            'start_ts': '2018-01-01T23:10:34',
            'start_sec': 30.0,
            'duration': 10.0,
        }],
    }


def hypnogram():
    return {
        'scorer': 'scorer_1',
        'type': 'hypnogram',
        'annotations': [
        {
            'name': 'N1',
            'start_ts': '2018-01-01T23:10:04',
            'start_sec': 0.0,
            'duration': 30.0,
        },
        {
            'name': 'W',
            'start_ts': '2018-01-01T23:10:34',
            'start_sec': 30.0,
            'duration': 30.0
        },
        ],
    }


def study_logs():
    return {
        'scorer': 'study',
        'type': 'logs',
        'annotations': [
        {
            'name': 'F3 - Impedance 1,4k',
            'start_ts': '2018-01-01T23:10:04',
            'start_sec': 0.0,
            'duration': 0.0   
        },
        {
            'name': 'LIGHTS OUT',
            'start_ts': '2018-01-01T23:10:04',
            'start_sec': 0.0,
            'duration': 0.0   
        },
        {
            'name': 'LIGHTS ON',
            'start_ts': '2018-01-01T23:11:04',
            'start_sec': 60.0,
            'duration': 0.0   
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
                'automatic_aasmevents': AASMEvents.model_validate(events()),
                'scorer_1_hypnogram': Hypnogram.model_validate(hypnogram()),
                'study_logs': Logs.model_validate(study_logs())
            }
        )

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

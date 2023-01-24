"""Data type definitions for the sleeplab format."""
import numpy as np
import pyarrow as pa

from collections.abc import Callable
from datetime import datetime
from enum import Enum
from functools import cached_property
from pydantic import BaseModel, Extra, Field, validator
from pydantic.datetime_parse import parse_datetime
from typing import Any, Optional


SLEEPLAB_FORMAT_VERSION = '0.1'


class NaiveDatetime(datetime):
    """Custom field that removes timezone information when serializing.
    
    This is needed because Pydantic automatically adds UTC as timezone
    when serializing if naive datetime object is passed.

    See https://stackoverflow.com/a/70726989
    """
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        v = parse_datetime(v)
        v = v.replace(tzinfo=None)
        return v


class Sex(str, Enum):
    FEMALE = 'FEMALE'
    MALE = 'MALE'
    OTHER = 'OTHER'


class SleepStage(str, Enum):
    WAKE = 'WAKE'
    N1 = 'N1'
    N2 = 'N2'
    N3 = 'N3'
    REM = 'REM'
    UNSURE = 'UNSURE'
    UNSCORED = 'UNSCORED'
    ARTIFACT = 'ARTIFACT'


class AASMEvent(str, Enum):
    """Enum for events scored according to the AASM manual v2.4."""
    # Arousal events
    AROUSAL = 'AROUSAL'
    AROUSAL_RESPIRATORY = 'AROUSAL_RESPIRATORY'

    # Cardiac events
    # TODO: Add these if a use case ever pops up

    # Movement events
    BRUXISM = 'BRUXISM'
    LM = 'LM'  # Leg movement
    PLM = 'PLM'  # Periodic leg movement
    
    # Respiratory events
    APNEA = 'APNEA'
    APNEA_CENTRAL = 'APNEA_CENTRAL'
    APNEA_OBSTRUCTIVE = 'APNEA_OBSTRUCTIVE'
    APNEA_MIXED = 'APNEA_MIXED'
    HYPOPNEA = 'HYPOPNEA'
    HYPOPNEA_CENTRAL = 'HYPOPNEA_CENTRAL'
    HYPOPNEA_OBSTRUCTIVE = 'HYPOPNEA_OBSTRUCTIVE'
    SPO2_DESAT = 'SPO2_DESAT'
    SNORE = 'SNORE'
    # TODO:
    # HYPOVENTILATION?
    # CHEYNE_STOKES?


class SubjectMetadata(BaseModel, extra=Extra.forbid):
    subject_id: str

    # Recording start time
    recording_start_ts: NaiveDatetime

    # TODO: add to Profusion converter
    lights_off: Optional[NaiveDatetime] = None
    lights_on: Optional[NaiveDatetime] = None
    analysis_start: Optional[NaiveDatetime] = None
    analysis_end: Optional[NaiveDatetime] = None

    age: Optional[float] = None
    bmi: Optional[float] = None
    sex: Optional[Sex] = None

    additional_info: Optional[dict[str, Any]] = None
    

class ArrayAttributes(BaseModel, extra=Extra.forbid,
        # Use smart_union to keep ints ints and floats floats
        # https://pydantic-docs.helpmanual.io/usage/model_config/#smart-union
        smart_union=True):
    name: str
    start_ts: NaiveDatetime
    sampling_rate: Optional[float | int] = None
    sampling_interval: Optional[float | int] = None
    unit: Optional[str] = None
    value_map: Optional[dict[int, str | int]] = None

    @validator('sampling_interval')
    def require_rate_or_interval(cls, v, values):
        if v is None:
            _msg = 'either sampling_rate or sampling_interval needs to be defined'
            assert values['sampling_rate'] is not None, _msg
        else:
            _msg = 'cannot define both sampling_rate and sampling_interval'
            assert values['sampling_rate'] is None, _msg

        return v


class SampleArray(
        BaseModel,
        extra=Extra.forbid,
        keep_untouched=(cached_property,)):
    """A pydantic model representing a numerical array with attributes.

    When writing data to sleeplab format, use `values_func` to access the array
    to avoid caching.

    When reading data in sleeplab format, use `values` since the `values_func`
    returned by the reader should return `np.memmap` instead of the full array.
    """
    attributes: ArrayAttributes
    values_func: Callable[[], np.ndarray]
    
    @cached_property
    def values(self) -> np.ndarray:
        """Use @cached_property so that values_func gets evaluated once
        when values is accessed first time.
        """
        return self.values_func()


class Annotation(BaseModel, extra=Extra.forbid):
    # Freely defined name of the event
    name: str

    # Start time as timestamp
    start_ts: NaiveDatetime

    # Start time as seconds from the start of recording
    start_sec: float

    # Duration of the event in seconds
    # 0.0 if the event is a point in time
    duration: float

    # Name of the channel used to annotate the eventb
    input_channel: Optional[str] = None

    # Freely defined extra attributes, such as desaturation depth
    extra_attributes: Optional[dict[str, Any]] = None


class Annotations(BaseModel):
    annotations: list[Annotation]
    scorer: Optional[str] = None


class SleepStageAnnotation(Annotation):
    """Override `name` to allow only `SleepStage` enum members."""
    name: SleepStage


class Hypnogram(Annotations):
    """A hypnogram is Annotations consisting of sleep stages."""
    annotations: list[SleepStageAnnotation]


class AASMAnnotation(Annotation):
    name: AASMEvent


class AASMAnnotations(Annotations):
    annotations: list[AASMAnnotation]


class LogEntry(BaseModel, extra=Extra.forbid):
    # The log time as timestamp
    ts: NaiveDatetime

    # The log row as plain text
    text: str


class Logs(BaseModel):
    logs: list[LogEntry]


class Subject(BaseModel, extra=Extra.forbid):
    metadata: SubjectMetadata
    sample_arrays: Optional[dict[str, SampleArray]] = Field(None, repr=False)
    annotations: Optional[dict[str, Annotations]] = Field(None, repr=False)
    study_logs: Optional[Logs] = Field(None, repr=False)


class Series(BaseModel, extra=Extra.forbid):
    name: str
    subjects: dict[str, Subject] = Field(repr=False)


class Dataset(BaseModel, extra=Extra.forbid):
    name: str
    series: dict[str, Series]

    # The sleeplab format version
    version: str = SLEEPLAB_FORMAT_VERSION


def lazy_memmap_array(fpath):
    """Return a function that will load a memmapped numpy array when called."""
    def inner():
        return np.load(fpath, mmap_mode='r', allow_pickle=False)

    return inner
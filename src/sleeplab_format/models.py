"""Data type definitions for the sleeplab format."""
import numpy as np
import pyarrow as pa

from collections.abc import Callable
from datetime import datetime
from enum import Enum
from functools import cached_property
from pydantic import BaseModel, Field, model_validator
from pydantic.functional_validators import AfterValidator
from typing import Any, Optional
from typing_extensions import Annotated


SLEEPLAB_FORMAT_VERSION = '0.2'


def unset_tzinfo(v: datetime):
    return v.replace(tzinfo=None)


# TODO: should the type be Any or datetime?
NaiveDatetime = Annotated[datetime, AfterValidator(unset_tzinfo)]


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
    # A generic class for artifacts
    ARTIFACT = 'ARTIFACT'

    # A generic class for unsure
    UNSURE = 'UNSURE'

    # Arousal events
    AROUSAL = 'AROUSAL'
    AROUSAL_RES = 'AROUSAL_RES'
    AROUSAL_SPONT = 'AROUSAL_SPONT'
    AROUSAL_LM = 'AROUSAL_LM'
    AROUSAL_PLM = 'AROUSAL_PLM'
    RERA = 'RERA'

    # Cardiac events
    # TODO: Add these if a use case ever pops up

    # Movement events
    BRUXISM = 'BRUXISM'
    LM = 'LM'  # Leg movement
    LM_LEFT = 'LM_LEFT',
    LM_RIGHT = 'LM_RIGHT',
    PLM = 'PLM'  # Periodic leg movement
    PLM_LEFT = 'PLM_LEFT'
    PLM_RIGHT = 'PLM_RIGHT'
    
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


class SubjectMetadata(BaseModel, extra='forbid'):
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
    

class ArrayAttributes(BaseModel, extra='forbid'):
    name: str
    start_ts: NaiveDatetime
    sampling_rate: Optional[float] = None
    sampling_interval: Optional[float] = None
    unit: Optional[str] = None
    value_map: Optional[dict[int, str | int]] = None

    @model_validator(mode='after')
    def require_rate_or_interval(self):
        if self.sampling_interval is None:
            _msg = 'either sampling_rate or sampling_interval needs to be defined'
            assert self.sampling_rate is not None, _msg
        else:
            _msg = 'cannot define both sampling_rate and sampling_interval'
            assert self.sampling_rate is None, _msg

        return self


class SampleArray(
        BaseModel,
        extra='forbid',
        ignored_types=(cached_property,)):
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


class Annotation(BaseModel, extra='forbid'):
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


class LogEntry(BaseModel, extra='forbid'):
    # The log time as timestamp
    ts: NaiveDatetime

    # The log row as plain text
    text: str


class Logs(BaseModel):
    logs: list[LogEntry]


class Subject(BaseModel, extra='forbid'):
    metadata: SubjectMetadata
    sample_arrays: Optional[dict[str, SampleArray]] = Field(None, repr=False)
    annotations: Optional[dict[str, Annotations]] = Field(None, repr=False)
    study_logs: Optional[Logs] = Field(None, repr=False)


class Series(BaseModel, extra='forbid'):
    name: str
    subjects: dict[str, Subject] = Field(repr=False)


class Dataset(BaseModel, extra='forbid'):
    name: str
    series: dict[str, Series]

    # The sleeplab format version
    version: str = SLEEPLAB_FORMAT_VERSION


def lazy_memmap_array(fpath):
    """Return a function that will load a memmapped numpy array when called."""
    def inner():
        return np.load(fpath, mmap_mode='r', allow_pickle=False)

    return inner
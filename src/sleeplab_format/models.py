"""Data type definitions for the sleeplab format."""
import numpy as np
import zarr

from collections.abc import Callable
from datetime import datetime
from enum import Enum
from functools import cached_property
from pydantic import BaseModel, Field, model_validator
from pydantic.functional_validators import AfterValidator
from typing import Any, Generic, Literal, Optional, TypeVar
from typing_extensions import Annotated
from .version import __version__


SLEEPLAB_FORMAT_VERSION = __version__


def unset_tzinfo(v: datetime):
    return v.replace(tzinfo=None)


NaiveDatetime = Annotated[datetime, AfterValidator(unset_tzinfo)]


class Sex(str, Enum):
    FEMALE = 'FEMALE'
    MALE = 'MALE'
    OTHER = 'OTHER'


class AASMSleepStage(str, Enum):
    """Sleep stages according to the AASM manual v2.6."""
    W = 'W'
    N1 = 'N1'
    N2 = 'N2'
    N3 = 'N3'
    R = 'R'

    # These are not part of the AASM v2.6 definition, but still commonly used
    UNSURE = 'UNSURE'
    UNSCORED = 'UNSCORED'
    ARTIFACT = 'ARTIFACT'


class RKSleepStage(str, Enum):
    """Sleep stages according to the Rechtschaffen and Kales manual.

    Stages 1, 2, 3, and 4 are prefixed with `S`.
    """
    W = 'W'
    S1 = 'S1'
    S2 = 'S2'
    S3 = 'S3'
    S4 = 'S4'
    R = 'R'

    # TODO: Are these part of the original manual?
    MOVEMENT = 'MOVEMENT'
    UNSCORED = 'UNSCORED'


class AASMEvent(str, Enum):
    """Enum for events scored according to the AASM manual v2.6."""
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

    amplifier_info: Optional[str] = None
    sensor_info: Optional[str] = None

    # An optional mapping from the array values to some other values,
    # e.g.  {0: 'off', 1: 'on'}
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
    def values(self) -> np.ndarray | zarr.Array:
        """Use @cached_property so that values_func gets evaluated once
        when values is accessed first time.
        """
        return self.values_func()


AnnotationT = TypeVar('AnnotationT', bound=str)


class Annotation(BaseModel, Generic[AnnotationT], extra='forbid'):
    # Freely defined name of the event
    name: AnnotationT

    # Start time as timestamp
    start_ts: NaiveDatetime

    # Start time as seconds from the start of recording
    start_sec: float

    # Duration of the event in seconds
    # 0.0 if the event is a point in time
    duration: float = 0.0

    # Name of the channel used to annotate the event
    input_channel: Optional[str] = None

    # Freely defined extra attributes, such as desaturation depth
    extra_attributes: Optional[dict[str, Any]] = None


class BaseAnnotations(BaseModel):
    scorer: str
    type: str
    annotations: list[Annotation]


class Annotations(BaseAnnotations):
    type: Literal['annotations'] = 'annotations'
    annotations: list[Annotation[str]]


class Hypnogram(BaseAnnotations):
    """A hypnogram is Annotations consisting of sleep stages."""
    type: Literal['hypnogram'] = 'hypnogram'
    annotations: list[Annotation[AASMSleepStage]]


class RKHypnogram(BaseAnnotations):
    """Hypnogram scored with R&K rules."""
    type: Literal['rkhypnogram'] = 'rkhypnogram'
    annotations: list[Annotation[RKSleepStage]]


class AASMEvents(BaseAnnotations):
    type: Literal['aasmevents'] = 'aasmevents'
    annotations: list[Annotation[AASMEvent]]


class Logs(BaseAnnotations):
    type: Literal['logs'] = 'logs'
    annotations: list[Annotation[str]]


class Subject(BaseModel, extra='forbid'):
    metadata: SubjectMetadata
    sample_arrays: Optional[dict[str, SampleArray]] = Field(None, repr=False)
    annotations: Optional[dict[str, BaseAnnotations]] = Field(None, repr=False)


class Series(BaseModel, extra='forbid'):
    name: str
    subjects: dict[str, Subject] = Field(repr=False)


class Dataset(BaseModel, extra='forbid'):
    name: str
    version: str = SLEEPLAB_FORMAT_VERSION
    series: Optional[dict[str, Series]] = None

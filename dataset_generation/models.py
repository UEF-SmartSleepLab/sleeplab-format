"""Data type definitions for the sleeplab format."""
import numpy as np
import pyarrow as pa

from collections.abc import Callable
from functools import cached_property
from pydantic import BaseModel, Extra, validator
from typing import Any, Iterable, Optional


class SubjectMetadata(BaseModel, extra=Extra.forbid):
    subject_id: str
    

class ArrayAttributes(BaseModel, extra=Extra.forbid,
        # Use smart_union to keep ints ints and floats floats
        # https://pydantic-docs.helpmanual.io/usage/model_config/#smart-union
        smart_union=True):
    name: str
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
    name: str
    start: float
    duration: float


class Subject(BaseModel, extra=Extra.forbid):
    metadata: SubjectMetadata
    sample_arrays: Optional[dict[str, SampleArray]] = None
    annotations: Optional[dict[str, list[Annotation]]] = None


class Study(BaseModel, extra=Extra.forbid):
    name: str
    subjects: dict[str, Subject]


class Dataset(BaseModel, extra=Extra.forbid):
    name: str
    studies: dict[str, Study]


def lazy_memmap_array(fpath):
    """Return a function that will load a memmapped numpy array when called."""
    def inner():
        return np.load(fpath, mmap_mode='r', allow_pickle=False)

    return inner
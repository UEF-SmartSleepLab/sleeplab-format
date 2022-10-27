"""Data type definitions for the sleeplab format."""
import numpy.typing as npt


from pydantic.dataclasses import dataclass
#from pydantic import BaseModel
from typing import Optional


@dataclass
class SubjectMetadata:
    subject_id: str
    

@dataclass
class ArrayAttributes:
    data_type: str
    unit: str
    sampling_rate: Optional[float] = None
    sampling_interval: Optional[float] = None


@dataclass
class Annotation:
    name: str
    start: float
    duration: float


@dataclass
class Subject:
    metadata: SubjectMetadata
    arrays: list[tuple[ArrayAttributes, list[float | int]]]


@dataclass
class Study:
    name: str
    subjects: list[Subject]


@dataclass
class Dataset:
    name: str
    studies: list[Study]

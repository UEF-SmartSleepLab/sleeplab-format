import yaml

from pathlib import Path
from pydantic import BaseModel
from typing import Any


class ArrayAction(BaseModel, extra='forbid'):
    name: str
    method: str

    # The name of an optional reference signal
    ref_name: str | None = None
    
    kwargs: dict[str, Any] = {}
    updated_attributes: dict[str, Any] | None = None


class ArrayConfig(BaseModel, extra='forbid'):
    name: str
    actions: list[ArrayAction] | None = None


class FilterCond(BaseModel, extra='forbid'):
    name: str
    method: str
    kwargs: dict[str, Any] | None = None


class SeriesConfig(BaseModel, extra='forbid'):
    name: str
    array_configs: list[ArrayConfig]
    filter_conds: list[FilterCond] | None = None


class DatasetConfig(BaseModel, extra='forbid'):
    new_dataset_name: str
    series_configs: list[SeriesConfig]
    annotation_format: str = 'json'
    array_format: str = 'numpy'


def parse_config(config_path: Path) -> DatasetConfig:
    with open(config_path, 'r') as f:
        cfg = yaml.safe_load(f)
    
    return DatasetConfig.model_validate(cfg)
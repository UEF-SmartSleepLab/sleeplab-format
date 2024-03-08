[![DOI](https://zenodo.org/badge/558261131.svg)](https://zenodo.org/badge/latestdoi/558261131)
[![PyPI version](https://badge.fury.io/py/sleeplab-format.svg)](https://badge.fury.io/py/sleeplab-format)
# sleeplab-format

Sleeplab format (SLF) is a both machine and human-readable format for storing and processing polysomnography data. SLF provides reader and writer with validation of data types and structures. The goal is to make it easier to apply analytics and machine learning pipelines to multiple datasets from different sources.

## Documentation

See [full documentation](https://uef-smartsleeplab.github.io/sleeplab-format/) and [the paper](https://arxiv.org/abs/2402.06702v1) for details.

## Related tools

[sleeplab-converters](https://github.com/UEF-SmartSleepLab/sleeplab-converters) for converting other formats exported from PSG software to sleeplab format.

[sleeplab-tf-dataset](https://github.com/UEF-SmartSleepLab/sleeplab-tf-dataset) for reading data in sleeplab format as a tensorflow Dataset.

## Installation

```bash
pip install sleeplab-format
```

## Usage

``` py
import sleeplab_format as slf
import pandas as pd
from pathlib import Path

# Read a toy dataset
DS_DIR = Path('tests/datasets/dataset1')
ds = slf.reader.read_dataset(DS_DIR)

# Get the list of subjects from series1
subjects = ds.series['series1'].subjects.values()

# Flatten the nested annotations and cast Pydantic models to dicts
all_events_dict = [dict(a)
    for s in subjects
    for a_model in s.annotations.values()
    for a in a_model.annotations
]

# Create a pandas DataFrame for analyses
event_df = pd.DataFrame(all_events_dict)

# Calculate the mean duration of hypopneas
hypopneas = event_df[event_df['name'] == 'HYPOPNEA']
mean_duration = sum(hypopneas['duration']) / len(hypopneas)

# Modify the dataset
additional_info = {'neck_size': 40.0}
ds.series['series1'].subjects['10001'].metadata.additional_info = additional_info
ds.name = 'dataset2'

# Write the modified dataset
MODIFIED_DS_DIR = Path('/tmp/datasets')
slf.writer.write_dataset(ds, MODIFIED_DS_DIR)
```

See [the automatic sleep staging example](examples/dod_sleep_staging/README.md) for a full end-to-end example.

## Contributing

See [contributing](docs/contributing.md).

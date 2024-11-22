# Sleeplab-format v0.4.1

Sleeplab format (SLF) is a both machine and human-readable format to store and process polysomnography recordings. It provides reader and writer with built-in validation of the data types and structures. SLF was designed for harmonization of datasets from different sources to enable easier application of analysis and machine learning pipelines on multiple datasets.

See [Concepts](concepts.md) and [the paper](https://arxiv.org/abs/2402.06702v1) for detailed description of the format.

## Installation

```console
pip install sleeplab-format
```

## Basic example

Read, analyse, modify, and write SLF datasets.

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

See [Examples](examples/automatic_sleep_staging.md) for end-to-end use cases.

## SLF extractor

The `sleeplab-format` package provides an extractor that can be used to select and preprocess a subset of signals for further analyses. See [the automatic sleep staging example](examples/automatic_sleep_staging.md#extract-and-preprocess-a-subset-of-the-signals) for usage instructions.

## Related tools

[sleeplab-converters](https://github.com/UEF-SmartSleepLab/sleeplab-converters) for converting other formats exported from PSG software to sleeplab format.

[sleeplab-tf-dataset](https://github.com/UEF-SmartSleepLab/sleeplab-tf-dataset) for reading data in sleeplab format as a tensorflow Dataset.

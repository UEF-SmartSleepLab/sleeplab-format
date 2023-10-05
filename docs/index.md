# Sleeplab-format v0.3.0

A standardized format for polysomnography recordings.

## Installation

```console
pip install sleeplab-format
```

## Basic example

``` py
import sleeplab_format as slf
from pathlib import Path

DS_DIR = Path('/path/to/dataset')
ds = slf.reader.read_dataset(DATASET_DIR)

# TODO: Example of how to access data

# ...Do some processing and modify the dataset

MODIFIED_DS_DIR = Path('/path/to/modified_dataset')
slf.writer.write_dataset(ds, MODIFIED_DATASET_DIR)
```

See [usage](usage.md) and [examples](examples/automatic_sleep_staging.md) for more detailed information.

## Related tools

[sleeplab-converters](https://github.com/UEF-SmartSleepLab/sleeplab-converters) for converting other formats exported from PSG software to sleeplab format.

[sleeplab-extractor](https://github.com/UEF-SmartSleepLab/sleeplab-extractor) for extracting and preprocessing a subset of data in sleeplab format for the needs of specific studies.

[sleeplab-tf-dataset](https://github.com/UEF-SmartSleepLab/sleeplab-tf-dataset) for reading data in sleeplab format as a tensorflow Dataset.

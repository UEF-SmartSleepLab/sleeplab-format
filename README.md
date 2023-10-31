

[![DOI](https://zenodo.org/badge/558261131.svg)](https://zenodo.org/badge/latestdoi/558261131)
# sleeplab-format

A standardized format for polysomnography recordings.

## Documentation

See [full documentation](https://uef-smartsleeplab.github.io/sleeplab-format/) for details.

## Related tools

[sleeplab-converters](https://github.com/UEF-SmartSleepLab/sleeplab-converters) for converting other formats exported from PSG software to sleeplab format.

[sleeplab-extractor](https://github.com/UEF-SmartSleepLab/sleeplab-extractor) for extracting and preprocessing a subset of data in sleeplab format for the needs of specific studies.

[sleeplab-tf-dataset](https://github.com/UEF-SmartSleepLab/sleeplab-tf-dataset) for reading data in sleeplab format as a tensorflow Dataset.

## Installation

```bash
pip install sleeplab-format
```

## Usage

```python
import sleeplab_format as slf
from pathlib import Path

DS_DIR = Path('/path/to/dataset')
ds = slf.reader.read_dataset(DATASET_DIR)

# TODO: Example of how to access data

# ...Do some processing and modify the dataset

MODIFIED_DS_DIR = Path('/path/to/modified_dataset')
slf.writer.write_dataset(ds, MODIFIED_DATASET_DIR)
```

See [the automatic sleep staging example](examples/dod_sleep_staging/README.md) for a full end-to-end example.

## Contributing

See [contributing](docs/contributing.md).
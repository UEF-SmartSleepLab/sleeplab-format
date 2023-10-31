# Converting the Sleep Cassette dataset to sleeplab-format

This is an example of how to convert EDF and EDF+ files to sleeplab-format. The example uses the [Sleep Cassette dataset](https://physionet.org/content/sleep-edfx/1.0.0/), which is openly available for download and usage.

## Setup

Clone the sleeplab-format repo and `cd` to the example folder.
```console
git clone https://github.com/UEF-SmartSleepLab/sleeplab-format.git
cd examples/sleep_edf_conversion
```

Create environment with Python 3.10, for example with conda:
```console
conda create -n sleep_edf_conversion python=3.10
conda activate sleep_edf_conversion
```

Install requirements
```console
pip install -r requirements.txt
```

## Download the data

```console
wget -r -N -c -np https://physionet.org/files/sleep-edfx/1.0.0/
```

## Convert to sleeplab-format

The code for conversion is in `convert_data.py`. The module provides a command line interface, which takes as arguments:
- --src-dir: The folder containing the original EDF data (`SC-subjects.xls` Excel and `sleep-cassette/` folder).
- --dst-dir: The folder where the sleeplab-format dataset will be saved.
- --array-format: The save format of the signals; `numpy` or `parquet`.
- --annotation-format: The save format of the annotation files; `json` or `parquet`.

For example, to store the signals as parquet files, and annotations as json files:
```console
python convert_data.py --src-dir physionet.org/files/sleep-edfx/1.0.0 \
    --dst-dir /tmp/sleeplab_format --array-format parquet --annotation-format json
```

The Sleep-Cassette dataset contains 153 PSG recordings, 20h duration each. There are two recordings recorded on consecutive dates for each subject. Detailed information can be found on the [dataset documentation](https://physionet.org/content/sleep-edfx/1.0.0/). The consecutive recordings are stored in separate sleeplab-format series `sc-night1` and `sc-night2`. Detailed information on the sleeplab-format data structures can be found in the [sleeplab-format documentation](https://uef-smartsleeplab.github.io/sleeplab-format/usage/).

## Resulting dataset sizes


| Dataset                       | Size (Gb) |
| -----------------             | ---------:|
| Original EDF files            | 7.42      |
| SLF, array format `numpy`     | 14.85     |
| SLF, array format `parquet`   | 5.36      |


The EDF files stores signals as 16-bit signed ints. In this example, the signals are stored as 32-bit floats in the sleeplab-format, which doubles the dataset size if uncompressed numpy files are used for the signals. However, if the signals are saved in parquet files, the size is reduced significantly from the original EDF files. The reason for this size reduction is currently not known. Parquet uses Snappy compression algorithm, which encodes recurring patterns as (pattern, count) pairs. However, EEG, EOG, and EMG signals are characterized by random fluctuations and noise, which means that a lossless compression algorithm should not be able to compress the data significantly. The size reduction might be related to the AD and EDF conversions, signal filtering, and artefacts.

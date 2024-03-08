# Sleep staging using Dreem Open Datasets

This is an end-to-end example of how to convert data from another format to sleeplab format, how to preprocess the data using sleeplab-extractor, and how to train a deep learning model utilizing sleeplab-tf-dataset. This example uses data from Dreem Open Datasets (DOD) since the DOD is well documented and open access ([https://doi.org/10.1109/TNSRE.2020.3011181](https://doi.org/10.1109/TNSRE.2020.3011181)).

## Prerequisites

 **The code is developed and tested with Linux and Python 3.10**. Windows users can install [Windows Subsystem for Linux](https://learn.microsoft.com/en-us/windows/wsl/install) to run this example (and to use Linux for development in general).

If you do not yet have a copy of this example, you can clone the repository to current working directory and go to the example folder:
```console
git clone https://github.com/UEF-SmartSleepLab/sleeplab-format.git
cd sleeplab-format/examples/dod_sleep_staging
```

## Install dependencies

```bash
pip install -r requirements.txt
```

## Convert data to sleeplab format

NOTE: This will download and convert the whole dataset with the original 250Hz sampling rate. The h5 files take 57 GB on disk, and the converted slf dataset takes 30 GB.

The examples below use `/tmp` as the base directory. Substitute it with another location if you want to persist the data and results.

First, download the datasets
```bash
mkdir /tmp/dod
python download_data.py --dst-dir /tmp/dod
```

Then, run the conversion
```bash
python convert_data.py --src-dir /tmp/dod --dst-dir /tmp/slf
```

## Extract and preprocess a subset of the signals

Use `sleeplab_format.extractor` to extract a single EEG channel, EOG channel, and EMG channel. Resample to 64Hz, highpass filter, and normalize the signals.

All configurations for the extractor are in `extractor_config.yml`.

To perform the extraction, run in this directory:
```bash
slf-extract --src_dir /tmp/slf/dod --dst_dir /tmp/slf --config_path ./extractor_config.yml
```

## Train a sleep staging model with the data

Now, use the preprocessed 64Hz data for automatic sleep staging. The model and training loop are defined in `train.py`.

```bash
python train.py --model-dir /tmp/dod_models --epochs 100
```

This should achieve 75-85% validation accuracy, and 70-80% test accuracy. Since the dataset is relatively small (50, 11, and 20 recordings for training, validation, and test sets), the performance fluctuates quite much between the runs. No hyperparameter tuning has been performed, default values are used everywhere.

# Sleep staging using Dreem Open Datasets

This is an end-to-end example of how to convert data from another format to sleeplab format, how to preprocess the data using sleeplab-extractor, and how to train a deep learning model utilizing sleeplab-tf-dataset. This example uses data from Dreem Open Datasets (DOD) since the DOD is well documented and open access ([https://doi.org/10.1109/TNSRE.2020.3011181](https://doi.org/10.1109/TNSRE.2020.3011181)).

The examples below use `/tmp` as the base directory. Substitute it with another location if you want to persist the data and results.

## Install dependencies

```bash
pip install -r requirements.txt
```

## Convert data to sleeplab format

NOTE: This will download and convert the whole dataset with the original 250Hz sampling rate. The h5 files take 57 GB on disk, and the converted slf dataset takes 30 GB.

First, download the datasets
```bash
python download_data.py --dst-dir /tmp/dod
```

Then, run the conversion
```bash
python convert_data.py --src-dir /tmp/dod --dst-dir /tmp/dod_slf
```

## Train a sleep staging model with the data

```bash
python train.py --ds-dir /tmp/dod_slf --model-dir /tmp/dod_model
```

## Evaluate the trained model

```bash
python evaluate.py --ds-dir /tmp/dod_slf --model_dir /tmp/dod_model
```

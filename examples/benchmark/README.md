# Benchmark SLF conversion and read performance

This benchmark uses [nocache](https://github.com/Feh/nocache) to prevent utilization of main memory to cache the files. The code was developed using Ubuntu 22.04 and Python 3.10.

## Prerequisites

Download the EDF files according to the [Sleep-Cassette conversion](https://github.com/UEF-SmartSleepLab/sleeplab-format/tree/main/examples/sleep_cassette_conversion) and [Dreem Open Data sleep staging](https://github.com/UEF-SmartSleepLab/sleeplab-format/tree/main/examples/dod_sleep_staging) examples.

## Usage

Clone the repo and go to the benchmark folder:
```bash
git clone https://github.com/UEF-SmartSleepLab/sleeplab-format.git
cd sleeplab-format/examples/benchmark
```

Install the requirements and `nocache` package:
```bash
pip install -r requirements.txt
sudo apt install nocache
```

Assuming you have downloaded the datasets under `tmp`, run the benchmark with:
```bash
nocache python benchmark.py --slf-dir /tmp/slf_benchmark --output-path benchmark_out.json --dod-orig-dir /tmp/dod --sc-orig-dir /tmp/physionet.org/files/sleep-edfx/1.0.0
```

Running the benchmark will take several hours due to testing Zstandard compression with maximum compression level. The results will be written to `./benchmark_out.json`

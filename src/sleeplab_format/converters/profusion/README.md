# Generating dataset from Compumedics Profusion 4.1 exports

## Requirements

To convert Profusion exports to the sleeplab format, following exported files for each subject are *required*:

- .edf file containing the signals
- .xml event file containing the event annotations and sleep stages
- .txt hypnogram to parse the sleep stage mapping information
- .txt study log file to parse log data, e.g. the lights on and off information
- .txt idinfo to parse the profusion's internal study id

### Required folder structure

The exported data needs to be structured in a specific manner:

```bash
<root_dir>
|-- edf_files
|-- event_files_txt
|-- event_files_xml
|-- log_files
|-- studycfg_files
```

## Running the generation

```bash
python convert.py \
    --src_dir <SOURCE_DIRECTORY> \
    --dst_dir <DESTINATION_DIRECTORY>
```
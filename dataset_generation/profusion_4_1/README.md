# Generating dataset from Compumedics Profusion 4.1 exports

## Requirements

To generate the sleeplab format, following exported files are *required*:

Original recording files from profusion:

- studycfg.xml to parse the start time and study ID

Export files generated from Profusion:

- .edf files containing the signals
- .xml event files containing the event annotations and sleep stages
- .txt event files to parse the sleep stage mapping information
- .txt log files to parse the lights on and off informaton

## Running the generation

```bash
python ...
```
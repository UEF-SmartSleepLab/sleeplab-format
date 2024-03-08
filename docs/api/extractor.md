# sleeplab_format.extractor.cli

::: sleeplab_format.extractor.cli
    options:
        members:
            - extract

# sleeplab_format.extractor.preprocess

::: sleeplab_format.extractor.preprocess
    options:
        members:
            - highpass
            - lowpass
            - resample_polyphase
            - decimate
            - upsample_linear
            - iqr_norm
            - z_score_norm
            - add_ref
            - sub_ref

# sleeplab_format.extractor.config

::: sleeplab_format.extractor.config
    options:
        members:
            - DatasetConfig
            - SeriesConfig
            - ArrayConfig
            - ArrayAction
            - FilterCond
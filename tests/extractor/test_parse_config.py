from sleeplab_format.extractor import config


def test_parse_config(example_extractor_config_path):
    cfg = config.parse_config(example_extractor_config_path)
    assert type(cfg) == config.DatasetConfig

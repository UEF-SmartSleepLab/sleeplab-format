"""CLI for extracting and preprocessing a subset of data in sleeplab format."""
import argparse
import json
import logging

from pathlib import Path
from sleeplab_format.extractor import config, preprocess
from sleeplab_format import reader, writer


logger = logging.getLogger(__name__)


def extract(src_dir: Path, dst_dir: Path, cfg: config.DatasetConfig) -> None:
    """Read, preprocess, and write data in sleeplab format.
    
    Arguments:
        src_dir: The source SLF dataset folder.
        dst_dir: The root folder where the extracted dataset will be saved.
        cfg: The extractor config.
    """ 
    logger.info(f'Reading dataset from {src_dir}')
    series_names = [series_config.name for series_config in cfg.series_configs]
    ds = reader.read_dataset(src_dir, series_names=series_names)
    
    updated_series = {}
    series_skipped = {}

    for series_config in cfg.series_configs:
        logger.info(f'Creating updated series {series_config.name}')
        _series, _skipped = preprocess.process_series(ds.series[series_config.name], series_config)
        updated_series[series_config.name] = _series
        series_skipped[series_config.name] = _skipped
    
    logger.info('Creating updated Dataset')
    ds = ds.model_copy(update={'name': cfg.new_dataset_name, 'series': updated_series})

    logger.info(f'Applying preprocessing and writing dataset to {dst_dir}')
    writer.write_dataset(
        ds, dst_dir, annotation_format=cfg.annotation_format, array_format=cfg.array_format)

    if series_skipped != {}:
        skipped_path = Path(dst_dir) / ds.name / '.extractor_skipped_subjects.json'
        logger.info(f'Writing skipped subject IDs and reasons to {skipped_path}')
        with open(skipped_path, 'w') as f:
            json.dump(series_skipped, f, indent=2)


def get_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('-s', '--src_dir', required=True)
    parser.add_argument('-d', '--dst_dir', required=True)
    parser.add_argument('-c', '--config_path', required=True)

    return parser


def run_cli():
    parser = get_parser()
    args = parser.parse_args()
    
    logger.info(f'Reading config from {args.config_path}')
    cfg = config.parse_config(Path(args.config_path))
    
    extract(
        Path(args.src_dir),
        Path(args.dst_dir),
        cfg
    )


if __name__ == '__main__':
    run_cli()

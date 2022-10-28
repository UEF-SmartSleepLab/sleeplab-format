"""Parse Profusion export data and write to sleeplab format."""
import argparse

from dataset_generation import edf, writer
from dataset_generation.models import *
from pathlib import Path


def read_data(basedir):
    pass


def generate_dataset(input_basedir: Path, output_basedir: Path) -> None:
    dataset = read_data(input_basedir)
    writer.write_dataset(dataset, output_basedir)


def create_parser():
    parser = argparse.ArgumentParser()
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()
    generate_dataset(args.input_basedir, args.output_basedir)


if __name__ == '__main__':
    main()
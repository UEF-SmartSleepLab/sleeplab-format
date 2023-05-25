"""Download Dreem datasets. Modified from
https://github.com/Dreem-Organization/dreem-learning-open/blob/master/download_data.py
"""
import argparse
import boto3
import tqdm

from botocore import UNSIGNED
from botocore.client import Config
from pathlib import Path


def download_data(dst_dir: Path):
    client = boto3.client('s3', config=Config(signature_version=UNSIGNED))

    bucket_objects = client.list_objects(Bucket='dreem-dod-o')["Contents"]
    print("\n Downloading H5 files and annotations from S3 for DOD-O")
    savedir = dst_dir / 'dodo'
    savedir.mkdir(exist_ok=True)
    for bucket_object in tqdm.tqdm(bucket_objects):
        filename = bucket_object["Key"]
        savepath = savedir / filename
        client.download_file(
            Bucket="dreem-dod-o",
            Key=filename,
            Filename=savepath 
        )
        
    bucket_objects = client.list_objects(Bucket='dreem-dod-h')["Contents"]
    print("\n Downloading H5 files and annotations from S3 for DOD-H")
    savedir = dst_dir / 'dodh'
    savedir.mkdir(exist_ok=True)
    for bucket_object in tqdm.tqdm(bucket_objects):
        filename = bucket_object["Key"]
        savepath = savedir / filename
        client.download_file(
            Bucket="dreem-dod-h",
            Key=filename,
            Filename=savepath
        )


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dst-dir',
                        help='the directory where to download the data')
    return parser


if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()
    dst_dir = Path(args.dst_dir)
    download_data(dst_dir=dst_dir)

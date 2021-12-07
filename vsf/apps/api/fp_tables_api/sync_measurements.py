from django.conf        import settings
import argparse
import datetime as dt
from functools import singledispatch
import gzip
import logging
from multiprocessing.pool import ThreadPool
import os
import pathlib
import sys
from typing import List
import shutil
import ujson
import json

from . import ooni_client


@singledispatch
def trim_measurement(json_obj, max_string_size: int):
    return json_obj


@trim_measurement.register(dict)
def _(json_dict: dict, max_string_size: int):
    keys_to_delete: List[str] = []
    for key, value in json_dict.items():
        if type(value) == str and len(value) > max_string_size:
            keys_to_delete.append(key)
        else:
            trim_measurement(value, max_string_size)
    for key in keys_to_delete:
        del json_dict[key]
    return json_dict


@trim_measurement.register(list)
def _(json_list: list, max_string_size: int):
    for item in json_list:
        trim_measurement(item, max_string_size)
    return json_list


class CostLimitError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)

def _make_local_path(output_dir: pathlib.Path, entry: ooni_client.FileEntry) -> pathlib.Path:
    basename = pathlib.PurePosixPath(entry.url.path).name
    # Convert .json.lz4 and .tar.lz4 filenames.
    if not basename.endswith('.jsonl'):
        basename = basename.rsplit(settings.MEDIA_ROOT, 2)[0] + '.jsonl'
    return output_dir / basename


def s3_measurements_download(test_type=None, country:str='VE', 
    first_date:str=(dt.date.today() - dt.timedelta(days=3)), 
    last_date:str=(dt.date.today() - dt.timedelta(days=2)), max_string_size:int=1000, 
    cost_limit_usd:float=100.00):

    print('Since: ', first_date, ' to: ', last_date)

    logging.basicConfig(level=logging.INFO)

    logging.basicConfig(level=logging.DEBUG)

    ooni = ooni_client.OoniClient()
    num_measurements = 0
    file_entries = ooni.list_files(
        first_date, last_date, test_type, country)

    def sync_file(entry: ooni_client.FileEntry):
        target_file_path = _make_local_path(pathlib.Path('./media/ooni_data/'), entry)
        if target_file_path.is_file():
            return f'Skipped existing {entry.url.geturl()}]'
        return fetch_file(entry, target_file_path)

    def fetch_file(entry: ooni_client.FileEntry, target_file_path: pathlib.Path):
        nonlocal num_measurements
        os.makedirs(target_file_path.parent, exist_ok=True)
        if ooni.cost_usd > cost_limit_usd:
            raise CostLimitError(
                f'Downloaded {ooni.bytes_downloaded / 2**20} MiB')
        # We use a temporary file to atomatically write the destination and make sure we don't have partially written files.
        # We put the temporary file in the same location as the destination because you can't atomically
        # rename if they are in different devices, as is the case for Kaggle.
        temp_path = target_file_path.with_name(f'{target_file_path.name}')
        try:
            #with gzip.open(temp_path, mode='wt', encoding='utf-8', newline='\n') as target_file:
            with open(temp_path, 'wt', encoding='utf-8', newline='\n') as f:
                f.write('[')
    
                for measurement in entry.get_measurements():
                    num_measurements += 1
                    m = trim_measurement(measurement, max_string_size)
                    ujson.dump(m, f)
                    f.write(',')

                #f.write(']')
                temp_path.replace(target_file_path)
        except:
            temp_path.unlink()
            raise
        return f'Downloaded {entry.url.geturl()} [{entry.size:,} bytes]'

    with ThreadPool(processes=5 * os.cpu_count()) as sync_pool:
        for msg in sync_pool.imap_unordered(sync_file, file_entries):
            logging.info(msg)

    logging.info(f'Measurements: {num_measurements}, Downloaded {ooni.bytes_downloaded/2**20:0.3f} MiB, Estimated Cost: ${ooni.cost_usd:02f}')


def _parse_date_flag(date_str: str) -> dt.date:
    return dt.datetime.strptime(date_str, "%Y-%m-%d").date()
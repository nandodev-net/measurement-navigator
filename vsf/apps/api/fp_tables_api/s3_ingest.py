"""
    Additional functionality to perform validations in the post request
"""

# Third party imports
from bz2 import decompress
#from memory_profiler import profile
from typing import List
from django.utils import timezone
import time
import json
import requests
import datetime
import collections
from pathlib import Path
import gzip
import json
import os

# Python imports
import tracemalloc
from pathlib import Path

# Local imports
from apps.main.sites.models             import URL
from apps.main.ooni_fp.fp_tables.models import FastPath
from apps.main.measurements.models      import RawMeasurement
from apps.api.fp_tables_api.utils import display_top_mem_intensive_lines
from .sync_measurements import *
from vsf.utils import Colors as c

# Bulk create manager import
from vsf.bulk_create_manager import BulkCreateManager
from apps.main.measurements.post_save_utils import post_save_rawmeasurement

import pytz
utc=pytz.UTC

meas_path = './media/ooni_data/'

class S3IngestManager:
    """All operations required to retrieve and store ooni data from s3
    """

    # Test types in the same format as in s3
    S3_TEST_TYPES : List[str] = ['tor','webconnectivity', 'vanillator', 'urlgetter', 
        'torsf', 'httpinvalidrequestline', 'httpheaderfieldmanipulation', 
        'whatsapp', 'facebookmessenger', 'ndt', 'tcpconnect', 'signal', 
        'riseupvpn', 'dash', 'telegram', 'psiphon', 'multiprotocoltraceroute', 
        'meekfrontedrequeststest', 'httprequests', 'httphost','dnscheck', 
        'dnsconsistency', 'bridgereachability']

    def __init__(self, measurements_path  : str = './media/ooni_data/', date_format : str = "%Y-%m-%d %H:%M:%S") -> None:
        self._measurements_path = measurements_path 
        self._date_format = date_format

    def process_jsonl_file(self, file_name : str, cache_min_date : datetime.datetime, save_chunk_size : int = 1000):
        """Process a single jsonl file, parsing its measurements and storing them in database

        Args:
            file_name (str): name of jsonl file
            cache_min_date (datetime.datetime): @TODO Write meaning of this date 
            save_chunk_size (int): how many measurements to save per batch
        """
        # Sanity check
        assert save_chunk_size > 0
        assert file_name.endswith(".jsonl"), "This should be a jsonl file"

        # Check if file exists
        path_to_jsonl = Path(file_name)
        if not path_to_jsonl.exists():
            raise ValueError(f"file {path_to_jsonl} does not exists")

        # Use this object to save measurements
        bulker = BulkCreateManager(chunk_size=save_chunk_size)

        # Dummy object used when some measurements don't have an url field. We
        # create it first in case it does not exists
        no_url_obj = URL.objects.get_or_create(url='no_url')

        # Get amount of line sin this file to plot progress
        with path_to_jsonl.open("r") as file:
            n_lines = sum(1 for _ in file)

        # Process file line by line
        with path_to_jsonl.open('r') as file:
            for (i, line) in enumerate(file):
                print(c.cyan(f"Processing line {i+1} / {n_lines}"))

                result = json.loads(line)

                # Get input of this measurement
                if result['test_name'] == 'tor' and result['test_keys']==None:
                        continue
                elif result['test_name'] == 'tor' or result['input'] == None:
                    measurement_input = 'no_url'
                else:
                    measurement_input = result['input']

                # Checking if the RawMeasurement exists
                raw_object = RawMeasurement.objects.filter(input=measurement_input, 
                                                            report_id=result['report_id'], 
                                                            probe_asn=result['probe_asn'], 
                                                            test_name=result['test_name'], 
                                                            measurement_start_time=result['measurement_start_time'])

                # If the RawMeasurement does exists, then nothing to do here
                if raw_object:
                    continue
                
                test_start_time = datetime.datetime.strptime(result['test_start_time'], "%Y-%m-%d %H:%M:%S")
                measurement_start_time = datetime.datetime.strptime(result['measurement_start_time'], "%Y-%m-%d %H:%M:%S")
                ms = RawMeasurement(
                    input=measurement_input,
                    report_id= result['report_id'],
                    report_filename= result.get('report_filename','NO_AVAILABLE'), #
                    options= result.get('options', "NO_AVAILABLE"), #
                    probe_cc= result.get('probe_cc','VE'),
                    probe_asn= result['probe_asn'],
                    probe_ip=result.get('probe_ip'),
                    data_format_version= result['data_format_version'],
                    test_name= result['test_name'],
                    test_start_time= test_start_time.replace(tzinfo=utc),
                    measurement_start_time= measurement_start_time.replace(tzinfo=utc),
                    test_runtime= result.get('test_runtime'),
                    test_helpers= result.get('test_helpers',"NO_AVAILABLE"),
                    software_name= result['software_name'],
                    software_version= result['software_version'],
                    test_version= result['test_version'],
                    bucket_date= result.get('bucket_date'), #
                    test_keys= result.get('test_keys',"NO_AVAILABLE"),
                    annotations= result['annotations'],
                    is_processed= False
                )

                # Delete web connectivity body, as it is takes too much memory
                if ms.test_name == 'web_connectivity':
                    if ms.test_keys and ms.test_keys.get("requests"):
                        for r in ms.test_keys['requests']:
                            if r['response'].get("body"):
                                del r['response']['body']
                                r['response']['body'] = "Not_available"
                try:
                    bulker.add(ms)
                    start_time_datetime = ms.measurement_start_time # convert date into string
                    if start_time_datetime < cache_min_date.replace(tzinfo=utc):
                        cache_min_date = start_time_datetime

                except Exception as e: 
                    print(e) # Ignore errors and keep saving measurements

        # Clean and quit
        bulker.done()
        os.remove(str(path_to_jsonl)) # Delete file when you're done with it

        print(c.green(f"[SUCCESS] Finished processing jsonl file"))

    def collect_incompatible_files(self, output_dir : str, incompatible_dir : str,  cache_min_date : datetime.datetime):
        """TODO explain this function

        Args:
            output_dir (str): TODO
            incompatible_dir (str): TODO
            cache_min_date (datetime.datetime): TODO
        """
        file_list = os.listdir(output_dir) # list of file names
        if not file_list:
            return
        else:
            print("Directory is not empty")
            for file_name in file_list:
                if file_name.endswith('.jsonl'):
                    try:
                        process_jsonl_file(output_dir + file_name, cache_min_date)
                    except Exception as e:
                        print(e)
                        os.rename(output_dir + file_name, incompatible_dir + file_name)

                else:
                    jsonl_file = self._decompress_file(output_dir, file_name)
                    try:
                        process_jsonl_file(output_dir + jsonl_file, cache_min_date)
                    except Exception as e:
                        print(e)
                        os.rename(output_dir + jsonl_file, incompatible_dir + jsonl_file)

    def _decompress_file(self, output_dir : str, gz_file : str):
        """Decompress a file

        Args:
            output_dir (str): Path where to store decompressed output
            gz_file (str): file to decompress

        Returns:
            TODO: TODO
        """
        full_route = output_dir + gz_file
        with gzip.open(full_route,'r') as current_file:
            file_content = current_file.read()
            file = open(full_route[:-3], "w")
            file.write(file_content.decode('UTF-8'))
            file.close()
            # Deleting Gzip file
            os.remove(full_route)

        return gz_file[:-3]

    def process_raw_measurements(self, first_date : datetime.datetime):
        """Process measurements that are not still processed (measurements with is_processed == False),
            creating their submeasurements as neeeded

        Args:
            first_date (datetime.datetime): Date of first measurement to update
        """

        print(c.cyan("Processing measurements..."))
        queryset_= RawMeasurement.objects.filter(is_processed=False)
        qs_size = len(queryset_)
        
        for (i, raw_meas) in enumerate(queryset_.iterator(chunk_size=1000)):
            print(c.green(f'Processing {i + 1} of {qs_size}'))
            post_save_rawmeasurement(raw_meas, first_date)
        
        print(c.green("Measurements succesfully processed!"))

    def ingest(
        self,
        test_types : List[str] = [],
        first_date : datetime.date = (datetime.date.today() - datetime.timedelta(days=3)), 
        last_date  : datetime.date = (datetime.date.today() - datetime.timedelta(days=2)),
        country    : str = 'VE',
        output_dir : str = './media/ooni_data/',
        incompatible_dir: str = './media/incompatible_data/'
        ):
        """Perform an ingestion process, saving measurements stored in ooni s3

        Args:
            test_types (List[str], optional): List of types of measurements to save, if empty or not provided, defaults to all types. Defaults to [].
            first_date (datetime.date, optional): min date of measurements to search for. Defaults to (datetime.date.today() - datetime.timedelta(days=3)).
            last_date (datetime.date, optional): max date of measurements to search for. Defaults to (datetime.date.today() - datetime.timedelta(days=2)).
            country (str, optional): country code for the country that all measurements should share. Defaults to 'VE'.
            output_dir (str, optional): where to store data when downloading. Defaults to './media/ooni_data/'.
            incompatible_dir (str, optional): Where to store incompatible data. Defaults to './media/incompatible_data/'.
        """

        # Set up types
        test_types = test_types or self.S3_TEST_TYPES

        # Take time to have some idea in performance
        time_ini = time.time()
        cache_min_date = datetime.datetime.now() + datetime.timedelta(days=1)

        # Searching previous files to add or store them
        self.collect_incompatible_files(output_dir, incompatible_dir, cache_min_date)

        # Downloading S3 measurements
        for test in test_types:
            s3_measurements_download(test, first_date=first_date, last_date=last_date, country=country, output_dir=output_dir)

        # Get all .gz names in the output directory in order to decompress them
        gz_list = os.listdir(output_dir)
        for (i, gzfile) in enumerate(gz_list):
            print(c.blue(f"processing json {i+1} / {len(gz_list)}"))
            json_file = self._decompress_file(output_dir, gzfile)

            try:
                # Create raw measurements
                self.process_jsonl_file(output_dir + json_file, cache_min_date)
                # Process raw measurements
                self.process_raw_measurements(first_date)
            except:
                os.rename(output_dir + json_file, incompatible_dir + json_file)

        ####### LOG JUST TO TAKE PROCESS TIME
        time_end = time.time()
        f = open("./media/inform.txt", "a+")
        print('\n\nS3 ingest time: ', time_end-time_ini)
        f.write(str(first_date)+' - '+str(last_date)+': '+ str(time_end-time_ini)+'\n')
        f.close()
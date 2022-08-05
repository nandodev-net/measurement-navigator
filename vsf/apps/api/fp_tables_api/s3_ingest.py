"""
    Additional functionality to perform validations in the post request
"""

# Third party imports
from bz2 import decompress
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
# Local imports
from apps.main.sites.models             import URL
from apps.main.ooni_fp.fp_tables.models import FastPath
from apps.main.measurements.models      import RawMeasurement
from .sync_measurements import *

# Bulk create manager import
from vsf.bulk_create_manager import BulkCreateManager
from apps.main.measurements.post_save_utils import post_save_rawmeasurement

import pytz
utc=pytz.UTC

meas_path = './media/ooni_data/'

def process_jsonl_file(file_name, cache_min_date):
    new_meas_list = []

    from vsf.utils import Colors as c
    bulk_mgr = BulkCreateManager(chunk_size=1000)
    with open(file_name) as f:
        for line in f:
            result = json.loads(line)
            if result['test_name'] == 'tor':
                if result['test_keys']==None:
                    continue
                else:
                    URL.objects.get_or_create(url='no_url')
                    input_ = 'no_url'
            else:
                if result['input'] == None:
                    URL.objects.get_or_create(url='no_url')
                    input_ = 'no_url'
                else:
                    URL.objects.get_or_create(url=result['input'])
                    input_ = result['input'] 


            # Checking if the RawMeasurement exists
            raw_object = RawMeasurement.objects.filter(input=input_, 
                                                        report_id=result['report_id'], 
                                                        probe_asn=result['probe_asn'], 
                                                        test_name=result['test_name'], 
                                                        measurement_start_time=result['measurement_start_time'])

            if len(raw_object) == 0:

                test_start_time = datetime.datetime.strptime(result['test_start_time'], "%Y-%m-%d %H:%M:%S")
                measurement_start_time = datetime.datetime.strptime(result['measurement_start_time'], "%Y-%m-%d %H:%M:%S")
                ms = RawMeasurement(
                    input=input_,
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

                # Eliminando body de las web_connectivity

                if ms.test_name == 'web_connectivity':
                    if not ms.test_keys or not ms.test_keys.get("requests"):
                        pass
                    else:
                        for r in ms.test_keys['requests']:
                            if r['response'].get("body"):
                                del r['response']['body']
                                r['response']['body'] = "Not_available"

                new_meas_list.append(ms)

                try:
                    print(c.magenta(">>>>>Bulk Creating new measurements<<<<"))

                    bulk_mgr.add(ms)
                    start_time_datetime = ms.measurement_start_time # convert date into string
                    #print(c.green(f"Trying to update cache, start time: {ms_.measurement_start_time}, cache: {cache_min_date}. Is less: {start_time_datetime < cache_min_date}"))
                    if start_time_datetime < cache_min_date.replace(tzinfo=utc):
                        cache_min_date = start_time_datetime
                        #print(c.red("Updating min date cache:"), c.cyan(cache_min_date))

                except Exception as e: print(e)
                
    os.remove(file_name)


def decompress_file(
    output_dir,
    gz_file,
    ):

    full_route = output_dir + gz_file
    with gzip.open(full_route,'r') as current_file:
        file_content = current_file.read()
        file = open(full_route[:-3], "w")
        file.write(file_content.decode('UTF-8'))
        file.close()
        # Deleting Gzip file
        os.remove(full_route)
    return gz_file[:-3]


def incompatible_file_collector(
    output_dir, 
    incompatible_dir, 
    cache_min_date, 
    ):

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
                jsonl_file = decompress_file(output_dir, file_name)
                try:
                    process_jsonl_file(output_dir + jsonl_file, cache_min_date)
                except Exception as e:
                    print(e)
                    os.rename(output_dir + jsonl_file, incompatible_dir + jsonl_file)


def process_raw_measurements(first_date):

    print('>>>>PROCESSING INFO<<<<')
    from vsf.utils import Colors as c
    queryset_= RawMeasurement.objects.filter(is_processed=False)
    size_qs = len(queryset_)
    current_qs = 1
    for raw_meas in queryset_.iterator(chunk_size=1000):
        print(c.green(f'Processing '+str(current_qs)+' of '+str(size_qs)))
        post_save_rawmeasurement(raw_meas, first_date)
        current_qs+=1   
            


def s3_ingest_manager(
    test_types : List[str] = ['tor','webconnectivity', 'vanillator', 'urlgetter', 
    'torsf', 'httpinvalidrequestline', 'httpheaderfieldmanipulation', 
    'whatsapp', 'facebookmessenger', 'ndt', 'tcpconnect', 'signal', 
    'riseupvpn', 'dash', 'telegram', 'psiphon', 'multiprotocoltraceroute', 
    'meekfrontedrequeststest', 'httprequests', 'httphost','dnscheck', 
    'dnsconsistency', 'bridgereachability'] ,
    first_date:datetime.datetime = (datetime.date.today() - datetime.timedelta(days=3)), 
    last_date:datetime.datetime = (datetime.date.today() - datetime.timedelta(days=2)),
    country: str = 'VE',
    output_dir: str = './media/ooni_data/',
    incompatible_dir: str = './media/incompatible_data/'
    ):

    time_ini = time.time()
    cache_min_date = datetime.datetime.now() + datetime.timedelta(days=1)
    jsonl_file_list = []

    # Searching previous files to add or store them
    incompatible_file_collector(output_dir, incompatible_dir, cache_min_date)

    # Downloading S3 measurements
    for test in test_types:
        s3_measurements_download(test, first_date=first_date, last_date=last_date, country=country, output_dir=output_dir)

    # Get all .gz names in the output directory in order to decompress them
    gz_list = os.listdir(output_dir)
    for gzfile in gz_list:
        jsol_file = decompress_file(output_dir, gzfile)
        jsonl_file_list.append(jsol_file)
    
    # Try to add the resultant .jsonl files.
    for jsonl in jsonl_file_list:
        print('Processing JsonL: ', jsonl)
        print('from: ', first_date)
        try:
            process_jsonl_file(output_dir + jsonl, cache_min_date)
        except:
            os.rename(output_dir + jsonl, incompatible_dir + jsonl)


    # Process all rar measurements in order to obtain the submeasurements.
    process_raw_measurements(first_date)

    ####### LOG JUST FOR TAKE PROCESS TIME
    time_end = time.time()
    f = open("./media/inform.txt", "a+")
    print('\n\nS3 ingest time: ', time_end-time_ini)
    f.write(str(first_date)+' - '+str(last_date)+': '+ str(time_end-time_ini)+'\n')
    f.close()

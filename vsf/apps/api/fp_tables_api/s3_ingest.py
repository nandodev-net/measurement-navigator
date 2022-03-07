"""
    Additional functionality to perform validations in the post request
"""

# Third party imports
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

meas_path = './media/ooni_data/'

def process_jsonl_file(file_name, cache_min_date):
    new_meas_list = []
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


            # Checking if the RM exists on the db
            raw_object = RawMeasurement.objects.filter(input=input_, 
                                                        report_id=result['report_id'], 
                                                        probe_asn=result['probe_asn'], 
                                                        test_name=result['test_name'], 
                                                        measurement_start_time=result['measurement_start_time']
                                                        )
            if len(raw_object) > 0:
                pass

            else:
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
                    test_start_time= result.get('test_start_time'),
                    measurement_start_time= result['measurement_start_time'],
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
    
    os.remove(file_name)
    from vsf.utils import Colors as c
    try:
        print(c.magenta(">>>>>Bulk Creating new measurements<<<<"))

        bulk_mgr = BulkCreateManager(chunk_size=500)
        for ms_ in new_meas_list:
            bulk_mgr.add(ms_)
            start_time_datetime = datetime.datetime.strptime(ms_.measurement_start_time, "%Y-%m-%d %H:%M:%S") # convert date into string
            #print(c.green(f"Trying to update cache, start time: {ms_.measurement_start_time}, cache: {cache_min_date}. Is less: {start_time_datetime < cache_min_date}"))
            if start_time_datetime < cache_min_date:
                cache_min_date = start_time_datetime
                #print(c.red("Updating min date cache:"), c.cyan(cache_min_date))
        bulk_mgr.done()

    except Exception as e: print(e)



def request_s3_meas_data(
    test_types = ['tor','webconnectivity', 'vanillator', 'urlgetter', 
    'torsf', 'httpinvalidrequestline', 'httpheaderfieldmanipulation', 
    'whatsapp', 'facebookmessenger', 'ndt', 'tcpconnect', 'signal', 
    'riseupvpn', 'dash', 'telegram', 'psiphon', 'multiprotocoltraceroute', 
    'meekfrontedrequeststest', 'httprequests', 'httphost','dnscheck', 
    'dnsconsistency', 'bridgereachability'],
    first_date:str=(datetime.date.today() - datetime.timedelta(days=3)), 
    last_date:str=(datetime.date.today() - datetime.timedelta(days=2)),
    country: str = 'VE',
    output_dir: str = './media/ooni_data/'  
    ):


    print('-----------------------')
    print('S3 INGEST BEGINS')
    print('-----------------------')
    print('-----------------------')
    print('\nRequesting ooni data... \n')
    time_ini = time.time()
    cache_min_date = datetime.datetime.now() + datetime.timedelta(days=1)
    # output_dir file list
    gz_list = []
    jsonl_list = []
    
    for test in test_types:
        s3_measurements_download(test, first_date=first_date, last_date=last_date, country=country, output_dir=output_dir)

    print('\nTemp files created... \n')
    print('\nInitializing temp files analysis... \n')

    time.sleep(2)
    print('Colecting Gzip files...')
    for child in Path(meas_path).iterdir():
        if child.is_file():
            if child.name.endswith('gz'):
                gz_list.append(meas_path + child.name)
            else:
                jsonl_list.append(meas_path + child.name)

    if jsonl_list:
        print('Adding JsonLFiles')
        for file_name in jsonl_list:
            try:
                process_jsonl_file(file_name,cache_min_date)
            except:
                os.remove(file_name)
                continue           

    elif gz_list:

        print('Decompressing Gzip files...')
        for gz_file in gz_list:
            file_name = gz_file
            if not gz_file.endswith('jsonl'):
                with gzip.open(gz_file,'r') as current_file:
                    file_content = current_file.read()
                    file = open(gz_file[:-3], "w")
                    file.write(file_content.decode('UTF-8'))
                    file.close()
                    file_name = gz_file[:-3]
                    # Deleting Gzip file
                    os.remove(gz_file)
            else:
                pass

            print('Processing JsonL: ', file_name)
            print('from: ', first_date)

            try:
                process_jsonl_file(file_name,cache_min_date)
            except:
                continue

           
    print('>>>>PROCESSING INFO<<<<')
    from vsf.utils import Colors as c
    queryset_= RawMeasurement.objects.filter(is_processed=False)
    size_qs = len(queryset_)
    current_qs = 1
    for raw_meas in queryset_.iterator(chunk_size=100):
        print(c.green(f'Processing '+str(current_qs)+' of '+str(size_qs)))
        post_save_rawmeasurement(raw_meas, first_date)
        current_qs+=1


    time_end = time.time()
    f = open("./media/inform.txt", "a+")
    print('\n\nS3 ingest time: ', time_end-time_ini)
    f.write(str(first_date)+' - '+str(last_date)+': '+ str(time_end-time_ini)+'\n')
    f.close()
    return (True)

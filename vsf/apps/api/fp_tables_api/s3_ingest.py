"""
    Additional functionality to perform validations in the post request
"""
import django.utils.timezone    as timezone
import django.utils.dateparse   as dateparse

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

meas_path = './media/ooni_data/'

gz_list = []
file_list = []

def checkPostData(data) -> bool:
        """
        This function will check if the input data on the post request is valid.
        The input data should contain:
            since: measurement since this date (date in string format)
            until: measurement until this date (date in string format)
            probe_cc: 2 chars country code

        The dates are expected to be in the following format: YYYY-mm-dd
        """

        # Check valid input
        if not isinstance(data, collections.Mapping):
            raise  TypeError('Data parameter in checkPostData should be a Mapping type object')

        since = data.get('since')
        until = data.get('until')
        probe_cc = data.get('probe_cc')

        # Check if every field is a string
        if (not isinstance(since, str)) or (not isinstance(until,str)) or (not isinstance(probe_cc,str)):
            print("bad types")
            return False

        # Check valid fields
        if (since == None) or (until == None) or (probe_cc == None):
            return False

        date_format = '%Y-%m-%d'
        # check date formats
        try:
            datetime.datetime.strptime(since, date_format)
        except:
            return False

        try:
            datetime.datetime.strptime(until, date_format)
        except:
            return False

        # Check country code has 2 chars & uppercase (ooni requires it to be upper)
        if len(probe_cc) != 2 or not probe_cc.isupper():
            # Warning: It's still possible that the country code is not valid,
            # further validation will be performed during the database queryng
            return False


        return True

def request_s3_meas_data():
    print('-----------------------')
    print('S3 INGEST BEGINS')
    print('-----------------------')
    print('-----------------------')
    print('\nRequesting ooni data... \n')
    time_ini = time.time()
    test_types = ['tor','webconnectivity', 'vanillator', 'urlgetter', 'torsf', 'httpinvalidrequestline', 
    'httpheaderfieldmanipulation', 'whatsapp', 'facebookmessenger', 'ndt', 'tcpconnect', 'signal', 'riseupvpn',
    'dash', 'telegram', 'psiphon', 'multiprotocoltraceroute', 'meekfrontedrequeststest', 'httprequests', 'httphost',
    'dnscheck', 'dnsconsistency', 'bridgereachability']

    #test_types = ['tor']
    
    for test in test_types:
        s3_measurements_download(test)

    print('\nTemp files created... \n')
    cache_min_date = datetime.datetime.now() + datetime.timedelta(days=1)
    print('\nInitializing temp files analysis... \n')

    time.sleep(2)
    print('Colecting Gzip files...')
    for child in Path(meas_path).iterdir():
        if child.is_file():
            gz_list.append(meas_path + child.name)


    print('Decompressing Gzip files...')
    for gz_file in gz_list:
        with gzip.open(gz_file,'r') as current_file:
            file_content = current_file.read()
            file = open(gz_file[:-3], "w")
            file.write(file_content.decode('UTF-8'))
            file.close()
            file_list.append(gz_file[:-3])
            os.remove(gz_file)


    print('Reading JSONL files...')
    for jsonl_file in file_list:
        with open(jsonl_file) as f:
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


                from vsf.utils import Colors as c
                try:
                    print(c.magenta("Creating a new measurement"))

                    ms = RawMeasurement.objects.create(
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
                        annotations= result['annotations']
                    )

                    start_time_datetime = datetime.datetime.strptime(ms.measurement_start_time, "%Y-%m-%d %H:%M:%S") # convert date into string
                    print(c.green(f"Trying to update cache, start time: {ms.measurement_start_time}, cache: {cache_min_date}. Is less: {start_time_datetime < cache_min_date}"))
                    if start_time_datetime < cache_min_date:
                        cache_min_date = start_time_datetime
                        print(c.red("Updating min date cache:"), c.cyan(cache_min_date))
                except Exception as e: print(e)

    print('Removing temporal files...')
    for jsonl_file in file_list:
       os.remove(jsonl_file)

    time_end = time.time()
    print('\n\n1-Day Measurement ingest time: ', time_end-time_ini)
    return (True)

def update_measurement_table(
                            n_measurements : int = None,
                            test_name      : str = None,
                            retrys         : int = -1
                            ) -> dict:
    """
        Store at the most 'n_measurements' ready measurements of type 'test_name'
        into the  database. Defaults to all measurements yo can add, for
        any kind of measurement.

        Set the measurements with a 'try' value greater than 'retrys' as DEAD.
        If 'retrys' is negative, then it is never set to DEAD, no matter how many trys it has.

        This function will update the Measurement table
        and the fast path table depending on the availability of
        measurements in the fast path table.

        Get every measurement in the database whose report_ready
        is set to false or None, and whose catch_date - now > 24h.
        perform a request for the measurementl.
        If the measurement is available, change report_ready to true and
        create a new measurement object in the database. Otherwise,
        report_ready is set to null.

        Returns a dict with two fields:
            success: Ammount of new measurements succesfully saved
            error:   Ammount of undetermined measurements
    """
    # from apps.api.fp_tables_api.utils import update_measurement_table

    treshold = timezone.now() - timezone.timedelta(days=1)
    # Get interesting measurements:
    fpMeasurements =    FastPath.objects\
                                .exclude(data_ready=FastPath.DataReady.READY)\
                                .exclude(data_ready=FastPath.DataReady.DEAD)\
                                .filter(catch_date__lt=treshold)

    # Filter by test_name
    if test_name:
        fpMeasurements = fpMeasurements.filter(test_name=test_name)

    # Limit to n_measurements
    if n_measurements:
        fpMeasurements = fpMeasurements[:n_measurements]

    measurements_url = "https://api.ooni.io/api/v1/measurements"

    # Save the measurements at the end
    # in case something fails
    meas_to_save = []       # Measurements with errors
    new_measurements = []   # New Measurements with their fp equivalent
    for fp in fpMeasurements:

        # Ask for the measurement based on its report id

        try:
            req = requests.get(
                measurements_url,
                params={
                    "report_id" : fp.report_id,
                    "input" : fp.input,
                    'test_name' : fp.test_name,
                    "limit":5000,
                })
        except:
            print("Could not find measurement: ", fp.input, ", ", fp.measurement_start_time)
            print("Unvalid GET request")
            fp.report_ready = None
            meas_to_save.append(fp)
            continue

        # If the measurement could not be found, search for it later
        if req.status_code != 200:
            print("Could not find measurement: ", fp.input, ", ", fp.measurement_start_time)
            print("Report not found")
            fp.report_ready = None
            meas_to_save.append(fp)
            continue

        data = req.json()
        data = data.get("results")

        if data == None:
            raise AttributeError("Unexpected data format from Ooni")

        measurement = [d for d in data if 
                        dateparse.parse_datetime(d.get("measurement_start_time")) == fp.measurement_start_time or
                        dateparse.parse_datetime(d.get("measurement_start_time")) == (fp.measurement_start_time + datetime.timedelta(days=4)) # PQC
                        ]

        print("data: ", data) 

        if len(measurement) != 1:
            print("Could not find measurement: ", fp.input, ", ", fp.measurement_start_time)
            print("Too many equal measurements: ", len(measurement))
            fp.report_ready = None
            meas_to_save.append(fp)
            continue

        # Get the measurement data
        measurement = measurement[0]

        # Update the url if it has changed
        new_url = measurement.get("measurement_url")
        if new_url != fp.measurement_url and new_url != None:
            fp.measurement_url = new_url

        # Request data for the Measurement Table
        try:
            req = requests.get(fp.measurement_url)
        except:
            print("Could not find measurement: ", fp.input, ", ", fp.measurement_start_time)
            print("invalid GET request fetching measurement data")
            fp.report_ready = None
            meas_to_save.append(fp)
            continue

        # If data could not be found or a network error ocurred,
        # mark this as incomplete and process the following measurements
        if req.status_code != 200:
            print("Could not find measurement: ", fp.input, ", ", fp.measurement_start_time)
            print("Could not fetch measurement data")
            fp.report_ready = None
            meas_to_save.append(fp)
            continue

        data = req.json()

        # Update the id if it has changed
        new_id = data.get("id")
        if new_id != fp.tid and new_id != None:
            fp.tid = new_id

        # If there's no id, then we have some unconsistent data. UPDATE: or not, because now is not provided
        # if new_id == None:
        #     print("Could not find measurement: ", fp.input, ", ", fp.measurement_start_time)
        #     print("Measurement does not provides any id")
        #     fp.report_ready = None
        #     meas_to_save.append(fp)
        #     continue    

        new_measurement = RawMeasurement(
            input=data['input'],
            report_id= data['report_id'],
            report_filename= data.get('report_filename','NO_AVAILABLE'), #
            options= data.get('options', "NO_AVAILABLE"), #
            probe_cc= data.get('probe_cc','VE'),
            probe_asn= data['probe_asn'],
            probe_ip=data.get('probe_ip'),
            data_format_version= data['data_format_version'],
            test_name= data['test_name'],
            test_start_time= data.get('test_start_time'),
            measurement_start_time= data['measurement_start_time'],
            test_runtime= data.get('test_runtime'),
            test_helpers= data.get('test_helpers',"NO_AVAILABLE"),
            software_name= data['software_name'],
            software_version= data['software_version'],
            test_version= data['test_version'],
            bucket_date= data.get('bucket_date'), #
            test_keys= data['test_keys'],
            annotations= data['annotations']
        )
        
        fp.report_ready = True
        new_measurements.append((new_measurement, fp))
        #new_measurements.append(new_measurement)
        #meas_to_save.append(fp)

    results = {
        "success" : 0, # ammount of succesfully saved new measurements
        "error"   : 0, # ammount of undetermined measurements
    }
    for fp in meas_to_save:
        results["error"] += 1
        if retrys >= 0 and fp.trys > retrys:
            fp.data_ready = FastPath.DataReady.DEAD
        else:
            fp.data_ready = FastPath.DataReady.UNDETERMINED
            fp.trys += 1

        fp.save()

    for (meas, fp) in new_measurements:
        try:
            meas.save()
            fp.data_ready = FastPath.DataReady.READY
            results["success"] += 1

        except Exception as e:
            print("Could not save measurement: ", fp.input, ", ", fp.measurement_start_time)
            print("Could not save measurement: ", meas.input, ", ", meas.measurement_start_time)
            print("Error", e)
            fp.report_ready = None
            # set this measurement as undetermined and increse its number of trys
            fp.data_ready = FastPath.DataReady.UNDETERMINED
            fp.trys += 1

            results["error"] += 1

        try:
            fp.save()
        except:
            pass

    return results
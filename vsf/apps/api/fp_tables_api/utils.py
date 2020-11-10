"""
    Additional functionality to perform validations in the post request
"""

from rest_framework.response    import Response
from rest_framework.generics    import  (
    ListCreateAPIView,
    RetrieveUpdateAPIView,
)
from rest_framework.status      import  (
    HTTP_200_OK, 
    HTTP_201_CREATED, 
    HTTP_204_NO_CONTENT, 
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_412_PRECONDITION_FAILED
)
import django.utils.timezone    as timezone
import django.utils.dateparse   as dateparse
from   django.shortcuts         import render
from   rest_framework.views     import APIView

# Third party imports
import time
import json
import requests
import datetime
import collections
from urllib.parse   import urlencode

# Local imports
from apps.main.sites.models             import URL
from .                                  import utils
from apps.main.ooni_fp.fp_tables.models import FastPath
from apps.main.measurements.models      import RawMeasurement

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

def request_fp_data(since: str, until: str, from_fastpath = True) -> (int, [str]):
    """
        Given the start and end date for a set of measurements, 
        perform a get request to ooni in order to get the 
        recent fast path objects and store them in the database. 
        
        The function returns the status code for the ooni request 
        and a list of tid corresponding to the actually added measurements. 

        both the since and until date should be in the following format:
        YYYY-mm-dd.
    """
    # Data validation
    data = {
        'probe_cc': 'VE', # In case we want to add other countries
        'since': since,
        'until': until,
        'limit': 1000
    }

    # Check if the post data is valid:
    if not checkPostData(data):
        raise AttributeError("Unvalid input arguments. Given: \n" + 
                                "   Since: " + since + "\n" + 
                                "   Until: " + until)

    # Perform a get request from Ooni
    next_url = 'https://api.ooni.io/api/v1/measurements?' + urlencode(data)
        
    objects = [] # List of measurement objects obtained
    while next_url != None:
        try:
            # If it wasn't able to get the next page data, just store the currently added data
            # @TODO we have to think what to do in this cases
            req = requests.get(next_url)
            assert(req.status_code == 200)
        except:
            break

        # Since everything went ok, we get the data in json format
        data = req.json()
        metadata = data['metadata'] 
        next_url = metadata.get('next_url')
        if from_fastpath:
            results = filter(
            # since we just care about fast path data, we filter the ones whose measurement_id begins with
            # 'temp-fid' according to what Federico (from ooni) told us
            # UPDATE: by today, measurement_id is not reported by the ooni queries, so 
            # we can't rely on it to check whether a measurement comes from the fastpath or not.
            # @TODO               
            lambda res: 
                    res.get('measurement_id',"").startswith("temp-fid"), 
                data['results']
            )
        else:
            results = data['results']

        for result in results:

            fp = FastPath(
                anomaly = result['anomaly'],
                confirmed = result['confirmed'],
                failure = result['failure'],
                input= str(result['input']),
                tid= result.get('measurement_id'),
                measurement_start_time=result['measurement_start_time'],
                measurement_url=result['measurement_url'],
                probe_asn= result['probe_asn'],
                probe_cc= result['probe_cc'],
                report_id= result['report_id'],
                scores=result['scores'],
                test_name= result['test_name'],
            )
            URL.objects.get_or_create(url=fp.input)
            objects.append(fp)
    

    # Save only if this measurement does not exists    
    saved_measurements = []
    for fp in objects:
        try: 
            FastPath.objects.get(
                        measurement_start_time=fp.measurement_start_time, 
                        input=fp.input,
                        report_id=fp.report_id,
                        test_name=fp.test_name)
        except:
            fp.save()
            saved_measurements.append(fp.id)
    
    return (req.status_code, saved_measurements)


def update_measurement_table(
                            n_measurements : int = None,
                            test_name      : str = None
                            ):
    """
        Store at the most 'n_measurements' ready measurements of type 'test_name' 
        into the  database. Defaults to all measurements yo can add, for
        any kind of measurement. 

        This function will update the Measurement table
        and the fast path table depending on the availability of 
        measurements in the fast path table.
        
        Get every measurement in the database whose report_ready
        is set to false or None, and whose catch_date - now > 24h. 
        perform a request for the measurementl.
        If the measurement is available, change report_ready to true and
        create a new measurement object in the database. Otherwise, 
        report_ready is set to null
    """
    # from apps.api.fp_tables_api.utils import update_measurement_table

    treshold = timezone.now() - timezone.timedelta(days=1)
    # Get interesting measurements:
    fpMeasurements =    FastPath.objects\
                                .exclude(report_ready=True)\
                                .filter(measurement_start_time__lt=treshold)

    # Filter by test_name
    if test_name:
        fpMeasurements = fpMeasurements.filter(test_name=test_name)

    # Limit to n_measurements
    if n_measurements:
        fpMeasurements = fpMeasurements[:n_measurements]
    
    measurements_url = "https://api.ooni.io/api/v1/measurements"

    # Save the measurements at the end 
    # in case something fails 
    meas_to_save = []
    new_measurements = []
    for fp in fpMeasurements:
        
        # Ask for the measurement based on its report id
        # Note that the 'limit' number needs to be high enough, so we don't need to paginate.
        try:
            req = requests.get(
                measurements_url, 
                params={
                    "report_id" : fp.report_id,
                    "input" : fp.input,
                    "limit":5000 
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
        
        measurement = filter(
            lambda d: 
                dateparse.parse_datetime(d.get("measurement_start_time")) == fp.measurement_start_time, 
            data) # Search for the one whose start_time matches with this measurement's start time

        measurement = list(measurement)
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
            
        # If there's no id, then we have some unconsistent data
        if new_id == None:
            print("Could not find measurement: ", fp.input, ", ", fp.measurement_start_time)
            print("Measurement does not provides any id")
            fp.report_ready = None
            meas_to_save.append(fp)
            continue

        new_measurement = RawMeasurement(
            id=data['id'],
            input=data['input'],
            report_id= data['report_id'],
            report_filename= data['report_filename'],
            options= data['options'],
            probe_cc= data['probe_cc'],
            probe_asn= data['probe_asn'],
            probe_ip=data['probe_ip'],
            data_format_version= data['data_format_version'],
            test_name= data['test_name'],
            test_start_time= data['test_start_time'],
            measurement_start_time= data['measurement_start_time'],
            test_runtime= data['test_runtime'],
            test_helpers= data['test_helpers'],
            software_name= data['software_name'],
            software_version= data['software_version'],
            test_version= data['test_version'],
            bucket_date= data['bucket_date'],
            test_keys= data['test_keys'],
            annotations= data['annotations']
        )
        fp.report_ready = True
        new_measurements.append((new_measurement, fp))
        #new_measurements.append(new_measurement)
        #meas_to_save.append(fp)

    for fp in meas_to_save:
        fp.save()
    
    for (meas, fp) in new_measurements:
        try:
            meas.save()
        except Exception as e:
            print("Could not save measurement: ", fp.input, ", ", fp.measurement_start_time)
            print("Could not save measurement: ", meas.input, ", ", meas.measurement_start_time)
            print("Error", e)
            fp.report_ready = None

        try:
            fp.save() 
        except:
            pass
